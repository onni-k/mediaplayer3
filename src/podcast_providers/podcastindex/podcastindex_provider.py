# ==============================================================================
#
# MediaPlayer3
#
# File        : podcastindex_provider.py
#
# Description :
#
#     PodcastIndexProvider
#
#     A concrete podcast provider (see PODCAST_PROVIDER_SPEC.md) for
#     the Podcast Index API (https://podcastindex.org). Confirmed
#     against the project's own reference example
#     (python-podcastindex-org-example-master/podcasting-index.py) and
#     the official docs
#     (https://podcastindex-org.github.io/docs-api/#overview--example-code).
#
#     Authentication is Amazon-S3-style, per Podcast Index's own docs:
#     the Authorization header is a SHA-1 hash of (api_key + api_secret
#     + unix_timestamp), sent alongside X-Auth-Date (the timestamp) and
#     X-Auth-Key (the api_key). Uses urllib (stdlib) rather than the
#     reference example's `requests` dependency, matching every other
#     network call in this project -- no third-party packages are
#     assumed to be installed on the Enigma2 box.
#
#     Credentials: resolved from Settings (podcast.podcastindex_api_key/
#     podcast.podcastindex_api_secret, user's own free key from
#     https://api.podcastindex.org/signup) when the user has provided
#     one, falling back to a bundled default pair otherwise so podcast
#     search works out of the box without requiring signup first. The
#     bundled default is lightly obfuscated (XOR + base64) rather than
#     stored as a plain string -- deliberately NOT real security: this
#     project is publicly distributed (Build 0010 -> 1.0-beta is headed
#     for public testing), so anyone who reads this source file has
#     the deobfuscation logic too. This only avoids the credentials
#     being an immediately greppable plaintext string; a user's own
#     key (Settings) is the only genuinely private option, and using
#     one also avoids every MediaPlayer3 installation sharing (and
#     potentially exhausting) the same bundled key's rate limit.
#
# Implements :
#
#     Podcast provider interface (PODCAST_PROVIDER_SPEC.md):
#     searchPodcasts(query), getPodcast(podcast_id),
#     getEpisodes(podcast_id), refreshPodcast(podcast_id).
#
# Project :
#
#     MediaPlayer3
#
# License :
#
#     GPL-2.0-or-later
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-08-08  Build 0010 (round 2)
#   - Initial version. Auth scheme and endpoint shapes confirmed
#     against the project's own reference example and the official
#     API docs; not yet confirmed against a real device (no network
#     access from the development environment) -- see this file's own
#     exception handling, designed so a failure here is reported to
#     PodcastManager, not a crash.
# ------------------------------------------------------------------------------

"""
podcastindex_provider -- a concrete podcast provider for the Podcast
Index API (https://podcastindex.org), implementing the interface
PODCAST_PROVIDER_SPEC.md defines for PodcastManager.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from ...config import config_manager
from ...logger import logger

API_BASE_URL = "https://api.podcastindex.org/api/1.0"

USER_AGENT = "MediaPlayer3-PodcastIndex/0.1"

REQUEST_TIMEOUT_SECONDS = 10

# Build 0010 -- light obfuscation only, see this file's own header for
# why. XOR against a fixed pad, then base64. PAD is not a secret in
# any real sense -- it's here purely so the credentials below aren't
# stored as plaintext strings in the source.
_OBFUSCATION_PAD = b"MediaPlayer3-PodcastIndex-Build0010"

# Bundled default credentials (obfuscated -- see _deobfuscate() and
# this file's own header). A user's own key/secret in Settings always
# takes priority when provided; see _resolveCredentials().
_DEFAULT_API_KEY_OBFUSCATED = "Fyc3LyUEODQ8MSpxGhQlMlEqJy0="
_DEFAULT_API_SECRET_OBFUSCATED = "BycCKDMXLgwzN0sHYDI9KholI005MDcVGXo0PjtPR3wTBGR4MgwaNQ=="


def _deobfuscate(value: str) -> str:
    """
    Reverses the XOR+base64 obfuscation described in this file's own
    header. Not real encryption -- see that header for why this is
    only meant to avoid a plaintext credential string, not to provide
    genuine secrecy in a publicly distributed plugin.
    """

    xored = base64.b64decode(value)

    data = bytes(byte ^ _OBFUSCATION_PAD[i % len(_OBFUSCATION_PAD)] for i, byte in enumerate(xored))

    return data.decode("utf-8")


class PodcastIndexProvider:
    """
    Podcast Index provider. See PODCAST_PROVIDER_SPEC.md for the
    interface this implements and PodcastManager for how it's used.
    """

    def __init__(self) -> None:

        self._log("Created")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[PodcastIndex] %s", message)

    # ------------------------------------------------------------------
    # Credentials (PODCAST_PROVIDER_SPEC.md "Authentication")
    # ------------------------------------------------------------------

    def _resolveCredentials(self) -> Optional[tuple]:
        """
        Returns (api_key, api_secret), preferring the user's own
        Settings-provided credentials (Settings -> Podcast Index API
        key/secret) over the bundled default. Returns None only if
        neither a user-provided pair nor the bundled default can be
        resolved (the bundled default deobfuscating cleanly is the
        only way this could fail, and would indicate a bug in this
        file, not a runtime condition -- still handled defensively
        rather than assumed).
        """

        user_key = config_manager.get("podcast.podcastindex_api_key", "")

        user_secret = config_manager.get("podcast.podcastindex_api_secret", "")

        if user_key and user_secret:

            return user_key, user_secret

        try:
            return _deobfuscate(_DEFAULT_API_KEY_OBFUSCATED), _deobfuscate(_DEFAULT_API_SECRET_OBFUSCATED)

        except Exception as error:

            # Build 0010 -- PODCAST_PROVIDER_SPEC.md "Authentication":
            # "Provider credentials shall not be written to normal
            # application logs." Deliberately does not include
            # `error` itself here, in case a future change to the
            # obfuscation format made it include fragment data.
            self._log("Unable to resolve bundled default credentials.")

            return None

    # ------------------------------------------------------------------

    def _buildAuthHeaders(self, api_key: str, api_secret: str) -> Dict[str, str]:
        """
        Podcast Index's own Amazon-S3-style scheme, confirmed against
        the project's reference example
        (python-podcastindex-org-example-master/podcasting-index.py)
        and the official docs: Authorization is sha1(api_key +
        api_secret + unix_timestamp), sent alongside X-Auth-Date (the
        timestamp) and X-Auth-Key (the api_key).
        """

        epoch_time = str(int(time.time()))

        data_to_hash = api_key + api_secret + epoch_time

        authorization = hashlib.sha1(data_to_hash.encode("utf-8")).hexdigest()

        return {
            "X-Auth-Date": epoch_time,
            "X-Auth-Key": api_key,
            "Authorization": authorization,
            "User-Agent": USER_AGENT,
        }

    # ------------------------------------------------------------------
    # Network (PODCAST_PROVIDER_SPEC.md "Network Communication",
    # "Error Handling")
    # ------------------------------------------------------------------

    def _apiGet(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Performs one authenticated GET against the Podcast Index API.
        Never raises -- returns None (and logs) for every failure
        category PODCAST_PROVIDER_SPEC.md's "Error Handling" section
        lists that a single request can hit: network unavailable,
        timeout, HTTP failure, invalid response, invalid JSON,
        authentication failure, rate limiting. Podcast Index itself
        also uses HTTP 200 with a JSON "status": "false" body for some
        failure cases (per the official docs) -- checked explicitly,
        not just the HTTP status code.
        """

        credentials = self._resolveCredentials()

        if credentials is None:

            self._log(f"Request to {endpoint} failed: no credentials available.")

            return None

        api_key, api_secret = credentials

        url = f"{API_BASE_URL}/{endpoint}"

        if params:

            url += "?" + urllib.parse.urlencode(params)

        headers = self._buildAuthHeaders(api_key, api_secret)

        request = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:

                raw_data = response.read().decode("utf-8")

        except urllib.error.HTTPError as error:

            # Build 0010 -- Podcast Index returns 401 for bad
            # credentials/expired X-Auth-Date, 429 for rate limiting;
            # both are genuine provider-level conditions
            # PODCAST_PROVIDER_SPEC.md expects to be reported rather
            # than crash, not caller bugs to raise on.
            self._log(f"Request to {endpoint} failed: HTTP {error.code}.")

            return None

        except (urllib.error.URLError, TimeoutError, OSError) as error:

            self._log(f"Request to {endpoint} failed: {error}.")

            return None

        try:
            data = json.loads(raw_data)

        except ValueError as error:

            self._log(f"Request to {endpoint} returned invalid JSON: {error}.")

            return None

        if not isinstance(data, dict):

            self._log(f"Request to {endpoint} returned an unexpected response shape.")

            return None

        if str(data.get("status", "true")).lower() == "false":

            self._log(f"Request to {endpoint} reported failure: {data.get('description', 'no description')}.")

            return None

        return data

    # ------------------------------------------------------------------
    # Provider interface (PODCAST_PROVIDER_SPEC.md)
    # ------------------------------------------------------------------

    def searchPodcasts(self, query: str) -> List[Dict[str, Any]]:
        """
        Returns a list of podcasts (common data model, see
        PODCAST_PROVIDER_SPEC.md "Common Podcast Data") matching
        `query`. Always returns a list -- empty on any failure or
        empty result, per spec ("Search failures shall be reported to
        PodcastManager without terminating MediaPlayer3" and "An
        empty result is a valid response").
        """

        if not query or not query.strip():
            return []

        data = self._apiGet("search/byterm", {"q": query})

        if data is None:
            return []

        feeds = data.get("feeds", [])

        if not isinstance(feeds, list):

            self._log("searchPodcasts(): 'feeds' field was not a list.")

            return []

        return [self._convertFeedToPodcast(feed) for feed in feeds if isinstance(feed, dict)]

    # ------------------------------------------------------------------

    def getPodcast(self, podcast_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns detailed information for one podcast (common data
        model), or None if it can't currently be retrieved --
        PODCAST_PROVIDER_SPEC.md: "Missing fields shall not be treated
        as provider failure", but a wholly failed lookup is still a
        None, for PodcastManager to handle (e.g. keep showing
        previously cached subscription data).
        """

        data = self._apiGet("podcasts/byfeedid", {"id": podcast_id})

        if data is None:
            return None

        feed = data.get("feed")

        if not isinstance(feed, dict):

            self._log(f"getPodcast({podcast_id}): no 'feed' in response.")

            return None

        return self._convertFeedToPodcast(feed)

    # ------------------------------------------------------------------

    def getEpisodes(self, podcast_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Returns episodes for `podcast_id` (common data model, see
        PODCAST_PROVIDER_SPEC.md "Episode Retrieval"). Episodes
        without a usable playback URL are omitted here rather than
        left for PodcastManager to filter -- spec: "Episodes without a
        valid playback URL may be returned as metadata, but
        PodcastManager shall not offer them as playable items"; this
        provider only ever returns the playable set, keeping that
        filtering decision in one place.
        """

        data = self._apiGet("episodes/byfeedid", {"id": podcast_id, "max": max_results})

        if data is None:
            return []

        items = data.get("items", [])

        if not isinstance(items, list):

            self._log(f"getEpisodes({podcast_id}): 'items' field was not a list.")

            return []

        episodes = []

        for item in items:

            if not isinstance(item, dict):
                continue

            episode = self._convertItemToEpisode(item, podcast_id)

            if episode.get("playback_url"):

                episodes.append(episode)

        return episodes

    # ------------------------------------------------------------------

    def refreshPodcast(self, podcast_id: str) -> Optional[Dict[str, Any]]:
        """
        Re-fetches a podcast's own metadata -- Podcast Index has no
        separate "refresh" endpoint, so this is the same lookup as
        getPodcast(); kept as its own method to match the interface
        PODCAST_MANAGER_SPEC.md's "Refresh Behaviour" expects
        (metadata + episode list both refreshed -- PodcastManager
        calls getEpisodes() separately for the episode half).
        """

        return self.getPodcast(podcast_id)

    # ------------------------------------------------------------------
    # Data conversion (PODCAST_PROVIDER_SPEC.md "Common Podcast Data")
    # ------------------------------------------------------------------

    def _convertFeedToPodcast(self, feed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts one Podcast Index "feed" object into the common
        podcast dict PODCAST_PROVIDER_SPEC.md/PODCAST_MANAGER_SPEC.md
        describe. Missing fields become "" rather than being omitted
        or raising -- spec: "Unavailable fields shall remain empty
        rather than causing an error."
        """

        return {
            "podcast_id": str(feed.get("id", "")),
            "title": feed.get("title", "") or "",
            "description": feed.get("description", "") or "",
            "author": feed.get("author", "") or "",
            "artwork": feed.get("artwork") or feed.get("image", "") or "",
            "language": feed.get("language", "") or "",
            "category": self._extractPrimaryCategory(feed),
            "feed_url": feed.get("url", "") or "",
            "website_url": feed.get("link", "") or "",
        }

    # ------------------------------------------------------------------

    def _extractPrimaryCategory(self, feed: Dict[str, Any]) -> str:
        """
        Podcast Index returns categories as a {"id": "name", ...}
        object rather than a simple field -- this just picks the
        first name, since PODCAST_PROVIDER_SPEC.md's common data model
        only asks for a single "Category" string, not the full set.
        """

        categories = feed.get("categories")

        if isinstance(categories, dict) and categories:

            return next(iter(categories.values()), "")

        return ""

    # ------------------------------------------------------------------

    def _convertItemToEpisode(self, item: Dict[str, Any], podcast_id: str) -> Dict[str, Any]:
        """
        Converts one Podcast Index episode "item" into the common
        episode dict. "enclosureUrl" is the actual audio file URL --
        mapped to both episode_url and playback_url since Podcast
        Index doesn't distinguish a separate "episode page" URL for
        most feeds; "link" (the episode's own web page, when present)
        is preferred for episode_url where available.
        """

        enclosure_url = item.get("enclosureUrl", "") or ""

        return {
            "episode_id": str(item.get("id", "")),
            "podcast_id": str(podcast_id),
            "title": item.get("title", "") or "",
            "description": item.get("description", "") or "",
            "published": item.get("datePublished"),
            "duration": item.get("duration"),
            "artwork": item.get("image") or item.get("feedImage", "") or "",
            "episode_url": item.get("link", "") or enclosure_url,
            "playback_url": enclosure_url,
        }


# ------------------------------------------------------------------------------
# Shared provider instance
# ------------------------------------------------------------------------------

podcastindex_provider = PodcastIndexProvider()

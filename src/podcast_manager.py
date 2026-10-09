# ==============================================================================
#
# MediaPlayer3
#
# File        : podcast_manager.py
#
# Description :
#
#     PodcastManager
#
#     Podcast discovery, subscription and episode management
#     (PODCAST_MANAGER_SPEC.md). Follows InternetRadioManager's own
#     established pattern closely (local JSON persistence under
#     storage_manager's own path convention, load/save helpers that
#     never raise, a coordinator that owns application state while
#     delegating actual external communication to a provider).
#
#     PodcastManager does not implement podcast provider network
#     communication itself (podcast_providers/podcastindex/ does that
#     -- see PODCAST_PROVIDER_SPEC.md) and does not implement
#     playback or user interface presentation (PodcastScreen, not yet
#     built as of this file's creation, will do that -- see
#     PODCAST_SCREEN_SPEC.md).
#
# Implements :
#
#     PODCAST_MANAGER_SPEC.md
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
#   - Initial version. Subscription persistence and provider
#     coordination confirmed via stub-environment testing; not yet
#     exercised by a real PodcastScreen (not yet built).
# ------------------------------------------------------------------------------

"""
podcast_manager -- podcast discovery, subscription and episode
management (PODCAST_MANAGER_SPEC.md). See podcast_providers/ for the
actual external-service communication this delegates to.
"""

from __future__ import annotations

import html
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from .logger import logger
from .podcast_providers.podcastindex.podcastindex_provider import podcastindex_provider
from .storage import storage_manager


class PodcastManager:
    """
    Owns podcast application state: subscriptions (persisted
    locally) and coordination of the podcast provider for search and
    episode/metadata retrieval. See PODCAST_MANAGER_SPEC.md
    "Responsibilities Summary".
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        # Build 0010 -- a single provider for now
        # (PODCAST_PROVIDER_SPEC.md "The initial Build 0010
        # implementation may use a single provider"), referenced by a
        # short name so a future multi-provider PodcastManager could
        # route by it without PodcastScreen needing to change at all.
        self._provider = podcastindex_provider

        self._subscriptions: List[Dict[str, Any]] = []

        # Build 0010 -- podcast_id -> list of episode dicts, populated
        # by getEpisodes() as podcasts are actually browsed. Not
        # persisted (PODCAST_MANAGER_SPEC.md "Subscription
        # Persistence" only requires the subscription itself to
        # survive, not its full episode list) -- refetched from the
        # provider each time a subscribed podcast's episodes are
        # needed, same as a search result would be.
        self._episode_cache: Dict[str, List[Dict[str, Any]]] = {}

        # Round 231: playback_url -> {"title", "podcast", "description"}
        # for episodes the user has played or added to a playlist, so
        # MainScreen can show the episode description while it plays
        # (a playing queue only carries bare URLs). Persisted, capped
        # at EPISODE_INFO_LIMIT entries (oldest dropped first).
        self._episode_info: Dict[str, Dict[str, str]] = {}

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Podcast] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._subscriptions = self._loadJSON(self._subscriptionsPath(), default=[])

        loaded_info = self._loadJSON(self._episodeInfoPath(), default={})

        self._episode_info = loaded_info if isinstance(loaded_info, dict) else {}

        self._initialized = True

        self._log(f"Ready ({len(self._subscriptions)} subscription(s))")

    # ------------------------------------------------------------------
    # Local storage
    # ------------------------------------------------------------------

    def _subscriptionsPath(self) -> str:
        return os.path.join(storage_manager.getPodcastPath(), "subscriptions.json")

    def _episodeInfoPath(self) -> str:
        return os.path.join(storage_manager.getPodcastPath(), "episode_info.json")

    # ------------------------------------------------------------------

    def _loadJSON(self, path: str, default: Any) -> Any:

        try:
            with open(path, encoding="utf-8") as handle:

                return json.load(handle)

        except (OSError, ValueError) as error:

            logger.verbose(f"[Podcast] Unable to read {path}: {error}")

            return default

    # ------------------------------------------------------------------

    def _saveJSON(self, path: str, data: Any) -> bool:

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding="utf-8") as handle:

                json.dump(data, handle, indent=2, ensure_ascii=False)

            return True

        except OSError as error:

            self._log(f"Unable to save {path}: {error}")

            return False

    # ------------------------------------------------------------------
    # Discovery (PODCAST_MANAGER_SPEC.md "Podcast Browser" -- Available
    # Podcasts column)
    # ------------------------------------------------------------------

    def searchPodcasts(self, query: str) -> List[Dict[str, Any]]:
        """
        Delegates to the provider. Always returns a list -- see
        PodcastIndexProvider.searchPodcasts()'s own guarantee (never
        raises, empty list on any failure).
        """

        try:
            return self._provider.searchPodcasts(query)

        except Exception as error:

            # Build 0010 -- PodcastIndexProvider.searchPodcasts()
            # itself never raises (PODCAST_PROVIDER_SPEC.md "Error
            # Handling"), but this guards PodcastManager against a
            # future/different provider that doesn't follow that
            # convention, same defense-in-depth EPGManager already
            # applies around its own provider calls.
            self._log(f"Search failed: {error}")

            return []

    def getTrendingPodcasts(self, language: str = "") -> List[Dict[str, Any]]:
        """
        Round 230: popular podcasts, optionally for one language code
        ("" = all languages). Always returns a list, never raises.
        """

        try:
            return self._provider.getTrendingPodcasts(language)

        except Exception as error:

            self._log(f"Trending fetch failed: {error}")

            return []

    # ------------------------------------------------------------------

    @staticmethod
    def filterByLanguage(podcasts: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """
        Round 230: keeps only podcasts whose own "language" field
        starts with `language` (case-insensitive, so "en" matches
        "en-US"). Empty `language` keeps everything. Podcasts with no
        language field at all are kept rather than silently dropped.
        """

        if not language:
            return podcasts

        wanted = language.lower()

        return [
            podcast
            for podcast in podcasts
            if not podcast.get("language") or podcast["language"].lower().startswith(wanted)
        ]

    # ------------------------------------------------------------------
    # Episode descriptions (round 231)
    # ------------------------------------------------------------------

    EPISODE_INFO_LIMIT = 300

    @staticmethod
    def cleanDescription(raw: str) -> str:
        """
        Round 231: podcast feeds often carry HTML in descriptions.
        Turns line-breaking tags into newlines, drops all other tags,
        unescapes entities and tidies whitespace.
        """

        text = raw or ""

        text = re.sub(r"(?i)<\s*br\s*/?>", "\n", text)

        text = re.sub(r"(?i)</\s*(p|div|li|h[1-6])\s*>", "\n\n", text)

        text = re.sub(r"<[^>]+>", "", text)

        text = html.unescape(text)

        text = re.sub(r"[ \t\r\f\v]+", " ", text)

        text = re.sub(r" ?\n ?", "\n", text)

        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    # ------------------------------------------------------------------

    def rememberEpisode(self, playback_url: str, title: str, podcast_title: str, description: str) -> None:
        """
        Round 231: remembers an episode's description under its
        playback URL (see _episode_info). Never raises.
        """

        if not playback_url:
            return

        cleaned = self.cleanDescription(description)

        if not cleaned:
            return

        try:
            self._episode_info.pop(playback_url, None)

            self._episode_info[playback_url] = {
                "title": title or "",
                "podcast": podcast_title or "",
                "description": cleaned,
            }

            while len(self._episode_info) > self.EPISODE_INFO_LIMIT:

                self._episode_info.pop(next(iter(self._episode_info)))

            self._saveJSON(self._episodeInfoPath(), self._episode_info)

        except Exception as error:

            self._log(f"rememberEpisode failed: {error}")

    # ------------------------------------------------------------------

    def getEpisodeInfo(self, playback_url) -> Optional[Dict[str, str]]:
        """
        Round 231: the remembered {"title", "podcast", "description"}
        for `playback_url`, or None.
        """

        if not playback_url:
            return None

        return self._episode_info.get(playback_url)

    # ------------------------------------------------------------------
    # Subscriptions (PODCAST_MANAGER_SPEC.md "Subscription")
    # ------------------------------------------------------------------

    def getSubscriptions(self) -> List[Dict[str, Any]]:
        """
        Returns the locally stored subscription list (Subscribed
        Podcasts column). Available even when the provider/network is
        currently unreachable -- PODCAST_MANAGER_SPEC.md "Subscription
        Persistence": "Subscriptions remain available even when the
        external podcast provider is temporarily unavailable."
        """

        return list(self._subscriptions)

    # ------------------------------------------------------------------

    def isSubscribed(self, podcast_id: str) -> bool:

        return any(entry.get("podcast_id") == podcast_id for entry in self._subscriptions)

    # ------------------------------------------------------------------

    def subscribe(self, podcast: Dict[str, Any]) -> bool:
        """
        Adds `podcast` (the common podcast dict -- see
        PODCAST_PROVIDER_SPEC.md "Common Podcast Data", typically one
        returned by searchPodcasts()) to the local subscription list
        and persists it. Does nothing (returns True) if already
        subscribed -- subscribing twice is not an error.
        """

        podcast_id = podcast.get("podcast_id")

        if not podcast_id:

            self._log("subscribe() called with no podcast_id.")

            return False

        if self.isSubscribed(podcast_id):

            return True

        entry = dict(podcast)

        entry["subscribed_at"] = time.time()

        self._subscriptions.append(entry)

        if not self._saveJSON(self._subscriptionsPath(), self._subscriptions):

            # Build 0010 -- keep the in-memory subscription even if
            # the write failed (matches InternetRadioManager's own
            # favicon-cache-write behaviour: a disk failure degrades,
            # it doesn't undo what already succeeded logically), but
            # the caller should know persistence didn't happen.
            self._log(f"Subscribed to {entry.get('title', podcast_id)}, but saving to disk failed.")

            return False

        self._log(f"Subscribed: {entry.get('title', podcast_id)}")

        return True

    # ------------------------------------------------------------------

    def unsubscribe(self, podcast_id: str) -> bool:

        before = len(self._subscriptions)

        self._subscriptions = [entry for entry in self._subscriptions if entry.get("podcast_id") != podcast_id]

        if len(self._subscriptions) == before:

            return False

        self._episode_cache.pop(podcast_id, None)

        self._saveJSON(self._subscriptionsPath(), self._subscriptions)

        self._log(f"Unsubscribed: {podcast_id}")

        return True

    # ------------------------------------------------------------------
    # Episodes (PODCAST_MANAGER_SPEC.md "Episode")
    # ------------------------------------------------------------------

    def getEpisodes(self, podcast_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Returns episodes for `podcast_id` (Episodes column, for either
        an Available or a Subscribed podcast). Cached in memory per
        podcast_id after the first successful fetch within this
        session, refetched only when `force_refresh` is set (explicit
        refresh -- PODCAST_MANAGER_SPEC.md "Refresh Behaviour") or
        nothing has been fetched yet. A failed refresh keeps whatever
        was already cached rather than clearing it -- spec: "A failed
        refresh shall not remove previously stored valid information."
        """

        if not force_refresh and podcast_id in self._episode_cache:

            return list(self._episode_cache[podcast_id])

        try:
            episodes = self._provider.getEpisodes(podcast_id)

        except Exception as error:

            self._log(f"getEpisodes({podcast_id}) failed: {error}")

            episodes = []

        if episodes:

            self._episode_cache[podcast_id] = episodes

        elif podcast_id in self._episode_cache:

            # Empty/failed refresh, but we already had something --
            # keep the old data rather than replacing it with nothing.
            return list(self._episode_cache[podcast_id])

        return list(episodes)

    # ------------------------------------------------------------------
    # Refresh (PODCAST_MANAGER_SPEC.md "Refresh Behaviour")
    # ------------------------------------------------------------------

    def refreshPodcast(self, podcast_id: str) -> bool:
        """
        Refreshes a subscribed podcast's metadata and episode list.
        Existing subscription data is preserved on failure -- only
        overwritten with genuinely new data from the provider.
        """

        try:
            updated = self._provider.refreshPodcast(podcast_id)

        except Exception as error:

            self._log(f"refreshPodcast({podcast_id}) failed: {error}")

            updated = None

        if updated is not None:

            for entry in self._subscriptions:

                if entry.get("podcast_id") == podcast_id:

                    subscribed_at = entry.get("subscribed_at")

                    entry.clear()

                    entry.update(updated)

                    entry["subscribed_at"] = subscribed_at

                    break

            self._saveJSON(self._subscriptionsPath(), self._subscriptions)

        # Episode list refresh is independent of whether the metadata
        # refresh itself succeeded -- getEpisodes() already preserves
        # previously cached data on its own failure.
        self.getEpisodes(podcast_id, force_refresh=True)

        return updated is not None

    # ------------------------------------------------------------------
    # Diagnostics (Build 0007-onward convention -- Developer Mode)
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> Dict[str, Any]:

        return {
            "provider": type(self._provider).__name__,
            "subscription_count": len(self._subscriptions),
            "subscriptions": ", ".join(entry.get("title", "?") for entry in self._subscriptions) or "None",
            "episode_cache_entries": len(self._episode_cache),
        }

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"PodcastManager(subscriptions={len(self._subscriptions)})"


# ------------------------------------------------------------------------------
# Shared manager instance
# ------------------------------------------------------------------------------

podcast_manager = PodcastManager()

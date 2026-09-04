# ==============================================================================
#
# MediaPlayer3
#
# File        : coverart_manager.py
#
# Description :
#
#     CoverArtManager
#
#     Downloads cover art for a local album (a directory of tracks)
#     from MusicBrainz + the Cover Art Archive, saving it as a
#     cover.jpg/cover.png in that directory -- the exact same
#     folder-cover convention MainScreen's own artwork resolution
#     already looks for (mainscreen.py's own COVER_ART_FILENAMES:
#     "cover.jpg", "cover.png", "folder.jpg", "folder.png"), so a
#     downloaded cover is picked up automatically the next time
#     anything in that folder plays. Never touches UI or playback
#     (matches every other *_manager.py module in this project).
#
#     Unlike lyrics (one file per track), cover art is one image per
#     album/directory -- downloadForFile() here just resolves to the
#     containing directory, using that specific file's own tags
#     rather than "whichever file happens to be found first".
#
# Implements :
#
#     Round 88 -- new Core module, mirrors lrclib_manager.py's own
#     shape and UX (round 84) for downloading cover art instead of
#     lyrics, per direct request ("kuvien lataus samalla tavalla kuin
#     sanoituksiin").
#
# Architecture :
#
#     ARCHITECTURE.md
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
# 2026-09-01  Build 0010 (device test round 88)
#   - Initial version. API usage confirmed directly from MusicBrainz's
#     and the Cover Art Archive's own official documentation (not
#     guessed, and not via the coverlovin2 reference app's own
#     approach, which depends on the third-party `musicbrainzngs`
#     library and a more involved multi-step artist/release-browsing
#     flow this project's stdlib-only policy can't use): a single
#     MusicBrainz release search combining artist and album in one
#     Lucene query (GET /ws/2/release/?query=artist:"..." AND
#     release:"..."&fmt=json), taking the top-scored result's MBID,
#     then GET https://coverartarchive.org/release/{mbid} for the
#     actual image URL (the officially documented, no-API-key-needed
#     Cover Art Archive REST API).
# ------------------------------------------------------------------------------

"""
CoverArtManager -- downloads album cover art from MusicBrainz/Cover
Art Archive for local albums (directories of tracks).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from .compatibility import compatibility
from .constants import SUPPORTED_AUDIO_EXTENSIONS
from .logger import logger
from .metadata import metadata_reader
from .project import PROJECT_NAME, VERSION

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

MUSICBRAINZ_BASE_URL = "https://musicbrainz.org/ws/2"

COVER_ART_ARCHIVE_BASE_URL = "https://coverartarchive.org"

REQUEST_TIMEOUT_SECONDS = 10

# Same folder-cover filenames MainScreen's own artwork resolution
# already looks for (mainscreen.py's own COVER_ART_FILENAMES) --
# duplicated here rather than imported, since importing a UI screen's
# class attribute into a Core manager would be the wrong direction of
# dependency for this project's own architecture (managers never
# import screens).
COVER_ART_FILENAMES = ("cover.jpg", "cover.png", "folder.jpg", "folder.png")

# MusicBrainz's own search results include a 0-100 Lucene relevance
# "score" per result -- below this, the match is too uncertain to
# trust (better to report "not found" than save the wrong album's
# cover).
MINIMUM_MATCH_SCORE = 80

# MusicBrainz asks unauthenticated clients to stay near 1 request/
# second -- only relevant for downloadForDirectory()'s own recursive,
# multi-album case (a single file/directory download is just one
# request either way). The Cover Art Archive itself documents no rate
# limit.
MUSICBRAINZ_MIN_REQUEST_INTERVAL_SECONDS = 1.1

# Round 89, per direct request (real device log showed MusicBrainz
# returning HTTP 503 -- their own standard "you're being rate
# limited, back off" response -- for the same album three times in a
# row across two separate manual download attempts, only succeeding
# on a fourth try): one automatic retry after this delay before
# giving up and reporting "temporarily busy" instead of silently
# treating a transient 503 the same as "no matching release found".
MUSICBRAINZ_RETRY_DELAY_SECONDS = 5

# Matches this project's own existing RadioBrowser/LRCLIB User-Agent
# convention exactly (internetradio_manager.py round 70,
# lrclib_manager.py round 84) -- also happens to be exactly the kind
# of descriptive, contactable User-Agent MusicBrainz's own API
# etiquette asks unauthenticated clients to send.
USER_AGENT = f"{PROJECT_NAME}/{VERSION} (Enigma2; Python/{compatibility.getPythonVersion()})"


class MusicBrainzRateLimited(Exception):
    """
    Raised internally when MusicBrainz is still returning HTTP 503
    after one automatic retry (round 89) -- kept distinct from a
    genuine "no matching release" result so callers can tell a user
    apart: "nothing found" needs no retry, "temporarily busy" does.
    """


class CoverArtManager:
    """
    Downloads album cover art from MusicBrainz/Cover Art Archive for
    a local directory of tracks.
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._last_musicbrainz_request_time = 0.0

        self._log("Created")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[CoverArt] %s", message)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def downloadForFile(self, filepath: str) -> str:
        """
        Download cover art for the album `filepath` belongs to, using
        `filepath`'s own artist/album tags specifically (not
        "whichever file in the directory happens to be found first"),
        saving to that directory. Returns one of: "saved",
        "already_has_cover", "not_found", "missing_tags", "error".
        """

        directory = os.path.dirname(filepath)

        return self._downloadForOneDirectory(directory, reference_file=filepath)

    # ------------------------------------------------------------------

    def downloadForDirectory(self, directory: str, recursive: bool = False) -> Dict[str, int]:
        """
        Download cover art for `directory` (treated as one album --
        uses its own first audio file's tags), and for every
        subdirectory that itself contains audio files too when
        `recursive` is true (same convention as LrclibManager's own
        downloadForDirectory(), round 85 -- each subdirectory is its
        own album, e.g. "Artist/Album1", "Artist/Album2"). Returns a
        dict of result code -> count.
        """

        counts: Dict[str, int] = {}

        for album_directory in self._collectAlbumDirectories(directory, recursive=recursive):

            result = self._downloadForOneDirectory(album_directory)

            counts[result] = counts.get(result, 0) + 1

        return counts

    # ------------------------------------------------------------------

    def hasSubdirectories(self, directory: str) -> bool:
        """
        Whether `directory` contains at least one subdirectory --
        used by BrowserScreen to decide whether the "also download
        cover art for subdirectories?" question is even worth asking
        (same convention as LrclibManager's own hasSubdirectories()).
        """

        try:
            return any(
                os.path.isdir(os.path.join(directory, entry)) for entry in os.listdir(directory)
            )

        except OSError as error:

            self._log(f"Unable to scan folder {directory}: {error}")

            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _downloadForOneDirectory(self, directory: str, reference_file: Optional[str] = None) -> str:

        if self._folderCoverExists(directory):

            self._log(f"Already has cover art, skipping: {directory}")

            return "already_has_cover"

        if reference_file is None:

            reference_file = self._firstAudioFile(directory)

        if reference_file is None:

            self._log(f"No audio files found, can't query MusicBrainz: {directory}")

            return "missing_tags"

        metadata = metadata_reader.read(reference_file)

        artist = metadata.get("artist")

        album = metadata.get("album")

        if not artist or artist == "Unknown" or not album or album == "Unknown":

            self._log(f"Missing artist/album tags, can't query MusicBrainz: {reference_file}")

            return "missing_tags"

        try:
            release_id = self._searchRelease(artist, album)

        except MusicBrainzRateLimited:

            self._log(f"MusicBrainz still rate-limited after retry, giving up for now: {reference_file}")

            return "rate_limited"

        if release_id is None:
            return "not_found"

        image_url = self._fetchCoverArtImageURL(release_id)

        if image_url is None:
            return "not_found"

        return self._downloadAndSaveImage(image_url, directory)

    # ------------------------------------------------------------------

    def _folderCoverExists(self, directory: str) -> bool:

        return any(os.path.isfile(os.path.join(directory, name)) for name in COVER_ART_FILENAMES)

    # ------------------------------------------------------------------

    def _firstAudioFile(self, directory: str) -> Optional[str]:

        try:
            for entry in sorted(os.listdir(directory), key=str.lower):

                if entry.startswith("."):
                    continue

                full_path = os.path.join(directory, entry)

                if os.path.isfile(full_path) and entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):

                    return full_path

        except OSError as error:

            self._log(f"Unable to scan folder {directory}: {error}")

        return None

    # ------------------------------------------------------------------

    def _collectAlbumDirectories(self, directory: str, recursive: bool = False) -> List[str]:

        directories = [directory]

        if not recursive:
            return directories

        try:
            for root, subdirectories, _files in os.walk(directory):

                subdirectories.sort(key=str.lower)

                for subdirectory in subdirectories:

                    full_path = os.path.join(root, subdirectory)

                    if not full_path.startswith("."):

                        directories.append(full_path)

        except OSError as error:

            self._log(f"Unable to scan folder {directory}: {error}")

        return directories

    # ------------------------------------------------------------------

    def _waitForMusicBrainzRateLimit(self) -> None:

        elapsed = time.monotonic() - self._last_musicbrainz_request_time

        remaining = MUSICBRAINZ_MIN_REQUEST_INTERVAL_SECONDS - elapsed

        if remaining > 0:
            time.sleep(remaining)

        self._last_musicbrainz_request_time = time.monotonic()

    # ------------------------------------------------------------------

    def _requestMusicBrainzWithRetry(self, url: str) -> Optional[str]:
        """
        Fetches `url`, retrying once after MUSICBRAINZ_RETRY_DELAY_
        SECONDS if MusicBrainz responds with HTTP 503 (round 89 --
        see this file's own change history entry for the device log
        that prompted this). Raises MusicBrainzRateLimited if it's
        still 503 after that one retry; returns None for any other
        request failure (nothing to usefully retry).
        """

        for attempt in range(2):

            self._waitForMusicBrainzRateLimit()

            logger.verbose(f"[CoverArt] MusicBrainz request\n\nURL: {url}\n")

            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})

            try:
                with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:

                    return response.read().decode("utf-8", errors="replace")

            except urllib.error.HTTPError as error:

                if error.code == 503 and attempt == 0:

                    logger.verbose(
                        f"[CoverArt] MusicBrainz rate-limited (503) -- "
                        f"retrying in {MUSICBRAINZ_RETRY_DELAY_SECONDS}s."
                    )

                    time.sleep(MUSICBRAINZ_RETRY_DELAY_SECONDS)

                    continue

                if error.code == 503:

                    logger.verbose("[CoverArt] MusicBrainz still rate-limited (503) after one retry.")

                    raise MusicBrainzRateLimited() from error

                logger.verbose(f"[CoverArt] MusicBrainz request failed: {error}")

                return None

            except (urllib.error.URLError, TimeoutError, OSError) as error:

                logger.verbose(f"[CoverArt] MusicBrainz request failed: {error}")

                return None

        return None

    # ------------------------------------------------------------------

    def _searchRelease(self, artist: str, album: str) -> Optional[str]:
        """
        GET {MUSICBRAINZ_BASE_URL}/release/?query=artist:"..." AND
        release:"..."&fmt=json -- a single combined Lucene query
        (matches MusicBrainz's own documented search syntax) rather
        than coverlovin2's own separate artist-search-then-browse-
        releases-then-fuzzy-match approach, which needs the
        `musicbrainzngs` library this project's stdlib-only policy
        can't use. Returns the top-scored result's MBID, or None if
        nothing scored high enough (MINIMUM_MATCH_SCORE) to trust.
        May raise MusicBrainzRateLimited -- see
        _requestMusicBrainzWithRetry().
        """

        query = f'artist:"{artist}" AND release:"{album}"'

        params = {"query": query, "fmt": "json", "limit": "5"}

        url = MUSICBRAINZ_BASE_URL + "/release/?" + urllib.parse.urlencode(params)

        body = self._requestMusicBrainzWithRetry(url)

        if body is None:
            return None

        try:
            data = json.loads(body)

        except ValueError as error:

            logger.verbose(f"[CoverArt] Unparseable MusicBrainz response: {error}")

            return None

        releases = data.get("releases") or []

        if not releases:

            logger.verbose(f"[CoverArt] No MusicBrainz release found for: {artist} - {album}")

            return None

        best = max(releases, key=lambda release: release.get("score", 0))

        if best.get("score", 0) < MINIMUM_MATCH_SCORE:

            logger.verbose(
                f"[CoverArt] Best MusicBrainz match scored too low "
                f"({best.get('score', 0)} < {MINIMUM_MATCH_SCORE}): {artist} - {album}"
            )

            return None

        return best.get("id")

    # ------------------------------------------------------------------

    def _fetchCoverArtImageURL(self, release_id: str) -> Optional[str]:
        """
        GET {COVER_ART_ARCHIVE_BASE_URL}/release/{release_id} --
        the officially documented Cover Art Archive REST API, no API
        key needed, no rate limit documented. Prefers the image
        marked "front": true; falls back to the first image if none
        is explicitly marked front.
        """

        url = f"{COVER_ART_ARCHIVE_BASE_URL}/release/{urllib.parse.quote(release_id, safe='')}"

        logger.verbose(f"[CoverArt] Cover Art Archive request\n\nURL: {url}\n")

        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})

        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:

                body = response.read().decode("utf-8", errors="replace")

        except urllib.error.HTTPError as error:

            if error.code == 404:

                logger.verbose(f"[CoverArt] No cover art archived for release: {release_id}")

            else:

                logger.verbose(f"[CoverArt] Cover Art Archive request failed: {error}")

            return None

        except (urllib.error.URLError, TimeoutError, OSError) as error:

            logger.verbose(f"[CoverArt] Cover Art Archive request failed: {error}")

            return None

        try:
            data = json.loads(body)

        except ValueError as error:

            logger.verbose(f"[CoverArt] Unparseable Cover Art Archive response: {error}")

            return None

        images = data.get("images") or []

        if not images:
            return None

        for image in images:

            if image.get("front"):

                return image.get("image")

        return images[0].get("image")

    # ------------------------------------------------------------------

    def _downloadAndSaveImage(self, image_url: str, directory: str) -> str:

        logger.verbose(f"[CoverArt] Downloading image\n\nURL: {image_url}\n")

        request = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})

        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:

                image_bytes = response.read()

                content_type = response.headers.get("Content-Type", "")

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as error:

            logger.verbose(f"[CoverArt] Image download failed: {error}")

            return "error"

        extension = ".png" if "png" in content_type.lower() else ".jpg"

        cover_path = os.path.join(directory, "cover" + extension)

        try:

            with open(cover_path, "wb") as cover_file:

                cover_file.write(image_bytes)

            self._log(f"Saved cover art: {cover_path}")

            return "saved"

        except OSError as error:

            self._log(f"Could not save cover art to '{cover_path}': {error}")

            return "error"

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> dict:

        return {
            "musicbrainz_base_url": MUSICBRAINZ_BASE_URL,
            "cover_art_archive_base_url": COVER_ART_ARCHIVE_BASE_URL,
            "user_agent": USER_AGENT,
        }


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

coverart_manager = CoverArtManager()

# ==============================================================================
# End of file
# ==============================================================================

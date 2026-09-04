# ==============================================================================
#
# MediaPlayer3
#
# File        : lrclib_manager.py
#
# Description :
#
#     LrclibManager
#
#     Downloads lyrics from LRCLIB (https://lrclib.net) for a single
#     local track or every track directly inside a directory, saving
#     them as a sibling .lrc (synchronized) or .txt (plain) file next
#     to the track -- the exact same sibling-file convention
#     LyricsManager already reads from (lyrics_manager.py's own
#     _siblingPath()/_getLRCLyrics()/_getPlainTextLyrics()), so a
#     downloaded file is picked up automatically the next time that
#     track plays. Never touches UI or playback (matches every other
#     *_manager.py module in this project).
#
# Implements :
#
#     Round 84 -- new Core module, first real step of the LRCLIB
#     lyrics-download feature (round 83 added the BrowserScreen
#     confirmation dialog only).
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
# 2026-09-01  Build 0010 (device test round 84)
#   - Initial version. API usage confirmed from lrcget's own Rust
#     client source and the lrclibapi Python package (both supplied
#     directly rather than guessed at): GET /api/get with artist_name/
#     track_name/album_name/duration(seconds, integer) for an exact
#     match, returning plainLyrics/syncedLyrics/instrumental in JSON;
#     404 means no match. Fuzzy /api/search fallback and the
#     publish-lyrics flow (which needs a proof-of-work challenge) are
#     both deliberately not implemented yet -- this round is
#     download-only, exact-match-only, matching what was actually
#     asked for.
# ------------------------------------------------------------------------------

"""
LrclibManager -- downloads lyrics from LRCLIB for local tracks.
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

BASE_URL = "https://lrclib.net/api"

REQUEST_TIMEOUT_SECONDS = 10

# Round 90, per direct request (a device log showed LRCLIB returning
# HTTP 503 for 20 of 673 requests in one batch download -- the same
# transient-rate-limit pattern round 89 already found and fixed for
# MusicBrainz): one automatic retry after this delay before giving up
# and reporting a distinct "temporarily busy" result instead of
# treating a transient 503 the same as a genuine request failure.
LRCLIB_RETRY_DELAY_SECONDS = 5

# Matches this project's own existing RadioBrowser User-Agent
# convention exactly (internetradio_manager.py, round 70) --
# LRCLIB's own reference client (lrcget) uses a similar
# "AppName/Version (detail)" format, recommended but not required by
# LRCLIB.
USER_AGENT = f"{PROJECT_NAME}/{VERSION} (Enigma2; Python/{compatibility.getPythonVersion()})"


class LrclibRateLimited(Exception):
    """
    Raised internally when LRCLIB is still returning HTTP 503 after
    one automatic retry (round 90, mirrors CoverArtManager's own
    MusicBrainzRateLimited from round 89) -- kept distinct from a
    genuine 404 "no lyrics for this track" so callers can tell a real
    miss apart from "temporarily busy, try again".
    """


class LrclibManager:
    """
    Downloads lyrics from LRCLIB for a local track or a whole
    directory of tracks.
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._log("Created")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Lrclib] %s", message)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def downloadForFile(self, filepath: str, mode: str = "all") -> str:
        """
        Download lyrics for a single file. `mode` (round 92, per
        direct request) is one of:
        - "all" (default): synced preferred, plain-text fallback --
          the original round-84 behaviour.
        - "synced_only": only saves a result that has synced lyrics;
          a track with plain-text-only lyrics on LRCLIB is reported as
          "not_found" rather than falling back to saving the .txt.
        - "plain_only": only ever saves plain text (as .txt), even
          for a track that also has synced lyrics available -- a
          track with no plain-text lyrics at all is "not_found" (this
          is rare in practice: LRCLIB entries with synced lyrics
          almost always carry the derived plain text too, but not
          guaranteed).
        Returns one of: "saved_synced", "saved_plain", "instrumental",
        "not_found", "already_has_lyrics", "missing_tags", "error",
        "rate_limited" -- callers translate this into a user-facing
        message themselves; kept here as plain result codes so
        downloadForDirectory() can tally them without needing its own
        copy of this logic.
        """

        if self._siblingLyricsExist(filepath):

            self._log(f"Already has lyrics, skipping: {filepath}")

            return "already_has_lyrics"

        metadata = metadata_reader.read(filepath)

        artist = metadata.get("artist")

        title = metadata.get("title")

        album = metadata.get("album")

        duration_seconds = metadata.get("duration_seconds")

        if not artist or artist == "Unknown" or not title or title == "Unknown":

            self._log(f"Missing artist/title tags, can't query LRCLIB: {filepath}")

            return "missing_tags"

        try:
            response = self._fetchLyrics(
                title,
                artist,
                album if album and album != "Unknown" else "",
                duration_seconds,
            )

        except LrclibRateLimited:

            self._log(f"LRCLIB still rate-limited after retry, giving up for now: {filepath}")

            return "rate_limited"

        if response is None:
            return "error"

        if response.get("instrumental"):
            return "instrumental"

        synced_lyrics = response.get("syncedLyrics")

        plain_lyrics = response.get("plainLyrics")

        if mode == "synced_only":

            if synced_lyrics:

                self._saveSibling(filepath, ".lrc", synced_lyrics)

                return "saved_synced"

            return "not_found"

        if mode == "plain_only":

            if plain_lyrics:

                self._saveSibling(filepath, ".txt", plain_lyrics)

                return "saved_plain"

            return "not_found"

        if synced_lyrics:

            self._saveSibling(filepath, ".lrc", synced_lyrics)

            return "saved_synced"

        if plain_lyrics:

            self._saveSibling(filepath, ".txt", plain_lyrics)

            return "saved_plain"

        return "not_found"

    # ------------------------------------------------------------------

    def downloadForDirectory(self, directory: str, recursive: bool = False, mode: str = "all") -> Dict[str, int]:
        """
        Download lyrics for every audio file directly inside
        `directory`, and inside every subdirectory too when
        `recursive` is true (round 85, per direct request -- asked
        as a separate yes/no question by the caller before this is
        called, not decided here). `mode` (round 92) is passed
        straight through to downloadForFile() for every file -- see
        its own docstring for the three modes. Non-recursive by
        default, matching Browser's own directory scope elsewhere (its
        file preview and "Add entire directory to playlist" both work
        one level at a time; subdirectories are browsed into
        separately). Returns a dict of result code -> count, e.g.
        {"saved_synced": 3, "not_found": 2}.
        """

        counts: Dict[str, int] = {}

        for filepath in self._collectAudioFiles(directory, recursive=recursive):

            result = self.downloadForFile(filepath, mode=mode)

            counts[result] = counts.get(result, 0) + 1

        return counts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _siblingLyricsExist(self, filepath: str) -> bool:

        base, _extension = os.path.splitext(filepath)

        return os.path.isfile(base + ".lrc") or os.path.isfile(base + ".txt")

    # ------------------------------------------------------------------

    def _saveSibling(self, filepath: str, extension: str, text: str) -> bool:

        base, _extension = os.path.splitext(filepath)

        sibling_path = base + extension

        try:

            with open(sibling_path, "w", encoding="utf-8") as sibling_file:

                sibling_file.write(text)

            self._log(f"Saved lyrics: {sibling_path}")

            return True

        except OSError as error:

            self._log(f"Could not save lyrics to '{sibling_path}': {error}")

            return False

    # ------------------------------------------------------------------

    def _collectAudioFiles(self, directory: str, recursive: bool = False) -> List[str]:

        collected = []

        try:
            if recursive:

                for root, _directories, files in os.walk(directory):

                    for entry in sorted(files, key=str.lower):

                        if entry.startswith("."):
                            continue

                        if entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):

                            collected.append(os.path.join(root, entry))

            else:

                for entry in sorted(os.listdir(directory), key=str.lower):

                    if entry.startswith("."):
                        continue

                    full_path = os.path.join(directory, entry)

                    if os.path.isfile(full_path) and entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):

                        collected.append(full_path)

        except OSError as error:

            self._log(f"Unable to scan folder {directory}: {error}")

        return collected

    # ------------------------------------------------------------------

    def hasSubdirectories(self, directory: str) -> bool:
        """
        Whether `directory` contains at least one subdirectory --
        used by BrowserScreen to decide whether the "also download
        subdirectories?" question (round 85) is even worth asking.
        """

        try:
            return any(
                os.path.isdir(os.path.join(directory, entry)) for entry in os.listdir(directory)
            )

        except OSError as error:

            self._log(f"Unable to scan folder {directory}: {error}")

            return False

    # ------------------------------------------------------------------

    def _fetchLyrics(
        self,
        title: str,
        artist: str,
        album: str,
        duration_seconds: Optional[float],
    ) -> Optional[Dict[str, Any]]:
        """
        GET {BASE_URL}/get -- exact-match lookup by track/artist/
        album/duration. Returns the parsed JSON response dict, or a
        synthetic "nothing found" dict on a 404 (kept as a normal
        return value rather than an error -- "no lyrics for this
        track" is an expected, common outcome, not a failure), or
        None if the request itself failed (network error, unparsable
        response, ...). Retries once after LRCLIB_RETRY_DELAY_SECONDS
        on HTTP 503 (round 90 -- see this file's own change history
        entry for the device log that prompted this); raises
        LrclibRateLimited if it's still 503 after that retry.
        """

        params: Dict[str, str] = {
            "track_name": title,
            "artist_name": artist,
        }

        if album:
            params["album_name"] = album

        if duration_seconds:
            params["duration"] = str(int(round(duration_seconds)))

        query_string = "?" + urllib.parse.urlencode(params)

        url = BASE_URL + "/get" + query_string

        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        body = None

        for attempt in range(2):

            logger.verbose(f"[Lrclib] Request\n\nURL: {url}\n")

            try:
                with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:

                    body = response.read().decode("utf-8", errors="replace")

                break

            except urllib.error.HTTPError as error:

                if error.code == 404:

                    logger.verbose(f"[Lrclib] No lyrics found: {artist} - {title}")

                    return {"instrumental": False, "syncedLyrics": None, "plainLyrics": None}

                if error.code == 503 and attempt == 0:

                    logger.verbose(f"[Lrclib] Rate-limited (503) -- retrying in {LRCLIB_RETRY_DELAY_SECONDS}s.")

                    time.sleep(LRCLIB_RETRY_DELAY_SECONDS)

                    continue

                if error.code == 503:

                    logger.verbose("[Lrclib] Still rate-limited (503) after one retry.")

                    raise LrclibRateLimited() from error

                logger.verbose(f"[Lrclib] Request failed: {error}")

                return None

            except (urllib.error.URLError, TimeoutError, OSError) as error:

                logger.verbose(f"[Lrclib] Request failed: {error}")

                return None

        if body is None:
            return None

        try:
            return json.loads(body)

        except ValueError as error:

            logger.verbose(f"[Lrclib] Unparseable response: {error}")

            return None

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> dict:

        return {
            "base_url": BASE_URL,
            "user_agent": USER_AGENT,
        }


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

lrclib_manager = LrclibManager()

# ==============================================================================
# End of file
# ==============================================================================

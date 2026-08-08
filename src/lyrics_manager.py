# ==============================================================================
#
# MediaPlayer3
#
# File        : lyrics_manager.py
#
# Description :
#
#     LyricsManager
#
#     Locates and loads lyrics for the currently playing track, in
#     priority order: embedded lyrics (via metadata.py's ID3 USLT /
#     FLAC-OGG Vorbis Comment LYRICS support, added for this build),
#     external .lrc (synchronized), external .txt (plain), or "not
#     available". Never controls playback, never displays UI
#     (LYRICS_MANAGER_SPEC.md).
#
# Implements :
#
#     LYRICS_MANAGER_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md (Build 0008 -- new Core module)
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
# 2026-07-28  Build 0008
#   - Initial version.
#
# 2026-07-29  Build 0008 (device test round 2)
#   - Added verbose logging for getLyrics()/getCurrentLine(): which
#     source was used and a size/line-count summary, or that nothing
#     was found and every source was checked; the currently active
#     synchronized line on every lookup. Requested after device
#     testing showed nothing in the log for lyrics activity at all.
#
# 2026-08-01  Build 0008 (device test round 9)
#   - Added getScrollWindow(): shows a window of lines centered on
#     whichever is "current" right now, instead of a single line
#     (synchronized .lrc) or the raw, unmoving lyrics block (embedded/
#     .txt) -- requested by the user ("alhaalta ylös vierivää tekstiä,
#     jonka nopeus tulisi siten että rivi on alueen keskikohdalla, kun
#     on oikea aika"). For unsynchronized lyrics, the "current" line
#     is computed proportionally from how far through the track
#     playback is (position / duration), so embedded/.txt lyrics now
#     scroll from first line at track start to last line at track end
#     -- this directly explains and fixes a real report ("01
#     -shakira-objection" only ever showed its first 5 lines): that
#     song's lyrics are embedded, not a .lrc file, so they were always
#     unsynchronized and previously just showed the unmoving start of
#     the block.
# ------------------------------------------------------------------------------

"""
LyricsManager -- locates, loads and presents lyrics for the currently
playing track.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from .localization import _
from .logger import logger
from .metadata import metadata_reader

# ------------------------------------------------------------------------------
# LRC timestamp parsing
# ------------------------------------------------------------------------------

# [mm:ss.xx] or [mm:ss] or [mm:ss.xxx] -- the fractional part's digit
# count varies between LRC writers, so it's captured loosely and
# scaled below rather than assumed to be exactly 2 or 3 digits.
_LRC_TIMESTAMP = re.compile(r"^\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\](.*)$")

# Metadata tags such as [ar:Artist]/[ti:Title]/[al:Album]/[by:Author]/
# [offset:...] are valid LRC syntax but are not timed lyric lines --
# recognized so they're skipped rather than mis-parsed as garbled
# timestamps.
_LRC_METADATA_TAG = re.compile(r"^\[[a-zA-Z]+:.*\]\s*$")


class LyricsManager:
    """
    Provides a single getLyrics(filepath) entry point that hides
    which of the three supported sources (embedded/.lrc/.txt) was
    actually used, per LYRICS_MANAGER_SPEC.md "MainScreen Integration".
    """

    SPECIFICATION_VERSION = "0.1"

    SOURCE_EMBEDDED = "embedded"
    SOURCE_LRC = "lrc"
    SOURCE_TXT = "txt"
    SOURCE_NONE = "none"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Lyrics] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Public interface (LYRICS_MANAGER_SPEC.md "MainScreen Integration")
    # ------------------------------------------------------------------

    def getLyrics(self, filepath: str) -> Dict[str, Any]:
        """
        Return a dict describing the best available lyrics for
        `filepath`, trying embedded lyrics, then external .lrc, then
        external .txt, in that fixed order
        (LYRICS_MANAGER_SPEC.md "Source Priority"). Never raises --
        any read/parse error is logged and treated the same as "not
        found", falling through to the next source.

        Keys:
            source:        one of SOURCE_EMBEDDED/SOURCE_LRC/
                            SOURCE_TXT/SOURCE_NONE
            text:           the full lyrics as a single string
                            (already assembled from `lines` when
                            synchronized)
            synchronized:   True if `lines` contains real timestamps
            lines:          list of (seconds: float, text: str) tuples
                            when synchronized, otherwise None
        """

        if not filepath:
            return self._notAvailable()

        embedded = self._getEmbeddedLyrics(filepath)

        if embedded is not None:

            logger.verbose(
                "[Lyrics] Found embedded lyrics for '%s' (%d character(s)).",
                filepath,
                len(embedded["text"]),
            )

            return embedded

        lrc = self._getLRCLyrics(filepath)

        if lrc is not None:

            logger.verbose(
                "[Lyrics] Found .lrc lyrics for '%s' (%d synchronized line(s)).",
                filepath,
                len(lrc["lines"]),
            )

            return lrc

        txt = self._getPlainTextLyrics(filepath)

        if txt is not None:

            logger.verbose(
                "[Lyrics] Found .txt lyrics for '%s' (%d character(s)).",
                filepath,
                len(txt["text"]),
            )

            return txt

        logger.verbose("[Lyrics] No lyrics found for '%s' (checked embedded/.lrc/.txt).", filepath)

        return self._notAvailable()

    # ------------------------------------------------------------------

    def getCurrentLine(self, lyrics: Dict[str, Any], position_seconds: float) -> str:
        """
        For synchronized (`lines` is not None) lyrics, return the
        line active at `position_seconds` -- the last line whose
        timestamp has passed. Returns the full text unchanged for
        unsynchronized lyrics (LYRICS_MANAGER_SPEC.md "LRC
        Synchronization" / "fall back to plain text presentation").
        """

        lines = lyrics.get("lines")

        if not lines:
            return lyrics.get("text", "")

        current = lines[0][1]

        for timestamp, text in lines:

            if timestamp > position_seconds:
                break

            current = text

        logger.verbose(
            "[Lyrics] Current line at %.2fs: '%s'",
            position_seconds,
            current,
        )

        return current

    # ------------------------------------------------------------------

    def getScrollWindow(
        self,
        lyrics: Dict[str, Any],
        position_seconds: float,
        duration_seconds: Optional[float],
        window_size: int = 5,
    ) -> str:
        """
        Return `window_size` lines of `lyrics`, with whichever line is
        "current" at `position_seconds` placed at the middle of the
        window -- the display-side request behind this: "alhaalta
        ylös vierivää tekstiä, jonka nopeus tulisi siten että rivi on
        alueen keskikohdalla, kun on oikea aika" (bottom-to-top
        scrolling text, timed so a line is in the middle of the area
        when it's the right time). Enigma2's Label widget has no
        smooth sub-line scrolling, so this achieves the same practical
        effect -- more of the lyrics gradually becoming visible as the
        track plays, always centered on "now" -- a line at a time
        instead of a pixel at a time.

        For synchronized (.lrc) lyrics, "current" is the real timed
        line (same rule as getCurrentLine()). For unsynchronized
        lyrics (embedded or .txt -- LYRICS_MANAGER_SPEC.md "fall back
        to plain text presentation"), "current" is instead a line
        index computed from how far through the track `position_seconds`
        is (position / duration_seconds), so a .txt/embedded lyrics
        block scrolls from its first line at the start of the track to
        its last line at the end of the track, exactly as requested
        ("Txt muotoiseen voisi ajatella saman, mutta vierimisaika
        olisi kappaleen alusta kappaleen loppuun").
        """

        all_lines = self._allLyricLines(lyrics)

        if not all_lines:
            return lyrics.get("text", "")

        center_index = self._currentLineIndex(lyrics, all_lines, position_seconds, duration_seconds)

        return self._windowAround(all_lines, center_index, window_size)

    # ------------------------------------------------------------------

    def _allLyricLines(self, lyrics: Dict[str, Any]) -> List[str]:
        """
        Return every line of `lyrics` as a flat list of strings,
        whether it came from synchronized .lrc entries or a plain
        text block -- blank lines are kept (they're natural pauses/
        verse breaks in most lyrics), only fully empty lyrics produce
        an empty list.
        """

        entries = lyrics.get("lines")

        if entries:
            return [text for _timestamp, text in entries]

        text = lyrics.get("text", "")

        if not text:
            return []

        return text.split("\n")

    # ------------------------------------------------------------------

    def _currentLineIndex(
        self,
        lyrics: Dict[str, Any],
        all_lines: List[str],
        position_seconds: float,
        duration_seconds: Optional[float],
    ) -> int:

        entries = lyrics.get("lines")

        if entries:

            index = 0

            for line_index, (timestamp, _text) in enumerate(entries):

                if timestamp > position_seconds:
                    break

                index = line_index

            return index

        # Unsynchronized (embedded/.txt): scroll from first line at
        # track start to last line at track end, proportional to how
        # far through the track playback currently is.
        if not duration_seconds or duration_seconds <= 0:
            return 0

        fraction = max(0.0, min(1.0, position_seconds / duration_seconds))

        return min(len(all_lines) - 1, int(fraction * len(all_lines)))

    # ------------------------------------------------------------------

    def _windowAround(self, all_lines: List[str], center_index: int, window_size: int) -> str:

        half = window_size // 2

        start = center_index - half

        end = start + window_size

        if start < 0:

            end -= start

            start = 0

        if end > len(all_lines):

            start = max(0, start - (end - len(all_lines)))

            end = len(all_lines)

        return "\n".join(all_lines[start:end])

    # ------------------------------------------------------------------
    # Embedded lyrics
    # ------------------------------------------------------------------

    def _getEmbeddedLyrics(self, filepath: str) -> Optional[Dict[str, Any]]:

        try:

            metadata = metadata_reader.read(filepath)

        except Exception as error:

            self._log(f"Could not read metadata for embedded lyrics from '{filepath}': {error}")

            return None

        text = (metadata.get("lyrics") or "").strip()

        if not text:
            return None

        return {
            "source": self.SOURCE_EMBEDDED,
            "text": text,
            "synchronized": False,
            "lines": None,
        }

    # ------------------------------------------------------------------
    # External .lrc
    # ------------------------------------------------------------------

    def _getLRCLyrics(self, filepath: str) -> Optional[Dict[str, Any]]:

        lrc_path = self._siblingPath(filepath, ".lrc")

        if lrc_path is None or not os.path.isfile(lrc_path):
            return None

        try:

            with open(lrc_path, "r", encoding="utf-8", errors="replace") as lrc_file:

                raw_lines = lrc_file.readlines()

        except OSError as error:

            self._log(f"Could not read LRC file '{lrc_path}': {error}")

            return None

        parsed = self._parseLRCLines(raw_lines)

        if not parsed:
            return None

        text = "\n".join(text for _timestamp, text in parsed)

        return {
            "source": self.SOURCE_LRC,
            "text": text,
            "synchronized": True,
            "lines": parsed,
        }

    # ------------------------------------------------------------------

    def _parseLRCLines(self, raw_lines: List[str]) -> List[Tuple[float, str]]:

        parsed: List[Tuple[float, str]] = []

        for raw_line in raw_lines:

            line = raw_line.rstrip("\r\n")

            if not line.strip():
                continue

            if _LRC_METADATA_TAG.match(line):
                continue

            match = _LRC_TIMESTAMP.match(line)

            if match is None:
                continue

            minutes_text, seconds_text, fraction_text, text = match.groups()

            try:

                minutes = int(minutes_text)

                seconds = int(seconds_text)

                fraction = 0.0

                if fraction_text:

                    # Normalize a 1-3 digit fraction to hundredths/
                    # thousandths correctly regardless of how many
                    # digits this particular LRC file used.
                    fraction = int(fraction_text) / (10 ** len(fraction_text))

                total_seconds = minutes * 60 + seconds + fraction

            except ValueError as error:

                self._log(f"Skipping malformed LRC timestamp '{line}': {error}")

                continue

            parsed.append((total_seconds, text.strip()))

        parsed.sort(key=lambda entry: entry[0])

        return parsed

    # ------------------------------------------------------------------
    # External .txt
    # ------------------------------------------------------------------

    def _getPlainTextLyrics(self, filepath: str) -> Optional[Dict[str, Any]]:

        txt_path = self._siblingPath(filepath, ".txt")

        if txt_path is None or not os.path.isfile(txt_path):
            return None

        try:

            with open(txt_path, "r", encoding="utf-8", errors="replace") as txt_file:

                text = txt_file.read().strip()

        except OSError as error:

            self._log(f"Could not read TXT lyrics file '{txt_path}': {error}")

            return None

        if not text:
            return None

        return {
            "source": self.SOURCE_TXT,
            "text": text,
            "synchronized": False,
            "lines": None,
        }

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _siblingPath(self, filepath: str, extension: str) -> Optional[str]:
        """
        Return `filepath` with its extension replaced by `extension`
        (e.g. "/music/song.flac" + ".lrc" -> "/music/song.lrc") --
        LYRICS_MANAGER_SPEC.md "External Lyrics": "Only files matching
        the current media filename are considered."
        """

        try:

            base, _extension = os.path.splitext(filepath)

            return base + extension

        except (TypeError, ValueError):

            return None

    # ------------------------------------------------------------------

    def _notAvailable(self) -> Dict[str, Any]:

        return {
            "source": self.SOURCE_NONE,
            "text": _("Lyrics not available."),
            "synchronized": False,
            "lines": None,
        }

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> dict:

        return {
            "specification_version": self.SPECIFICATION_VERSION,
            "source_priority": [self.SOURCE_EMBEDDED, self.SOURCE_LRC, self.SOURCE_TXT],
        }


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

lyrics_manager = LyricsManager()

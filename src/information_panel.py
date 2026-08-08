# ==============================================================================
#
# MediaPlayer3
#
# File        : information_panel.py
#
# Description :
#
#     InformationPanel
#
#     Unified presentation layer for MainScreen's Information Panel
#     (Build 0009 -- INFORMATION_PANEL_SPEC.md). Replaces the fixed
#     Lyrics/Metadata/Codec cycle from Build 0008's MainScreen
#     (_formatLyricsPanel/_formatMetadataPanel/_formatCodecPanel) with
#     a dynamically-built list of "pages", one per information type
#     that actually has content right now -- an empty page (e.g.
#     Metadata for a file with no tags at all) is never included, and
#     Internet Radio automatically gets Radio EPG/Now Playing/Station
#     pages instead of Lyrics.
#
#     InformationPanel owns no playback or UI state of its own beyond
#     which page is currently selected and how far it's scrolled --
#     every information VALUE comes from an existing manager
#     (LyricsManager, PlaybackController's metadata/stream-info,
#     EPGManager). MainScreen calls refresh() once per display update
#     and reads getCurrentTitle()/getCurrentContent() for what to
#     show; switchPage()/scroll() handle LEFT/RIGHT and UP/DOWN while
#     the Information Panel is the active panel.
#
# Implements :
#
#     INFORMATION_PANEL_SPEC.md v1 (Build 0009)
#
# Architecture :
#
#     ARCHITECTURE.md (Build 0009 -- new Core module, MainScreen's
#     Information Panel; sits between MainScreen and the existing
#     LyricsManager/PlaybackController/EPGManager, same "Screens never
#     talk to a data source directly" convention every other Screen in
#     this codebase already follows)
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
# 2026-08-02  Build 0009
#   - Initial version.
# ------------------------------------------------------------------------------

"""
InformationPanel -- builds and navigates MainScreen's unified
Information Panel pages (Lyrics/Metadata/Codec for local media;
Radio EPG/Now Playing/Station for Internet Radio).
"""

from __future__ import annotations

from datetime import datetime
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from . import metadata as metadata_module
from .config import config_manager
from .epg_manager import epg_manager
from .localization import _
from .logger import logger
from .lyrics_manager import lyrics_manager

# Lines visible at once in a page's content area. MainScreen's Build
# 0009 layout gives the Information Panel the entire right-hand side
# of the screen (INFORMATION_PANEL_SPEC.md "Layout") -- substantially
# taller than Build 0008's info_panel widget, hence the larger window
# than that build's LYRICS_WINDOW_SIZE (5).
DEFAULT_VISIBLE_LINES = 14

# Build 0009, device test round 8 -- how many upcoming programmes the
# Radio EPG page lists below the current one, per user request
# ("Voisi lisata ainakin 3 seuraavan ohjelman tiedot, kun naytolla on
# tilaa").
RADIO_EPG_UPCOMING_COUNT = 3

_LYRICS_SOURCE_TITLES = {
    "lrc": "Lyrics LRC",
    "embedded": "Lyrics Embedded",
    "txt": "Lyrics TXT",
}


class InformationPanel:
    """
    Owns the current Information Panel page list, selection and
    scroll position. Content itself always comes from an existing
    manager -- InformationPanel formats and paginates, it never
    originates data.
    """

    def __init__(self, visible_lines: int = DEFAULT_VISIBLE_LINES) -> None:

        self._visible_lines = visible_lines

        self._pages: List[Tuple[str, str]] = []

        self._current_index = 0

        self._scroll_offset = 0

        # Build 0009, device test round 4 -- which page (by title) is
        # synchronized lyrics, if any is currently in the page list.
        # scroll() routes UP/DOWN to _adjustLyricsOffset() instead of
        # normal line-scrolling while that page is selected (see
        # scroll()'s own docstring for why).
        self._synchronized_lyrics_title: Optional[str] = None

        # Build 0009, device test round 4 -- user-adjustable offset
        # (seconds) applied to synchronized lyrics, per user request:
        # "Pitaisi muuttaa tekstin ajoitusta suhteessa kappaleeseen
        # ylos-alas-napeilla" (should be able to adjust the text's
        # timing relative to the song using up/down). A positive
        # value makes lyrics appear LATER relative to playback
        # (delays them); negative makes them appear EARLIER. Persists
        # across refresh() calls for the same track -- reset when the
        # lyrics page itself changes (new track).
        self._lyrics_offset_seconds = 0.0

        # Build 0009, device test round 4 -- (filename, stationuuid)
        # of whatever was active on the last refresh() call, used to
        # detect a genuine track/station change vs. just another
        # periodic refresh of the same one (see refresh()'s own
        # docstring for why that distinction matters).
        self._current_track_key = None

        self._log("Created")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[InfoPanel] %s", message)

    # ------------------------------------------------------------------
    # Page construction (INFORMATION_PANEL_SPEC.md "Page Selection")
    # ------------------------------------------------------------------

    def refresh(
        self,
        playback,
        filename: Optional[str],
        elapsed: Optional[float],
        duration: Optional[float],
        station: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Rebuild the list of available pages from current playback
        state. Call once per MainScreen display update -- cheap
        enough (a handful of manager calls, no I/O of its own) to run
        unconditionally rather than trying to detect what actually
        changed.

        Preserves the current page selection across a refresh when
        that page is still available (matched by title), so the user
        isn't silently bounced back to the first page every second
        while watching, say, Metadata -- only resets to page 0 when
        the previously-selected page has genuinely disappeared (e.g.
        Radio EPG page vanishing because programme data expired).

        Build 0009, device test round 4: a device user reported manual
        scrolling appearing not to work at all ("Tekstin siirtaminen ei
        toimi"). Traced to this method: refresh() runs on every
        periodic display update (roughly once per second while
        something plays), and previously reset scroll_offset to 0
        UNCONDITIONALLY every single time -- so a manual UP/DOWN
        scroll was wiped out again within about a second, making it
        look broken even though the scroll() call itself worked fine.
        Now only resets scroll_offset when switching to a genuinely
        different page (by title) or when the active track/station
        itself changed -- staying on the same page for the same track
        keeps whatever scroll position the user set.
        """

        previous_title = self._pages[self._current_index][0] if self._pages else None

        previous_track_key = self._current_track_key

        self._current_track_key = (filename, station.get("stationuuid") if station else None)

        if playback.isPlayingStream():

            self._pages = self._buildRadioPages(playback, station)

        else:

            self._pages = self._buildLocalPages(playback, filename, elapsed, duration)

        track_changed = previous_track_key != self._current_track_key

        if track_changed:

            self._scroll_offset = 0

            self._lyrics_offset_seconds = 0.0

        if previous_title is not None:

            for index, (title, _content) in enumerate(self._pages):

                if title == previous_title:

                    self._current_index = index

                    if track_changed:

                        self._scroll_offset = 0

                    return

        self._current_index = 0

        self._scroll_offset = 0

    # ------------------------------------------------------------------

    def _buildLocalPages(self, playback, filename, elapsed, duration) -> List[Tuple[str, str]]:

        pages: List[Tuple[str, str]] = []

        if filename:

            lyrics_page = self._buildLyricsPage(filename, elapsed, duration)

            if lyrics_page is not None:
                pages.append(lyrics_page)

        metadata_page = self._buildMetadataPage(playback)

        if metadata_page is not None:
            pages.append(metadata_page)

        codec_page = self._buildCodecPage(playback, filename, duration)

        if codec_page is not None:
            pages.append(codec_page)

        return pages

    # ------------------------------------------------------------------

    def _buildRadioPages(self, playback, station) -> List[Tuple[str, str]]:

        pages: List[Tuple[str, str]] = []

        if station is not None:

            epg_page = self._buildRadioEPGPage(station)

            if epg_page is not None:
                pages.append(epg_page)

        now_playing_page = self._buildNowPlayingPage(station)

        if now_playing_page is not None:
            pages.append(now_playing_page)

        if station is not None:

            station_page = self._buildStationPage(station)

            if station_page is not None:
                pages.append(station_page)

        codec_page = self._buildCodecPage(playback, station=station)

        if codec_page is not None:
            pages.append(codec_page)

        return pages

    # ------------------------------------------------------------------
    # Individual page builders -- each returns None (page omitted
    # entirely) when it has nothing useful to show
    # (INFORMATION_PANEL_SPEC.md "Only information containing actual
    # content is presented").
    # ------------------------------------------------------------------

    def _buildLyricsPage(self, filename, elapsed, duration) -> Optional[Tuple[str, str]]:

        try:
            lyrics = lyrics_manager.getLyrics(filename)

        except Exception as error:

            self._log(f"Lyrics lookup failed: {error}")

            return None

        if lyrics.get("source") == "none":
            return None

        source_label = _LYRICS_SOURCE_TITLES.get(lyrics["source"], "Lyrics")

        title = f"{_('Information')}: {_(source_label)}"

        if lyrics.get("synchronized") and elapsed is not None:

            # Build 0009, device test round 4: user-adjustable offset
            # (_lyrics_offset_seconds, adjustSyncOffset()) applied
            # here -- a positive offset delays the lyrics (shows an
            # earlier line for the same elapsed time), matching what
            # the user asked for ("muuttaa tekstin ajoitusta suhteessa
            # kappaleeseen"). Tracks this page's own title so scroll()
            # knows to route UP/DOWN to offset adjustment instead of
            # normal line-scrolling while this page is active -- the
            # two would otherwise conflict (auto-following playback
            # position vs. a fixed manual scroll window).
            self._synchronized_lyrics_title = title

            adjusted_elapsed = max(0.0, elapsed + self._lyrics_offset_seconds)

            text = lyrics_manager.getScrollWindow(
                lyrics, adjusted_elapsed, duration, window_size=self._visible_lines
            )

        else:

            if self._synchronized_lyrics_title == title:

                self._synchronized_lyrics_title = None

            text = lyrics.get("text", "")

        return title, text

    # ------------------------------------------------------------------

    def _buildMetadataPage(self, playback) -> Optional[Tuple[str, str]]:

        metadata = playback.getMetadata()

        if not metadata:
            return None

        lines = []

        field_labels = (
            ("artist", _("Artist")),
            ("album", _("Album")),
            ("title", _("Title")),
            ("genre", _("Genre")),
            ("year", _("Year")),
            ("composer", _("Composer")),
        )

        has_any_known_field = False

        for field_name, label in field_labels:

            value = metadata.get(field_name, metadata_module.UNKNOWN)

            if value != metadata_module.UNKNOWN:
                has_any_known_field = True

            lines.append(f"{label}: {value}")

        if not has_any_known_field:

            # Every field is "Unknown" -- nothing useful to show,
            # matching INFORMATION_PANEL_SPEC.md's "Local music
            # without lyrics: Metadata, Codec" example implying
            # Metadata is only listed when it actually has something.
            return None

        title = f"{_('Information')}: {_('Metadata')}"

        return title, "\n".join(lines)

    # ------------------------------------------------------------------

    def _buildCodecPage(
        self,
        playback,
        filename: Optional[str] = None,
        duration: Optional[float] = None,
        station: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[str, str]]:
        """
        Build 0009, device test round 3: a device log showed
        compatibility.py's getStreamInfo() never getting real values
        for local FLAC playback at all -- codec/sample_rate/channels'
        own iServiceInformation constants don't exist on that image
        (silently skipped, not even an error), and bitrate is always
        -1 ("not available"). Confirmed these constants are likely
        DVB-tuning-specific, not populated for GStreamer-based file/
        stream playback. Per the user's own suggestion ("laskettu
        bittinopeus (koko/aika)"), local files now get a computed
        fallback instead of leaving the whole page empty: format
        guessed from the file extension, bitrate computed from file
        size and duration (file_size_bits / duration_seconds) --
        both need only the filesystem and metadata this class already
        has, no uncertain Enigma2 API involved. Only used to FILL IN
        whatever getStreamInfo() itself couldn't answer -- a real
        value from the API always wins where one exists.

        Build 0009, device test round 5: confirmed the same
        getStreamInfo() gap applies to Internet Radio too (same
        device log, same missing constants, while a Yle station was
        playing) -- but the file-based fallback above needs an actual
        file to check, which a live stream doesn't have. RadioBrowser
        station dicts commonly carry their own "codec"/"bitrate"
        fields as station metadata (e.g. the AAC/64kbps visible in a
        Bauer station's own stream URL in a device screenshot,
        "nostalgia_64.aac") -- used as a second fallback source when
        streaming, filling in only whatever's still missing after the
        API and file-based fallbacks (station metadata is Whatever
        RadioBrowser itself was told, not a live measurement, so it
        never overrides a real value from the other two).
        """

        stream_info = playback.getStreamInfo() or {}

        field_labels = (
            ("codec", _("Codec")),
            ("sample_rate", _("Sample rate")),
            ("bitrate", _("Bitrate")),
            ("channels", _("Channels")),
        )

        values = {field_name: stream_info.get(field_name, metadata_module.UNKNOWN) for field_name, _label in field_labels}

        if filename:

            self._fillCodecFallbacksFromFile(values, filename, duration)

        if station:

            self._fillCodecFallbacksFromStation(values, station)

        has_any_known_field = any(value != metadata_module.UNKNOWN for value in values.values())

        if not has_any_known_field:
            return None

        lines = [f"{label}: {values[field_name]}" for field_name, label in field_labels]

        title = f"{_('Information')}: {_('Codec')}"

        return title, "\n".join(lines)

    # ------------------------------------------------------------------

    def _fillCodecFallbacksFromFile(self, values: Dict[str, str], filename: str, duration: Optional[float]) -> None:
        """
        Fills in `values["codec"]`/`values["bitrate"]` from the file
        itself when getStreamInfo() didn't already provide them --
        see _buildCodecPage()'s own docstring for why this exists.
        Leaves sample_rate/channels alone; neither is derivable from
        just the file size and duration.
        """

        if values.get("codec") == metadata_module.UNKNOWN:

            extension = os.path.splitext(filename)[1].lstrip(".").upper()

            if extension:

                values["codec"] = f"{extension} ({_('from file extension')})"

        if values.get("bitrate") == metadata_module.UNKNOWN and duration:

            try:
                file_size_bytes = os.path.getsize(filename)

            except OSError:

                return

            if file_size_bytes > 0 and duration > 0:

                computed_kbps = int((file_size_bytes * 8) / duration / 1000)

                values["bitrate"] = f"{computed_kbps} kbps ({_('computed: size/duration')})"

    # ------------------------------------------------------------------

    def _fillCodecFallbacksFromStation(self, values: Dict[str, str], station: Dict[str, Any]) -> None:
        """
        Fills in `values["codec"]`/`values["bitrate"]` from
        RadioBrowser's own station metadata when neither the API nor
        (there being no file for a stream) the file-based fallback
        provided them -- see _buildCodecPage()'s own docstring.
        Labelled "(station info)" since this is what RadioBrowser was
        told about the stream, not a live measurement of it.
        """

        if values.get("codec") == metadata_module.UNKNOWN:

            station_codec = station.get("codec")

            if station_codec:

                values["codec"] = f"{station_codec} ({_('station info')})"

        if values.get("bitrate") == metadata_module.UNKNOWN:

            station_bitrate = station.get("bitrate")

            if station_bitrate:

                values["bitrate"] = f"{station_bitrate} kbps ({_('station info')})"

    # ------------------------------------------------------------------

    def _buildRadioEPGPage(self, station) -> Optional[Tuple[str, str]]:
        """
        Build 0009, device test round 8: extended from showing only
        the current programme to also listing the next few, per user
        request ("YLE EPG nayttaa meneillaan olevan ohjelman, mutta
        sielta saa varmaan myos seuraavat ohjelmatiedot. Voisi lisata
        ainakin 3 seuraavan ohjelman tiedot"). getSchedule() already
        returns the full day's lineup (confirmed working against real
        Yle data in earlier sessions) -- this was previously only
        ever searched for whichever single entry covers right now
        (getCurrentProgramme()); reads the full list directly instead
        so upcoming entries are available too, without asking
        EPGManager for anything it didn't already have.
        """

        try:
            schedule = epg_manager.getSchedule(station)

        except Exception as error:

            self._log(f"EPG lookup failed for station {station.get('stationuuid')}: {error}")

            return None

        if not schedule:
            return None

        now = time.time()

        current_entry = None

        upcoming_entries = []

        for entry in schedule:

            start = entry.get("start")

            end = entry.get("end")

            if start is None or end is None:
                continue

            if start <= now < end:

                current_entry = entry

            elif start > now:

                upcoming_entries.append(entry)

        if current_entry is None and not upcoming_entries:
            return None

        lines: List[str] = []

        if current_entry is not None:

            lines.extend(self._formatEPGEntry(current_entry, prefix=_("Now") + ": "))

        for entry in upcoming_entries[:RADIO_EPG_UPCOMING_COUNT]:

            lines.append("")

            lines.extend(self._formatEPGEntry(entry, prefix=""))

        title = f"{_('Information')}: {_('Radio EPG')}"

        return title, "\n".join(lines)

    # ------------------------------------------------------------------

    def _formatEPGEntry(self, entry: Dict[str, Any], prefix: str) -> List[str]:
        """
        Formats one schedule entry (current or upcoming) as 1-3 lines:
        "<prefix><title>", "HH:MM-HH:MM", and the description if one
        exists. Shared between the current-programme and upcoming-
        programmes formatting in _buildRadioEPGPage() so both look
        consistent.
        """

        lines = [f"{prefix}{entry.get('title', '')}"]

        start = entry.get("start")

        end = entry.get("end")

        if start is not None and end is not None:

            start_text = datetime.fromtimestamp(start).strftime("%H:%M")

            end_text = datetime.fromtimestamp(end).strftime("%H:%M")

            lines.append(f"{start_text}-{end_text}")

        description = entry.get("description")

        if description:

            lines.append(description)

        return lines

    # ------------------------------------------------------------------

    def _buildNowPlayingPage(self, station) -> Optional[Tuple[str, str]]:

        try:
            now_playing = epg_manager.getNowPlaying(station)

        except Exception as error:

            self._log(f"Now-playing lookup failed: {error}")

            return None

        if not now_playing.get("available"):
            return None

        text = epg_manager.formatNowPlaying(now_playing)

        title = f"{_('Information')}: {_('Now Playing')}"

        return title, text

    # ------------------------------------------------------------------

    def _buildStationPage(self, station) -> Optional[Tuple[str, str]]:

        name = station.get("name")

        if not name:
            return None

        lines = [name]

        for field_name, label in (("country", _("Country")), ("language", _("Language")), ("tags", _("Tags"))):

            value = station.get(field_name)

            if value:
                lines.append(f"{label}: {value}")

        title = f"{_('Information')}: {_('Station')}"

        return title, "\n".join(lines)

    # ------------------------------------------------------------------
    # Navigation (INFORMATION_PANEL_SPEC.md "Navigation")
    # ------------------------------------------------------------------

    def switchPage(self, direction: int) -> None:
        """
        LEFT/RIGHT: move to the next/previous available page,
        wrapping around. `direction` is +1 (RIGHT/next) or -1
        (LEFT/previous). A no-op when there are 0 or 1 pages.
        """

        if len(self._pages) <= 1:
            return

        self._current_index = (self._current_index + direction) % len(self._pages)

        self._scroll_offset = 0

    # ------------------------------------------------------------------

    def scroll(self, direction: int) -> None:
        """
        UP/DOWN: scroll the current page's content by one line.
        `direction` is +1 (DOWN) or -1 (UP). Clamped to the content's
        actual line count -- never scrolls past the last line or
        before the first.

        Build 0009, device test round 4: while the current page is
        synchronized lyrics, routes to _adjustLyricsOffset() instead --
        normal line-scrolling doesn't make sense for a view that's
        already auto-following playback position, and the user
        specifically asked for UP/DOWN to adjust the lyrics' timing
        instead ("Pitaisi muuttaa tekstin ajoitusta suhteessa
        kappaleeseen ylos-alas-napeilla").
        """

        if not self._pages:
            return

        title, content = self._pages[self._current_index]

        if title == self._synchronized_lyrics_title:

            self._adjustLyricsOffset(direction)

            return

        total_lines = content.count("\n") + 1

        max_offset = max(0, total_lines - self._visible_lines)

        self._scroll_offset = max(0, min(max_offset, self._scroll_offset + direction))

    # ------------------------------------------------------------------

    def _adjustLyricsOffset(self, direction: int) -> None:
        """
        Nudges _lyrics_offset_seconds by
        cfg.playback.lyrics_offset_step_seconds (Build 0009, device
        test round 7 -- made configurable per user request, default
        1 second). DOWN (direction=+1) delays the lyrics (shows an
        earlier line for the same elapsed time); UP (direction=-1)
        advances them. No hard limit -- an extreme offset just means
        the shown line stays clamped to the first/last available
        line, same as any other out-of-range elapsed time would.
        """

        try:
            step = config_manager.get("playback.lyrics_offset_step_seconds", 1)

        except Exception:

            step = 1

        self._lyrics_offset_seconds += direction * step

    # ------------------------------------------------------------------
    # Display (what MainScreen actually reads)
    # ------------------------------------------------------------------

    def getCurrentTitle(self) -> str:
        """
        Build 0009, device test round 5: appends the current lyrics
        offset (e.g. "+3.5s") to the title while on the synchronized
        lyrics page and the offset is non-zero, per user request:
        "Voisiko tekstityksessa nakya otsikkorivilla paljonko
        ajoitusta on muutettu esim. +3.5 s."
        """

        if not self._pages:
            return _("Information")

        title = self._pages[self._current_index][0]

        if title == self._synchronized_lyrics_title and self._lyrics_offset_seconds != 0:

            sign = "+" if self._lyrics_offset_seconds > 0 else ""

            title = f"{title} ({sign}{self._lyrics_offset_seconds:g}s)"

        return title

    # ------------------------------------------------------------------

    def getCurrentContent(self) -> str:
        """
        Returns the current page's content, windowed to
        `visible_lines` starting at the current scroll offset -- the
        same "show the maximum information that fits, only reveal
        the rest as the user scrolls" pattern DeveloperScreen and
        HelpScreen already use.
        """

        if not self._pages:
            return _("No information available.")

        _title, content = self._pages[self._current_index]

        lines = content.split("\n")

        window = lines[self._scroll_offset : self._scroll_offset + self._visible_lines]

        return "\n".join(window)

    # ------------------------------------------------------------------

    def getPageCount(self) -> int:

        return len(self._pages)

    # ------------------------------------------------------------------

    def getCurrentPageIndex(self) -> int:

        return self._current_index

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> dict:

        return {
            "page_count": len(self._pages),
            "page_titles": [title for title, _content in self._pages],
            "current_index": self._current_index,
            "scroll_offset": self._scroll_offset,
        }

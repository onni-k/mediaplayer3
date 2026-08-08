# ==============================================================================
#
# MediaPlayer3
#
# File        : epg_manager.py
#
# Description :
#
#     EPGManager
#
#     Internet Radio "EPG" (Electronic Programme Guide) support,
#     split into two genuinely different problems:
#
#       1. Now Playing -- the current track/show a station is
#          broadcasting right now. Achievable today: Icecast/Shoutcast
#          streams commonly embed this as ICY metadata (a station's
#          live "StreamTitle"), which GStreamer already parses and
#          exposes as ordinary service tags -- compatibility.py's
#          getStreamTags() reads it through the exact same
#          iServiceInformation interface getStreamInfo() already uses
#          for codec/bitrate. Not every station provides this.
#
#       2. Schedule -- a station's upcoming programme lineup (e.g.
#          "Aamu-tv, 08:00-10:00"). There is no universal, machine-
#          readable format for this across radio stations the way
#          XMLTV exists for TV -- RadioBrowser (already integrated via
#          InternetRadioManager) does not provide it, and no broadly
#          applicable free API was found. Rather than hardcode
#          scrapers for a handful of stations (fragile, and outside
#          what a general-purpose plugin should own long-term), this
#          module defines a small provider interface
#          (EPGScheduleProvider) that a future build -- or a station-
#          specific configuration -- can plug real data into. With no
#          provider registered, schedule queries simply report
#          unavailable; this is the expected, honest default, not a
#          missing feature.
#
#     EPGManager never touches playback and never opens UI itself,
#     the same convention every other Manager in this codebase
#     follows.
#
# Implements :
#
#     EPG_MANAGER_SPEC.md v0.1 (planning)
#
# Architecture :
#
#     ARCHITECTURE.md (Build 0009 planning -- new Core module)
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
# 2026-08-02  Build 0009 (planning)
#   - Initial version. Requested by the user with an unrelated
#     third-party project (iptv-org/epg, a Node.js/TypeScript tool for
#     scraping TV channel schedules from broadcaster websites) as a
#     starting point -- not usable here: wrong language/runtime (no
#     Node.js on Enigma2), wrong domain (zero radio stations in it,
#     confirmed by inspection), and wrong scale (a server-side batch
#     scraper, not an embedded on-device lookup). Built from scratch
#     instead, scoped to what's actually achievable for radio.
#
# 2026-08-02  Build 0009 (planning, cont.)
#   - Added NowPlayingProvider, parallel to EPGScheduleProvider --
#     confirmed a broadcaster (Bauer Media/Rayo Finland) embeds real,
#     current now-playing data directly in its own website's markup
#     (a Next.js page's __NEXT_DATA__ payload,
#     props.initialState.station.data.stationNowPlaying), independent
#     of whether the actual audio stream sends ICY metadata at all.
#     getNowPlaying() now accepts an optional `station` and checks for
#     a registered provider first, falling back to the existing ICY-
#     tag mechanism otherwise -- existing callers that never pass
#     `station` are unaffected.
# ------------------------------------------------------------------------------

"""
EPGManager -- Internet Radio now-playing info and an extensible
schedule-provider interface.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .compatibility import compatibility
from .localization import _
from .logger import logger


class EPGScheduleProvider:
    """
    Interface a future schedule data source implements. EPGManager
    ships with none registered -- this is a seam for later, not a
    working scraper (see this file's own header for why a general one
    isn't feasible to build now).

    A provider is anything exposing:

        getSchedule(station: dict) -> List[Dict[str, Any]]

    returning entries shaped like:

        {"start": <unix timestamp>, "end": <unix timestamp>,
         "title": <str>, "description": <str, optional>}

    in chronological order. Raising is treated the same as returning
    an empty list -- EPGManager never lets a provider's own failure
    propagate.
    """

    def getSchedule(self, station: Dict[str, Any]) -> List[Dict[str, Any]]:

        raise NotImplementedError


class NowPlayingProvider:
    """
    Interface a per-station "now playing" data source implements, as
    an alternative to the default ICY/Shoutcast stream-tag mechanism
    (compatibility.getStreamTags()) -- added after confirming some
    broadcasters embed real, current now-playing data directly in
    their own website's markup (Bauer Media/Rayo Finland: a Next.js
    page's __NEXT_DATA__ payload), independent of whether the actual
    audio stream sends ICY metadata at all.

    A provider is anything exposing:

        getNowPlaying(station: dict) -> Dict[str, Any]

    returning a dict shaped like EPGManager.getNowPlaying()'s own
    return value (see its docstring) -- "available", "title",
    "artist", "organization". Raising is treated the same as
    returning {"available": False}: EPGManager never lets a
    provider's own failure propagate.
    """

    def getNowPlaying(self, station: Dict[str, Any]) -> Dict[str, Any]:

        raise NotImplementedError


class EPGManager:
    """
    Internet Radio "EPG": now-playing stream tags (real, working
    today) plus a pluggable interface for future schedule data (not
    populated by this build -- see module header).
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._schedule_providers: Dict[str, EPGScheduleProvider] = {}

        self._now_playing_providers: Dict[str, NowPlayingProvider] = {}

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[EPG] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Now Playing
    # ------------------------------------------------------------------

    def getNowPlaying(self, station: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return "now playing" info for whatever Internet Radio stream
        is currently active.

        When `station` is given and has a NowPlayingProvider
        registered for its stationuuid, that provider is used --
        added after confirming some broadcasters (Bauer Media/Rayo
        Finland) embed real, current now-playing data directly in
        their own website, independent of whether the audio stream
        itself sends ICY metadata at all. Otherwise falls back to the
        stream's own ICY/Shoutcast metadata
        (compatibility.getStreamTags()), as before -- existing
        callers that never pass `station` keep working unchanged.

        Returns:
            Dict with keys:
                available:  True if a source provided anything
                             usable, False otherwise (a station simply
                             not providing this, by either path, is
                             the normal, expected case for many
                             stations -- not an error).
                title:      Track/show title, or "" when unavailable.
                artist:     Performer, or "" when unavailable
                             (streams often fold this into `title`
                             instead, e.g. "Artist - Track" -- callers
                             needing to split that should do so
                             themselves; EPGManager passes through
                             whatever the source actually sent).
                organization: Station-provided name, when the source
                             advertises one distinct from the
                             configured station name (rare).
        """

        if station is not None:

            station_uuid = station.get("stationuuid")

            provider = self._now_playing_providers.get(station_uuid)

            if provider is not None:

                try:
                    result = provider.getNowPlaying(station)

                except Exception as error:

                    self._log(f"Now-playing provider for station {station_uuid} failed: {error}")

                    result = {"available": False}

                logger.verbose(
                    "[EPG] Now playing (provider): available=%s, title='%s', artist='%s'",
                    result.get("available"),
                    result.get("title", ""),
                    result.get("artist", ""),
                )

                return {
                    "available": bool(result.get("available")),
                    "title": result.get("title", ""),
                    "artist": result.get("artist", ""),
                    "organization": result.get("organization", ""),
                }

        try:
            tags = compatibility.getStreamTags()

        except Exception as error:

            self._log(f"Unable to read now-playing tags: {error}")

            tags = {}

        title = tags.get("title", "Unknown")
        artist = tags.get("artist", "Unknown")
        organization = tags.get("organization", "Unknown")

        available = title != "Unknown" or artist != "Unknown"

        result = {
            "available": available,
            "title": title if title != "Unknown" else "",
            "artist": artist if artist != "Unknown" else "",
            "organization": organization if organization != "Unknown" else "",
        }

        logger.verbose(
            "[EPG] Now playing (ICY tags): available=%s, title='%s', artist='%s'",
            result["available"],
            result["title"],
            result["artist"],
        )

        return result

    # ------------------------------------------------------------------

    def registerNowPlayingProvider(self, station_uuid: str, provider: NowPlayingProvider) -> None:
        """
        Associate `provider` with a specific station (by RadioBrowser
        stationuuid, matching registerScheduleProvider()'s own
        convention). Optional -- with nothing registered for a given
        station, getNowPlaying() falls back to ICY stream tags as
        before.
        """

        self._now_playing_providers[station_uuid] = provider

        self._log(f"Now-playing provider registered for station {station_uuid}.")

    # ------------------------------------------------------------------

    def unregisterNowPlayingProvider(self, station_uuid: str) -> None:

        if station_uuid in self._now_playing_providers:

            del self._now_playing_providers[station_uuid]

            self._log(f"Now-playing provider removed for station {station_uuid}.")

    # ------------------------------------------------------------------

    def hasNowPlayingProvider(self, station_uuid: str) -> bool:

        return station_uuid in self._now_playing_providers

    # ------------------------------------------------------------------

    def formatNowPlaying(self, now_playing: Optional[Dict[str, Any]] = None) -> str:
        """
        Convenience formatter: "Artist - Title", just "Title", or a
        clear "not available" message -- for a Screen to display
        directly without re-implementing this each time. Pass an
        already-fetched dict from getNowPlaying() to avoid querying
        twice in the same tick; omit it to fetch fresh.
        """

        if now_playing is None:
            now_playing = self.getNowPlaying()

        if not now_playing.get("available"):
            return _("Now playing information not available.")

        title = now_playing.get("title", "")
        artist = now_playing.get("artist", "")

        if artist and title:
            return f"{artist} - {title}"

        return title or artist

    # ------------------------------------------------------------------
    # Schedule (provider interface -- see module header)
    # ------------------------------------------------------------------

    def registerScheduleProvider(self, station_uuid: str, provider: EPGScheduleProvider) -> None:
        """
        Associate `provider` with a specific station (by RadioBrowser
        stationuuid). Optional -- with nothing registered,
        getSchedule() always reports unavailable, which is the
        expected default for this build (see module header).
        """

        self._schedule_providers[station_uuid] = provider

        self._log(f"Schedule provider registered for station {station_uuid}.")

    # ------------------------------------------------------------------

    def unregisterScheduleProvider(self, station_uuid: str) -> None:

        if station_uuid in self._schedule_providers:

            del self._schedule_providers[station_uuid]

            self._log(f"Schedule provider removed for station {station_uuid}.")

    # ------------------------------------------------------------------

    def hasScheduleProvider(self, station_uuid: str) -> bool:

        return station_uuid in self._schedule_providers

    # ------------------------------------------------------------------

    def getSchedule(self, station: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Return the upcoming programme lineup for `station` (a
        RadioBrowser-shaped dict, same as InternetRadioManager already
        hands around), via whichever provider is registered for its
        stationuuid. Returns an empty list when no provider is
        registered, or when the provider itself raises -- a schedule
        being unavailable is never allowed to disrupt anything else in
        the application (PLAYBACK_CONTROLLER_SPEC.md's general
        principle that metadata problems must never affect playback
        applies here too, even though EPGManager itself never touches
        playback).
        """

        station_uuid = station.get("stationuuid")

        provider = self._schedule_providers.get(station_uuid)

        if provider is None:

            logger.verbose(f"[EPG] No schedule provider for station {station_uuid}.")

            return []

        try:
            schedule = provider.getSchedule(station)

        except Exception as error:

            self._log(f"Schedule provider for station {station_uuid} failed: {error}")

            return []

        logger.verbose(f"[EPG] Schedule for station {station_uuid}: {len(schedule)} entr(y/ies).")

        return schedule

    # ------------------------------------------------------------------

    def getCurrentProgramme(self, station: Dict[str, Any], now: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Return whichever schedule entry from getSchedule(station)
        covers `now` (real time, defaulting to the current moment), or
        None when there's no schedule data or nothing covers this
        moment.
        """

        if now is None:
            now = time.time()

        for entry in self.getSchedule(station):

            start = entry.get("start")

            end = entry.get("end")

            if start is not None and end is not None and start <= now < end:

                return entry

        return None

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> dict:

        return {
            "specification_version": self.SPECIFICATION_VERSION,
            "schedule_providers_registered": len(self._schedule_providers),
        }


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

epg_manager = EPGManager()

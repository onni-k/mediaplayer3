# ==============================================================================
#
# MediaPlayer3
#
# File        : bauer_nowplaying_provider.py
#
# Description :
#
#     BauerNowPlayingProvider
#
#     A concrete NowPlayingProvider (epg_manager.py) for Bauer Media
#     Finland stations (Radio Nova, Iskelmä, Radio City, Radio Rock
#     and the rest of the rayo.fi/radioplay.fi portfolio).
#
#     Unlike Yle (yle_teletext_provider.py), Bauer publishes no
#     official developer API for this at all. What this module uses
#     instead, confirmed working end to end by the user
#     (2026-08-02): rayo.fi's own station pages are Next.js pages
#     that embed the station's current now-playing data directly in
#     the page's __NEXT_DATA__ payload
#     (props.initialState.station.data.stationNowPlaying) --
#     genuinely current data (confirmed against real playback: track
#     title, artist, duration, image, and timestamp all matched), not
#     a stale cache. This was found only after three other avenues
#     were tried and ruled out:
#
#       1. The user's own original script (bare "https://radioplay.fi")
#          was not an API endpoint at all.
#       2. RadioDNS SPI 3.1 (an open, documented standard Bauer does
#          publish an endpoint for, listenapi.planetradio.co.uk) --
#          confirmed working, but confirmed to cover ONLY Bauer UK's
#          DAB broadcast services; zero Finnish stations found among
#          141 entries.
#       3. A third-party Lyrion Media Server plugin author has working
#          PlanetRadio now-playing support, but the plugin's source
#          isn't public, so its exact endpoint couldn't be inspected.
#
#     No equivalent embedded data was found for schedule/song-history
#     (props.initialState.schedule/playlist.items are both empty on
#     initial page load -- the site fetches those separately, client-
#     side, via a call this investigation didn't identify). This
#     module is now-playing only; EPG_MANAGER_SPEC.md's Bauer section
#     documents the schedule gap as still open.
#
# Implements :
#
#     EPG_MANAGER_SPEC.md's NowPlayingProvider interface
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
#   - Initial version, built directly from real, user-confirmed page
#     data for Radio Nova (rayo.fi/radio-nova/playlist) -- not guessed
#     at. See this file's own header for the full path that led here
#     and what was ruled out first.
#   - Confirmed the same mechanism against three more stations: Iskelmä
#     and Radio City both returned real, current now-playing data
#     immediately (rayo.fi/iskelma, rayo.fi/radio-city); "suomirock"
#     was a wrong slug guess (HTTP 404), removed rather than left in
#     as a broken entry. Also confirmed a real, normal edge case while
#     testing: Radio Nova can return stationNowPlaying with empty
#     nowPlayingTrack/nowPlayingArtist (station not reporting a
#     specific track at that moment) -- getNowPlaying() already
#     checked for this correctly (title and artist both empty ->
#     unavailable), so no code change was needed here, just
#     confirmation that the existing check handles a real response
#     shape, not only the happy path.
#   - Confirmed 8 more station slugs in one pass, guessed from Bauer's
#     own published Finnish station roster using simple
#     lowercase/hyphenated naming: basso, ysari, kasari, suomirap,
#     radio-classic, nrj, radio-nostalgia, radio-pooki -- all 8
#     returned live, current now-playing data on the first try. Radio
#     City and Basso also showed the same empty-now-playing state
#     Radio Nova did in the previous round, at 3 different stations in
#     the same test run -- confirms this is a real, recurring,
#     ordinary condition (not a one-off fluke, not specific to one
#     station), not something to special-case or treat as an error.
#   - Confirmed the last 6 stations in Bauer's published Finnish
#     roster: kiss, radio-957, auran-aallot, radio-pori, fresh, rodeo
#     -- all 6 slug guesses correct, 5 returned live now-playing data
#     immediately and radio-957 showed the same confirmed-normal empty
#     state. This completes the roster except "SuomiRock", whose slug
#     is still unknown (the one guess, out of 18, that returned HTTP
#     404) -- 17 of Bauer's 18 published Finnish stations now have a
#     confirmed working slug.
#   - Found the last one. "suomirock" (no hyphen) had returned HTTP
#     404; "suomi-rock" (with a hyphen) succeeded, and was confirmed
#     to genuinely be the SuomiRock station -- not just a page that
#     happened to return HTTP 200 -- via its own
#     stationBrandCode == "FI_SUOMIROCK" and stationName == "SuomiRock"
#     in the fetched page's data, plus live now-playing data at the
#     time of the test. This completes Bauer's entire published
#     Finnish station roster: all 18 stations now have a confirmed
#     working slug.
# ------------------------------------------------------------------------------

"""
BauerNowPlayingProvider -- Bauer Media Finland (Rayo) now-playing
info, extracted from each station's own Next.js page payload.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from ...epg_manager import NowPlayingProvider
from ...logger import logger

# Confirmed real station page slugs (2026-08-02, all 18 fetched and
# verified -- 15 returned live now-playing data immediately, the
# other 3 returned the page correctly but with the empty now-playing
# state described in this file's getNowPlaying() docstring --
# confirmed a real, recurring, normal condition at 3+ different
# stations, not a fluke). This is Bauer's ENTIRE published Finnish
# station roster, complete -- "suomi-rock" (with a hyphen) was the
# correct SuomiRock slug; "suomirock" (no hyphen, the first guess)
# was wrong. Confirmed via stationBrandCode == "FI_SUOMIROCK" in the
# page's own data, not just a successful HTTP fetch. Exposed so
# callers can register additional Bauer Finland stations without
# editing this file, as long as the station has its own
# rayo.fi/<slug> page.
KNOWN_STATION_SLUGS = {
    "radio-nova": "radio-nova",
    "iskelma": "iskelma",
    "radio-city": "radio-city",
    "basso": "basso",
    "ysari": "ysari",
    "kasari": "kasari",
    "suomirap": "suomirap",
    "radio-classic": "radio-classic",
    "nrj": "nrj",
    "radio-nostalgia": "radio-nostalgia",
    "radio-pooki": "radio-pooki",
    "kiss": "kiss",
    "radio-957": "radio-957",
    "auran-aallot": "auran-aallot",
    "radio-pori": "radio-pori",
    "fresh": "fresh",
    "rodeo": "rodeo",
    "suomirock": "suomi-rock",
}

_NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.DOTALL,
)


class BauerNowPlayingProvider(NowPlayingProvider):
    """
    Fetches a single Bauer Media Finland station's rayo.fi page and
    extracts its embedded now-playing data. One instance per station
    -- construct with that station's page slug (see
    KNOWN_STATION_SLUGS) and register it with EPGManager under
    whatever key identifies the station in your application:

        from ...epg_manager import epg_manager
        from .bauer_nowplaying_provider import BauerNowPlayingProvider, KNOWN_STATION_SLUGS

        epg_manager.registerNowPlayingProvider(
            "radio-nova",
            BauerNowPlayingProvider(KNOWN_STATION_SLUGS["radio-nova"]),
        )
    """

    BASE_URL = "https://rayo.fi"

    # A real desktop browser User-Agent -- confirmed necessary during
    # investigation; some responses differ by client type.
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def __init__(self, station_slug: str, timeout_seconds: float = 8.0) -> None:

        self._station_slug = station_slug
        self._timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------

    def getNowPlaying(self, station: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a dict shaped per NowPlayingProvider's interface
        (available/title/artist/organization).
        """

        try:
            html = self._fetchPage()

        except Exception as error:

            logger.info(f"[BauerNowPlaying] Fetch failed for '{self._station_slug}': {error}")

            return {"available": False}

        try:
            return self._parseNowPlaying(html)

        except Exception as error:

            logger.info(f"[BauerNowPlaying] Parse failed for '{self._station_slug}': {error}")

            return {"available": False}

    # ------------------------------------------------------------------

    def _fetchPage(self) -> str:

        url = f"{self.BASE_URL}/{self._station_slug}"

        request = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})

        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:

            return response.read().decode("utf-8", errors="replace")

    # ------------------------------------------------------------------

    def _parseNowPlaying(self, html: str) -> Dict[str, Any]:

        match = _NEXT_DATA_PATTERN.search(html)

        if not match:
            return {"available": False}

        data = json.loads(match.group(1))

        now_playing = (
            data.get("props", {})
            .get("initialState", {})
            .get("station", {})
            .get("data", {})
            .get("stationNowPlaying", {})
        )

        title = now_playing.get("nowPlayingTrack", "")

        artist = now_playing.get("nowPlayingArtist", "")

        if not title and not artist:
            return {"available": False}

        return {
            "available": True,
            "title": title,
            "artist": artist,
            "organization": "",
        }

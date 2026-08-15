# ==============================================================================
#
# MediaPlayer3
#
# File        : finland_radio_epg_registry.py
#
# Description :
#
#     The missing piece between "a YleTeletextScheduleProvider and a
#     BauerNowPlayingProvider exist and are confirmed working" and "a
#     station the user actually plays shows EPG/now-playing data" --
#     something has to recognize that the RadioBrowser station the
#     user just tuned to IS Yle Radio 1, or Radio Nova, and register
#     the matching provider for its real stationuuid. Nothing did
#     that before this file: the providers and EPGManager's whole
#     registration mechanism existed and were unit-tested, but no code
#     anywhere ever called registerScheduleProvider()/
#     registerNowPlayingProvider() for a real station. Confirmed
#     missing by the user's own testing: "Radiolla en saanut epg
#     toimimaan. Mitenköhän se yhdistää soitetun kanavan ja
#     epg-tiedon?"
#
#     RadioBrowser identifies stations by stationuuid, which is
#     opaque and not something this project has confirmed values for
#     ahead of time (unlike the Yle Teksti-TV page numbers and Bauer
#     rayo.fi slugs, both confirmed against real data in earlier
#     sessions). Matching is therefore done by STATION NAME instead --
#     normalized (lowercased, punctuation/whitespace collapsed) and
#     checked as a substring match, not exact equality, since the
#     exact string RadioBrowser uses for e.g. "Yle Radio 1" hasn't
#     been confirmed either (could carry a country suffix, different
#     capitalization, etc.). This is inherently best-effort -- see
#     this file's own verbose logging, which records the normalized
#     name checked and whether anything matched, so the next real
#     device test either confirms this works or reveals exactly what
#     the real station names look like so the patterns can be
#     corrected.
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
# 2026-08-03  Build 0009 (device test round 2)
#   - Initial version. Not yet confirmed against real RadioBrowser
#     station names -- see this file's own header.
# ------------------------------------------------------------------------------

"""
finland_radio_epg_registry -- matches a real RadioBrowser station to
a known Yle/Bauer EPG provider by (normalized, best-effort) name, and
registers it with EPGManager.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .epg_manager import epg_manager
from .epg_providers.Finland_radio_epg.bauer_nowplaying_provider import (
    KNOWN_STATION_SLUGS as BAUER_STATION_SLUGS,
    BauerNowPlayingProvider,
)
from .epg_providers.Finland_radio_epg.yle_teletext_provider import (
    KNOWN_STATION_PAGES as YLE_STATION_PAGES,
    YleTeletextScheduleProvider,
)
from .epg_providers.Finland_radio_epg import yle_credentials
from .logger import logger

# Normalized (see _normalize()) name fragments -> Yle Teksti-TV page
# key (matching yle_teletext_provider.KNOWN_STATION_PAGES). Written by
# hand from Yle's own station names, NOT confirmed against real
# RadioBrowser listings except where a change history entry below
# says otherwise.
#
# Order matters: "ylex3m" MUST be checked before "ylex", since "ylex"
# is itself a substring of "ylex3m" ("Yle X3M" would otherwise
# incorrectly match as YleX first) -- found and fixed while writing
# this, not from a device test.
#
# Build 0009, multi-image device test round (2026-08-07): confirmed
# via real logs (OpenViX/OpenPLI/OpenATV/OpenBH) that Yle Vega never
# matched -- RadioBrowser's real name is "Yle radio Vega Ostnyland"
# (note "radio" between "Yle" and "Vega", plus a regional suffix,
# mirroring "YLE radio Suomi, Jyvaskyla" confirmed earlier -- Yle
# Radio Suomi already matched fine since "yleradiosuomi" already
# included "radio", but "ylevega" never did). Added "yleradiovega" as
# the correct pattern; kept "ylevega" too in case some other Vega
# regional variant omits "radio".
_YLE_NAME_PATTERNS = {
    "yleradio1": "yle-radio-1",
    "yleradiosuomi": "yle-radio-suomi",
    "yleradiovega": "yle-vega",
    "ylevega": "yle-vega",
    "ylex3m": "yle-x3m",
    "ylex": "ylex",
}

# Normalized name fragments -> Bauer/Rayo slug key (matching
# bauer_nowplaying_provider.KNOWN_STATION_SLUGS). Also hand-written,
# not confirmed against real RadioBrowser listings. Longer/more
# specific fragments are listed first where one name could otherwise
# be a substring of another (e.g. "radionova" is unambiguous, but
# order still matters for anything added later).
# Build 0009, multi-image device test round (2026-08-07): confirmed
# via a real log that Bauer's "Radio Nostalgia" is listed on
# RadioBrowser as just "Nostalgia" -- no "Radio" prefix at all
# (stream URL confirmed it's genuinely stream-redirect.bauermedia.fi/
# nostalgia/..., the same Bauer station). "radionostalgia" alone never
# matched it. Added "nostalgia" as a second, shorter pattern for that
# one (confirmed), and applied the same precaution to the other
# "radio<name>"-only Bauer patterns below (city/classic/pooki/957/
# pori) since they follow the identical naming convention and could
# plausibly drop the prefix the same way -- NOT individually
# confirmed against RadioBrowser the way Nostalgia was, but safe to
# add regardless: each short pattern maps to the exact same station
# key as its "radio"-prefixed counterpart, so there's no risk of
# matching the wrong station, only of matching one that was already
# going to match anyway.
_BAUER_NAME_PATTERNS = {
    "radionova": "radio-nova",
    "iskelma": "iskelma",
    "radiocity": "radio-city",
    "city": "radio-city",
    "suomirock": "suomirock",
    "suomirap": "suomirap",
    "radioclassic": "radio-classic",
    "classic": "radio-classic",
    "radionostalgia": "radio-nostalgia",
    "nostalgia": "radio-nostalgia",
    "radiopooki": "radio-pooki",
    "pooki": "radio-pooki",
    "radio957": "radio-957",
    "957": "radio-957",
    "auranaallot": "auran-aallot",
    "radiopori": "radio-pori",
    "pori": "radio-pori",
    "basso": "basso",
    "ysari": "ysari",
    "kasari": "kasari",
    "kiss": "kiss",
    "fresh": "fresh",
    "rodeo": "rodeo",
    "nrj": "nrj",
}

_NORMALIZE_PATTERN = re.compile(r"[^a-z0-9]+")

# Transliterated before stripping non-alphanumeric characters, or
# "Iskelmä"/"Ysäri"/"SuomiRäp" would normalize to "iskelm"/"ysri"/
# "suomirp" (ä/ö simply dropped, not matching this file's own
# "iskelma"/"ysari"/"suomirap" patterns at all) -- found by testing
# all 23 known stations against realistic names, not from a device
# test. å is included for completeness even though none of the
# station names in this file currently use it.
_TRANSLITERATION = str.maketrans("äöå", "aoa")


def _normalize(name: str) -> str:
    """
    Lowercases, transliterates Scandinavian characters, and strips
    everything but letters/digits, so "Yle Radio 1", "yle-radio-1",
    "YLE RADIO 1 (FI)" and "Iskelmä" all normalize to something
    comparable ("yleradio1", "yleradio1", "yleradio1fi", "iskelma").
    Deliberately loose -- see this file's own header for why exact
    matching isn't used.
    """

    return _NORMALIZE_PATTERN.sub("", name.lower().translate(_TRANSLITERATION))


def registerProvidersForStation(station: Dict[str, Any]) -> None:
    """
    Call whenever Internet Radio playback starts for `station`
    (RadioBrowser-shaped dict, needs at least "name" and
    "stationuuid"). Matches the station's name against known Yle/
    Bauer stations and registers the appropriate provider(s) with
    EPGManager under this station's real stationuuid, if not already
    registered. Safe to call every time a station starts playing,
    including repeatedly for the same station -- registration is
    idempotent (EPGManager.registerScheduleProvider()/
    registerNowPlayingProvider() simply overwrite any existing entry
    for the same key).
    """

    station_uuid = station.get("stationuuid")

    station_name = station.get("name")

    if not station_uuid or not station_name:
        return

    normalized_name = _normalize(station_name)

    logger.verbose(f"[FinlandRadioEPG] Checking station for a known EPG source: name={station_name!r}, normalized={normalized_name!r}")

    yle_key = _matchYle(normalized_name)

    if yle_key is not None:

        _registerYle(station_uuid, yle_key)

        return

    bauer_key = _matchBauer(normalized_name)

    if bauer_key is not None:

        _registerBauer(station_uuid, bauer_key)

        return

    logger.info(f"[FinlandRadioEPG] No known EPG source matched '{station_name}'.")


# ------------------------------------------------------------------------------


def _matchYle(normalized_name: str) -> Optional[str]:

    for pattern, key in _YLE_NAME_PATTERNS.items():

        if pattern in normalized_name:

            return key

    return None


# ------------------------------------------------------------------------------


def _matchBauer(normalized_name: str) -> Optional[str]:

    for pattern, key in _BAUER_NAME_PATTERNS.items():

        if pattern in normalized_name:

            return key

    return None


# ------------------------------------------------------------------------------


def _registerYle(station_uuid: str, yle_key: str) -> None:

    # Build 0010, device test round 16: "Yle txt -koodin voisi laittaa
    # salattuna mukaan, kuten on podcast index koodikin laitettu.
    # Erillistä tiedostosta lukemista ei silloin tarvita." Was a
    # direct cfg.epg.yle_app_id/yle_app_key read before this round --
    # now goes through yle_credentials.resolveCredentials(), which
    # still prefers the user's own Settings-provided pair first, and
    # only falls back to a bundled default (see that module's own
    # header for why it's currently a placeholder) rather than simply
    # giving up when the user hasn't configured one.
    credentials = yle_credentials.resolveCredentials()

    if credentials is None:

        logger.info(
            f"[FinlandRadioEPG] Matched Yle station ({yle_key}) but no app_id/app_key available "
            "(Settings -> Yle EPG app_id/app_key, or a bundled default) -- skipping registration."
        )

        return

    app_id, app_key = credentials

    page_number = YLE_STATION_PAGES.get(yle_key)

    if page_number is None:
        return

    provider = YleTeletextScheduleProvider(page_number, app_id, app_key)

    epg_manager.registerScheduleProvider(station_uuid, provider)

    logger.info(f"[FinlandRadioEPG] Registered Yle Teletext schedule provider for stationuuid={station_uuid} (page {page_number}).")


# ------------------------------------------------------------------------------


def _registerBauer(station_uuid: str, bauer_key: str) -> None:

    slug = BAUER_STATION_SLUGS.get(bauer_key)

    if slug is None:
        return

    provider = BauerNowPlayingProvider(slug)

    epg_manager.registerNowPlayingProvider(station_uuid, provider)

    logger.info(f"[FinlandRadioEPG] Registered Bauer now-playing provider for stationuuid={station_uuid} (slug {slug}).")

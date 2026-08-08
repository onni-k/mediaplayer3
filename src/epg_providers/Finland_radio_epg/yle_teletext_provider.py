# ==============================================================================
#
# MediaPlayer3
#
# File        : yle_teletext_provider.py
#
# Description :
#
#     YleTeletextScheduleProvider
#
#     A concrete EPGScheduleProvider (epg_manager.py) for Yle radio
#     stations, using Yle's Teletext API -- confirmed by the user to
#     be working with their own registered app_id/app_key (2026-08-02
#     test run against pages 349/340/341/342/777/778, all succeeded).
#
#     This is the ONLY currently-open Yle API for this purpose --
#     the older, purpose-built programs/nowplaying and
#     programs/schedules endpoints (whose URL shape and "service id"
#     naming, e.g. "yle-radio-1", inspired the user's original script)
#     were officially deprecated in spring 2021 and are no longer
#     part of Yle's public API surface (confirmed directly from
#     developer.yle.fi: "The following API is currently open:
#     Teletext"). Teletext pages are TV-screen-formatted text (40
#     columns per line), not a structured programme object -- this
#     module parses "HH.MM Title" lines out of that text. Titles
#     longer than the remaining line width are truncated by Yle's own
#     teletext renderer before this code ever sees them; there is no
#     way to recover the missing text from this API.
#
# Implements :
#
#     EPG_MANAGER_SPEC.md's EPGScheduleProvider interface
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
#   - Initial version, built directly from real, user-confirmed
#     Teletext API responses (not guessed at) for six pages: 349
#     (general "Radiossa nyt" overview, all stations), 340 (Yle Radio
#     1), 341 (YleX), 342 (Yle Radio Suomi), 777 (Yle Vega), 778 (Yle
#     X3M). Page numbers 340-342 read from Yle Teksti-TV's own page
#     300 index; 777/778 supplied directly by the user.
#   - Rewrote the parser as a state machine after the user's own real
#     test output revealed two things the initial version got wrong:
#     (1) titles routinely continue on to further lines with no time
#     prefix ("19.02 Jazzklubin viikon keikka: aja" / "monet Tampere
#     Jazz Happeningissä." / ">346") -- the original parser silently
#     dropped every continuation line; (2) a single page can cover
#     MULTIPLE days across its subpages (a fresh "Maanantai 3.8."
#     date line partway through), not just "today" as first assumed
#     -- the original parser read the date once from the first
#     subpage and never updated it. Also added hyphenation handling
#     for wrapped words ("Kylä-" + "liuhala" -> "Kylä-liuhala", no
#     space) distinguished from real dash punctuation ("Tolkien -" +
#     "radikalhögerns..." -> "Tolkien - radikalhögerns...", keeps its
#     space) by whether the trailing hyphen has a space before it.
#     Verified against fixtures reconstructed from the user's own
#     real output for four of the five stations (Radio 1, YleX, Radio
#     Suomi, Vega), plus the Vega/X3M header line's own quirk (the
#     subpage counter appears on the same line as "Radio", not
#     isolated the way it is on the other three stations' pages).
#
# 2026-08-02  Build 0009 (planning, cont.)
#   - Moved from src/ into src/epg_providers/Finland_radio_epg/ at the
#     user's request, to give Finnish radio EPG providers a shared,
#     dedicated home as more are added (Bauer Media/Rayo next).
#     Relative imports adjusted accordingly (three dots instead of
#     one, to reach epg_manager.py/logger.py from two directories
#     deeper).
# ------------------------------------------------------------------------------

"""
YleTeletextScheduleProvider -- Yle radio schedules via the Teksti-TV
(Teletext) API, the only Yle API currently open to the public for
this purpose.
"""

from __future__ import annotations

import json
import re
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...epg_manager import EPGScheduleProvider
from ...logger import logger

TELETEXT_BASE_URL = "https://external.api.yle.fi/v1/teletext/pages"

# Confirmed real page numbers (see this file's change history) --
# 340-342 from Yle Teksti-TV's own page 300 index, 777/778 supplied
# by the user directly. Exposed so callers can build providers for
# additional stations without editing this file, if Yle adds/moves
# pages in the future.
KNOWN_STATION_PAGES = {
    "yle-radio-1": 340,
    "ylex": 341,
    "yle-radio-suomi": 342,
    "yle-vega": 777,
    "yle-x3m": 778,
}

# "19.02 Jazzklubin viikon keikka: aja" -- one or two digit hour,
# always two-digit minute, separated by a literal '.', followed by
# whitespace and the (possibly further-truncated -- see LINE_IS_A_*
# patterns below) title. Anchored to the start of the line after
# stripping leading spaces -- Teksti-TV pads every line to a fixed
# 40-column width with leading/trailing spaces for on-screen
# centering/alignment, which carries no schedule meaning and must be
# stripped before matching.
_SCHEDULE_LINE = re.compile(r"^(\d{1,2})\.(\d{2})\s+(.+?)\s*$")

# A "D.M." date, e.g. "2.8." or "3.8." -- appears both on the page's
# very first line (combined with the station name and weekday, e.g.
# "Yle Radio 1       Sunnuntai 2.8.") and, confirmed by a real user
# test run, standalone on later subpages whenever the schedule crosses
# into a new day (e.g. "        Maanantai 3.8."). Matches either
# weekday name (Finnish or Swedish -- Vega/X3M use Swedish) without
# needing to parse the name itself, only the date that follows it.
_DATE_LINE = re.compile(r"(\d{1,2})\.(\d{1,2})\.\s*$")

# A bare subpage counter, e.g. "1/5" or "2/3", right-padded to the
# 40-column width -- appears on every subpage and must never be
# mistaken for a title continuation line.
_SUBPAGE_COUNTER = re.compile(r"^\d+/\d+$")

# A trailing internal cross-reference to another teletext page, e.g.
# "...radikalhögerns nya guru >346" -- stripped from the end of a
# title/continuation line since it points at a page number, not
# programme content.
_PAGE_REFERENCE = re.compile(r"\s*>\d+\s*$")


class YleTeletextScheduleProvider(EPGScheduleProvider):
    """
    Fetches and parses a single Yle radio station's Teksti-TV
    schedule page. One instance per station -- construct with that
    station's page number (see KNOWN_STATION_PAGES) and register it
    with EPGManager under whatever key identifies the station in your
    application:

        from ...epg_manager import epg_manager
        from .yle_teletext_provider import YleTeletextScheduleProvider, KNOWN_STATION_PAGES

        epg_manager.registerScheduleProvider(
            "yle-radio-1",
            YleTeletextScheduleProvider(KNOWN_STATION_PAGES["yle-radio-1"], app_id, app_key),
        )
    """

    def __init__(self, page_number: int, app_id: str, app_key: str, timeout_seconds: float = 8.0) -> None:

        self._page_number = page_number
        self._app_id = app_id
        self._app_key = app_key
        self._timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------

    def getSchedule(self, station: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Returns entries shaped per EPGScheduleProvider's interface
        (start/end unix timestamps, title). Only ever covers the
        single day Yle's own page currently displays -- there is no
        confirmed "tomorrow" page for radio the way TV channels have
        one (Teksti-TV's own page 300 index lists tomorrow/day-after
        pages for TV channels only); requesting a schedule for any
        other day will simply return what today's page currently
        shows, which the caller must not mistake for that other day's
        actual schedule.
        """

        try:
            page_data = self._fetchPage()

        except Exception as error:

            # Build 0009, device test round 5: a device log showed
            # "Fetch failed for page 342: 'ascii' codec can't encode
            # character '\u01e9' in position 49" -- genuinely unclear
            # from the error message alone which line actually raised
            # this (url/headers here are pure ASCII by construction;
            # the error's own str() doesn't say where it originated).
            # Logging the full traceback so the next device test
            # pinpoints the exact source instead of guessing again.
            logger.info(f"[YleTeletext] Fetch failed for page {self._page_number}: {error}\n{traceback.format_exc()}")

            return []

        try:
            return self._parseSchedule(page_data)

        except Exception as error:

            logger.info(f"[YleTeletext] Parse failed for page {self._page_number}: {error}\n{traceback.format_exc()}")

            return []

    # ------------------------------------------------------------------

    def _fetchPage(self) -> dict:
        """
        Build 0009, device test round 7: a device log's full traceback
        (added the previous round specifically to pin this down)
        confirmed the "'ascii' codec can't encode character" failure
        happens inside http.client's putrequest() while constructing
        the HTTP request line itself -- i.e. something in the URL
        isn't pure ASCII, even though app_id/app_key are meant to be
        plain hex strings. The exact origin (Settings' ConfigText
        storage, a copy-paste artifact when the user entered them,
        something else) is still unconfirmed, but urllib.parse.quote()
        makes the request safe regardless of what's actually in
        there, and .strip() guards against stray leading/trailing
        whitespace from config storage/display padding.
        """

        app_id = urllib.parse.quote(self._app_id.strip())

        app_key = urllib.parse.quote(self._app_key.strip())

        url = f"{TELETEXT_BASE_URL}/{self._page_number}.json?app_id={app_id}&app_key={app_key}"

        request = urllib.request.Request(url, headers={"User-Agent": "MediaPlayer3-EPG/0.1"})

        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:

            raw_data = response.read().decode("utf-8")

            return json.loads(raw_data)

    # ------------------------------------------------------------------

    def _parseSchedule(self, page_data: dict) -> List[Dict[str, Any]]:
        """
        Walks every line of every subpage in order, maintaining two
        pieces of state as it goes -- both confirmed necessary by a
        real Teksti-TV response, not anticipated up front:

        1. The current date. Teksti-TV does NOT always cover only
           "today" as originally assumed -- a real response showed a
           later subpage containing a fresh date line
           ("        Maanantai 3.8.") partway through, after which
           every subsequent "HH.MM Title" line belongs to THAT day,
           not the page's original date. The date must therefore be
           tracked as it changes, not read once from the first
           subpage.

        2. The entry currently being built. A programme's title
           routinely continues on to further lines with no time
           prefix, e.g.:

               19.02 Jazzklubin viikon keikka: aja
                     monet Tampere Jazz Happeningissä.
                     >346

           A naive parser that only matches "HH.MM Title" lines would
           silently drop "monet Tampere Jazz Happeningissä." entirely
           -- continuation lines are appended to whichever entry is
           currently open, until the next schedule line, date line, or
           blank line closes it.
        """

        page = page_data["teletext"]["page"]

        subpages = page.get("subpage", [])

        if isinstance(subpages, dict):
            subpages = [subpages]

        entries: List[Dict[str, Any]] = []

        current_date: Optional[datetime] = None
        open_entry: Optional[Dict[str, Any]] = None

        for subpage in subpages:

            for content_block in subpage.get("content", []):

                if content_block.get("type") != "text":
                    continue

                for line in content_block.get("line", []):

                    text = line.get("Text", "").strip()

                    if not text or _SUBPAGE_COUNTER.match(text):

                        # Blank lines and subpage counters ("1/5")
                        # neither start nor extend an entry, but a
                        # blank line does mark the end of whichever
                        # title was accumulating continuation lines.
                        open_entry = None

                        continue

                    date_match = _DATE_LINE.search(text)

                    schedule_match = _SCHEDULE_LINE.match(text)

                    if date_match and not schedule_match:

                        current_date = self._resolveDate(
                            int(date_match.group(1)), int(date_match.group(2))
                        )

                        open_entry = None

                        continue

                    if schedule_match:

                        hour, minute, title = schedule_match.groups()

                        start = self._toTimestamp(current_date, int(hour), int(minute))

                        title = _PAGE_REFERENCE.sub("", title).strip()

                        if start is None:

                            open_entry = None

                            continue

                        open_entry = {"start": start, "title": title}

                        entries.append(open_entry)

                        continue

                    if open_entry is not None:

                        continuation = _PAGE_REFERENCE.sub("", text).strip()

                        if continuation:

                            title_so_far = open_entry["title"]

                            # Word-wrap hyphenation ("Sonny Kylä-" +
                            # "liuhala" -> "Sonny Kylä-liuhala") has no
                            # space before the trailing hyphen -- a
                            # real dash used as punctuation ("Tolkien
                            # -" + "radikalhögerns...") does, and must
                            # still get a space when joined.
                            is_wrapped_word = (
                                title_so_far.endswith("-") and not title_so_far.endswith(" -")
                            )

                            if is_wrapped_word:

                                open_entry["title"] = f"{title_so_far}{continuation}"

                            else:

                                open_entry["title"] = f"{title_so_far} {continuation}".strip()

        entries.sort(key=lambda entry: entry["start"])

        return self._fillEndTimes(entries)

    # ------------------------------------------------------------------

    def _resolveDate(self, day: int, month: int) -> Optional[datetime]:
        """
        Resolves a "D.M." date against the current year -- Teksti-TV's
        own pages never print a year, since a station's schedule page
        never runs more than a few days ahead. Handles the one
        genuine ambiguity this creates: in late December, a "1.1."
        line means next year, not this one.
        """

        now = datetime.now()

        year = now.year

        if month == 1 and now.month == 12:

            year += 1

        try:
            return datetime(year, month, day)

        except ValueError:

            return None

    # ------------------------------------------------------------------

    def _toTimestamp(self, schedule_date: Optional[datetime], hour: int, minute: int) -> Optional[float]:

        if schedule_date is None or not (0 <= hour <= 23) or not (0 <= minute <= 59):
            return None

        try:
            moment = schedule_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        except ValueError:

            return None

        return time.mktime(moment.timetuple())

    # ------------------------------------------------------------------

    def _fillEndTimes(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Teksti-TV only ever states when something starts, never when
        it ends -- each entry's end is inferred as the next entry's
        start, and the last entry of the (single) day this page
        covers is given an end of midnight. Genuinely uncertain right
        up against that boundary -- a programme actually continuing
        past midnight would be reported as ending at midnight
        regardless.
        """

        result = []

        for index, entry in enumerate(entries):

            if index + 1 < len(entries):

                end = entries[index + 1]["start"]

            else:

                start_dt = datetime.fromtimestamp(entry["start"])

                midnight = start_dt.replace(hour=23, minute=59, second=59) 

                end = time.mktime(midnight.timetuple())

            result.append({"start": entry["start"], "end": end, "title": entry["title"]})

        return result

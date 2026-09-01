# ==============================================================================
#
# MediaPlayer3
#
# File        : internetradio_manager.py
#
# Description :
#
#     InternetRadioManager
#
#     Owns all Internet Radio functionality: RadioBrowser API
#     communication, station search/filtering, favorite lists,
#     listening history and stream preparation. All RadioBrowser
#     communication is encapsulated here -- no other module accesses
#     the API directly.
#
#     Uses Python's standard library `urllib` (no third-party HTTP
#     library assumed present on the receiver) against the public
#     RadioBrowser API at https://api.radio-browser.info/, modelled
#     on the endpoint conventions of the pyradios reference project
#     (checked per user request -- see docs/Claude_notes_build0007.txt).
#
# Implements :
#
#     INTERNETRADIO_MANAGER_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md (Build 0007 -- new Core module)
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
# 2026-07-19  Build 0007
#   - Initial version. NOT YET VERIFIED against a real network
#     connection (this sandbox has no network egress) -- every
#     request is defensively wrapped so a network failure degrades to
#     an empty result rather than raising, but the actual RadioBrowser
#     endpoint/response shapes need real-device confirmation. See
#     docs/Claude_notes_build0007.txt.
#
# 2026-07-19  Build 0007 (device test round 1)
#   - Fixed a real bug found on device: every request to
#     "https://api.radio-browser.info/..." returned HTTP 404. The
#     plain domain does not serve API requests directly -- confirmed
#     against the official docs, the pyradios reference project and
#     the user-provided serverlist_python3.py example: the API
#     requires resolving "all.api.radio-browser.info" via DNS,
#     reverse-resolving each IP to a mirror hostname, and calling one
#     of those mirrors instead. Added _discoverServers()/_getServers()
#     and rewrote _apiGet() to try each discovered mirror in turn
#     (retry-on-failure, matching the example script), caching
#     whichever mirror last answered successfully so subsequent
#     requests try it first.
#
# 2026-07-24  Build 0007 (device test round 3)
#   - Added downloadFavicon(): downloads and caches a station's
#     favicon image (by URL hash, under StorageManager.getCachePath()),
#     for MainScreen to use as cover art while playing that station.
#     Keeps all network I/O centralized here rather than in the Screen
#     layer. Not yet verified against a real network connection --
#     favicon URLs are hosted by individual stations, not RadioBrowser
#     itself, so their reachability/format can vary far more widely.
#
# 2026-07-24  Build 0007 (device test round 4)
#   - Fixed a real CRASH confirmed by a device log: RadioBrowser can
#     return the literal string "null" for a missing favicon field
#     (not JSON null/empty). That string is truthy in Python, so it
#     passed downloadFavicon()'s `if not favicon_url` check and
#     reached urllib.request.Request(), which raised an uncaught
#     ValueError ("unknown url type: 'null'") that took down the
#     whole enigma2 process. Added _cleanUrlField(), a shared helper
#     that rejects "null"/"none"/"n/a" sentinel strings, applied to
#     downloadFavicon() and (as defense in depth) prepareStream()'s
#     url/url_resolved fields too, since they come from the same API
#     and could plausibly have the same quirk. Also moved
#     urllib.request.Request() construction inside the try/except in
#     downloadFavicon() as a second layer of defense.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 Internet Radio management.

RadioBrowser (https://api.radio-browser.info/) is a community-run,
mirrored station database with no API key requirement. Confirmed on a
real device (Build 0007 test round 1): the plain
"api.radio-browser.info" hostname does NOT serve API requests
directly (every request returned HTTP 404) -- the API requires
resolving "all.api.radio-browser.info" via DNS, reverse-resolving
each returned IP to a mirror hostname, and calling one of those
mirrors instead. This is documented in RadioBrowser's own API docs
and matches both the pyradios reference project and the
serverlist_python3.py example script the user provided; the earlier
assumption that the base domain round-robins on its own was wrong.
"""

from __future__ import annotations

import json
import os
import random
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from .compatibility import compatibility
from .logger import logger
from .project import PROJECT_NAME, VERSION
from .storage import storage_manager

# Used only to discover the actual mirror servers via DNS -- never
# queried for station data itself (see _discoverServers()).
MIRROR_DISCOVERY_HOST = "all.api.radio-browser.info"

# Fallback mirror, used only if DNS-based discovery itself fails
# (e.g. no DNS resolution available at all) -- a single, long-lived
# RadioBrowser mirror, better than having no fallback whatsoever.
FALLBACK_SERVER = "https://de1.api.radio-browser.info"

# Device test round 70 -- per direct request: RadioBrowser's own API
# documentation (api.radio-browser.info) asks clients to identify
# themselves via User-Agent; this now also names the actual runtime
# (Enigma2, and the specific Python version already exposed by
# compatibility.py's own getPythonVersion() -- reused rather than
# querying sys.version/platform directly a second time) so
# RadioBrowser's own maintainers can see what environments are
# actually querying their database, not just which app version.
# compatibility.getPythonVersion() only reads a value cached once at
# CompatibilityLayer's own construction (platform.python_version()),
# so calling it here at module import time is safe and free of I/O.
USER_AGENT = f"{PROJECT_NAME}/{VERSION} (Enigma2; Python/{compatibility.getPythonVersion()})"

REQUEST_TIMEOUT_SECONDS = 8

DEFAULT_SEARCH_LIMIT = 100

DEFAULT_FAVORITE_LIST = "General"

DEFAULT_HISTORY_SIZE = 50


class InternetRadioManager:
    """
    Owns RadioBrowser communication, favorites and listening history.
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._favorites: Dict[str, List[Dict[str, Any]]] = {}
        self._history: List[Dict[str, Any]] = []

        # Discovered RadioBrowser mirror servers (see
        # _discoverServers()), cached after the first successful
        # discovery so every request doesn't re-run DNS resolution.
        # The last server that actually answered successfully is kept
        # at the front of the list, so subsequent requests try it
        # first rather than a random one every time.
        self._servers: List[str] = []

        # Build 0010 -- local station database cache (see
        # _loadStationDatabase()). None means "not yet loaded from
        # disk this process"; [] means "loaded, and genuinely empty".
        self._stations_db: Optional[List[Dict[str, Any]]] = None

        self._stations_db_updated: Optional[float] = None

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Radio] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._favorites = self._loadJSON(self._favoritesPath(), default={DEFAULT_FAVORITE_LIST: []})

        self._history = self._loadJSON(self._historyPath(), default=[])

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Local storage paths
    # ------------------------------------------------------------------

    def _favoritesPath(self) -> str:
        return os.path.join(storage_manager.getRadioPath(), "favorites.json")

    def _historyPath(self) -> str:
        return os.path.join(storage_manager.getRadioPath(), "history.json")

    # ------------------------------------------------------------------

    def _loadJSON(self, path: str, default: Any) -> Any:

        try:
            with open(path, encoding="utf-8") as handle:

                return json.load(handle)

        except (OSError, ValueError) as error:

            logger.verbose(f"[Radio] Unable to read {path}: {error}")

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

# End of Part 1
    # ------------------------------------------------------------------
    # RadioBrowser API communication
    # ------------------------------------------------------------------

    def _discoverServers(self) -> List[str]:
        """
        Discover RadioBrowser's currently available mirror servers via
        DNS (confirmed required on a real device -- see the module
        docstring above): resolve MIRROR_DISCOVERY_HOST to a set of
        IPs, then reverse-resolve each IP to a hostname. Matches the
        official API docs, the pyradios reference project and the
        user-provided serverlist_python3.py example script.

        Never raises. Returns FALLBACK_SERVER alone if DNS discovery
        itself fails entirely (e.g. no DNS available), so callers
        always have at least one server to try.
        """

        hosts = []

        try:
            addresses = socket.getaddrinfo(MIRROR_DISCOVERY_HOST, 80, 0, 0, socket.IPPROTO_TCP)

            for entry in addresses:

                ip = entry[4][0]

                try:
                    hostname = socket.gethostbyaddr(ip)[0]

                    if hostname not in hosts:
                        hosts.append(hostname)

                except (socket.herror, socket.gaierror, OSError) as error:

                    logger.verbose(f"[Radio] Reverse DNS lookup failed for {ip}: {error}")

        except (socket.gaierror, OSError) as error:

            self._log(f"RadioBrowser mirror discovery failed: {error}")

        if not hosts:

            self._log(f"No mirrors discovered via DNS; using fallback server {FALLBACK_SERVER}.")

            return [FALLBACK_SERVER]

        hosts.sort()

        servers = [f"https://{host}" for host in hosts]

        logger.verbose(f"[Radio] Discovered {len(servers)} RadioBrowser mirror(s): {', '.join(servers)}\n")

        return servers

    # ------------------------------------------------------------------

    def _getServers(self) -> List[str]:
        """
        Return the cached mirror server list, discovering it first if
        this is the first request. The list is cached for the process
        lifetime -- mirrors don't change often enough to justify
        re-running DNS discovery on every single request.
        """

        if not self._servers:

            self._servers = self._discoverServers()

        return self._servers

    # ------------------------------------------------------------------

    def _apiGet(self, endpoint: str, params: Optional[Dict[str, Any]] = None):
        """
        GET `endpoint` (with `params` as the query string) from a
        RadioBrowser mirror, trying each discovered mirror in turn
        until one answers successfully -- matching the retry-on-
        failure behaviour of the official example script
        (serverlist_python3.py's downloadRadiobrowser()).

        Never raises. Returns None if every mirror fails, so every
        caller can treat None the same way as "no results" rather than
        needing its own try/except. Every request/response is logged
        at verbose level only (INTERNETRADIO_MANAGER_SPEC.md "Verbose
        logging additionally records: RadioBrowser requests, API
        responses").
        """

        if params:

            # RadioBrowser is documented as case-sensitive for tag
            # parameters (confirmed in the pyradios reference project,
            # checked per user request).
            for key in ("tag", "tagList"):

                if key in params and isinstance(params[key], str):
                    params[key] = params[key].lower()

            query_string = "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})

        else:

            query_string = ""

        servers = self._getServers()

        # Try the cached "last known good" server first (servers[0]),
        # then the rest in random order -- same strategy as the
        # official example script, just biased toward whatever worked
        # most recently instead of a fresh random pick every time.
        ordered_servers = servers[:1]

        remaining = servers[1:]

        random.shuffle(remaining)

        ordered_servers += remaining

        for server in ordered_servers:

            url = server + "/" + endpoint + query_string

            logger.verbose(f"[Radio] RadioBrowser request\n\nURL: {url}\n")

            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

            try:
                with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:

                    body = response.read().decode("utf-8", errors="replace")

            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as error:

                logger.verbose(f"[Radio] Mirror {server} failed: {error}")

                continue

            try:
                data = json.loads(body)

            except ValueError as error:

                logger.verbose(f"[Radio] Mirror {server} returned unparseable response: {error}")

                continue

            logger.verbose(f"[Radio] RadioBrowser response\n\nItems: {len(data) if isinstance(data, list) else 1}\n")

            # This server just answered successfully -- keep it first
            # for the next request.
            if self._servers and self._servers[0] != server:

                self._servers = [server] + [s for s in self._servers if s != server]

            return data

        self._log(f"RadioBrowser request failed on all {len(ordered_servers)} mirror(s).")

        return None

    # ------------------------------------------------------------------
    # Search (INTERNETRADIO_MANAGER_SPEC.md "Search")
    # ------------------------------------------------------------------

    def search(
        self,
        name: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
    ) -> List[Dict[str, Any]]:
        """
        Search for stations matching any combination of
        `name`/`country`/`language`/`tag`.

        Build 0010, BUILD_0010_PLAN.md "RadioBrowser Database" /
        RADIOBROWSER_SPEC.md "Local Station Database": searches the
        local station database first, so browsing works without a
        live RadioBrowser round-trip on every keystroke/filter change
        (and works at all when the network is unavailable). Falls
        back to a live RadioBrowser search only if the local database
        has never been populated yet (getStationDatabaseInfo()'s own
        "count" is 0) -- once populated, the local copy is
        authoritative for search; updateStationDatabase() is the only
        method that talks to the live API for station data.

        Returns a list of station dicts (RadioBrowser's own field
        names -- stationuuid, name, url, url_resolved, homepage,
        favicon, tags, country, language, codec, bitrate, votes,
        lastcheckok, ...), or an empty list if nothing matched (or,
        pre-first-sync, the request failed). Never raises.
        """

        self._log("Search started.")

        self._loadStationDatabase()

        if self._stations_db:

            filtered = self._filterStations(self._stations_db, name, country, language, tag)

            # Device test round 68 -- limit=0 means "no limit" (a new
            # user-facing setting, radio.search_limit, can be set to
            # 0 for exactly this), which needed its own explicit
            # check here: Python's own list[:0] slice returns an
            # EMPTY list, the opposite of what "0 = unlimited" needs.
            results = filtered if limit == 0 else filtered[:limit]

            self._log(f"Search completed (local database): {len(results)} station(s).")

            return results

        self._log("Local database empty -- falling back to a live RadioBrowser search.")

        params = {
            "name": name,
            "country": country,
            "language": language,
            "tag": tag,
            # Device test round 68 -- same "0 = unlimited" meaning as
            # the local-database path above, but RadioBrowser's own
            # API behaviour for a literal limit=0 isn't something this
            # project can verify -- reusing DATABASE_DOWNLOAD_LIMIT
            # (already trusted elsewhere in this file as "as many as
            # we'd ever realistically want") instead of assuming.
            "limit": self.DATABASE_DOWNLOAD_LIMIT if limit == 0 else limit,
            "hidebroken": "true",
            "order": "name",
        }

        logger.verbose(f"[Radio] Search filters\n\n{params}\n")

        results = self._apiGet("json/stations/search", params)

        if results is None:

            self._log("Search failed (RadioBrowser unreachable).")

            return []

        self._log(f"Search completed (live fallback): {len(results)} station(s).")

        return results

    # ------------------------------------------------------------------

    def _filterStations(
        self,
        stations: List[Dict[str, Any]],
        name: Optional[str],
        country: Optional[str],
        language: Optional[str],
        tag: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        In-memory filter over a station list, matching search()'s own
        parameter semantics as closely as practical against a static
        local copy: case-insensitive substring match on name/tag
        (RadioBrowser's own "fuzzy" behaviour for these), exact
        case-insensitive match on country/language (RadioBrowser
        stores these as fixed vocabulary values, not free text).
        Results are name-sorted, matching the live API's own
        "order": "name" search parameter.
        """

        name_q = (name or "").strip().lower()
        country_q = (country or "").strip().lower()
        language_q = (language or "").strip().lower()
        tag_q = (tag or "").strip().lower()

        def matches(station: Dict[str, Any]) -> bool:

            if name_q and name_q not in str(station.get("name", "")).lower():
                return False

            if country_q and country_q != str(station.get("country", "")).lower():
                return False

            if language_q and language_q != str(station.get("language", "")).lower():
                return False

            if tag_q and tag_q not in str(station.get("tags", "")).lower():
                return False

            return True

        filtered = [station for station in stations if matches(station)]

        filtered.sort(key=lambda station: str(station.get("name", "")).lower())

        return filtered

    # ------------------------------------------------------------------

    def getCountries(self) -> List[Dict[str, Any]]:
        """
        Return {"name": ..., "stationcount": ...} country entries,
        aggregated from the local station database when one is
        available (Build 0010 -- avoids a separate live API call on
        every RadioBrowserScreen open), falling back to a live
        RadioBrowser request otherwise.
        """

        self._loadStationDatabase()

        if self._stations_db:

            return self._aggregateField("country")

        return self._apiGet("json/countries") or []

    # ------------------------------------------------------------------

    def getLanguages(self) -> List[Dict[str, Any]]:
        """
        Return {"name": ..., "stationcount": ...} language entries --
        see getCountries()'s own docstring for the local-database-
        first reasoning.
        """

        self._loadStationDatabase()

        if self._stations_db:

            return self._aggregateField("language")

        return self._apiGet("json/languages") or []

    # ------------------------------------------------------------------

    def _aggregateField(self, field: str) -> List[Dict[str, Any]]:
        """
        Build {"name": ..., "stationcount": ...} entries by counting
        distinct, non-empty values of `field` across the local station
        database -- the same shape RadioBrowser's own json/countries
        and json/languages endpoints return, so callers (RadioBrowser
        Screen's _reloadFilters()) don't need to know which source
        the data actually came from.
        """

        counts: Dict[str, int] = {}

        for station in self._stations_db:

            value = str(station.get(field, "")).strip()

            if not value:
                continue

            counts[value] = counts.get(value, 0) + 1

        entries = [{"name": name, "stationcount": count} for name, count in counts.items()]

        entries.sort(key=lambda entry: entry["name"].lower())

        return entries

    # ------------------------------------------------------------------

    def getTags(self) -> List[Dict[str, Any]]:

        return self._apiGet("json/tags") or []

    # ------------------------------------------------------------------
    # Local Station Database (Build 0010, BUILD_0010_PLAN.md
    # "RadioBrowser Database" / RADIOBROWSER_SPEC.md "Local Station
    # Database")
    # ------------------------------------------------------------------

    # Practical cap on a single bulk download -- RadioBrowser's full
    # global catalogue runs well into the tens of thousands of
    # stations, most of which are of no interest to any one listener
    # and would cost real storage/memory on a set-top box for little
    # benefit. hidebroken=true + ordering by click count (RadioBrowser's
    # own popularity signal) biases the local copy toward stations
    # actually worth having offline, rather than an arbitrary or
    # purely-alphabetical slice.
    #
    # Device test round 69 -- per direct request (a user comparing
    # against radio-browser.info's own reported totals -- 58362
    # stations, 88 of them Finnish -- found MediaPlayer3's own local
    # database stalled at exactly this constant's value, and asked for
    # the real full catalogue instead): this is now only the ultimate
    # safety ceiling (in case radio.search_limit is left at some very
    # large value by mistake), not the actual per-download target.
    # updateStationDatabase() below now honours radio.search_limit's
    # own "0 = unlimited" meaning (round 68) here too, fetched via
    # proper offset-based pagination in DATABASE_DOWNLOAD_PAGE_SIZE-
    # sized pages rather than one single oversized request -- a single
    # request for tens of thousands of stations was never confirmed to
    # actually work end-to-end against RadioBrowser's own live API
    # (unverifiable from this environment), whereas paging in
    # reasonably-sized chunks is the standard, robust way to fetch an
    # arbitrarily large result set from a REST API regardless of
    # whatever server-side per-request limit RadioBrowser may or may
    # not itself enforce.
    DATABASE_DOWNLOAD_LIMIT = 100000

    DATABASE_DOWNLOAD_PAGE_SIZE = 5000

    def _stationsDbPath(self) -> str:
        return os.path.join(storage_manager.getRadioPath(), "stations.json")

    # ------------------------------------------------------------------

    def _loadStationDatabase(self) -> None:
        """
        Load the local station database into memory, once per process
        lifetime (like _getServers()'s own mirror-list caching) --
        re-read only after updateStationDatabase()/clearStationDatabase()
        explicitly invalidate the cache.
        """

        if self._stations_db is not None:
            return

        data = self._loadJSON(self._stationsDbPath(), default=None)

        if not isinstance(data, dict) or not isinstance(data.get("stations"), list):

            self._stations_db = []

            self._stations_db_updated = None

            return

        self._stations_db = data["stations"]

        self._stations_db_updated = data.get("last_updated")

    # ------------------------------------------------------------------

    def getStationDatabaseInfo(self) -> Dict[str, Any]:
        """
        Return {"count": int, "last_updated": Optional[float]} for the
        local station database -- used by RadioBrowserScreen/
        SettingsScreen to show the user what's currently stored
        without needing to know the storage format themselves.
        """

        self._loadStationDatabase()

        return {"count": len(self._stations_db), "last_updated": self._stations_db_updated}

    # ------------------------------------------------------------------

    def shouldAutoUpdateDatabase(self) -> bool:
        """
        RADIOBROWSER_SPEC.md "Automatic Updates": "The update interval
        shall be configurable where appropriate. The default interval
        may be seven days." True when cfg.radio.database_auto_update
        is on AND (the database has never been populated, OR the
        configured interval has elapsed since the last successful
        update). Callers (RadioBrowserScreen's initial load) decide
        when/how to actually act on this -- this method only answers
        the question, it never triggers an update itself
        (RADIOBROWSER_SPEC.md "An automatic update shall not interrupt
        active playback" -- something only the caller's own context
        can guarantee).
        """

        try:
            from .config import config_manager

        except ImportError:

            return False

        if not config_manager.get("radio.database_auto_update", True):
            return False

        info = self.getStationDatabaseInfo()

        if info["count"] == 0:
            return True

        if info["last_updated"] is None:
            return True

        interval_days = config_manager.get("radio.database_update_interval_days", 7)

        elapsed_days = (time.time() - info["last_updated"]) / 86400.0

        return elapsed_days >= interval_days

    # ------------------------------------------------------------------

    def updateStationDatabase(self) -> bool:
        """
        Download a fresh station list from RadioBrowser and replace
        the local database with it.

        RADIOBROWSER_SPEC.md "Database Integrity": "Updates should
        preferably be written to a temporary location before replacing
        the active database. If the new database cannot be validated
        or written successfully, the previous valid database shall
        remain available." -- writes to a *.tmp path first, validates
        the parsed result is a non-empty list of station-shaped dicts,
        and only then renames it over the real path (os.replace() is
        atomic on the same filesystem, so a crash or power loss
        mid-write can never leave a half-written stations.json).
        RADIOBROWSER_SPEC.md "A normal update shall not remove
        existing stations before new station data has been
        successfully obtained." -- the existing file is never touched
        until the new one is confirmed good; any failure below leaves
        it completely untouched, exactly like the temp-podcast-episode-
        cache/playlist-refresh "failure keeps the old data" pattern
        already used elsewhere in this project (podcast_manager.py).

        Returns True on success, False on any failure (network,
        invalid response, empty result, write failure) -- never
        raises.
        """

        self._log("Station database update started.")

        from .config import config_manager

        # Device test round 69 -- reuses radio.search_limit (round 68)
        # as the actual download target too, not just the per-search
        # result cap: a user who sets this to 0 expects "no limit,
        # anywhere," matching the report that motivated this round.
        target_limit = config_manager.get("radio.search_limit", 100)

        if target_limit <= 0:

            target_limit = self.DATABASE_DOWNLOAD_LIMIT

        results = []

        offset = 0

        while len(results) < target_limit:

            page_size = min(self.DATABASE_DOWNLOAD_PAGE_SIZE, target_limit - len(results))

            params = {
                "hidebroken": "true",
                "order": "clickcount",
                "reverse": "true",
                "limit": page_size,
                "offset": offset,
            }

            page = self._apiGet("json/stations", params)

            if not isinstance(page, list) or not page:

                # Either a request failed (None) or RadioBrowser has
                # genuinely run out of stations to return (empty
                # list) -- either way, stop paginating rather than
                # looping forever. A failure partway through still
                # keeps whatever pages were already fetched, subject
                # to the same "keep the existing database on overall
                # failure" rule below (results is only trusted once
                # it passes the emptiness/validity check that follows
                # this loop).
                break

            results.extend(page)

            offset += len(page)

            if len(page) < page_size:

                # RadioBrowser returned fewer than asked for -- this
                # is the real end of the catalogue, not just this
                # page's own size; stop rather than requesting an
                # empty page next time round.
                break

        self._log(f"Station database update: fetched {len(results)} station(s) across {offset // self.DATABASE_DOWNLOAD_PAGE_SIZE + 1} page(s).")

        if not isinstance(results, list) or not results:

            self._log("Station database update failed (empty or invalid response); keeping existing database.")

            return False

        # Validate each entry is at least station-shaped (has a name
        # and a usable stream URL field) before trusting any of it --
        # RADIOBROWSER_SPEC.md "Validate the received data."
        valid = [
            station for station in results
            if isinstance(station, dict) and station.get("name") and (station.get("url") or station.get("url_resolved"))
        ]

        if not valid:

            self._log("Station database update failed (no valid stations in response); keeping existing database.")

            return False

        payload = {"last_updated": time.time(), "stations": valid}

        db_path = self._stationsDbPath()

        tmp_path = db_path + ".tmp"

        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            with open(tmp_path, "w", encoding="utf-8") as handle:

                json.dump(payload, handle, ensure_ascii=False)

            os.replace(tmp_path, db_path)

        except OSError as error:

            self._log(f"Station database update failed (write error, keeping existing database): {error}")

            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            except OSError:
                pass

            return False

        self._stations_db = valid

        self._stations_db_updated = payload["last_updated"]

        self._log(f"Station database updated: {len(valid)} station(s).")

        return True

    # ------------------------------------------------------------------

    def clearStationDatabase(self) -> bool:
        """
        RADIOBROWSER_SPEC.md / BUILD_0010_PLAN.md: "A separate 'Clear
        station list' operation may remove the existing stations" --
        deliberately distinct from a normal update, which never
        removes stations on its own. Does not touch Favorites
        (RADIOBROWSER_SPEC.md "Design Principles": "It shall not...
        Remove Favorites as a side effect of database updates.").
        """

        db_path = self._stationsDbPath()

        try:
            if os.path.exists(db_path):
                os.remove(db_path)

        except OSError as error:

            self._log(f"Unable to clear station database: {error}")

            return False

        self._stations_db = []

        self._stations_db_updated = None

        self._log("Station database cleared.")

        return True

# End of Part 2
    # ------------------------------------------------------------------
    # Stream preparation (INTERNETRADIO_MANAGER_SPEC.md "Stream Preparation")
    # ------------------------------------------------------------------

    def prepareStream(self, station: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate `station` and resolve its actual playable stream URL.

        RadioBrowser's own convention (confirmed in the pyradios
        reference project, checked per user request) is to call
        json/url/<uuid> before playback: this both registers a
        "click" (so the station's popularity stats stay meaningful)
        and returns "url_resolved", the actual stream URL after
        following any redirects -- using the raw "url" field directly
        is discouraged.

        Returns a dict with "url" (the resolved stream URL) and
        "name"/"station" (the original station dict), or None if the
        station has no usable stream URL at all. PlaybackController
        receives only this resolved URL -- never the RadioBrowser
        station dict itself (INTERNETRADIO_MANAGER_SPEC.md
        "PlaybackController receives only the final validated stream
        URL.").
        """

        stationuuid = station.get("stationuuid")

        fallback_url = self._cleanUrlField(station.get("url_resolved")) or self._cleanUrlField(station.get("url"))

        if not stationuuid:

            self._log("Station playback preparation failed: no stationuuid.")

            return {"url": fallback_url, "station": station} if fallback_url else None

        # Build 0009, device test round 10: a device log showed a
        # station's cover art still falling back to the default
        # artwork when played from History, even after History
        # entries started storing "favicon" -- traced to entries
        # saved BEFORE that fix (or otherwise missing the field)
        # perpetuating themselves: playing an incomplete History
        # entry fed the same incomplete dict straight back through
        # addHistoryEntry() below, so it never gained a favicon. If
        # "favicon" is missing/empty here, fetches the full, current
        # station record from RadioBrowser by stationuuid and merges
        # it in -- never overwrites fields the caller already
        # provided, only fills the gap. Best-effort: a failed lookup
        # (no network, station removed from RadioBrowser since,
        # mirror down) just leaves the dict as it was, same as before
        # this existed.
        if not station.get("favicon"):

            station = self._enrichStationData(station, stationuuid)

        self._log(f"Playback requested: {station.get('name', stationuuid)}")

        resolved = self._apiGet(f"json/url/{urllib.parse.quote(stationuuid, safe='')}")

        stream_url = None

        if isinstance(resolved, dict):

            stream_url = self._cleanUrlField(resolved.get("url")) or fallback_url

        if not stream_url:

            stream_url = fallback_url

        if not stream_url:

            self._log(f"Station playback preparation failed: no stream URL for {stationuuid}.")

            return None

        self.addHistoryEntry(station)

        return {"url": stream_url, "station": station}

    # ------------------------------------------------------------------

    def _enrichStationData(self, station: Dict[str, Any], stationuuid: str) -> Dict[str, Any]:
        """
        Fetches the current, full station record from RadioBrowser by
        stationuuid and merges any fields it has that `station` is
        missing (favicon in particular -- see prepareStream()'s own
        docstring for the bug this fixes) -- never overwrites a field
        the caller already had a value for, only fills genuine gaps.
        Best-effort: returns `station` unchanged if the lookup fails
        for any reason (no network, mirror down, station no longer
        listed), same as if this method didn't exist.
        """

        try:
            results = self._apiGet(f"json/stations/byuuid/{urllib.parse.quote(stationuuid, safe='')}")

        except Exception as error:

            self._log(f"Station enrichment lookup failed for {stationuuid}: {error}")

            return station

        if not isinstance(results, list) or not results:

            return station

        full_station = results[0]

        if not isinstance(full_station, dict):

            return station

        enriched = dict(full_station)

        enriched.update(station)

        for field_name in full_station:

            if not enriched.get(field_name) and full_station.get(field_name):

                enriched[field_name] = full_station[field_name]

        self._log(f"Station data enriched from RadioBrowser: {enriched.get('name', stationuuid)}")

        return enriched

    # ------------------------------------------------------------------

    @staticmethod
    def _cleanUrlField(value) -> Optional[str]:
        """
        Return `value` if it looks like a real URL, or None if it's
        empty or one of the "null"-ish sentinel strings RadioBrowser
        sometimes returns instead of JSON null/empty for a missing
        field (confirmed as a real crash for the favicon field on a
        real device -- see downloadFavicon()'s docstring and
        docs/Claude_notes_build0007.txt). Applied everywhere a
        RadioBrowser URL-shaped field is read, not just favicon.
        """

        if not value or not isinstance(value, str):
            return None

        if value.strip().lower() in ("null", "none", "n/a"):
            return None

        return value

    # ------------------------------------------------------------------
    # Favorite lists (INTERNETRADIO_MANAGER_SPEC.md "Favorite Lists")
    # ------------------------------------------------------------------

    def getFavoriteListNames(self) -> List[str]:

        return sorted(self._favorites.keys())

    # ------------------------------------------------------------------

    def createFavoriteList(self, name: str) -> bool:

        if name in self._favorites:
            return False

        self._favorites[name] = []

        self._log(f"Favorite list created: {name}")

        return self._saveFavorites()

    # ------------------------------------------------------------------

    def deleteFavoriteList(self, name: str) -> bool:

        if name not in self._favorites:
            return False

        del self._favorites[name]

        self._log(f"Favorite list deleted: {name}")

        return self._saveFavorites()

    # ------------------------------------------------------------------

    def renameFavoriteList(self, old_name: str, new_name: str) -> bool:

        if old_name not in self._favorites or new_name in self._favorites:
            return False

        self._favorites[new_name] = self._favorites.pop(old_name)

        return self._saveFavorites()

    # ------------------------------------------------------------------

    def getFavorites(self, list_name: str = DEFAULT_FAVORITE_LIST) -> List[Dict[str, Any]]:

        return list(self._favorites.get(list_name, []))

    # ------------------------------------------------------------------

    def addFavorite(self, station: Dict[str, Any], list_name: str = DEFAULT_FAVORITE_LIST) -> bool:

        self._favorites.setdefault(list_name, [])

        stationuuid = station.get("stationuuid")

        if stationuuid and any(entry.get("stationuuid") == stationuuid for entry in self._favorites[list_name]):

            self._log(f"Favorite already present: {station.get('name', stationuuid)}")

            return False

        self._favorites[list_name].append(station)

        self._log(f"Favorite added: {station.get('name', stationuuid)} -> {list_name}")

        return self._saveFavorites()

    # ------------------------------------------------------------------

    def removeFavorite(self, stationuuid: str, list_name: str = DEFAULT_FAVORITE_LIST) -> bool:

        entries = self._favorites.get(list_name, [])

        remaining = [entry for entry in entries if entry.get("stationuuid") != stationuuid]

        if len(remaining) == len(entries):
            return False

        self._favorites[list_name] = remaining

        self._log(f"Favorite removed: {stationuuid} <- {list_name}")

        return self._saveFavorites()

    # ------------------------------------------------------------------

    def _saveFavorites(self) -> bool:

        return self._saveJSON(self._favoritesPath(), self._favorites)

# End of Part 3
    # ------------------------------------------------------------------
    # History (INTERNETRADIO_MANAGER_SPEC.md "History")
    # ------------------------------------------------------------------

    def getHistory(self) -> List[Dict[str, Any]]:

        return list(self._history)

    # ------------------------------------------------------------------

    def addHistoryEntry(self, station: Dict[str, Any]) -> None:
        """
        Build 0009, device test round 8: previously always inserted a
        new entry regardless of whether the same station was already
        in the history, so playing the same station repeatedly filled
        the list with duplicates of itself. Now removes any existing
        entry for the same stationuuid first, per user request ("kun
        siihen lisataan kanava, niin ensin katsotaan onko sama kanava
        jo olemassa historia listalla ja poistetaan vanhat, etta
        jokainen kanava on vain 1 kerran historialistalla") -- the
        station still always ends up at the top (most recent), it
        just doesn't also linger at its old position anymore.
        """

        station_uuid = station.get("stationuuid")

        if station_uuid is not None:

            self._history = [entry for entry in self._history if entry.get("stationuuid") != station_uuid]

        entry = {
            "name": station.get("name", "Unknown"),
            "stream_url": station.get("url_resolved") or station.get("url", ""),
            "stationuuid": station_uuid,
            # Build 0009, device test round 9: history entries never
            # stored this, so a station played from History always
            # fell back to the default artwork -- confirmed by the
            # user's own comparison ("Latautuu kylla kun soitetaan
            # muulta listalta", i.e. it DID load from Favorites,
            # whose station dicts come straight from RadioBrowser and
            # always carry this field).
            "favicon": station.get("favicon", ""),
            # Device test round 28: same problem, same shape, for the
            # Information Panel's Codec and Station Information pages
            # this time -- both read these fields straight off
            # whatever "current station" dict MainScreen hands them
            # (information_panel.py's _fillCodecFallbacksFromStation()/
            # _buildStationPage()), and a History entry is exactly
            # that "current station" dict every time playback started
            # from RadioBrowserScreen's own search results (Round 26's
            # own fix routes display state through History specifically
            # because a station just played is always guaranteed to be
            # at History[0]). Without these, both pages showed nothing
            # for the vast majority of stations right after Round 26,
            # not because of anything actually wrong with the station
            # or its stream -- confirmed from a real device log
            # (History-sourced playback, systematically checking many
            # Finnish stations) where ffprobe's own failures for
            # several streams made the gap especially visible, but the
            # missing station-metadata fallback was the deeper,
            # always-present cause underneath that.
            "codec": station.get("codec", ""),
            "bitrate": station.get("bitrate", ""),
            "country": station.get("country", ""),
            "language": station.get("language", ""),
            "tags": station.get("tags", ""),
            "homepage": station.get("homepage", ""),
            "timestamp": time.time(),
        }

        self._history.insert(0, entry)

        max_size = self._getMaxHistorySize()

        del self._history[max_size:]

        self._saveJSON(self._historyPath(), self._history)

        self._log(f"History updated: {entry['name']}")

    # ------------------------------------------------------------------

    def clearHistory(self) -> bool:

        self._history = []

        self._log("History cleared.")

        return self._saveJSON(self._historyPath(), self._history)

    # ------------------------------------------------------------------

    def _getMaxHistorySize(self) -> int:

        try:
            from .config import config_manager

            return int(config_manager.get("radio.history_size", DEFAULT_HISTORY_SIZE))

        except Exception:
            return DEFAULT_HISTORY_SIZE

    # ------------------------------------------------------------------
    # Favicon (Build 0007, device test round 3)
    # ------------------------------------------------------------------

    def downloadFavicon(self, favicon_url: str) -> Optional[str]:
        """
        Download and cache a station's favicon image, returning the
        local cached file path, or None if `favicon_url` is empty or
        the download fails.

        Requested after real device testing ("MainScreen -näkymässä
        Voisi laittaa kuvakkeeksi radiokanavan kuvakkeen, jos on
        saatavilla"). Cached by a hash of the URL under
        StorageManager.getCachePath() so the same station's icon isn't
        re-downloaded every time it plays; MainScreen's ePicLoad-based
        artwork display needs a filesystem path, not raw bytes, the
        same way embedded/folder artwork already does.

        Never raises. Not yet verified against a real network
        connection (this sandbox has no network egress) -- the
        RadioBrowser mirror-connectivity fix (device test round 1)
        confirms network calls DO work on a real device, but favicon
        URLs are hosted by individual stations, not RadioBrowser
        itself, so their reachability/format can vary far more widely
        and specifically hasn't been confirmed yet.
        """

        favicon_url = self._cleanUrlField(favicon_url)

        if not favicon_url:

            # RadioBrowser sometimes returns the literal string "null"
            # for a station with no favicon (not JSON null/empty) --
            # confirmed as a real crash on a real device: this string
            # is truthy in Python, so it passed a plain `if not
            # favicon_url` check and reached urllib.request.Request(),
            # which raised an uncaught ValueError ("unknown url type:
            # 'null'") that took down the whole enigma2 process (see
            # docs/Claude_notes_build0007.txt). _cleanUrlField() now
            # catches this consistently everywhere a RadioBrowser
            # URL-shaped field is read.
            return None

        import hashlib

        extension = os.path.splitext(urllib.parse.urlparse(favicon_url).path)[1]

        if not extension or len(extension) > 5:
            extension = ".ico"

        cache_key = hashlib.sha1(favicon_url.encode("utf-8")).hexdigest()

        cache_path = os.path.join(storage_manager.getCachePath(), f"favicon_{cache_key}{extension}")

        if os.path.isfile(cache_path) and os.path.getsize(cache_path) > 0:

            return cache_path

        logger.verbose(f"[Radio] Downloading favicon\n\nURL: {favicon_url}\n")

        # Request() construction moved inside the try/except as
        # defense in depth -- any other malformed URL RadioBrowser
        # might return should degrade to "no favicon" the same way a
        # network failure already does, never crash the caller.
        try:
            request = urllib.request.Request(favicon_url, headers={"User-Agent": USER_AGENT})

            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:

                data = response.read()

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as error:

            logger.verbose(f"[Radio] Favicon download failed: {error}")

            return None

        if not data:
            return None

        try:
            os.makedirs(storage_manager.getCachePath(), exist_ok=True)

            with open(cache_path, "wb") as handle:

                handle.write(data)

        except OSError as error:

            self._log(f"Unable to cache favicon: {error}")

            return None

        return cache_path

    # ------------------------------------------------------------------
    # Diagnostics (Build 0007 -- Developer Mode)
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> Dict[str, Any]:

        return {
            "mirror_discovery_host": MIRROR_DISCOVERY_HOST,
            "discovered_servers": ", ".join(self._servers) if self._servers else "Not yet discovered",
            "favorite_lists": ", ".join(self.getFavoriteListNames()) or "None",
            "favorite_count": sum(len(v) for v in self._favorites.values()),
            "history_count": len(self._history),
            "radio_path": storage_manager.getRadioPath(),
        }

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"InternetRadioManager(favorite_lists={len(self._favorites)}, history={len(self._history)})"


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

internetradio_manager = InternetRadioManager()


# ==============================================================================
#
# Build Notes
#
# InternetRadioManager depends on StorageManager, Logger and
# ConfigurationManager (for history size only). It never depends on
# BrowserScreen, RadioBrowserScreen or PlaybackController
# implementation details (INTERNETRADIO_MANAGER_SPEC.md
# "Dependencies").
#
# All RadioBrowser communication is defensive: _apiGet() never raises,
# degrading to None (treated as "no results") on any network/parse
# failure. This has NOT been verified against a live network
# connection (no network egress in the sandbox this was written in);
# see docs/Claude_notes_build0007.txt for what still needs real-device
# confirmation.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

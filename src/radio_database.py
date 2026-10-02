# ==============================================================================
#
# MediaPlayer3
#
# File        : radio_database.py
#
# Description :
#
#     RadioStationDatabase
#
#     SQLite-backed local station database for InternetRadioManager
#     (round 198 introduced a streaming JSONL format specifically to
#     avoid the memory pressure of loading the full RadioBrowser
#     catalogue into memory at once; round 200 adds this SQLite-backed
#     store on top of it, keeping the JSONL implementation as a
#     fallback for a receiver whose Python build doesn't include the
#     sqlite3 module -- see internetradio_manager.py's own round 200
#     comment). Every consumer (search/getCountries/getLanguages/
#     getStationDatabaseInfo) now runs as an indexed SQL query instead
#     of a full linear scan+parse of every stored station, which is
#     what made round 198's fix for the MEMORY problem still slow in
#     practice (bounded memory, but still O(n) CPU time per query).
#
#     Stores the FULL original station dict as a JSON blob per row
#     (never losing/needing to enumerate individual RadioBrowser
#     fields, matching every other part of this project that treats a
#     station as an opaque dict), plus a handful of precomputed,
#     indexed lowercase "shadow" columns (name/country/language/tags)
#     purely so SQLite's own query planner can filter/sort without
#     ever touching the JSON blob for a non-matching row.
#
# Implements :
#
#     RADIOBROWSER_SPEC.md "Local Station Database"
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
# 2026-09-30  Build 0010 (round 200)
#   - Initial version, per direct request + three example files the
#     user supplied illustrating the general approach (a different
#     schema/API shape than this project's own conventions -- this
#     module follows this project's own existing station-dict/filter
#     semantics exactly instead of adopting those examples verbatim,
#     so behaviour matches internetradio_manager.py's own established
#     search()/getCountries()/getLanguages() contracts precisely).
#     NOT YET VERIFIED against a real device -- see
#     compatibility.py's own hasSqlite3() for why this is guarded
#     rather than assumed.
# ------------------------------------------------------------------------------

"""
SQLite-backed local RadioBrowser station database.

Only imported/used when compatibility.hasSqlite3() is True --
internetradio_manager.py falls back to the round-198 JSONL streaming
implementation otherwise. See that module's own round-200 comment.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from .logger import logger


class RadioStationDatabase:
    """
    One instance per on-disk database file (InternetRadioManager keeps
    exactly one, at storage_manager.getRadioPath()/stations.db).

    Every write (replaceAll()/migrateFromJsonl()) rebuilds the whole
    table from scratch inside a single transaction, matching this
    project's own existing "never remove existing stations before new
    station data has been successfully obtained" invariant
    (RADIOBROWSER_SPEC.md) -- done via a temp file + atomic rename
    (open_sqlite_and_replace()'s own docstring), never by deleting
    rows from the live, already-open database file in place.
    """

    # Commit every this many inserted rows during a bulk load, rather
    # than one single multi-tens-of-thousands-of-rows transaction --
    # keeps a single commit's own memory/lock overhead bounded, and
    # gives a progress-reporting hook (unused here, but keeps this in
    # the same shape as internetradio_manager.py's own paginated
    # download loop for consistency).
    BATCH_SIZE = 2000

    def __init__(self, db_path: str) -> None:

        self._db_path = db_path

        self._conn: Optional[sqlite3.Connection] = None

        self._open()

    # ------------------------------------------------------------------

    def _open(self) -> None:

        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        self._conn = sqlite3.connect(self._db_path, timeout=10.0)

        # Manual transaction control (BEGIN/commit/rollback issued
        # explicitly below) rather than Python's own sqlite3 module
        # auto-managing one -- avoids the two mechanisms disagreeing
        # about whether a transaction is already open (which raises
        # "cannot start a transaction within a transaction" the moment
        # this module's own explicit BEGIN collides with sqlite3's
        # own implicit one).
        self._conn.isolation_level = None

        self._conn.row_factory = sqlite3.Row

        self._initSchema()

    # ------------------------------------------------------------------

    def _initSchema(self) -> None:

        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY,
                stationuuid TEXT,
                name TEXT NOT NULL,
                name_lower TEXT NOT NULL,
                country_lower TEXT,
                language_lower TEXT,
                tags_lower TEXT,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_stations_name_lower
                ON stations(name_lower);
            CREATE INDEX IF NOT EXISTS idx_stations_country_lower
                ON stations(country_lower);
            CREATE INDEX IF NOT EXISTS idx_stations_language_lower
                ON stations(language_lower);
            """
        )

        self._conn.commit()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    @staticmethod
    def _escapeLike(value: str) -> str:
        """
        Escapes SQLite LIKE's own wildcard characters (% and _) in
        user-supplied search text, plus the escape character itself --
        paired with "ESCAPE '\\'" in every query below. Without this,
        a station name search containing a literal "%" or "_" (both
        appear in real station names/tags) would silently behave as a
        wildcard instead of a literal character.
        """

        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def search(
        self,
        name: Optional[str],
        country: Optional[str],
        language: Optional[str],
        tag: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Same parameter semantics as internetradio_manager.py's own
        search()/_stationMatches() (round 198): case-insensitive
        substring match on name/tag, exact case-insensitive match on
        country/language, name-sorted results, limit=0 meaning "no
        limit". Every filter here runs as a native SQL WHERE clause
        against the indexed shadow columns -- the (potentially large)
        `data` JSON blob is only ever deserialized for rows that
        actually made it into the final, already-filtered/limited
        result set, not for every row in the table.
        """

        name_q = (name or "").strip().lower()
        country_q = (country or "").strip().lower()
        language_q = (language or "").strip().lower()
        tag_q = (tag or "").strip().lower()

        clauses = []
        params: List[Any] = []

        if name_q:
            clauses.append("name_lower LIKE ? ESCAPE '\\'")
            params.append(f"%{self._escapeLike(name_q)}%")

        if country_q:
            clauses.append("country_lower = ?")
            params.append(country_q)

        if language_q:
            clauses.append("language_lower = ?")
            params.append(language_q)

        if tag_q:
            clauses.append("tags_lower LIKE ? ESCAPE '\\'")
            params.append(f"%{self._escapeLike(tag_q)}%")

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        query = f"SELECT data FROM stations {where} ORDER BY name_lower"

        if limit != 0:
            query += " LIMIT ?"
            params.append(limit)

        try:
            cursor = self._conn.execute(query, params)

            return [json.loads(row["data"]) for row in cursor.fetchall()]

        except MemoryError:

            # Round 200: the one combination that can still exhaust
            # memory -- no filter narrows the row set AND limit=0
            # (unlimited), so the final result set really is the
            # whole database. Every other combination stays bounded
            # by either a selective WHERE clause or a SQL-level LIMIT,
            # which SQLite applies before this process ever
            # materializes the matching rows as Python objects.
            # Matches internetradio_manager.py's own round-198
            # MemoryError handling for the equivalent JSONL-streaming
            # case -- degrade this one query gracefully rather than
            # crash.
            logger.verbose(
                "[Radio] Out of memory collecting every local station with "
                "no filter and no limit (SQLite path)."
            )

            raise

    # ------------------------------------------------------------------

    def getCountries(self) -> List[Dict[str, Any]]:
        return self._aggregate("country_lower")

    def getLanguages(self) -> List[Dict[str, Any]]:
        return self._aggregate("language_lower")

    def _aggregate(self, column: str) -> List[Dict[str, Any]]:
        """
        {"name": ..., "stationcount": ...} entries, aggregated with a
        single native SQL GROUP BY -- SQLite counts and groups the
        already-indexed shadow column directly, never touching the
        `data` blob at all for this (the original-case display name
        needed for each group is fetched via MIN(name), i.e.
        whichever original-case spelling happens to sort first --
        RadioBrowser's own country/language names are consistently
        spelled per value in practice, so this is equivalent to the
        old per-station-dict aggregation in every case that matters).
        """

        query = (
            f"SELECT MIN(name) AS display, {column} AS key_value, COUNT(*) AS n "
            f"FROM stations WHERE {column} IS NOT NULL AND {column} != '' "
            f"GROUP BY {column} ORDER BY {column}"
        )

        cursor = self._conn.execute(query)

        # The aggregated field itself (country/language) isn't stored
        # in its original casing separately from `data` -- re-deriving
        # a display name from MIN(name) would be wrong (that's the
        # STATION name, not the country/language name). Look the
        # original-case value up from one representative row per
        # group instead; still one indexed query per group, not a
        # full-table scan.
        entries = []

        for row in cursor.fetchall():

            key_value = row["key_value"]

            sample = self._conn.execute(
                f"SELECT data FROM stations WHERE {column} = ? LIMIT 1",
                (key_value,),
            ).fetchone()

            if sample is None:
                continue

            station = json.loads(sample["data"])

            field = "country" if column == "country_lower" else "language"

            display_name = str(station.get(field, key_value)).strip() or key_value

            entries.append({"name": display_name, "stationcount": row["n"]})

        entries.sort(key=lambda entry: entry["name"].lower())

        return entries

    # ------------------------------------------------------------------

    def getInfo(self) -> Dict[str, Any]:

        count = self._conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0]

        row = self._conn.execute("SELECT value FROM meta WHERE key = 'last_updated'").fetchone()

        last_updated = float(row["value"]) if row is not None and row["value"] is not None else None

        return {"count": count, "last_updated": last_updated}

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def replaceAll(self, stations: List[Dict[str, Any]], last_updated: float) -> None:
        """
        Rebuilds the whole `stations` table from `stations`, inside a
        single transaction (all-or-nothing: a failure partway through
        rolls back to the previous, still-intact table rather than
        leaving a half-written database). Called only after
        internetradio_manager.py's own updateStationDatabase() has
        already confirmed the freshly-downloaded data is valid and
        non-empty -- this never runs against a partial/failed
        download.
        """

        try:
            self._conn.execute("BEGIN")

            self._conn.execute("DELETE FROM stations")

            self._insertBatch(stations)

            self._conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_updated', ?)",
                (str(last_updated),),
            )

            self._conn.commit()

        except Exception:

            self._conn.rollback()

            raise

        self._conn.execute("VACUUM")

    # ------------------------------------------------------------------

    def migrateFromJsonl(self, jsonl_path: str, last_updated: Optional[float]) -> int:
        """
        One-time migration for an install upgrading from round 198's
        own stations.jsonl (streams it line by line -- never
        materializes the whole file as a Python list at once, keeping
        the same memory-bounded property round 198 itself introduced)
        into this SQLite database. Returns the number of stations
        migrated (0 if the file didn't exist or contained nothing
        usable).
        """

        migrated = 0

        try:
            self._conn.execute("BEGIN")

            self._conn.execute("DELETE FROM stations")

            batch: List[Dict[str, Any]] = []

            with open(jsonl_path, encoding="utf-8") as handle:

                for line in handle:

                    line = line.strip()

                    if not line:
                        continue

                    try:
                        station = json.loads(line)

                    except ValueError:
                        continue

                    if not isinstance(station, dict):
                        continue

                    batch.append(station)

                    if len(batch) >= self.BATCH_SIZE:

                        self._insertBatch(batch)

                        migrated += len(batch)

                        batch = []

            if batch:

                self._insertBatch(batch)

                migrated += len(batch)

            if last_updated is not None:

                self._conn.execute(
                    "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_updated', ?)",
                    (str(last_updated),),
                )

            self._conn.commit()

        except OSError as error:

            self._conn.rollback()

            logger.verbose(f"[Radio] Unable to migrate {jsonl_path} to SQLite: {error}")

            return 0

        except Exception:

            self._conn.rollback()

            raise

        if migrated:
            self._conn.execute("VACUUM")

        return migrated

    # ------------------------------------------------------------------

    def _insertBatch(self, stations: List[Dict[str, Any]]) -> None:

        rows = []

        for station in stations:

            name = str(station.get("name", ""))

            country = str(station.get("country", "") or "")

            language = str(station.get("language", "") or "")

            tags = str(station.get("tags", "") or "")

            rows.append(
                (
                    station.get("stationuuid"),
                    name,
                    name.lower(),
                    country.lower() or None,
                    language.lower() or None,
                    tags.lower() or None,
                    json.dumps(station, ensure_ascii=False),
                )
            )

        self._conn.executemany(
            """
            INSERT INTO stations
                (stationuuid, name, name_lower, country_lower, language_lower, tags_lower, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    # ------------------------------------------------------------------

    def clear(self) -> None:

        self._conn.execute("DELETE FROM stations")

        self._conn.execute("DELETE FROM meta")

        self._conn.commit()

        self._conn.execute("VACUUM")

    # ------------------------------------------------------------------

    def close(self) -> None:

        if self._conn is not None:

            try:
                self._conn.close()

            except sqlite3.Error:
                pass

            self._conn = None

#end_of_file

# ==============================================================================
#
# MediaPlayer3
#
# File        : library_manager.py
#
# Description :
#
#     LibraryManager
#
#     Metadata-based view of the music collection: scans
#     library.scan_directory, reads each supported audio file's
#     metadata (metadata.py -- the same manual-parsing reader
#     PlaybackController uses, no third-party dependency), and builds
#     an in-memory index browsable/searchable by artist, album, genre
#     and year. Never performs playback -- always hands
#     MusicLibraryScreen a plain list of file paths (a PlaybackQueue)
#     for PlaybackController.playQueue() to consume, exactly like
#     BrowserScreen/PlaylistScreen already do.
#
# Implements :
#
#     LIBRARY_MANAGER_SPEC.md v0.1
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
#   - Fixed untagged artist/album/genre/year showing generic "Unknown"
#     instead of "Unknown Artist"/"Unknown Album"/etc: metadata.py's
#     own UNKNOWN placeholder is a non-empty string, so a plain
#     `value or default` never fell through to this module's own,
#     more specific labels. Added _orDefault() to check for both
#     empty/None and the UNKNOWN sentinel explicitly.
#
# 2026-07-29  Build 0008 (device test round 2)
#   - Added verbose logging for scan()/search(): per-file index
#     details and an index summary (track/artist/album/genre/year
#     counts), requested after device testing showed nothing in the
#     log for library activity at all. The actual scan-finding-
#     nothing bug this round turned out to be in config.py
#     (library.scan_directory was never registered in _ENTRIES) --
#     see config.py's own change history.
# ------------------------------------------------------------------------------

"""
LibraryManager -- metadata-based music library index, search and
PlaybackQueue generation.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .config import config_manager
from .constants import SUPPORTED_AUDIO_EXTENSIONS
from .localization import _
from .logger import logger
from .metadata import UNKNOWN, metadata_reader


class LibraryManager:
    """
    Builds and serves a metadata-based index of the local music
    collection, independent of BrowserScreen's filesystem view
    (LIBRARY_MANAGER_SPEC.md).
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        # Not scanned automatically on construction -- scanning a
        # large collection is a genuinely slow, blocking filesystem +
        # metadata-parsing walk (LIBRARY_MANAGER_SPEC.md "The library
        # may be refreshed manually"). MusicLibraryScreen triggers the
        # first scan itself, the same "please wait" deferred-timer
        # pattern RadioBrowserScreen's search already uses (Build
        # 0007, device test round 8) so the UI isn't left looking
        # frozen.
        self._tracks: List[Dict[str, Any]] = []

        self._scanned = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Library] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Scanning (LIBRARY_MANAGER_SPEC.md "Responsibilities" /
    # "Library Updates" / "Error Handling")
    # ------------------------------------------------------------------

    def scan(self, directory: Optional[str] = None) -> int:
        """
        (Re)build the index by walking `directory` (or
        library.scan_directory when not given). Unreadable files are
        skipped and logged, never raised -- "Scanning errors are
        written to the application log but never terminate the
        application." Returns the number of tracks indexed.
        """

        scan_directory = directory or config_manager.get("library.scan_directory", "")

        self._tracks = []

        if not scan_directory or not os.path.isdir(scan_directory):

            self._log(f"Scan directory not available: '{scan_directory}'")

            self._scanned = True

            return 0

        self._log(f"Scanning '{scan_directory}'.")

        for root, _dirs, files in os.walk(scan_directory):

            for filename in files:

                if not filename.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):
                    continue

                filepath = os.path.join(root, filename)

                entry = self._readTrack(filepath, filename)

                if entry is not None:

                    self._tracks.append(entry)

                    logger.verbose(
                        "[Library] Indexed '%s' -- artist: %s, album: %s, genre: %s, year: %s",
                        filepath,
                        entry["artist"],
                        entry["album"],
                        entry["genre"],
                        entry["year"],
                    )

        self._scanned = True

        self._log(f"Scan complete: {len(self._tracks)} track(s) indexed.")

        logger.verbose(
            "[Library] Index summary -- tracks: %d, artists: %d, albums: %d, genres: %d, years: %d",
            len(self._tracks),
            len(self.getArtists()),
            len(self.getAlbums()),
            len(self.getGenres()),
            len(self.getYears()),
        )

        return len(self._tracks)

    # ------------------------------------------------------------------

    def _readTrack(self, filepath: str, filename: str) -> Optional[Dict[str, Any]]:

        try:

            metadata = metadata_reader.read(filepath)

        except Exception as error:

            # Deliberately broad: MetadataReader.read() already
            # guards its own per-format parsers, but scanning a whole
            # tree must never abort because of one bad file
            # (LIBRARY_MANAGER_SPEC.md "Missing metadata never
            # prevents a file from being added to the library.").
            self._log(f"Skipping unreadable file '{filepath}': {error}")

            metadata = {}

        title = self._orDefault(metadata.get("title"), None)

        if title is None:
            title = os.path.splitext(filename)[0]

        artist = self._orDefault(metadata.get("artist"), _("Unknown Artist"))

        album = self._orDefault(metadata.get("album"), _("Unknown Album"))

        return {
            "path": filepath,
            "artist": artist,
            "album": album,
            "album_artist": self._orDefault(metadata.get("album_artist"), None) or artist,
            "title": title,
            "track_number": metadata.get("track_number"),
            "genre": self._orDefault(metadata.get("genre"), _("Unknown Genre")),
            "year": self._orDefault(metadata.get("year"), _("Unknown Year")),
        }

    # ------------------------------------------------------------------

    def _orDefault(self, value, default):
        """
        Return `value` unless it's empty/None or metadata.py's own
        generic UNKNOWN placeholder ("Unknown") -- otherwise `default`.
        A plain `value or default` isn't enough on its own: UNKNOWN is
        a non-empty string, so it would never fall through to our own
        more specific "Unknown Artist"/"Unknown Album"/etc. labels.
        """

        if not value or value == UNKNOWN:
            return default

        return value

    # ------------------------------------------------------------------

    def isScanned(self) -> bool:

        return self._scanned

    # ------------------------------------------------------------------

    def getTrackCount(self) -> int:

        return len(self._tracks)

    # ------------------------------------------------------------------
    # Browsing (LIBRARY_MANAGER_SPEC.md "Responsibilities")
    # ------------------------------------------------------------------

    def getArtists(self) -> List[str]:

        return sorted({track["artist"] for track in self._tracks})

    # ------------------------------------------------------------------

    def getAlbums(self, artist: Optional[str] = None) -> List[str]:

        tracks = self._tracks if artist is None else [t for t in self._tracks if t["artist"] == artist]

        return sorted({track["album"] for track in tracks})

    # ------------------------------------------------------------------

    def getTracks(self, artist: Optional[str] = None, album: Optional[str] = None) -> List[Dict[str, Any]]:

        tracks = self._tracks

        if artist is not None:
            tracks = [t for t in tracks if t["artist"] == artist]

        if album is not None:
            tracks = [t for t in tracks if t["album"] == album]

        return sorted(tracks, key=self._trackSortKey)

    # ------------------------------------------------------------------

    def getGenres(self) -> List[str]:

        return sorted({track["genre"] for track in self._tracks})

    # ------------------------------------------------------------------

    def getYears(self) -> List[str]:

        return sorted({track["year"] for track in self._tracks})

    # ------------------------------------------------------------------

    def _trackSortKey(self, track: Dict[str, Any]):

        track_number = track.get("track_number")

        try:
            track_number = int(str(track_number).split("/")[0])
        except (TypeError, ValueError):
            track_number = 0

        return (track.get("album", ""), track_number, track.get("title", ""))

    # ------------------------------------------------------------------
    # Search (LIBRARY_MANAGER_SPEC.md "Search")
    # ------------------------------------------------------------------

    def search(self, query: str, field: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Case-insensitive substring search across
        artist/album/title/genre/year (or just `field` when given).
        Returns matching track entries, sorted the same way
        getTracks() does.
        """

        if not query:
            return []

        query_lower = query.strip().lower()

        fields = [field] if field else ["artist", "album", "title", "genre", "year"]

        results = [
            track
            for track in self._tracks
            if any(query_lower in str(track.get(f, "")).lower() for f in fields)
        ]

        sorted_results = sorted(results, key=self._trackSortKey)

        logger.verbose(
            "[Library] Search '%s' (field: %s) -> %d result(s).",
            query,
            field or "all",
            len(sorted_results),
        )

        return sorted_results

    # ------------------------------------------------------------------
    # PlaybackQueue generation (LIBRARY_MANAGER_SPEC.md
    # "PlaybackQueue Generation")
    # ------------------------------------------------------------------

    def createQueue(
        self,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[str] = None,
        tracks: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        Return an ordered list of file paths for the given selection
        -- a PlaybackQueue ready for PlaybackController.playQueue().
        LibraryManager never starts playback itself.

        `tracks`, when given (e.g. a search result list), is used
        directly instead of filtering the full index -- lets
        MusicLibraryScreen build a queue straight from
        search()'s own results without a second lookup.
        """

        if tracks is not None:

            selected = tracks

        else:

            selected = self._tracks

            if artist is not None:
                selected = [t for t in selected if t["artist"] == artist]

            if album is not None:
                selected = [t for t in selected if t["album"] == album]

            if genre is not None:
                selected = [t for t in selected if t["genre"] == genre]

            if year is not None:
                selected = [t for t in selected if t["year"] == year]

            selected = sorted(selected, key=self._trackSortKey)

        return [track["path"] for track in selected]

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> dict:

        return {
            "scan_directory": config_manager.get("library.scan_directory", ""),
            "scanned": self._scanned,
            "track_count": len(self._tracks),
            "artist_count": len(self.getArtists()),
            "album_count": len(self.getAlbums()),
            "genre_count": len(self.getGenres()),
        }


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

library_manager = LibraryManager()

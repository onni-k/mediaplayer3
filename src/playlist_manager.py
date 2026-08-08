# ==============================================================================
#
# MediaPlayer3
#
# File        : playlist_manager.py
#
# Description :
#
#     PlaylistManager
#
#     Owns all playlist management: creation, deletion, renaming,
#     loading, saving, import, export, track/folder insertion and
#     playback queue generation. Stores playlists as Extended M3U
#     files under StorageManager.getPlaylistsPath().
#
#     PlaylistManager never performs playback -- it prepares an
#     ordered playback queue (a plain list of file paths) that
#     BrowserScreen/PlaylistScreen hand to PlaybackController.playQueue(),
#     exactly the same way BrowserScreen already builds queues from a
#     directory listing (PLAYBACK_QUEUE_SPEC.md, Build 0005).
#
# Implements :
#
#     PLAYLIST_MANAGER_SPEC.md v0.1
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
#   - Initial version.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 playlist management.

Playlists are stored as Extended M3U files, one file per playlist,
under StorageManager.getPlaylistsPath(). PlaylistManager reads/writes
these directly -- it never depends on BrowserScreen, PlaylistScreen or
PlaybackController (PLAYLIST_MANAGER_SPEC.md "Dependencies").
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from .constants import SUPPORTED_AUDIO_EXTENSIONS
from .logger import logger
from .storage import storage_manager

_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def _sanitizePlaylistName(name: str) -> str:
    """
    Replace filesystem-invalid characters in a playlist name
    (PLAYLIST_MANAGER_SPEC.md "Invalid filename characters shall
    automatically be removed or replaced.").
    """

    sanitized = _INVALID_FILENAME_CHARS.sub("_", name).strip()

    return sanitized or "Playlist"


class PlaylistManager:
    """
    Owns playlist creation, storage and playback queue generation.
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Playlist] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Playlist file paths
    # ------------------------------------------------------------------

    def _playlistPath(self, name: str) -> str:

        return os.path.join(storage_manager.getPlaylistsPath(), f"{_sanitizePlaylistName(name)}.m3u")

    # ------------------------------------------------------------------
    # Public interface (PLAYLIST_MANAGER_SPEC.md "Playlist Operations")
    # ------------------------------------------------------------------

    def getPlaylistNames(self) -> List[str]:
        """
        Return the names of every playlist currently in storage,
        sorted alphabetically.
        """

        try:
            entries = os.listdir(storage_manager.getPlaylistsPath())

        except OSError as error:

            self._log(f"Unable to list playlists: {error}")

            return []

        names = sorted(
            os.path.splitext(entry)[0]
            for entry in entries
            if entry.lower().endswith(".m3u")
        )

        return names

    # ------------------------------------------------------------------

    def createPlaylist(self, name: str) -> bool:
        """
        Create a new, empty playlist named `name`.

        Returns False (without overwriting) if a playlist with that
        name already exists -- PLAYLIST_MANAGER_SPEC.md "Playlist
        names shall be unique."
        """

        path = self._playlistPath(name)

        if os.path.exists(path):

            self._log(f"Playlist already exists: {name}")

            return False

        return self.savePlaylist(name, [])

    # ------------------------------------------------------------------

    def deletePlaylist(self, name: str) -> bool:

        path = self._playlistPath(name)

        try:
            os.remove(path)

            self._log(f"Playlist deleted: {name}")

            return True

        except OSError as error:

            self._log(f"Playlist deletion failed: {name} ({error})")

            return False

    # ------------------------------------------------------------------

    def renamePlaylist(self, old_name: str, new_name: str) -> bool:

        old_path = self._playlistPath(old_name)

        new_path = self._playlistPath(new_name)

        if os.path.exists(new_path):

            self._log(f"Playlist rename failed, name already exists: {new_name}")

            return False

        try:
            os.rename(old_path, new_path)

            self._log(f"Playlist renamed: {old_name} -> {new_name}")

            return True

        except OSError as error:

            self._log(f"Playlist rename failed: {old_name} -> {new_name} ({error})")

            return False

    # ------------------------------------------------------------------

    def loadPlaylist(self, name: str) -> List[Dict[str, Any]]:
        """
        Load playlist `name`'s tracks.

        Returns a list of track dicts (see _parseM3U()); an empty list
        if the playlist doesn't exist or can't be parsed -- never
        raises (PLAYLIST_MANAGER_SPEC.md "Errors shall never terminate
        the application.").
        """

        path = self._playlistPath(name)

        tracks = self._readM3UFile(path)

        self._log(f"Playlist loaded: {name} ({len(tracks)} track(s))")

        logger.verbose(f"[Playlist] Playlist parsing\n\nFile: {path}\n\nTracks: {len(tracks)}\n")

        return tracks

    # ------------------------------------------------------------------

    def savePlaylist(self, name: str, tracks: List[Dict[str, Any]]) -> bool:

        path = self._playlistPath(name)

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding="utf-8") as handle:

                self._writeM3U(handle, tracks)

            self._log(f"Playlist saved: {name} ({len(tracks)} track(s))")

            return True

        except OSError as error:

            self._log(f"Playlist saving failed: {name} ({error})")

            return False

# End of Part 1
    # ------------------------------------------------------------------
    # Track / folder operations
    # ------------------------------------------------------------------

    def addTrack(self, name: str, filepath: str) -> bool:
        """
        Append `filepath` to playlist `name`, creating the playlist
        first if it doesn't exist yet.
        """

        tracks = self.loadPlaylist(name) if self._playlistExists(name) else []

        tracks.append(self._trackFromPath(filepath))

        ok = self.savePlaylist(name, tracks)

        if ok:
            self._log(f"Track added: {os.path.basename(filepath)} -> {name}")

        return ok

    # ------------------------------------------------------------------

    def addFolder(self, name: str, directory: str) -> int:
        """
        Recursively collect every supported audio file under
        `directory` and append them to playlist `name`
        (PLAYLIST_MANAGER_SPEC.md "Folder Handling" -- folder
        structure is not stored, only individual tracks; the original
        music directory is never modified).

        Returns the number of tracks actually added.
        """

        collected = self._collectAudioFiles(directory)

        if not collected:

            self._log(f"No supported audio files found in folder: {directory}")

            return 0

        tracks = self.loadPlaylist(name) if self._playlistExists(name) else []

        tracks.extend(self._trackFromPath(path) for path in collected)

        if self.savePlaylist(name, tracks):

            self._log(f"Folder added: {directory} ({len(collected)} track(s)) -> {name}")

            return len(collected)

        return 0

    # ------------------------------------------------------------------

    def removeTrack(self, name: str, index: int) -> bool:

        tracks = self.loadPlaylist(name)

        if not (0 <= index < len(tracks)):
            return False

        removed = tracks.pop(index)

        if self.savePlaylist(name, tracks):

            self._log(f"Track removed: {removed.get('file_name', '?')} <- {name}")

            return True

        return False

    # ------------------------------------------------------------------

    def moveTrack(self, name: str, index: int, direction: int) -> bool:
        """
        Move the track at `index` up (direction=-1) or down
        (direction=+1) within playlist `name`.
        """

        tracks = self.loadPlaylist(name)

        target = index + direction

        if not (0 <= index < len(tracks) and 0 <= target < len(tracks)):
            return False

        tracks[index], tracks[target] = tracks[target], tracks[index]

        return self.savePlaylist(name, tracks)

    # ------------------------------------------------------------------

    def _playlistExists(self, name: str) -> bool:

        return os.path.exists(self._playlistPath(name))

    # ------------------------------------------------------------------

    def _collectAudioFiles(self, directory: str) -> List[str]:

        collected = []

        try:
            for root, _directories, files in os.walk(directory):

                for entry in sorted(files, key=str.lower):

                    if entry.startswith("."):
                        continue

                    if entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):

                        collected.append(os.path.join(root, entry))

        except OSError as error:

            self._log(f"Unable to scan folder {directory}: {error}")

        return collected

    # ------------------------------------------------------------------

    def _trackFromPath(self, filepath: str) -> Dict[str, Any]:

        return {
            "path": filepath,
            "file_name": os.path.basename(filepath),
            "title": os.path.basename(filepath),
            "artist": "Unknown",
            "album": "Unknown",
            "duration": None,
        }

# End of Part 2
    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def importPlaylist(self, source_path: str, name: Optional[str] = None) -> Optional[str]:
        """
        Import an existing M3U/Extended M3U file at `source_path` into
        MediaPlayer3's own playlist storage. The original file is
        never modified (PLAYLIST_MANAGER_SPEC.md "Playlist Import").

        Returns the new playlist's name, or None on failure.
        """

        tracks = self._readM3UFile(source_path)

        if not tracks:

            self._log(f"Playlist import failed or empty: {source_path}")

            return None

        playlist_name = name or os.path.splitext(os.path.basename(source_path))[0]

        if self.savePlaylist(playlist_name, tracks):

            self._log(f"Playlist imported: {source_path} -> {playlist_name}")

            return playlist_name

        return None

    # ------------------------------------------------------------------

    def exportPlaylist(self, name: str) -> Optional[str]:
        """
        Export playlist `name` as an Extended M3U file into
        StorageManager.getExportsPath().

        Returns the export file path, or None on failure.
        """

        tracks = self.loadPlaylist(name)

        export_path = os.path.join(storage_manager.getExportsPath(), f"{_sanitizePlaylistName(name)}.m3u")

        try:
            with open(export_path, "w", encoding="utf-8") as handle:

                self._writeM3U(handle, tracks)

            self._log(f"Playlist exported: {name} -> {export_path}")

            return export_path

        except OSError as error:

            self._log(f"Playlist export failed: {name} ({error})")

            return None

    # ------------------------------------------------------------------
    # M3U parsing / writing
    # ------------------------------------------------------------------

    def readPlaylistFile(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Read tracks directly from an arbitrary M3U file path -- unlike
        loadPlaylist(), this does not require the file to already be
        one of MediaPlayer3's own stored playlists (used by
        BrowserScreen's "Play Playlist"/"Information" actions on a
        playlist file found while browsing, before it has been
        imported).
        """

        return self._readM3UFile(filepath)

    # ------------------------------------------------------------------

    def _readM3UFile(self, path: str) -> List[Dict[str, Any]]:

        try:
            with open(path, encoding="utf-8", errors="replace") as handle:

                lines = handle.readlines()

        except OSError as error:

            logger.verbose(f"[Playlist] Unable to read M3U file {path}: {error}")

            return []

        tracks: List[Dict[str, Any]] = []

        pending_title: Optional[str] = None
        pending_duration: Optional[int] = None

        for raw_line in lines:

            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#EXTINF:"):

                pending_duration, pending_title = self._parseExtinf(line)

                continue

            if line.startswith("#"):
                continue

            # A plain (non-comment) line is a file path -- both
            # Standard and Extended M3U agree on this
            # (PLAYLIST_MANAGER_SPEC.md "PlaylistManager shall accept
            # both Standard M3U and Extended M3U.").
            track = self._trackFromPath(line)

            if pending_title:

                artist, _, title = pending_title.partition(" - ")

                if title:

                    track["artist"] = artist.strip()
                    track["title"] = title.strip()

                else:

                    track["title"] = pending_title.strip()

            if pending_duration is not None:

                track["duration"] = pending_duration

            tracks.append(track)

            pending_title = None
            pending_duration = None

        return tracks

    # ------------------------------------------------------------------

    def _parseExtinf(self, line: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Parse an "#EXTINF:355,Queen - Bohemian Rhapsody" line into
        (duration_seconds, display_title). Never raises -- returns
        (None, None) on any malformed line.
        """

        try:
            body = line[len("#EXTINF:"):]

            duration_part, _, title_part = body.partition(",")

            duration = int(duration_part.strip())

            if duration < 0:
                duration = None

            return duration, title_part.strip() or None

        except (ValueError, IndexError):
            return None, None

    # ------------------------------------------------------------------

    def _writeM3U(self, handle, tracks: List[Dict[str, Any]]) -> None:

        handle.write("#EXTM3U\n")

        for track in tracks:

            duration = track.get("duration")

            duration_value = duration if isinstance(duration, int) and duration >= 0 else -1

            artist = track.get("artist", "Unknown")
            title = track.get("title", track.get("file_name", "Unknown"))

            if artist and artist != "Unknown":

                display = f"{artist} - {title}"

            else:

                display = title

            handle.write(f"#EXTINF:{duration_value},{display}\n")

            handle.write(f"{track.get('path', '')}\n")

# End of Part 3
    # ------------------------------------------------------------------
    # Validation / Playback Queue
    # ------------------------------------------------------------------

    def validatePlaylist(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return only the tracks in `tracks` whose file still exists on
        disk, preserving order. Missing files are skipped, not
        treated as an error (PLAYLIST_MANAGER_SPEC.md "Missing files
        shall be skipped." / "Playlist playback shall continue
        whenever possible.").
        """

        valid = []

        for track in tracks:

            path = track.get("path", "")

            if path and os.path.isfile(path):

                valid.append(track)

            else:

                logger.verbose(f"[Playlist] Missing file skipped: {path}")

        if len(valid) != len(tracks):

            self._log(f"Playlist validation: {len(tracks) - len(valid)} missing file(s) skipped.")

        return valid

    # ------------------------------------------------------------------

    def generatePlaybackQueue(self, name: str) -> List[str]:
        """
        Return an ordered list of file paths for playlist `name`,
        ready to hand to PlaybackController.playQueue() -- exactly
        the same queue shape BrowserScreen already builds from a
        directory listing (PLAYBACK_QUEUE_SPEC.md).

        Missing files are silently skipped (validatePlaylist()).
        """

        tracks = self.validatePlaylist(self.loadPlaylist(name))

        logger.verbose(
            "[Playlist] Queue generation\n\nPlaylist: %s\n\nTracks: %s\n" % (name, len(tracks))
        )

        return [track["path"] for track in tracks]

    # ------------------------------------------------------------------
    # Diagnostics (Build 0007 -- Developer Mode "Playlist statistics")
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> Dict[str, Any]:

        names = self.getPlaylistNames()

        return {
            "playlists_path": storage_manager.getPlaylistsPath(),
            "playlist_count": len(names),
            "playlist_names": ", ".join(names) or "None",
        }

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"PlaylistManager(playlists={len(self.getPlaylistNames())})"


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

playlist_manager = PlaylistManager()


# ==============================================================================
#
# Build Notes
#
# PlaylistManager depends on StorageManager, Logger and
# ConfigurationManager (indirectly, via constants only in this build --
# no user-configurable playlist behaviour needs config.py directly
# yet). It never depends on BrowserScreen, PlaylistScreen or
# PlaybackController (PLAYLIST_MANAGER_SPEC.md "Dependencies").
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

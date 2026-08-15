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

        # Build 0010, device test round 20 (OpenPLI, disk-full test
        # box): savePlaylist() already logged the specific OSError on
        # failure, but every caller collapsed "genuinely no files to
        # add" and "found files, but the save itself failed" into the
        # same falsy return value -- so a real disk-full condition
        # showed the user a misleading "Nothing was added"/"No
        # playable files found" instead of the actual reason. Set
        # whenever savePlaylist() fails, cleared on success; see
        # getLastSaveError().
        self._last_save_error: Optional[str] = None

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

            self._last_save_error = None

            return True

        except OSError as error:

            self._log(f"Playlist saving failed: {name} ({error})")

            self._last_save_error = str(error)

            return False

    # ------------------------------------------------------------------

    def getLastSaveError(self) -> Optional[str]:
        """
        The OSError message from the most recent failed savePlaylist()
        call, or None if the most recent call (if any) succeeded.
        Build 0010, device test round 20 -- lets a caller distinguish
        "nothing to save" from "tried to save, but it failed" without
        savePlaylist()'s own return type needing to change.
        """

        return self._last_save_error

# End of Part 1
    # ------------------------------------------------------------------
    # Track / folder operations
    # ------------------------------------------------------------------

    def addTrack(self, name: str, filepath: str, title: Optional[str] = None, artist: Optional[str] = None) -> bool:
        """
        Append `filepath` to playlist `name`, creating the playlist
        first if it doesn't exist yet.

        Args:
            title: Build 0010 -- use this as the stored track's
                display title instead of deriving one from `filepath`
                via os.path.basename(). Needed for anything that isn't
                a local file path with a sensible filename -- a
                podcast episode's playback_url, for instance, may
                carry query-string parameters (confirmed from a real
                device log: Bauer's own podcast CDN does exactly
                this), which os.path.basename() would include
                verbatim in the derived title. Callers that already
                have a real title (PodcastScreen does, from the
                episode's own metadata) should always pass it.
            artist: Build 0010, device test round 23 -- use this as
                the stored track's artist instead of the "Unknown"
                default. PodcastScreen passes the podcast's own show
                name here so MainScreen can display it (a queue built
                from a playlist otherwise only ever carries a bare
                path -- see generatePlaybackQueue() -- with no way to
                recover which show an episode belongs to once it's
                playing).
        """

        tracks = self.loadPlaylist(name) if self._playlistExists(name) else []

        tracks.append(self._trackFromPath(filepath, title=title, artist=artist))

        ok = self.savePlaylist(name, tracks)

        if ok:
            self._log(f"Track added: {title or os.path.basename(filepath)} -> {name}")

        return ok

    # ------------------------------------------------------------------

    def addFilesInDirectory(self, name: str, directory: str, from_filename: Optional[str] = None) -> int:
        """
        Add the supported audio files directly inside `directory`
        (non-recursive -- deliberately distinct from addFolder()'s
        recursive os.walk()) to playlist `name`, creating the playlist
        first if it doesn't exist yet.

        Build 0010 -- File Browser's three-column redesign
        (BUILD_0010_PLAN.md "File Browser Actions"): backs both
        "Add all files from directory" (from_filename=None, everything
        in the directory) and "Add this file and remaining files in
        directory" (from_filename set -- only that file and whatever
        sorts after it, alphabetically, the same ordering
        BrowserScreen's own queue-building already uses). Matching by
        basename, not full-path equality, for the same reason
        BrowserScreen._buildQueueFromCurrentDirectory() already does
        (see its own docstring / Claude_notes_build0005.txt) -- a real
        device test showed FileList-derived paths don't reliably
        string-match an os.path.join()-built listing.

        Returns the number of tracks actually added.
        """

        files = self.listDirectoryAudioFiles(directory)

        if from_filename:

            target_basename = os.path.basename(from_filename)

            start = 0

            for index, path in enumerate(files):

                if os.path.basename(path) == target_basename:

                    start = index

                    break

            files = files[start:]

        if not files:

            self._log(f"No supported audio files found in directory: {directory}")

            return 0

        tracks = self.loadPlaylist(name) if self._playlistExists(name) else []

        tracks.extend(self._trackFromPath(path) for path in files)

        if self.savePlaylist(name, tracks):

            self._log(f"Directory files added: {directory} ({len(files)} track(s)) -> {name}")

            return len(files)

        return 0

    # ------------------------------------------------------------------

    def listDirectoryAudioFiles(self, directory: str) -> List[str]:
        """
        Non-recursive, alphabetically sorted list of supported audio
        files directly inside `directory` (subdirectories and hidden
        dotfiles excluded) -- the same listing convention
        BrowserScreen's queue-building already uses, moved here so
        addFilesInDirectory() can share it without BrowserScreen
        needing to duplicate playlist_manager's own file-writing.
        """

        try:
            entries = os.listdir(directory)

        except OSError as error:

            self._log(f"Unable to scan directory: {directory} ({error})")

            return []

        result = []

        for entry in sorted(entries, key=str.lower):

            if entry.startswith("."):
                continue

            full_path = os.path.join(directory, entry)

            if os.path.isdir(full_path):
                continue

            if not entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):
                continue

            result.append(full_path)

        return result

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

    def createPlaylistFromFolder(self, name: str, directory: str) -> int:
        """
        Build 0010, device test round 5 -- BrowserScreen's Directories-
        column "Play" action (user request: "Jos valitsee kansion
        kohdalla soita, niin se voisi luoda suoraan soittolistan koko
        kansiosta ja alkaa soittamaan"). Unlike addFolder(), this
        REPLACES playlist `name`'s entire content with exactly the
        supported audio files recursively under `directory` -- a
        fresh, single-purpose playlist matching that folder right now,
        not an accumulation across repeated presses. Creates the
        playlist if it doesn't exist yet. Any existing playlist of the
        same name is overwritten, by design (this is a "play this
        folder" shortcut, not an archival add) -- worth knowing if a
        folder's name happens to match an existing hand-curated
        playlist.

        Returns the number of tracks in the resulting playlist (0 if
        the folder had no supported audio files -- in which case
        nothing is written, the same as addFolder()'s own "no files
        found" case).
        """

        collected = self._collectAudioFiles(directory)

        if not collected:

            self._log(f"No supported audio files found in folder: {directory}")

            return 0

        tracks = [self._trackFromPath(path) for path in collected]

        if self.savePlaylist(name, tracks):

            self._log(f"Playlist created from folder: {directory} ({len(collected)} track(s)) -> {name}")

            return len(collected)

        return 0

    # ------------------------------------------------------------------

    def createPlaylistFromFile(self, name: str, filepath: str, title: Optional[str] = None) -> bool:
        """
        Build 0010, device test round 5 -- BrowserScreen's Files-column
        "Play" action (user request: "Tiedoston kohdalla voisi luoda
        soittolistan vain siitä tiedostosta ja alkaa soittamaan").
        Unlike addTrack(), this REPLACES playlist `name`'s entire
        content with just `filepath` -- see createPlaylistFromFolder()'s
        own docstring for why (same "fresh, single-purpose, overwrites
        by design" reasoning, just for one file instead of a folder).
        """

        tracks = [self._trackFromPath(filepath, title=title)]

        ok = self.savePlaylist(name, tracks)

        if ok:

            self._log(f"Playlist created from file: {title or os.path.basename(filepath)} -> {name}")

        return ok

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

    def _trackFromPath(self, filepath: str, title: Optional[str] = None, artist: Optional[str] = None) -> Dict[str, Any]:

        return {
            "path": filepath,
            "file_name": os.path.basename(filepath),
            "title": title or os.path.basename(filepath),
            "artist": artist or "Unknown",
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

        Build 0010, device test round 2 (test_2_openvix.log): a
        podcast episode added via PodcastScreen._addEpisodeToPlaylist()
        stores an http(s):// URL as `path` (this is the same
        os.path.isfile()-hostile URL playback_controller.py's own
        playStream()/play() docstrings already describe as resolved
        transparently by Enigma2's GStreamer/MP3 service factory, same
        as a local path). os.path.isfile() unconditionally returns
        False for a URL, so every podcast episode in a playlist was
        being silently validated out on every single playback attempt
        -- confirmed from the log: a one-track playlist consisting of
        just a podcast episode produced "1 missing file(s) skipped"
        and an empty playback queue, with no error shown to the user.
        Local playlists were URL-only-content-free before podcasts
        existed, so this never surfaced until now. Fixed: a path
        starting with http:// or https:// is treated as always valid
        (existence isn't checkable/meaningful for a remote URL the way
        it is for a local file); only local paths still go through
        os.path.isfile(). Tested: the exact URL from the device log
        now passes validation; local missing-file skipping is
        unaffected (a nonexistent local path is still skipped).
        """

        valid = []

        for track in tracks:

            path = track.get("path", "")

            is_remote_url = path.startswith("http://") or path.startswith("https://")

            if path and (is_remote_url or os.path.isfile(path)):

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

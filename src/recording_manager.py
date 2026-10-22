# ==============================================================================
# MediaPlayer3
#
# File        : recording_manager.py
# Description : Recording of Internet Radio streams to files.
#
# Author      : MediaPlayer3 Project
# Copyright   : (C) 2026 MediaPlayer3 Project
# License     : GNU General Public License v2 (GPL-2.0)
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-10-17  Round 240 (1.3.002)
#   - Initial version: radio recording (stream copied as-is by a worker
#     thread; no re-encoding), file naming, folder/space checks, an
#     automatic "Recordings (Radio)" local playlist.
# ------------------------------------------------------------------------------

"""
RecordingManager copies an Internet Radio stream to a file while it keeps
playing normally. It has no user interface code: MainScreen starts and
stops it, polls getStatus() once a second for the REC display, and
collects the result with popFinishedEvent().

The stream bytes are written exactly as received (mp3, aac or ogg),
so nothing is decoded or re-encoded. The file is written as
"<name>.part" while recording and renamed when it ends.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from . import hls_support
from .config import config_manager
from .constants import SUPPORTED_AUDIO_EXTENSIONS
from .logger import logger
from .playlist_manager import playlist_manager
from .project import PROJECT_NAME, VERSION
from .storage import storage_manager

USER_AGENT = f"{PROJECT_NAME}/{VERSION} (Enigma2 recorder)"

CONNECT_TIMEOUT_SECONDS = 15

CHUNK_SIZE = 16 * 1024

# Reconnect attempts (2 s apart) after the stream drops, before the
# recording is ended with what has been written so far.
MAX_RECONNECTS = 5

RECONNECT_DELAY_SECONDS = 2.0

# Refuse to start with less free space than this, and stop when it runs
# out.
MIN_FREE_BYTES_TO_START = 100 * 1024 * 1024
MIN_FREE_BYTES_TO_CONTINUE = 20 * 1024 * 1024

# Recordings smaller than this are removed as empty.
MIN_KEEP_BYTES = 64 * 1024

# Playlist names (one per supported language) that may already hold
# the radio recordings, so a language change never creates a second one.
RADIO_PLAYLIST_NAMES = (
    "Recordings (Radio)",
    "Tallennukset (Radio)",
    "Inspelningar (Radio)",
    "Aufnahmen (Radio)",
    "Grabaciones (Radio)",
)

# Extension of the episode information file saved next to a downloaded
# podcast episode.
EPISODE_INFO_EXTENSION = ".json"

PODCAST_PLAYLIST_NAMES = (
    "Recordings (Podcast)",
    "Tallennukset (Podcast)",
    "Inspelningar (Podcast)",
    "Aufnahmen (Podcast)",
    "Grabaciones (Podcast)",
)

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

# Result codes of start(): (True, path) or (False, <code>).
START_NO_FOLDER = "no_folder"
START_ALREADY = "already"
START_NO_SPACE = "no_space"
START_NO_URL = "no_url"

_CONTENT_TYPE_EXTENSIONS = (
    ("audio/mpeg", ".mp3"),
    ("audio/mp3", ".mp3"),
    ("audio/aacp", ".aac"),
    ("audio/aac", ".aac"),
    ("audio/x-aac", ".aac"),
    ("audio/ogg", ".ogg"),
    ("application/ogg", ".ogg"),
    ("audio/opus", ".ogg"),
    ("audio/mp4", ".m4a"),
    ("audio/x-m4a", ".m4a"),
)


def sanitizeFileName(text: str, max_length: int = 80) -> str:
    """Return `text` made safe for use in a file name."""

    cleaned = _INVALID_CHARS.sub("_", text or "").strip(" .")

    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned[:max_length].strip(" .") or "Radio"


class _Job:
    """State of one background copy (a radio recording or a podcast download)."""

    def __init__(self, kind: str) -> None:

        self.kind = kind

        self.thread: Optional[threading.Thread] = None

        self.stop_event = threading.Event()

        self.active = False

        self.name = ""

        self.title = ""

        self.description = ""

        self.url = ""

        # Round 244: the user-visible stream a recording belongs to when
        # `url` is a local timeshift relay address.
        self.source_url = ""

        self.base_path = ""

        self.bytes = 0

        self.total = 0

        self.started_at = 0.0


class RecordingManager:
    """
    Copies one Internet Radio stream ("radio") and one podcast episode
    ("podcast") at a time, each in its own thread.
    """

    def __init__(self) -> None:

        self._lock = threading.Lock()

        self._jobs = {"radio": _Job("radio"), "podcast": _Job("podcast")}

        self._finished: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Recording] %s", message)

    # ------------------------------------------------------------------
    # Folder
    # ------------------------------------------------------------------

    def getRecordingFolder(self) -> Optional[str]:
        """
        The configured recording folder, or the default
        "<MediaPlayer3 data folder>/Recordings". None when the data
        folder is non-persistent (/tmp, no disk found) and no folder
        was configured.
        """

        configured = (config_manager.get("recording.folder", "") or "").strip()

        if configured:

            return configured.rstrip("/") or "/"

        try:

            diagnostics = storage_manager.getDiagnostics()

            if str(diagnostics.get("using_fallback_location")) == "True":

                return None

            return os.path.join(storage_manager.getWorkingDirectory(), "Recordings")

        except Exception as error:

            self._log(f"Could not determine default folder: {error}")

            return None

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def isRecording(self) -> bool:
        """True while a radio recording runs."""

        with self._lock:

            return self._jobs["radio"].active

    def isDownloading(self) -> bool:
        """True while a podcast episode is being downloaded."""

        with self._lock:

            return self._jobs["podcast"].active

    def _status(self, kind: str) -> Dict[str, Any]:

        with self._lock:

            job = self._jobs[kind]

            return {
                "active": job.active,
                "name": job.name,
                "title": job.title,
                "url": job.source_url or job.url,
                "elapsed": int(time.time() - job.started_at) if job.active else 0,
                "bytes": job.bytes,
                "total": job.total,
                "percent": int(job.bytes * 100 / job.total) if job.total > 0 else -1,
            }

    def getStatus(self) -> Dict[str, Any]:
        """Radio recording snapshot for the UI: active, name, url, elapsed, bytes."""

        return self._status("radio")

    def getDownloadStatus(self) -> Dict[str, Any]:
        """Podcast download snapshot (percent is -1 when the size is unknown)."""

        return self._status("podcast")

    def popFinishedEvent(self) -> Optional[Dict[str, Any]]:
        """
        The next result of a copy that has ended (oldest first), or
        None. Keys: kind ("radio"/"podcast"), status ("done"/"error"),
        path, name, title, message. A finished file is also added to
        its "Recordings (...)" playlist here, on the caller's (main)
        thread.
        """

        with self._lock:

            event = self._finished.pop(0) if self._finished else None

        if event is None:
            return None

        if event.get("status") == "done" and event.get("path"):

            event["playlist"] = self._addToPlaylist(event)

        return event

    # ------------------------------------------------------------------
    # Start / stop
    # ------------------------------------------------------------------

    def startRadioRecording(self, station_name: str, url: str, source_url: str = "") -> Tuple[bool, str]:
        """
        Start recording `url`. Returns (True, final base path) or
        (False, one of the START_* codes).
        """

        stamp = time.strftime("%Y-%m-%d-%H.%M")

        return self._start(
            "radio", station_name, "", url, f"{stamp}_{sanitizeFileName(station_name, 80)}", "Radio", source_url=source_url
        )

    def startPodcastDownload(
        self, podcast_name: str, episode_title: str, url: str, description: str = ""
    ) -> Tuple[bool, str]:
        """
        Download a podcast episode. The file is named
        "<podcast>_<episode>". Returns (True, base path) or
        (False, START_* code).
        """

        base_name = f"{sanitizeFileName(podcast_name, 50)}_{sanitizeFileName(episode_title, 70)}"

        return self._start("podcast", podcast_name, episode_title, url, base_name, "Podcast", description)

    def _start(
        self,
        kind: str,
        name: str,
        title: str,
        url: str,
        base_name: str,
        subfolder: str,
        description: str = "",
        source_url: str = "",
    ) -> Tuple[bool, str]:

        if not url:
            return False, START_NO_URL

        with self._lock:

            if self._jobs[kind].active:
                return False, START_ALREADY

        folder = self.getRecordingFolder()

        if not folder:
            return False, START_NO_FOLDER

        target_folder = os.path.join(folder, subfolder)

        try:

            os.makedirs(target_folder, exist_ok=True)

            if not os.access(target_folder, os.W_OK):
                raise OSError("not writable")

        except OSError as error:

            self._log(f"Recording folder unusable ({target_folder}): {error}")

            return False, START_NO_FOLDER

        if self._freeBytes(target_folder) < MIN_FREE_BYTES_TO_START:

            self._log(f"Not enough free space in {target_folder}")

            return False, START_NO_SPACE

        base = self._uniqueBase(os.path.join(target_folder, base_name))

        with self._lock:

            job = self._jobs[kind]

            job.active = True
            job.name = name or ("Radio" if kind == "radio" else "Podcast")
            job.title = title
            job.description = description or ""
            job.url = url
            job.source_url = source_url
            job.base_path = base
            job.bytes = 0
            job.total = 0
            job.started_at = time.time()
            job.stop_event.clear()

        job.thread = threading.Thread(
            target=self._runRadio if kind == "radio" else self._runPodcast,
            name=f"MP3Recorder-{kind}",
            daemon=True,
        )

        job.thread.start()

        self._log(f"{kind} copy started: {name} {title} -> {base} ({url})")

        return True, base

    def stop(self) -> None:
        """Ask the radio recording to finish; the result arrives via popFinishedEvent()."""

        if self.isRecording():

            self._log("Radio stop requested.")

            self._jobs["radio"].stop_event.set()

    def stopDownload(self) -> None:
        """Cancel the podcast download (the partial file is removed)."""

        if self.isDownloading():

            self._log("Podcast download cancel requested.")

            self._jobs["podcast"].stop_event.set()

    def stopAndWait(self, timeout: float = 3.0) -> None:
        """Stop the radio recording and wait briefly (used when MediaPlayer3 closes)."""

        self.stop()

        thread = self._jobs["radio"].thread

        if thread is not None and thread.is_alive():

            thread.join(timeout)

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

    def _runRadio(self) -> None:

        job = self._jobs["radio"]

        part_path = job.base_path + ".part"

        extension = ""

        error_message = ""

        reconnects = 0

        handle = None

        hls_done = False

        try:

            handle = open(part_path, "wb")

            while not job.stop_event.is_set():

                response = None

                try:

                    request = urllib.request.Request(
                        job.url,
                        headers={"User-Agent": USER_AGENT, "Icy-MetaData": "0"},
                    )

                    response = urllib.request.urlopen(request, timeout=CONNECT_TIMEOUT_SECONDS)

                    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()

                    first = response.read(CHUNK_SIZE)

                    unsupported = self._unsupportedReason(content_type, first)

                    if unsupported == "hls":

                        text = (first + response.read(1024 * 1024)).decode("utf-8", "replace")

                        if "#EXT-X-" not in text:

                            error_message = "playlist"

                        else:

                            extension, error_message = self._recordHls(job, handle, response.geturl(), text)

                            hls_done = True

                        break

                    if unsupported:

                        error_message = unsupported

                        break

                    if not extension:

                        extension = self._extensionFor(content_type, job.url)

                    reconnects = 0

                    chunk = first

                    while chunk and not job.stop_event.is_set():

                        handle.write(chunk)

                        with self._lock:

                            job.bytes += len(chunk)

                            written = job.bytes

                        if written // (5 * 1024 * 1024) != (written - len(chunk)) // (5 * 1024 * 1024):

                            if self._freeBytes(os.path.dirname(part_path)) < MIN_FREE_BYTES_TO_CONTINUE:

                                error_message = "no_space"

                                job.stop_event.set()

                                break

                        chunk = response.read(CHUNK_SIZE)

                except (urllib.error.URLError, OSError, ValueError) as error:

                    self._log(f"Stream error: {error}")

                    if isinstance(error, OSError) and getattr(error, "errno", None) in (28, 30):

                        error_message = "no_space"

                        break

                finally:

                    if response is not None:

                        try:
                            response.close()
                        except Exception:
                            pass

                if job.stop_event.is_set() or error_message or hls_done:
                    break

                reconnects += 1

                if reconnects > MAX_RECONNECTS:

                    error_message = "connection_lost"

                    break

                self._log(f"Stream ended or dropped; reconnecting ({reconnects}/{MAX_RECONNECTS}).")

                job.stop_event.wait(RECONNECT_DELAY_SECONDS)

        except Exception as error:

            self._log(f"Recording failed: {error}")

            error_message = error_message or "write_failed"

        finally:

            if handle is not None:

                try:
                    handle.close()
                except Exception:
                    pass

        self._finish(job, part_path, extension or ".mp3", error_message, keep_partial=True)

    # ------------------------------------------------------------------
    # HLS (Round 246, 1.3.008): see hls_support.py.
    # ------------------------------------------------------------------

    def _recordHls(self, job: _Job, handle: Any, url: str, text: str) -> Tuple[str, str]:
        """Follow an HLS playlist into `handle`. Returns (extension, error code)."""

        def write(chunk: bytes, _duration: float) -> None:
            handle.write(chunk)
            job.bytes += len(chunk)

        def check() -> str:
            if self._freeBytes(os.path.dirname(job.base_path)) < MIN_FREE_BYTES_TO_CONTINUE:
                return "no_space"
            return ""

        return hls_support.follow(url, text, job.stop_event, write, USER_AGENT, check=check)

    # ------------------------------------------------------------------

    def _runPodcast(self) -> None:
        """
        Download one episode. A dropped connection is resumed with an
        HTTP Range request (when the server allows it); an incomplete
        file is not kept.
        """

        job = self._jobs["podcast"]

        part_path = job.base_path + ".part"

        extension = ""

        error_message = ""

        retries = 0

        complete = False

        handle = None

        try:

            handle = open(part_path, "wb")

            while not job.stop_event.is_set() and not complete:

                response = None

                try:

                    headers = {"User-Agent": USER_AGENT}

                    if job.bytes > 0:

                        headers["Range"] = f"bytes={job.bytes}-"

                    request = urllib.request.Request(job.url, headers=headers)

                    response = urllib.request.urlopen(request, timeout=CONNECT_TIMEOUT_SECONDS)

                    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()

                    if job.bytes > 0 and getattr(response, "status", 200) != 206:

                        # The server ignored the Range request.
                        error_message = "connection_lost"

                        break

                    if not extension:

                        if content_type.startswith("text/") or content_type in ("application/json", "application/xml"):

                            error_message = "not_audio"

                            break

                        extension = self._extensionFor(content_type, job.url)

                        length = response.headers.get("Content-Length")

                        if length and length.isdigit():

                            with self._lock:

                                job.total = int(length)

                    chunk = response.read(CHUNK_SIZE)

                    while chunk and not job.stop_event.is_set():

                        handle.write(chunk)

                        with self._lock:

                            job.bytes += len(chunk)

                            written = job.bytes

                        if written // (5 * 1024 * 1024) != (written - len(chunk)) // (5 * 1024 * 1024):

                            if self._freeBytes(os.path.dirname(part_path)) < MIN_FREE_BYTES_TO_CONTINUE:

                                error_message = "no_space"

                                job.stop_event.set()

                                break

                        chunk = response.read(CHUNK_SIZE)

                    if not chunk and not job.stop_event.is_set():

                        complete = job.total <= 0 or job.bytes >= job.total

                except (urllib.error.URLError, OSError, ValueError) as error:

                    self._log(f"Download error: {error}")

                    if isinstance(error, OSError) and getattr(error, "errno", None) in (28, 30):

                        error_message = "no_space"

                        break

                finally:

                    if response is not None:

                        try:
                            response.close()
                        except Exception:
                            pass

                if complete or job.stop_event.is_set() or error_message:
                    break

                retries += 1

                if retries > MAX_RECONNECTS:

                    error_message = "connection_lost"

                    break

                self._log(f"Download interrupted at {job.bytes} bytes; resuming ({retries}/{MAX_RECONNECTS}).")

                job.stop_event.wait(RECONNECT_DELAY_SECONDS)

        except Exception as error:

            self._log(f"Download failed: {error}")

            error_message = error_message or "write_failed"

        finally:

            if handle is not None:

                try:
                    handle.close()
                except Exception:
                    pass

        if not complete:

            # Cancelled or failed: an incomplete episode is removed.
            try:
                os.remove(part_path)
            except OSError:
                pass

            with self._lock:

                job.active = False

                if job.stop_event.is_set() and not error_message:

                    self._log("Podcast download cancelled.")

                    return

                self._finished.append(
                    {
                        "kind": "podcast",
                        "status": "error",
                        "path": "",
                        "name": job.name,
                        "title": job.title,
                        "message": error_message or "connection_lost",
                        "bytes": job.bytes,
                    }
                )

            return

        self._finish(job, part_path, extension or ".mp3", "", keep_partial=False)

    # ------------------------------------------------------------------

    def _finish(self, job: _Job, part_path: str, extension: str, error_message: str, keep_partial: bool) -> None:

        size = 0

        try:
            size = os.path.getsize(part_path)
        except OSError:
            pass

        final_path = ""

        if size >= MIN_KEEP_BYTES:

            final_path = job.base_path + extension

            counter = 2

            while os.path.exists(final_path):

                final_path = f"{job.base_path}-{counter}{extension}"

                counter += 1

            try:

                os.rename(part_path, final_path)

            except OSError as error:

                self._log(f"Could not rename file: {error}")

                final_path = part_path

        else:

            try:
                os.remove(part_path)
            except OSError:
                pass

            if not error_message:

                error_message = "empty"

        if final_path and job.kind == "podcast":

            self._writeEpisodeInfo(final_path, job)

        with self._lock:

            job.active = False

            # A radio recording that ended with an error but kept
            # useful data is still a (partial) recording.
            status = "done" if final_path else "error"

            self._finished.append(
                {
                    "kind": job.kind,
                    "status": status,
                    "path": final_path,
                    "name": job.name,
                    "title": job.title,
                    "message": error_message,
                    "bytes": size,
                }
            )

        self._log(
            f"{job.kind} copy ended: status={status} file={final_path or '-'} bytes={size} note={error_message or '-'}"
        )

    # ------------------------------------------------------------------
    # Episode information file (Round 242)
    # ------------------------------------------------------------------

    def _writeEpisodeInfo(self, audio_path: str, job: _Job) -> None:
        """
        Saves the podcast name, episode title and description next to
        the downloaded episode ("<file>.json", same name) so they can
        be shown again when the recording is played (see
        PodcastManager.getEpisodeInfo()).
        """

        info_path = os.path.splitext(audio_path)[0] + EPISODE_INFO_EXTENSION

        try:

            with open(info_path, "w", encoding="utf-8") as handle:

                json.dump(
                    {"podcast": job.name, "title": job.title, "description": job.description},
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )

        except OSError as error:

            self._log(f"Could not write episode information file: {error}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _freeBytes(path: str) -> int:

        try:

            stat = os.statvfs(path)

            return stat.f_bavail * stat.f_frsize

        except OSError:

            return 0

    @staticmethod
    def _uniqueBase(base: str) -> str:
        """`base` itself, or base-2, base-3 ... when a file already uses it."""

        def taken(candidate: str) -> bool:

            directory = os.path.dirname(candidate)

            prefix = os.path.basename(candidate)

            try:

                return any(
                    entry == prefix + ".part" or os.path.splitext(entry)[0] == prefix
                    for entry in os.listdir(directory)
                )

            except OSError:

                return False

        if not taken(base):
            return base

        counter = 2

        while taken(f"{base}-{counter}"):
            counter += 1

        return f"{base}-{counter}"

    @staticmethod
    def _unsupportedReason(content_type: str, first_bytes: bytes) -> str:
        """Why this response cannot be recorded as a plain stream, or ''."""

        head = first_bytes[:16].lstrip()

        if head.startswith(b"#EXT") or "mpegurl" in content_type:
            return "hls"

        if content_type in ("audio/x-scpls", "application/pls+xml") or head.startswith(b"[playlist]"):
            return "playlist"

        if content_type.startswith("text/") or head.lower().startswith((b"<!doc", b"<html")):
            return "not_audio"

        return ""

    @staticmethod
    def _extensionFor(content_type: str, url: str) -> str:

        for prefix, extension in _CONTENT_TYPE_EXTENSIONS:

            if content_type == prefix:
                return extension

        path = url.split("?", 1)[0].lower()

        for extension in (".mp3", ".aac", ".ogg", ".m4a", ".opus"):

            if path.endswith(extension):
                return ".ogg" if extension == ".opus" else extension

        return ".mp3"

    # ------------------------------------------------------------------
    # Recordings playlists: kind, refresh from folder, file deletion
    # (Round 243)
    # ------------------------------------------------------------------

    @staticmethod
    def kindOfPlaylist(name: str) -> Optional[str]:
        """"radio" / "podcast" if `name` is one of the Recordings playlists, else None."""

        if name in RADIO_PLAYLIST_NAMES:
            return "radio"

        if name in PODCAST_PLAYLIST_NAMES:
            return "podcast"

        return None

    def refreshPlaylist(self, playlist_name: str) -> int:
        """
        Adds the audio files found in the recording folder (Radio or
        Podcast sub-folder, matching the playlist) that are not in the
        playlist yet. Returns how many were added, or -1 when there is
        no recording folder.
        """

        kind = self.kindOfPlaylist(playlist_name)

        if kind is None:
            return 0

        folder = self.getRecordingFolder()

        if not folder:
            return -1

        directory = os.path.join(folder, "Radio" if kind == "radio" else "Podcast")

        if not os.path.isdir(directory):
            return 0

        try:

            files = sorted(
                entry for entry in os.listdir(directory) if entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS)
            )

        except OSError as error:

            self._log(f"Could not list {directory}: {error}")

            return 0

        tracks = playlist_manager.loadPlaylist(playlist_name) if playlist_name in playlist_manager.getPlaylistNames() else []

        known = {track.get("path") for track in tracks}

        added = 0

        for entry in files:

            path = os.path.join(directory, entry)

            if path in known:
                continue

            base = os.path.splitext(entry)[0]

            title = base

            artist = None

            if kind == "radio":

                artist = base.split("_", 1)[1] if "_" in base else None

            else:

                try:

                    with open(os.path.splitext(path)[0] + EPISODE_INFO_EXTENSION, "r", encoding="utf-8") as handle:

                        data = json.load(handle)

                    title = str(data.get("title") or base)

                    artist = str(data.get("podcast") or "") or None

                except (OSError, ValueError, AttributeError):

                    pass

            tracks.append(playlist_manager._trackFromPath(path, title=title, artist=artist))

            added += 1

        if added and not playlist_manager.savePlaylist(playlist_name, tracks):

            return 0

        self._log(f"Playlist {playlist_name} refreshed from {directory}: {added} added.")

        return added

    def deleteRecordingFile(self, path: str) -> bool:
        """
        Deletes a recorded file (and its episode information file).
        Only files in a "Radio" or "Podcast" folder are deleted.
        """

        if os.path.basename(os.path.dirname(path)) not in ("Radio", "Podcast"):

            self._log(f"Refusing to delete outside a recording folder: {path}")

            return False

        try:

            os.remove(path)

        except OSError as error:

            self._log(f"Could not delete {path}: {error}")

            return False

        try:

            os.remove(os.path.splitext(path)[0] + EPISODE_INFO_EXTENSION)

        except OSError:

            pass

        self._log(f"Deleted recording: {path}")

        return True

    # ------------------------------------------------------------------
    # Playlist
    # ------------------------------------------------------------------

    def _addToPlaylist(self, event: Dict[str, Any]) -> str:
        """
        Add the finished file to the matching recordings playlist
        (an existing one in any supported language, else a new one named
        in the current language). Returns the playlist name, or "".
        """

        try:

            from .localization import _

            path = event["path"]

            if event.get("kind") == "podcast":

                names = PODCAST_PLAYLIST_NAMES

                label = _("Podcast")

                title = event.get("title") or os.path.splitext(os.path.basename(path))[0]

            else:

                names = RADIO_PLAYLIST_NAMES

                label = _("Radio")

                title = os.path.splitext(os.path.basename(path))[0]

            existing = set(playlist_manager.getPlaylistNames())

            target = next((candidate for candidate in names if candidate in existing), None)

            if target is None:

                target = f"{_('Recordings')} ({label})"

            if playlist_manager.addTrack(target, path, title=title, artist=event.get("name") or None):

                return target

        except Exception as error:

            self._log(f"Could not add recording to playlist: {error}")

        return ""


recording_manager = RecordingManager()

#end_of_file

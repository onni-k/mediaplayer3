# ==============================================================================
#
# MediaPlayer3
#
# File        : storage.py
#
# Description :
#
#     StorageManager
#
#     Centralized interface for MediaPlayer3's application storage:
#     creates and validates the hidden working directory and its
#     subdirectories, recovers missing directories automatically, and
#     provides every other module's application paths. Contains no
#     application-specific data of its own -- its responsibility is
#     limited to storage infrastructure.
#
#     Other modules shall never use hard coded filesystem paths for
#     application data; they ask StorageManager instead.
#
# Implements :
#
#     STORAGE_MANAGER_SPEC.md v0.1
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
MediaPlayer3 application storage.
"""

from __future__ import annotations

import os
from typing import Dict

from .logger import logger

# ------------------------------------------------------------------------------
# Working directory
# ------------------------------------------------------------------------------

WORKING_DIRECTORY_NAME = ".mediaplayer3"

SUBDIRECTORIES = (
    "playlists",
    "radio",
    "podcast",
    "artwork",
    "cache",
    "logs",
    "imports",
    "exports",
    "backups",
    "userdata",
)

# Candidate parent locations, in preference order -- the first one
# that actually exists and is writable is used. This mirrors
# paths.default_media_directory()'s own drive-detection approach
# (STORAGE_MANAGER_SPEC.md gives a single fixed default,
# "/media/hdd/.mediaplayer3/", but a receiver without a hard disk
# would otherwise have nowhere to create it).
_CANDIDATE_PARENTS = (
    "/media/hdd",
    "/media",
)

# Absolute last resort if none of the above exist/are writable --
# non-persistent (tmpfs), so a warning is always logged when this is
# used. Better than failing startup entirely.
_FALLBACK_PARENT = "/tmp"


def _pickWorkingDirectoryParent() -> str:

    for candidate in _CANDIDATE_PARENTS:

        if os.path.isdir(candidate) and os.access(candidate, os.W_OK):
            return candidate

    return _FALLBACK_PARENT


class StorageManager:
    """
    Creates, validates and provides MediaPlayer3's application storage
    directories.
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._working_directory = ""

        self._subdirectory_paths: Dict[str, str] = {}

        self._using_fallback_location = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Storage] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:
        """
        Directory Initialization (STORAGE_MANAGER_SPEC.md):

            1. Verify working directory.
            2. Create working directory if missing.
            3. Verify required subdirectories.
            4. Create missing subdirectories.
            5. Verify write permissions.
            6. Report initialization status.

        Never raises -- initialization failures are logged and
        startup continues regardless (STORAGE_MANAGER_SPEC.md
        "Application startup shall never fail because a directory is
        missing.").
        """

        self._log("Initializing")

        parent = _pickWorkingDirectoryParent()

        self._using_fallback_location = (parent == _FALLBACK_PARENT)

        if self._using_fallback_location:

            self._log(
                f"No writable /media/hdd or /media found; using {_FALLBACK_PARENT} "
                "(non-persistent -- playlists/favorites will not survive a reboot)."
            )

        self._working_directory = os.path.join(parent, WORKING_DIRECTORY_NAME)

        self._ensureDirectory(self._working_directory, "Working directory")

        for name in SUBDIRECTORIES:

            path = os.path.join(self._working_directory, name)

            self._subdirectory_paths[name] = path

            self._ensureDirectory(path, f"Directory ({name})")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _ensureDirectory(self, path: str, label: str) -> bool:
        """
        Verify `path` exists and is writable, creating it if missing.

        Returns True if `path` is usable afterwards, False if creation
        or the write-permission check failed (logged as a WARNING/
        ERROR, never raised).
        """

        if not os.path.isdir(path):

            try:
                os.makedirs(path, exist_ok=True)

                self._log(f"{label} created: {path}")

            except OSError as error:

                self._log(f"{label} creation failed: {path} ({error})")

                return False

        else:

            logger.verbose(f"[Storage] {label} verified: {path}")

        if not os.access(path, os.W_OK):

            self._log(f"{label} has limited write permission: {path}")

            return False

        return True

    # ------------------------------------------------------------------
    # Public interface (STORAGE_MANAGER_SPEC.md)
    # ------------------------------------------------------------------

    def getWorkingDirectory(self) -> str:
        return self._working_directory

    # ------------------------------------------------------------------

    def _getSubdirectory(self, name: str) -> str:
        """
        Return the path for subdirectory `name`, recovering it first
        if it went missing since initialization (STORAGE_MANAGER_SPEC.md
        "Storage Recovery" -- "whenever required", not just at
        startup).
        """

        path = self._subdirectory_paths.get(name, os.path.join(self._working_directory, name))

        if not os.path.isdir(path):

            self._log(f"Directory missing, recovering: {name}")

            self._ensureDirectory(path, f"Directory ({name})")

        return path

    # ------------------------------------------------------------------

    def getPlaylistsPath(self) -> str:
        return self._getSubdirectory("playlists")

    def getRadioPath(self) -> str:
        return self._getSubdirectory("radio")

    def getPodcastPath(self) -> str:
        return self._getSubdirectory("podcast")

    def getArtworkPath(self) -> str:
        return self._getSubdirectory("artwork")

    def getCachePath(self) -> str:
        return self._getSubdirectory("cache")

    def getLogsPath(self) -> str:
        return self._getSubdirectory("logs")

    def getImportsPath(self) -> str:
        return self._getSubdirectory("imports")

    def getExportsPath(self) -> str:
        return self._getSubdirectory("exports")

    def getBackupsPath(self) -> str:
        return self._getSubdirectory("backups")

    def getUserDataPath(self) -> str:
        return self._getSubdirectory("userdata")

    # ------------------------------------------------------------------
    # Diagnostics (Build 0007 -- Developer Mode "Storage diagnostics")
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> Dict[str, str]:

        report = {
            "working_directory": self._working_directory,
            "using_fallback_location": str(self._using_fallback_location),
        }

        for name in SUBDIRECTORIES:

            path = self._subdirectory_paths.get(name, "?")

            exists = os.path.isdir(path)

            writable = exists and os.access(path, os.W_OK)

            report[name] = f"{path} (exists={exists}, writable={writable})"

        return report

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"StorageManager(working_directory={self._working_directory!r})"


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

storage_manager = StorageManager()


# ==============================================================================
#
# Build Notes
#
# StorageManager depends only on logger.py (STORAGE_MANAGER_SPEC.md
# "Dependencies"). It is initialized before PlaylistManager and
# InternetRadioManager, both of which depend on it for their own
# storage locations.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

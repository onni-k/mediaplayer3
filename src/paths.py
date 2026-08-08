# ==============================================================================
# MediaPlayer3
#
# File        : paths.py
# Description : Common filesystem paths used by MediaPlayer3.
#
# Author      : MediaPlayer3 Project
# Copyright   : (C) 2026 MediaPlayer3 Project
# License     : GNU General Public License v2 (GPL-2.0)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Compatible  : OpenViX 6.8+, OpenATV (planned)
# Python      : 3.13+
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-07-05  Build 0002
#   - Initial version.
#
# 2026-07-13  Build 0004
#   - default_media_directory() now always returns a trailing "/", and
#     added ensure_trailing_slash() -- fixes a real device bug where a
#     subdirectory (e.g. "flac") was misclassified as a file because
#     FileList string-concatenates directory + entry name without
#     inserting a separator.
#
# 2026-07-28  Build 0008
#   - Added HELP_PATH (resources/help/) -- bundled Markdown help
#     documents for HelpManager/HelpScreen.
# ------------------------------------------------------------------------------

"""
Filesystem paths used throughout MediaPlayer3.

All modules should use this file instead of hard coding paths.
"""

from os.path import abspath
from os.path import dirname
from os.path import isdir
from os.path import join

# ------------------------------------------------------------------------------
# Plugin directories
# ------------------------------------------------------------------------------

PLUGIN_PATH = abspath(dirname(__file__))

RESOURCE_PATH = join(PLUGIN_PATH, "resources")

SKIN_PATH = join(RESOURCE_PATH, "skins")

ICON_PATH = join(RESOURCE_PATH, "icons")

LOCALE_PATH = join(RESOURCE_PATH, "locale")

HELP_PATH = join(RESOURCE_PATH, "help")

DOC_PATH = join(PLUGIN_PATH, "docs")

# ------------------------------------------------------------------------------
# Runtime directories
# ------------------------------------------------------------------------------

LOG_PATH = "/tmp"

CACHE_PATH = "/tmp/mediaplayer3"

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

PLUGIN_ICON = join(PLUGIN_PATH, "plugin.png")

# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def resource(filename):
    """
    Return full path to a resource file.
    """
    return join(RESOURCE_PATH, filename)


def skin(filename):
    """
    Return full path to a skin file.
    """
    return join(SKIN_PATH, filename)


def icon(filename):
    """
    Return full path to an icon.
    """
    return join(ICON_PATH, filename)


def locale(filename):
    """
    Return full path to a locale file.
    """
    return join(LOCALE_PATH, filename)


# ------------------------------------------------------------------------------
# Media directories
# ------------------------------------------------------------------------------

def default_media_directory():
    """
    Return the default media directory.

    The directory is selected using the following priority:

        1. /media/hdd/music
        2. /media/hdd/Music
        3. /media/hdd
        4. /media
        5. /

    The returned path always ends with "/". Components.FileList.FileList
    builds child paths by string-concatenating `directory` with each
    entry name; without a trailing slash, a subdirectory such as
    "flac" under "/media/hdd/music" is concatenated into the
    non-existent path "/media/hdd/musicflac", which then fails the
    directory check and gets misclassified as a file (a real device
    build 0004 bug: see docs/Claude_notes_build0004.txt).
    """

    candidates = (
        "/media/hdd/music",
        "/media/hdd/Music",
        "/media/hdd",
        "/media",
        "/",
    )

    for directory in candidates:
        if isdir(directory):
            return ensure_trailing_slash(directory)

    return "/"


def ensure_trailing_slash(directory):
    """
    Return `directory` with exactly one trailing "/".

    Components.FileList.FileList requires a trailing slash on its
    `directory` argument (see default_media_directory() above); this
    helper normalizes any directory string -- including ones the user
    typed into Settings -- before it is handed to FileList.
    """

    if not directory:
        return "/"

    if not directory.endswith("/"):
        return directory + "/"

    return directory

# ------------------------------------------------------------------------------
# End of file

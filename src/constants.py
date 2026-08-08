# ==============================================================================
# MediaPlayer3
#
# File        : constants.py
# Description : Global constants used throughout the project.
#
# Author      : MediaPlayer3 Project
# Copyright   : (C) 2026 MediaPlayer3 Project
# License     : GNU General Public License v2 (GPL-2.0)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Compatible  : OpenViX, OpenATV (planned)
# Python      : 3.13+
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-07-04  Build 0001
#   - Initial version.
# ------------------------------------------------------------------------------

"""
Global constants.

This module contains application-wide constants shared by all modules.

Do not duplicate constant values in other modules.
"""

# ------------------------------------------------------------------------------
# Player states
# ------------------------------------------------------------------------------

STATE_IDLE = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_STOPPED = 3
STATE_SEEKING = 4
STATE_ERROR = 5

# ------------------------------------------------------------------------------
# Playback directions
# ------------------------------------------------------------------------------

SEEK_FORWARD = 1
SEEK_BACKWARD = -1

# ------------------------------------------------------------------------------
# Playlist modes
# ------------------------------------------------------------------------------

PLAYLIST_NORMAL = 0
PLAYLIST_REPEAT = 1
PLAYLIST_REPEAT_ONE = 2
PLAYLIST_SHUFFLE = 3

# ------------------------------------------------------------------------------
# Log levels
# ------------------------------------------------------------------------------

LOG_DEBUG = "DEBUG"
LOG_INFO = "INFO"
LOG_WARNING = "WARNING"
LOG_ERROR = "ERROR"

# ------------------------------------------------------------------------------
# Event names
# ------------------------------------------------------------------------------

EVENT_STARTUP = "startup"
EVENT_SHUTDOWN = "shutdown"

EVENT_PLAY = "play"
EVENT_PAUSE = "pause"
EVENT_STOP = "stop"

EVENT_SEEK = "seek"

EVENT_NEXT = "next"
EVENT_PREVIOUS = "previous"

EVENT_EOF = "end_of_file"

EVENT_ERROR = "error"

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

DEFAULT_LANGUAGE = "fi"

DEFAULT_LOG_DIRECTORY = "/tmp"

DEFAULT_LOG_KEEP = 10

DEFAULT_DEVELOPER_MODE = False

DEFAULT_DEBUG_LOGGING = False

# ------------------------------------------------------------------------------
# Supported audio file extensions
# ------------------------------------------------------------------------------

SUPPORTED_AUDIO_EXTENSIONS = (
    ".mp3",
    ".flac",
    ".wav",
    ".ogg",
    ".aac",
    ".m4a",
)

# ------------------------------------------------------------------------------
# Playlist file extensions (Build 0007 -- PLAYLIST_MANAGER_SPEC.md)
# ------------------------------------------------------------------------------

PLAYLIST_FILE_EXTENSIONS = (
    ".m3u",
    ".m3u8",
)

# ------------------------------------------------------------------------------
# Default filenames
# ------------------------------------------------------------------------------

LOG_CURRENT_NAME = "MediaPlayer3.current.log"

LOG_FILE_PREFIX = "MediaPlayer3"

SETTINGS_FILENAME = "settings.json"

# ------------------------------------------------------------------------------
# End of file
# ------------------------------------------------------------------------------

#end_of_file

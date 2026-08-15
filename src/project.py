# ==============================================================================
# MediaPlayer3
#
# File        : project.py
# Description : Project information and build metadata.
#
# Author      : MediaPlayer3 Project
# Copyright   : (C) 2026 MediaPlayer3 Project
# License     : GNU General Public License v3 (GPL-3.0-or-later)
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
#
# 2026-07-12  Build 0004
#   - Version bumped to 0.4.0-dev / Build 0004 (Screen Layer redesign).
#
# 2026-07-14  Build 0005
#   - Version bumped to 0.5.0-dev / Build 0005 (Playback Experience:
#     Playback Queue, progress bar, Previous/Next, Auto Next).
#
# 2026-07-19  Build 0006
#   - Version bumped to 0.6.0-dev / Build 0006 (Customization & Rich
#     Metadata: LocalizationManager, SkinManager, metadata/artwork,
#     themes, expanded PlaybackInfoScreen, developer diagnostics).
#
# 2026-07-19  Build 0007
#   - Version bumped to 0.7.0-dev / Build 0007 (Media Collections:
#     PlaylistManager, InternetRadioManager, StorageManager,
#     PlaylistScreen, RadioBrowserScreen).
#
# 2026-07-28  Build 0008
#   - Version bumped to 0.8.0-dev / Build 0008 (Music Discovery &
#     Help: LibraryManager, MusicLibraryScreen, LyricsManager,
#     HelpManager, HelpScreen, MainScreen information views).
#
# 2026-08-11  Build 0010
#   - Version bumped to 1.0.0-beta (BUILD_0010_PLAN.md fully
#     implemented and device-confirmed; entering beta). BUILD stays
#     "0010" -- the internal build/round-tracking identifier used
#     throughout CHANGELOG.md and the per-build spec documents is
#     unrelated to the user-facing VERSION string bumped here.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 project information.

This module contains all project-wide metadata that may be displayed
in the About dialog, diagnostic reports, log files and package
information.

Other modules should import these values instead of defining their own.
"""

# ------------------------------------------------------------------------------
# Project information
# ------------------------------------------------------------------------------

PROJECT_NAME = "MediaPlayer3"
PROJECT_SHORT_NAME = "mediaplayer3"

APPLICATION_ID = "org.enigma2.mediaplayer3"

# ------------------------------------------------------------------------------
# Version information
# ------------------------------------------------------------------------------

VERSION = "1.0.0-beta"
BUILD = "0010"

# ------------------------------------------------------------------------------
# Author information
# ------------------------------------------------------------------------------

AUTHOR = "MediaPlayer3 Project"

COPYRIGHT = "Copyright (C) 2026 MediaPlayer3 Project"

LICENSE = "GPL-3.0-or-later"

# ------------------------------------------------------------------------------
# Project URLs
# ------------------------------------------------------------------------------

HOMEPAGE = ""

REPOSITORY = ""

ISSUE_TRACKER = ""

# ------------------------------------------------------------------------------
# Compatibility
# ------------------------------------------------------------------------------

SUPPORTED_IMAGES = (
    "OpenViX",
    "OpenATV",
)

MINIMUM_PYTHON = (3, 13)

# ------------------------------------------------------------------------------
# Log file prefix
# ------------------------------------------------------------------------------

LOG_PREFIX = "mediaplayer3"

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

CONFIG_NAMESPACE = "plugins.mediaplayer3"

# ------------------------------------------------------------------------------
# End of file
# ------------------------------------------------------------------------------

#end_of_file

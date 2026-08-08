# ==============================================================================
# MediaPlayer3
#
# File        : features.py
# Description : Feature flags for development and future functionality.
#
# Author      : MediaPlayer3 Project
# Copyright   : (C) 2026 MediaPlayer3 Project
# License     : GNU General Public License v2 (GPL-2.0)
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
Feature flags.

Feature flags are compile/development time switches.

These are NOT user settings.
"""

# ------------------------------------------------------------------------------
# Core
# ------------------------------------------------------------------------------

FEATURE_DEVELOPER = True

FEATURE_DIAGNOSTICS = True

FEATURE_LOG_EXPORT = True

# ------------------------------------------------------------------------------
# Playback
# ------------------------------------------------------------------------------

FEATURE_PLAYLIST = True

FEATURE_RESUME = True

FEATURE_SHUFFLE = False

FEATURE_REPEAT = False

# ------------------------------------------------------------------------------
# Metadata
# ------------------------------------------------------------------------------

FEATURE_ALBUM_ART = False

FEATURE_LYRICS = False

FEATURE_ID3 = False

# ------------------------------------------------------------------------------
# Future
# ------------------------------------------------------------------------------

FEATURE_INTERNET_RADIO = False

FEATURE_PODCASTS = False

FEATURE_DLNA = False

FEATURE_NETWORK_BROWSER = False

# ------------------------------------------------------------------------------
# End of file
# ------------------------------------------------------------------------------

#end_of_file

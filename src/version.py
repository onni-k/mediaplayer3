# ==============================================================================
# MediaPlayer3
#
# File        : version.py
# Description : Version helper functions.
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
Version helper functions.

This module provides a single place to retrieve formatted version
information for the About dialog, log files and diagnostic reports.
"""

from .project import (
    PROJECT_NAME,
    VERSION,
    BUILD,
)

# ------------------------------------------------------------------------------
# Public helper functions
# ------------------------------------------------------------------------------

def get_project_name():
    """Return project name."""
    return PROJECT_NAME


def get_version():
    """Return version string."""
    return VERSION


def get_build():
    """Return build number."""
    return BUILD


def get_version_string():
    """
    Return formatted version string.

    Example:
        MediaPlayer3 0.1.0-dev (Build 0001)
    """
    return f"{PROJECT_NAME} {VERSION} (Build {BUILD})"


def get_short_version():
    """
    Return compact version string.

    Example:
        0.1.0-dev
    """
    return VERSION


# ------------------------------------------------------------------------------
# End of file
# ------------------------------------------------------------------------------

#end_of_file

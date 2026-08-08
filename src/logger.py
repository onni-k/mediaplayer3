# ==============================================================================
# MediaPlayer3
#
# File        : logger.py
# Description : Application logging.
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
# Implements  : LOGGER_SPEC.md v0.1
# Architecture: ARCHITECTURE.md v0.3
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-07-04  Build 0001
#   - Initial version.
#
# 2026-07-10  Build 0003
#   - Added printf-style argument support to debug()/info()/warning()/error()
#     so callers can use logger.info("[Tag] %s", value).
#   - Added a shared module-level `logger` instance.
#
# 2026-07-12  Build 0004
#   - Added Developer Mode verbosity levels (OFF / BASIC / VERBOSE) as
#     defined in LOGGER_SPEC.md section 4.
#   - Added state()/action() convenience methods (LOGGER_SPEC.md section 3).
#   - Added basic()/verbose() helpers that are only written when Developer
#     Mode is at least BASIC/VERBOSE, so Screens and Controllers can log
#     lifecycle/navigation detail without flooding normal user logs.
#   - Existing debug()/info()/warning()/error() calls remain unchanged, so
#     Build 0003 Revision 1 code keeps working without modification.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 logger.

Provides timestamped logging to stdout and an optional log file.

Developer Mode controls verbosity, per LOGGER_SPEC.md section 4:

    OFF      - only major application events (existing info()/error() calls).
    BASIC    - additionally: screen lifecycle, controller lifecycle,
               state transitions, configuration loading.
    VERBOSE  - additionally: remote control keys, navigation decisions,
               compatibility decisions, service references, internal
               controller state, timing information.

Future versions will support:

    * Log rotation
    * Automatic cleanup
    * Current log symlink
    * Log export (see DeveloperScreen / RELEASE_CHECKLIST.md)
"""

from datetime import datetime

from .constants import (
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARNING,
    LOG_ERROR,
)

# ------------------------------------------------------------------------------
# Additional logical log levels (LOGGER_SPEC.md section 3)
# ------------------------------------------------------------------------------
#
# INFO, WARNING, ERROR and DEBUG already existed in constants.py (Build
# 0001). STATE and ACTION are new logical levels introduced by Build 0004;
# both are currently mapped onto the plain INFO level for display, since
# LOGGER_SPEC.md section 3 notes that "future versions may map these
# logical levels to Python logging levels" -- Build 0004 only needs the
# distinction to exist, not a separate output format.

LOG_STATE = "STATE"
LOG_ACTION = "ACTION"

# ------------------------------------------------------------------------------
# Developer Mode verbosity levels
# ------------------------------------------------------------------------------

DEVELOPER_MODE_OFF = "OFF"
DEVELOPER_MODE_BASIC = "BASIC"
DEVELOPER_MODE_VERBOSE = "VERBOSE"

_DEVELOPER_MODE_ORDER = {
    DEVELOPER_MODE_OFF: 0,
    DEVELOPER_MODE_BASIC: 1,
    DEVELOPER_MODE_VERBOSE: 2,
}


class Logger:
    """
    Simple application logger.
    """

    def __init__(self, debug=False, developer_mode=DEVELOPER_MODE_OFF):

        self.debug_enabled = debug

        if developer_mode not in _DEVELOPER_MODE_ORDER:
            developer_mode = DEVELOPER_MODE_OFF

        self._developer_mode = developer_mode

    # ------------------------------------------------------------------
    # Developer Mode
    # ------------------------------------------------------------------

    def setDeveloperMode(self, mode):
        """
        Set the current Developer Mode verbosity level.

        `mode` must be one of DEVELOPER_MODE_OFF, DEVELOPER_MODE_BASIC or
        DEVELOPER_MODE_VERBOSE. Unknown values fall back to OFF rather than
        raising, since logging must never change application behaviour.
        """

        if mode not in _DEVELOPER_MODE_ORDER:
            mode = DEVELOPER_MODE_OFF

        previous = self._developer_mode

        self._developer_mode = mode

        if mode != previous:
            self.info("Developer mode: %s -> %s", previous, mode)

    # ------------------------------------------------------------------

    def getDeveloperMode(self):
        """
        Return the current Developer Mode verbosity level.
        """

        return self._developer_mode

    # ------------------------------------------------------------------

    def _developerLevelActive(self, required_mode):

        return (
            _DEVELOPER_MODE_ORDER[self._developer_mode]
            >= _DEVELOPER_MODE_ORDER[required_mode]
        )

    # ------------------------------------------------------------------

    def _timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------

    def _write(self, level, message, *args):

        if level == LOG_DEBUG and not self.debug_enabled:
            return

        if args:
            try:
                message = message % args
            except Exception:
                # Never let a bad format string crash the caller.
                message = "{} {}".format(message, args)

        line = "[{}] [{:<7}] {}".format(
            self._timestamp(),
            level,
            message
        )

        print(line)

    # ------------------------------------------------------------------
    # Standard log levels (unchanged public API)
    # ------------------------------------------------------------------

    def debug(self, message, *args):
        self._write(LOG_DEBUG, message, *args)

    # ------------------------------------------------------------------

    def info(self, message, *args):
        self._write(LOG_INFO, message, *args)

    # ------------------------------------------------------------------

    def warning(self, message, *args):
        self._write(LOG_WARNING, message, *args)

    # ------------------------------------------------------------------

    def error(self, message, *args):
        self._write(LOG_ERROR, message, *args)

    # ------------------------------------------------------------------
    # New logical levels (Build 0004)
    # ------------------------------------------------------------------

    def state(self, message, *args):
        """
        Log a state transition (LOGGER_SPEC.md section 3, STATE level).
        """

        self._write(LOG_STATE, message, *args)

    # ------------------------------------------------------------------

    def action(self, message, *args):
        """
        Log a user initiated operation (LOGGER_SPEC.md section 3, ACTION
        level).
        """

        self._write(LOG_ACTION, message, *args)

    # ------------------------------------------------------------------
    # Developer Mode gated helpers
    # ------------------------------------------------------------------

    def basic(self, message, *args):
        """
        Write a log entry only when Developer Mode is BASIC or VERBOSE.

        Intended for Screen/Controller lifecycle and navigation detail
        that LOGGER_SPEC.md section 10 assigns to Developer Mode BASIC.
        """

        if self._developerLevelActive(DEVELOPER_MODE_BASIC):
            self._write(LOG_INFO, message, *args)

    # ------------------------------------------------------------------

    def verbose(self, message, *args):
        """
        Write a log entry only when Developer Mode is VERBOSE.

        Intended for remote control keys, navigation decisions,
        compatibility decisions and internal controller state, per
        LOGGER_SPEC.md section 10.
        """

        if self._developerLevelActive(DEVELOPER_MODE_VERBOSE):
            self._write(LOG_DEBUG if self.debug_enabled else LOG_INFO, message, *args)


# ------------------------------------------------------------------------------
# Shared logger instance
# ------------------------------------------------------------------------------
#
# Every module (Screens, Controllers, Core) does `from .logger import logger`
# and expects a ready-to-use, shared instance -- the same singleton pattern
# already used for `compatibility` in compatibility.py and `systeminfo` in
# systeminfo.py.
#
# plugin.py still creates and uses its own Logger(debug=True) instance for
# the very first startup banner; this shared instance is what every other
# module uses afterwards. plugin.py applies the saved Developer Mode
# configuration value to this shared instance during startup.
#
logger = Logger(debug=True)


#end_of_file

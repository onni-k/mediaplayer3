# ==============================================================================
#
# MediaPlayer3
#
# File        : statusbar.py
#
# Description :
#
#     StatusBar
#
#     Formats and displays playback status information in the Screen
#     Layer UI. Used by MainScreen since Build 0004 (previously used by
#     Browser, now BrowserScreen, in Build 0003). StatusBar owns no
#     playback state of its own -- it only renders whatever
#     PlaybackController reports.
#
#     StatusBar communicates only with the Label widget it is given.
#     It never talks to PlaybackController, ServiceController or
#     Enigma2 directly -- see ARCHITECTURE.md section 4
#     (Controller Layer) and BUILD_0003_PLAN.md section 3
#     (Build 0003 Goals -> User Interface).
#
# Implements :
#
#     BUILD_0003_PLAN.md v0.1 (User Interface / StatusBar)
#
# Architecture :
#
#     ARCHITECTURE.md v0.2
#
# Project :
#
#     MediaPlayer3
#
# License :
#
#     GPL-2.0-or-later
#
# ==============================================================================

from __future__ import annotations

import os

from .logger import logger
from .playback_controller import PlaybackController


class StatusBar:
    """
    Playback status display.

    Wraps a single Label widget (Browser's "status" widget) and
    translates PlaybackController state into readable text.

    StatusBar is intentionally passive: Browser decides *when* to
    update, StatusBar only decides *how* the update is displayed.
    """

    TEXT_READY = "Ready"
    TEXT_PLAYING = "Playing: {filename}"
    TEXT_PAUSED = "Paused: {filename}"
    TEXT_STOPPED = "Stopped"
    TEXT_ERROR = "Error: {message}"

    # Map PlaybackController state strings to display templates.
    _STATE_TEXT = {
        PlaybackController.STATE_PLAYING: TEXT_PLAYING,
        PlaybackController.STATE_PAUSED: TEXT_PAUSED,
        PlaybackController.STATE_STOPPED: TEXT_STOPPED,
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, widget):
        """
        Create a StatusBar bound to a Label widget.

        `widget` is expected to be Browser's self["status"] Label,
        already created by the caller.
        """

        self._widget = widget

        self._log("Created")

        self._log("Initializing")

        self.showReady()

        self._log("Ready")

    # ------------------------------------------------------------------

    def _log(self, message: str):

        logger.info("[StatusBar] %s", message)

    # ------------------------------------------------------------------
    # Display Helpers
    # ------------------------------------------------------------------

    def _setText(self, text: str) -> None:
        """
        Push text to the bound widget.

        Guards against a missing/torn-down widget so a late status
        update during shutdown never raises.
        """

        if self._widget is None:
            return

        try:

            self._widget.setText(text)

        except Exception as error:

            self._log(f"Unable to update status widget: {error}")

# End of Part 1
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def showReady(self) -> None:
        """
        Display the initial/idle state.
        """

        self._setText(self.TEXT_READY)

    # ------------------------------------------------------------------

    def showPlaying(self, filename: str | None = None) -> None:
        """
        Display the playing state for the given filename.
        """

        self._setText(
            self.TEXT_PLAYING.format(filename=self._basename(filename))
        )

    # ------------------------------------------------------------------

    def showPaused(self, filename: str | None = None) -> None:
        """
        Display the paused state for the given filename.
        """

        self._setText(
            self.TEXT_PAUSED.format(filename=self._basename(filename))
        )

    # ------------------------------------------------------------------

    def showStopped(self) -> None:
        """
        Display the stopped state.
        """

        self._setText(self.TEXT_STOPPED)

    # ------------------------------------------------------------------

    def showError(self, message: str) -> None:
        """
        Display an error message.
        """

        self._log(f"Error: {message}")

        self._setText(self.TEXT_ERROR.format(message=message))

# End of Part 2
    # ------------------------------------------------------------------

    def showState(self, state: str, filename: str | None = None) -> None:
        """
        Display a PlaybackController state string directly.

        Convenience entry point for callers that already hold a
        PlaybackController state (e.g. PlaybackController.getState()),
        so Browser does not need an if/elif ladder of its own.

        Falls back to displaying the raw state string for any state
        not explicitly known to StatusBar, rather than failing.
        """

        template = self._STATE_TEXT.get(state)

        if template is None:

            self._setText(state)

            return

        if "{filename}" in template:

            self._setText(template.format(filename=self._basename(filename)))

            return

        self._setText(template)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _basename(filename: str | None) -> str:
        """
        Return a display-friendly filename.

        Full paths are shortened to the bare filename so the status
        line stays readable regardless of directory depth.
        """

        if not filename:
            return ""

        return os.path.basename(filename)


# ==============================================================================
#
# Build Notes
#
# Build 0003 introduces StatusBar as a thin presentation helper used
# by Browser. StatusBar responsibilities:
#
#   - Formatting playback state text
#   - Updating the "status" Label widget
#   - Shortening filenames for display
#
# StatusBar is intentionally NOT responsible for:
#
#   - Holding playback state
#   - Deciding when a state change occurred
#   - Talking to PlaybackController, ServiceController or Enigma2
#
# Those responsibilities remain with PlaybackController and Browser,
# per ARCHITECTURE.md section 4 (Controller Layer).
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

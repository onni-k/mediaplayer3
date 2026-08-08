# ==============================================================================
#
# MediaPlayer3
#
# File        : service_controller.py
#
# Description :
#
#     ServiceController provides the interface between MediaPlayer3 and
#     Enigma2 playback services.
#
#     Browser communicates with PlaybackController.
#     PlaybackController communicates with ServiceController.
#     ServiceController communicates with Enigma2 through compatibility.py.
#
# Implements :
#
#     SERVICE_CONTROLLER_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md v0.3
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
# 2026-07-10  Build 0003 Revision 1
#   - Previous service capture/restore (see docs/Claude_korjaukset.txt).
#
# 2026-07-12  Build 0004
#   - No functional changes. ServiceController's public interface and
#     behaviour are unchanged; only the Screen Layer above it (MainScreen,
#     BrowserScreen) and PlaybackController's new query methods changed.
#
# 2026-07-14  Build 0005
#   - Added getPlaybackPosition() and getStreamInfo(): thin delegates to
#     compatibility.py's new version-dependent queries, so
#     PlaybackController can keep talking only to ServiceController
#     (never to compatibility.py directly) while still getting real
#     elapsed/duration/stream-info data for the Build 0005 progress bar
#     and Playback Statistics.
#
# 2026-07-19  Build 0006 (device test round 3)
#   - Added stopPreviousServiceNow(): stops whatever's playing
#     (typically live TV) immediately, for MainScreen to call once at
#     startup, instead of waiting for the first track. Distinct from
#     the safety-guarded _stopService() (which only ever stops a
#     service we started ourselves); also sets _took_over_playback so
#     restoration on close still works even if the user never ends up
#     playing anything.
#
# 2026-08-01  Build 0008 (device test round 7)
#   - Added seekTo(): delegates to compatibility.seekTo() for absolute
#     seeking, alongside the existing seekRelative() delegate -- see
#     compatibility.py's own change history for why this was needed.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Optional

from .compatibility import compatibility
from .logger import logger


class ServiceController:
    """
    Interface between MediaPlayer3 and Enigma2 playback services.

    This class intentionally hides Enigma2-specific implementation details
    from higher application layers. All access to NavigationInstance and
    eServiceReference happens through compatibility.py, never directly.
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.3"

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------

    STATE_STOPPED = "STOPPED"
    STATE_PLAYING = "PLAYING"
    STATE_PAUSED = "PAUSED"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Initialize ServiceController."""

        self._log("Created")

        self._initialized = False

        self._current_service = None
        self._service_reference = None

        # Whatever was playing before MediaPlayer3 took over playback
        # (typically live TV), captured once so it can be restored when
        # MediaPlayer3 closes. See _capturePreviousService() and
        # _restorePreviousService().
        self._previous_service = None

        # True only once we have actually replaced the box's playing
        # service with our own (i.e. _startService() succeeded at
        # least once). Restoring the previous service on close is only
        # meaningful -- and should only ever be attempted -- if we
        # really took over playback; otherwise nothing was displaced
        # and "restoring" would just cause a pointless re-zap.
        self._took_over_playback = False

        self._playback_state = self.STATE_STOPPED

        self._last_error: Optional[str] = None

        self._initialize()

    # ------------------------------------------------------------------

    def _initialize(self) -> None:
        """Initialize internal controller state."""

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _reset(self) -> None:
        """Reset internal playback state."""

        self._current_service = None
        self._service_reference = None
        self._previous_service = None
        self._took_over_playback = False

        self._playback_state = self.STATE_STOPPED

        self._last_error = None

        self._log("Controller state reset.")

    # ------------------------------------------------------------------

    def _cleanup(self) -> None:
        """Release controller resources."""

        self._log("Closing")

        self._stopService()

        self._restorePreviousService()

        self._reset()

        self._initialized = False

        self._log("Closed")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        """Write a controller log entry."""

        logger.info("[ServiceController] %s", message)

# End of Part 1
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play(self, filename: str, use_exteplayer3: bool = False) -> bool:
        """
        Start playback of the given file.

        Args:
            filename: File path or stream URL.
            use_exteplayer3: Build 0009, device test round 11 -- use
                ExtEplayer3 instead of the default GStreamer-based
                service type. See compatibility.createServiceReference()
                for the full reasoning; always False for local file
                playback (only PlaybackController.playStream() ever
                passes True, gated by cfg.radio.use_exteplayer3).

        Returns:
            True if playback was started successfully.
        """

        if not self._initialized:
            self._log("play() called before initialization.")
            return False

        self._log(f"Play requested: {filename}")

        #
        # Remember whatever was playing before we take over (see
        # _capturePreviousService()), so it can be restored when
        # MediaPlayer3 closes. This must happen before we touch
        # anything else, and regardless of whether the rest of play()
        # below succeeds.
        #
        self._capturePreviousService()

        if not self._createServiceReference(filename, use_exteplayer3=use_exteplayer3):
            self._log("Playback aborted: unable to create service reference.")
            return False

        if not self._startService():
            self._log("Playback aborted: unable to start playback service.")
            return False

        self._playback_state = self.STATE_PLAYING

        self._log("Playback started.")

        return True

    # ------------------------------------------------------------------

    def stop(self) -> bool:
        """
        Stop playback.
        """

        if not self._initialized:
            self._log("stop() called before initialization.")
            return False

        self._log("Stop requested.")

        if not self._stopService():
            return False

        self._playback_state = self.STATE_STOPPED

        self._log("Playback stopped.")

        return True

    # ------------------------------------------------------------------

    def pause(self) -> bool:
        """
        Pause playback.
        """

        if not self._initialized:
            self._log("pause() called before initialization.")
            return False

        if self._playback_state != self.STATE_PLAYING:
            self._log("Pause ignored: playback is not active.")
            return False

        self._log("Pause requested.")

        navigation = compatibility.getNavigationInstance()

        if navigation is not None:

            try:
                service = navigation.getCurrentService()

                pauseable = service.pause() if service is not None else None

                if pauseable is not None:
                    pauseable.pause()

            except Exception as error:

                self._last_error = f"Unable to pause playback: {error}"

                self._log(self._last_error)

                return False

        self._playback_state = self.STATE_PAUSED

        self._log("Playback paused.")

        return True

    # ------------------------------------------------------------------

    def resume(self) -> bool:
        """
        Resume playback.
        """

        if not self._initialized:
            self._log("resume() called before initialization.")
            return False

        if self._playback_state != self.STATE_PAUSED:
            self._log("Resume ignored: playback is not paused.")
            return False

        self._log("Resume requested.")

        navigation = compatibility.getNavigationInstance()

        if navigation is not None:

            try:
                service = navigation.getCurrentService()

                pauseable = service.pause() if service is not None else None

                if pauseable is not None:
                    pauseable.unpause()

            except Exception as error:

                self._last_error = f"Unable to resume playback: {error}"

                self._log(self._last_error)

                return False

        self._playback_state = self.STATE_PLAYING

        self._log("Playback resumed.")

        return True

    # ------------------------------------------------------------------

    def getCurrentService(self):
        """
        Return the current service object.
        """

        return self._current_service

    # ------------------------------------------------------------------

    def getPlaybackState(self) -> str:
        """
        Return the current playback state.
        """

        return self._playback_state

    # ------------------------------------------------------------------

    def isServiceRunning(self) -> bool:
        """
        Check whether a playback service is currently active.
        """

        return self._current_service is not None

    # ------------------------------------------------------------------

    def getPlaybackPosition(self):
        """
        Return (elapsed_seconds, duration_seconds) for the currently
        playing service, or (None, None) if no service is running or
        the position/duration cannot be determined.

        Delegates to compatibility.py -- see
        Compatibility.getPlaybackPosition() for the version-dependent
        implementation. ServiceController never queries
        iSeekableService itself.
        """

        if not self.isServiceRunning():
            return None, None

        return compatibility.getPlaybackPosition()

    # ------------------------------------------------------------------

    def getStreamInfo(self):
        """
        Return best-effort stream information (codec, sample rate,
        bitrate, channels) for the currently playing service.

        Delegates to compatibility.py -- see
        Compatibility.getStreamInfo(). Returns all-"Unknown" values
        when no service is running.
        """

        if not self.isServiceRunning():

            return {
                "codec": "Unknown",
                "sample_rate": "Unknown",
                "bitrate": "Unknown",
                "channels": "Unknown",
            }

        return compatibility.getStreamInfo()

    # ------------------------------------------------------------------

    def seekRelative(self, offset_seconds) -> bool:
        """
        Seek the currently playing service by `offset_seconds`
        (positive = forward, negative = backward).

        Delegates to compatibility.py -- see
        Compatibility.seekRelative(). Returns False when no service
        is running.
        """

        if not self.isServiceRunning():
            return False

        return compatibility.seekRelative(offset_seconds)

    # ------------------------------------------------------------------

    def seekTo(self, position_seconds) -> bool:
        """
        Seek the currently playing service to an absolute position
        (seconds from the start of the track).

        Delegates to compatibility.py -- see Compatibility.seekTo().
        Returns False when no service is running.
        """

        if not self.isServiceRunning():
            return False

        return compatibility.seekTo(position_seconds)

# End of Part 2
    # ------------------------------------------------------------------
    # Internal Service Methods
    # ------------------------------------------------------------------

    def _createServiceReference(self, filename: str, use_exteplayer3: bool = False) -> bool:
        """
        Create a playback service reference through compatibility.py.
        """

        self._log(f"Creating service reference: {filename}")

        reference = compatibility.createServiceReference(filename, use_exteplayer3=use_exteplayer3)

        if reference is None:

            self._last_error = "Unable to create service reference."

            self._log(self._last_error)

            return False

        self._service_reference = reference

        return True

    # ------------------------------------------------------------------

    def _startService(self) -> bool:
        """
        Start the playback service through NavigationInstance.
        """

        self._log("Starting playback service.")

        navigation = compatibility.getNavigationInstance()

        if navigation is None:

            self._last_error = "NavigationInstance not available."

            self._log(self._last_error)

            return False

        try:
            navigation.playService(self._service_reference)

        except Exception as error:

            self._last_error = f"Unable to start playback service: {error}"

            self._log(self._last_error)

            return False

        self._current_service = self._service_reference

        self._took_over_playback = True

        return True

    # ------------------------------------------------------------------

    def _stopService(self) -> bool:
        """
        Stop the playback service through NavigationInstance.

        navigation.stopService() is global -- it stops whatever
        service is currently playing on the box, not specifically
        "our" service. If ServiceController never actually started a
        service (e.g. play() failed before _startService()), there is
        nothing of ours to stop, and calling stopService() anyway
        would tear down an unrelated service the user was already
        watching (typically live TV running in the background).

        Only ever stop when self._current_service shows we are the
        ones who started it.
        """

        if self._current_service is None:

            self._log("No active service to stop.")

            return True

        self._log("Stopping playback service.")

        navigation = compatibility.getNavigationInstance()

        if navigation is not None:

            try:
                navigation.stopService()

            except Exception as error:

                self._log(f"Error while stopping playback service: {error}")

        self._current_service = None
        self._service_reference = None

        return True

    # ------------------------------------------------------------------

    def stopPreviousServiceNow(self) -> bool:
        """
        Stop whatever service is currently active (typically live TV)
        and capture it for later restoration, immediately -- rather
        than waiting until the first track is actually played.

        Build 0006 (device test round 3), requested after real device
        feedback: TV audio kept playing in the background until the
        user actually picked a track, instead of stopping as soon as
        MediaPlayer3 opened.

        Unlike the internal _stopService() (which deliberately only
        ever stops a service *we* started, to avoid tearing down
        unrelated live TV when we have nothing of our own running),
        this is an explicit, intentional "stop whatever's on screen
        right now" action, meant to be called once, right at startup.

        Also sets _took_over_playback, so _restorePreviousService()
        still restores TV on close even if the user never ends up
        playing anything (just browses/opens Settings and exits).

        Never raises. Safe to call even if nothing is currently
        playing (navigation.stopService() is a no-op in that case).
        """

        if not self._initialized:

            self._log("stopPreviousServiceNow() called before initialization.")

            return False

        self._capturePreviousService()

        navigation = compatibility.getNavigationInstance()

        if navigation is None:

            self._log("Unable to stop current service: NavigationInstance not available.")

            return False

        try:
            navigation.stopService()

        except Exception as error:

            self._log(f"Error while stopping current service at startup: {error}")

            return False

        self._took_over_playback = True

        self._log("Stopped current service at startup.")

        return True

    # ------------------------------------------------------------------

    def _capturePreviousService(self) -> None:
        """
        Remember whatever service is currently playing before
        MediaPlayer3 takes it over (typically live TV), so it can be
        restored via _restorePreviousService() once MediaPlayer3
        closes.

        Captured at most once per ServiceController lifetime: the
        first capture is assumed to represent the state the box was
        in before MediaPlayer3 started, and must not be silently
        replaced by our own service on a later play() call (e.g. the
        user picking a second track without stopping the first).
        """

        if self._previous_service is not None:

            return

        if self._current_service is not None:

            # We already own whatever is "current" right now -- it is
            # our own previous track, not something to restore later.
            return

        reference = compatibility.getCurrentServiceReference()

        if reference is not None:

            self._previous_service = reference

            self._log("Captured previous service for later restoration.")

    # ------------------------------------------------------------------

    def _restorePreviousService(self) -> None:
        """
        Restore the service that was playing before MediaPlayer3 took
        over playback (typically live TV), if one was captured.

        Only called from _cleanup(), i.e. when MediaPlayer3 itself is
        closing -- not from every stop() -- so that stopping or
        switching tracks while browsing does not repeatedly re-zap
        the tuner. Also only attempted when we actually displaced a
        service in the first place (_took_over_playback); otherwise
        there is nothing to hand back and doing so would just cause a
        pointless re-zap.
        """

        if not self._took_over_playback:

            return

        if self._previous_service is None:

            return

        self._log("Restoring previous service.")

        navigation = compatibility.getNavigationInstance()

        if navigation is None:

            self._log("Unable to restore previous service: NavigationInstance not available.")

            return

        try:
            navigation.playService(self._previous_service)

        except Exception as error:

            self._log(f"Unable to restore previous service: {error}")

    # ------------------------------------------------------------------

    def _handleServiceEvent(self, event) -> None:
        """
        Handle playback events from the underlying service.

        Reserved for Build 0004, when ServiceEventTracker integration
        (see compatibility.hasServiceEventTracker()) will drive automatic
        end-of-file detection and position/duration updates.
        """

        self._log(f"Service event received: {event}")

# End of Part 3

# ==============================================================================
# End of file
# ==============================================================================

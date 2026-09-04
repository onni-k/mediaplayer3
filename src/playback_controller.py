# ==============================================================================
#
# MediaPlayer3
#
# File        : playback_controller.py
#
# Description :
#
#     Playback Controller
#
#     Coordinates playback requests between Browser and
#     ServiceController.
#
#     PlaybackController communicates only with ServiceController.
#     It never talks to compatibility.py or Enigma2 directly -- see
#     ARCHITECTURE.md section 4 (Controller Layer) and
#     PLAYBACK_CONTROLLER_SPEC.md section 3 (Design Principles).
#
# Implements :
#
#     PLAYBACK_CONTROLLER_SPEC.md v0.1
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
# 2026-07-10  Build 0003
#   - Initial PlaybackController.
#
# 2026-07-12  Build 0004
#   - Added hasMedia(), getElapsedTime(), getDuration() and getProgress()
#     so MainScreen, PlaybackInfoScreen and DeveloperScreen can query
#     playback progress through the public PlaybackController interface
#     (MAINSCREEN_SPEC.md section 8, PLAYBACKINFO_SPEC.md section 7)
#     without talking to ServiceController directly.
#   - Position/duration reporting is not yet implemented at the
#     ServiceController/Compatibility layer, so these currently return
#     None ("Unknown") rather than fabricated values; wiring them up to
#     real eServiceReference position/length queries is reserved for a
#     future build (see BUILD_0004_PLAN.md section 10).
#
# 2026-07-14  Build 0005
#   - Added Playback Queue: setQueue()/playQueue(), nextTrack(),
#     previousTrack(), hasNext(), hasPrevious(), getCurrentTrack(),
#     getQueueSize(), getQueuePosition() (PLAYBACK_QUEUE_SPEC.md).
#     BrowserScreen builds the queue and hands it to
#     PlaybackController once; PlaybackController owns all navigation
#     within it afterwards and no longer depends on BrowserScreen.
#   - getElapsedTime()/getDuration()/getProgress() now return real
#     values via ServiceController.getPlaybackPosition() (previously
#     always None). tick() refreshes them and drives Automatic Next
#     Track; MainScreen calls tick() once per second.
#   - Added getStreamInfo() passthrough for DeveloperScreen's Playback
#     Statistics page.
#   - PlaybackController still never talks to compatibility.py or
#     Enigma2 directly -- all of the above goes through
#     ServiceController, which is the one delegating to compatibility.py.
#
# 2026-07-16  Build 0005 (device test round 2)
#   - tick()'s "track finished" threshold changed from
#     `elapsed >= duration - 1` to `elapsed >= duration`. A real
#     device test showed tracks ending audibly early (elapsed=199,
#     duration=200 triggered Auto Next with real audio still playing)
#     -- elapsed/duration are already floor-truncated to whole seconds,
#     so the extra 1-second margin was unnecessary and cut up to ~2
#     real seconds off the end of every track.
#   - Added seekForward()/seekBackward(), delegating to
#     ServiceController.seekRelative() -> compatibility.py.
#
# 2026-07-19  Build 0006
#   - play() now caches tag metadata (via metadata.metadata_reader,
#     pure-Python FLAC/ID3v2/Ogg parsing -- no Enigma2 dependency) for
#     the current file, exposed through getMetadata()/
#     getEmbeddedArtwork(). Metadata extraction can never fail
#     playback startup -- read() itself never raises, and this is
#     wrapped in an additional try/except regardless.
#   - PlaybackController still never talks to compatibility.py,
#     LocalizationManager or SkinManager directly (BUILD_0006_PLAN.md
#     "Design Principles").
#
# 2026-07-19  Build 0006 (device test round 2)
#   - play() now clears cached position/duration for the previous
#     track immediately, instead of leaving them until the next
#     tick() call -- confirmed on a real device: switching tracks
#     briefly showed the OLD track's stale elapsed/duration/progress.
#
# 2026-07-19  Build 0006 (device test round 3)
#   - Added stopPreviousServiceNow(): passthrough to
#     ServiceController, for MainScreen to stop live TV immediately
#     at startup instead of waiting for the first track.
#
# 2026-07-19  Build 0007
#   - Added playStream()/isPlayingStream() for Internet Radio
#     (INTERNETRADIO_MANAGER_SPEC.md "PlaybackController receives
#     only the final validated stream URL."). Reuses the same
#     ServiceController.play()/compatibility.createServiceReference()
#     path as local files -- Enigma2's GStreamer/MP3 service factory
#     already resolves http(s):// URIs the same as local paths, so no
#     separate playback path was needed. Builds synthetic metadata
#     (station name as Title) instead of calling metadata_reader.read()
#     on the URL, which would only waste time.
#
# 2026-07-28  Build 0008
#   - Added getAdjacentFiles(): returns (previous_filename,
#     next_filename) for MainScreen's new Previous/Next queue preview
#     panel (BUILD_0008_PLAN.md "Previous / Next Preview").
#
# 2026-08-01  Build 0008 (device test round 3)
#   - Fixed a real bug confirmed by device logs across three rounds
#     (two images): the elapsed reading immediately after a track
#     starts is sometimes wildly wrong -- not a fixed offset, a
#     different, essentially random value each time (confirmed real
#     values: 0, 10, 12, 14, 15, 17, 41, 42, 49 seconds, all within
#     about a second of the track actually starting). This caused
#     both "song sounds like it ends early" (round 1) and "progress
#     bar gets stuck near the end" (round 2). Root cause: a known
#     class of GStreamer/DVB race condition where a fresh service can
#     report success (error_code 0) alongside a stale PTS value left
#     over from whatever played previously, before its own pipeline
#     has reset position tracking -- compatibility.py's existing
#     error_code check can't catch this, since the error code itself
#     is genuinely 0. tick() now rejects a reading that violates a
#     simple, provable invariant (elapsed can't exceed real wall-clock
#     time since the track started, plus a small buffering
#     allowance), but ONLY within a short settling window right after
#     playback begins -- the same invariant does NOT hold once a
#     legitimate forward seek has happened later in the track, so
#     applying it indefinitely would have broken seeking.
#
# 2026-08-01  Build 0008 (device test round 4)
#   - Added an "estimated position" diagnostic to tick()'s verbose
#     log: real wall-clock time since the track started, adjusted for
#     every seekForward()/seekBackward() call since then (tracked via
#     new _seek_offset_seconds), logged next to GStreamer's own
#     reported elapsed value on every tick -- including when that
#     reading gets discarded by the round-3 sanity check. Requested so
#     a future device log can show exactly how far GStreamer's
#     position tracking has drifted from real time, rather than only
#     ever showing GStreamer's own number with nothing to compare it
#     against. Neither value drives playback or the UI on its own.
#
# 2026-08-01  Build 0008 (device test round 5)
#   - Fixed two real gaps in round 3/4's position-sanity work, both
#     confirmed by a device log and one caught directly by the user
#     asking whether pause was accounted for:
#     (1) Pause wasn't excluded from the wall-clock estimate at all --
#         real time keeps advancing while paused even though the
#         track's own position does not, so any pause would have made
#         every subsequent reading look implausible and get wrongly
#         discarded. Added _paused_seconds_total/_pause_wall_time,
#         updated in pause()/resume().
#     (2) The fixed 5-second settling window let a persistently-wrong
#         GStreamer baseline through once it expired -- the log showed
#         one track's wrong ~52s baseline still completely unchanged
#         right as the window closed, then accepted and carried for
#         the rest of the track, reproducing the exact "ends early"
#         symptom this was meant to fix. The check now compares
#         against the seek/pause-adjusted estimate indefinitely
#         instead of only during a start-up window, which is sound
#         precisely because that estimate already reflects a seek or a
#         pause the moment the user acts, not only at track start.
#
# 2026-08-01  Build 0008 (device test round 6)
#   - Fixed a real bug confirmed by a device log: seekForward()/
#     seekBackward() accumulated the seek offset used for the
#     estimated-position diagnostic BEFORE checking whether the
#     underlying seek actually succeeded. A device log showed the
#     dedicated seek keys reaching here while an Internet Radio stream
#     was playing (MainScreen's LEFT/RIGHT already avoids this by
#     switching radio lists instead of seeking while streaming, but
#     the dedicated seek keys didn't check this) -- streams have no
#     seekable timeline, so the offset became wrong regardless of
#     whether the call underneath did anything meaningful. Both
#     methods now reject outright while _is_stream is set, and only
#     apply the offset once the seek has actually succeeded.
#   - Fixed a real UX regression from round 5's indefinite check: a
#     device log showed GStreamer's own reported elapsed getting stuck
#     at one wrong value for over twenty consecutive ticks (291s on a
#     231s track) -- correctly rejected the whole time, but the
#     practical effect was the displayed time going blank for that
#     entire stretch, worse for the user than a reading that's a
#     little off. tick() now falls back to the wall-clock estimate for
#     DISPLAY when GStreamer's own reading is rejected, but still never
#     lets a rejected reading itself trigger Automatic Next Track --
#     only a GStreamer value this method has actually trusted can do
#     that.
#
# 2026-08-01  Build 0008 (device test round 7)
#   - Fixed a real bug confirmed precisely by a device log: seeking
#     used compatibility.seekRelative(), which seeks relative to
#     GStreamer's OWN reported position -- unsafe, since that position
#     can itself be stale (rounds 1-6). GStreamer had gotten stuck
#     reporting 231 (the track's own duration) while the track was
#     genuinely only ~84s in (confirmed by the wall-clock estimate). A
#     "+30s" seek-forward request landed at 231 + 30 = 261, past the
#     end of the track, matching the math exactly -- explaining why
#     seeking "looked right" on screen (the display used the correct,
#     wall-clock-based estimate) but the audio itself jumped to
#     silence. seekForward()/seekBackward() now compute an absolute
#     target from THIS class's own trusted `_position` and call the
#     new compatibility.seekTo() instead, which never depends on
#     GStreamer's own current-position belief being correct. The
#     wall-clock estimate is also re-baselined to the seek target
#     (_rebaselineAfterSeek()) rather than accumulating an offset on
#     top of assumptions about where the track started.
#
# 2026-08-01  Build 0008 (device test round 9)
#   - Fixed a real bug confirmed by a device log: a fixed 5s sanity
#     tolerance was too tight for tracks that had been playing for
#     several minutes -- a track's own final, genuinely correct
#     GStreamer reading (224, matching duration exactly) was rejected
#     because the wall-clock estimate had drifted to 218.4 by then, a
#     normal ~2.5% divergence after 220s of continuous playback, not a
#     stale/wrong value. Visible as the progress bar showing a few
#     seconds remaining right as a track that had actually finished
#     should have moved on. Added POSITION_DRIFT_TOLERANCE_RATIO: the
#     tolerance now scales with how long the track has been running,
#     on top of the existing fixed base -- verified this still
#     reliably rejects the much larger stale-value gaps confirmed in
#     earlier rounds (all 10s or more, and usually far larger), since
#     those show up immediately at track start, before drift allowance
#     has had a chance to accumulate.
#
# 2026-08-03  Build 0009
#   - Added jumpToQueueIndex(): jumps directly to a specific index
#     within the current PlaybackQueue without replacing the queue
#     itself, delegating to the existing private _playIndex() (already
#     used internally by nextTrack()/previousTrack()). Needed for
#     MainScreen's new interactive Playlist Panel (MAINSCREEN_SPEC.md):
#     selecting an entry and pressing OK jumps there directly.
# ------------------------------------------------------------------------------

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from . import metadata
from .config import config_manager
from .logger import logger
from .metadata import metadata_reader
from .service_controller import ServiceController


class PlaybackController:
    """
    Playback coordinator.

    Browser communicates only with this class.
    """

    STATE_STOPPED = "Stopped"
    STATE_PLAYING = "Playing"
    STATE_PAUSED = "Paused"

    # Build 0008 -- tick()'s elapsed sanity check. Deliberately
    # generous: the goal is to catch only readings that are provably
    # implausible relative to the wall-clock/seek/pause-adjusted
    # estimate (see tick()'s own docstring), not to be a tight
    # tolerance.
    #
    # Device test round 9: a fixed 5s tolerance was too tight for
    # tracks that had been playing for several minutes -- a device log
    # showed a track's own final, genuinely correct GStreamer reading
    # (224, matching duration exactly) rejected because the wall-clock
    # estimate had drifted to 218.4 by then, a normal ~2.5% divergence
    # after 220s of continuous playback, not a stale/wrong value. The
    # tolerance now scales with how long the track has been running
    # (POSITION_DRIFT_TOLERANCE_RATIO), on top of the fixed base --
    # comfortably covers gradual real-world clock drift over a long
    # track while staying far below the smallest confirmed bad-value
    # gap seen in any device log (10s, and usually much larger), since
    # that kind of gap shows up immediately when a track starts, before
    # significant playback time -- and therefore drift allowance --
    # has had a chance to accumulate.
    POSITION_SANITY_TOLERANCE_SECONDS = 5
    POSITION_DRIFT_TOLERANCE_RATIO = 0.03

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self):

        self._log("Created")

        self._service = ServiceController()

        self._state = self.STATE_STOPPED

        # Only current_file and state are actively used in Build 0003.
        # current_service, position, duration and error_state are
        # reserved for future builds (see PLAYBACK_CONTROLLER_SPEC.md
        # section 5, Internal State).
        self._current_file = None
        self._current_service = None
        self._position = None
        self._duration = None
        self._error_state = None

        # Build 0010, device test round 10 -- user request: lyrics
        # sync should follow this wall-clock estimate exclusively,
        # never GStreamer's own raw reading directly, even when that
        # reading is within tick()'s own "plausible" tolerance and
        # therefore still accepted for self._position (used for the
        # elapsed/remaining time display and progress bar, which the
        # user did NOT ask to change). GStreamer's reported position
        # can visibly jump by a second or two while still remaining
        # inside that tolerance band -- fine for a once-a-second time
        # label, but enough to make time-synced lyrics visibly skip a
        # line and then skip back. Updated on every tick() call
        # (unlike self._position, always the wall-clock estimate,
        # never the possibly-jumpy GStreamer value) -- see
        # getEstimatedElapsedTime().
        self._estimated_position = None

        # Build 0008 -- wall-clock time a track was told to start,
        # used by tick() to reject an early, physically-impossible
        # elapsed reading (see tick()'s own docstring for why this is
        # needed).
        self._track_start_wall_time = None

        # Build 0008, device test round 4 -- net seek adjustment
        # applied since the track started, used together with
        # _track_start_wall_time to log an independently-computed
        # "estimated position" alongside GStreamer's own reported
        # elapsed value (tick()'s docstring explains why), so a
        # device log can show exactly how much timing error remains
        # by comparing the two directly.
        self._seek_offset_seconds = 0

        # Build 0008, device test round 5 -- total time spent paused
        # during the current track, and the wall-clock moment the
        # current pause began (None while playing). Real wall-clock
        # time keeps advancing during a pause even though the track's
        # own position does not, so the estimated-position calculation
        # above must exclude paused time or it drifts further wrong
        # for every second the user leaves playback paused -- caught
        # by the user asking directly whether pause was accounted for.
        self._paused_seconds_total = 0
        self._pause_wall_time = None

        # Playback Queue (Build 0005 -- PLAYBACK_QUEUE_SPEC.md).
        # BrowserScreen builds this once and hands it to playQueue();
        # PlaybackController owns all navigation within it afterwards.
        self._queue = []
        self._queue_index = -1

        # Metadata cache for the current file (Build 0006 -- populated
        # by play(), read via getMetadata()/getEmbeddedArtwork()).
        self._metadata = None

        # True if the current/last media is an Internet Radio stream
        # rather than a local file (Build 0007). Set by play()/
        # playStream(); read via isPlayingStream().
        self._is_stream = False

        self._initialized = False

        self._initialize()

    # ------------------------------------------------------------------

    def _initialize(self):

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _log(self, message: str):

        logger.info("[Playback] %s", message)

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def play(self, filename: str) -> bool:
        """
        Play a media file.

        Service reference creation is ServiceController's responsibility
        (via compatibility.py) -- PlaybackController only forwards the
        filename, per ARCHITECTURE.md section 8 (Event Flow).
        """

        self._log(f"Play requested: {filename}")

        if not self._service.play(filename):

            self._error_state = "Playback failed"

            self._log("Playback start failed.")

            return False

        self._current_file = filename
        self._current_service = self._service.getCurrentService()
        self._error_state = None
        self._is_stream = False

        self._track_start_wall_time = time.time()
        self._seek_offset_seconds = 0
        self._paused_seconds_total = 0
        self._pause_wall_time = None

        # Clear the previous track's cached position/duration
        # immediately -- confirmed on a real device: without this,
        # switching tracks briefly displayed the OLD track's elapsed/
        # duration/progress (e.g. "01:35 / 02:49") until the next
        # tick() call overwrote them with the new track's real values
        # a moment later. tick() only runs once the service has
        # actually reached PLAYING, so there is a real window where
        # stale data would otherwise be shown.
        self._position = None
        self._duration = None
        self._estimated_position = None

        # Metadata extraction never blocks or fails playback startup
        # (BUILD_0006_PLAN.md "Metadata processing shall never block
        # playback startup unnecessarily.") -- metadata_reader.read()
        # already can't raise, but this is one more safety net.
        try:
            self._metadata = metadata_reader.read(filename)

        except Exception as error:

            self._log(f"Metadata extraction failed: {error}")

            self._metadata = None

        self._setState(self.STATE_PLAYING)

        self._log("Started")

        return True

    # ------------------------------------------------------------------

    def playStream(self, url: str, station: Optional[Dict[str, Any]] = None) -> bool:
        """
        Play an Internet Radio stream URL (Build 0007 --
        INTERNETRADIO_MANAGER_SPEC.md "PlaybackController receives
        only the final validated stream URL.").

        `station` (a RadioBrowser station dict, already resolved by
        InternetRadioManager.prepareStream()) is used only to build a
        synthetic metadata dict (station name as Title) -- it is
        never passed further than this method. Unlike play(), this
        never calls metadata_reader.read() on the URL: local tag
        parsing on a network stream would only waste time and always
        return "Unknown" fields anyway (metadata.py has no reader for
        a URL's "extension").

        Uses the same eServiceReference construction as local files
        (compatibility.createServiceReference()) -- Enigma2's
        GStreamer/MP3 service factory already resolves http(s):// URIs
        transparently, the same as it resolves local paths, so no
        separate playback path is needed at the ServiceController
        layer.

        Build 0009, device test round 11: cfg.radio.use_exteplayer3
        (off by default) switches this to ExtEplayer3 instead --
        requested after a real device log showed specific streams
        (Bauer Media's Radio Nova/SuomiRock) repeatedly failing with
        GStreamer-internal reconnect errors ("Not Found (3) from
        source"), independently confirmed as a known class of issue
        with a known workaround (multiple Enigma2 forum threads, a
        GitHub issue showing the identical error resolved by the same
        service-type switch for a different stream). See
        compatibility.createServiceReference()'s own docstring for
        the full reasoning and caveats (requires ExtEplayer3/FFmpeg to
        actually be installed).
        """

        self._log(f"Stream play requested: {url}")

        use_exteplayer3 = bool(config_manager.get("radio.use_exteplayer3", False))

        if not self._service.play(url, use_exteplayer3=use_exteplayer3):

            self._error_state = "Playback failed"

            self._log("Stream playback start failed.")

            return False

        self._current_file = url
        self._current_service = self._service.getCurrentService()
        self._error_state = None
        self._is_stream = True

        self._track_start_wall_time = time.time()
        self._seek_offset_seconds = 0
        self._paused_seconds_total = 0
        self._pause_wall_time = None

        self._position = None
        self._duration = None
        self._estimated_position = None

        station_name = (station or {}).get("name", "Internet Radio")

        self._metadata = self._buildStreamMetadata(station_name, station)

        self._setState(self.STATE_PLAYING)

        self._log("Started")

        return True

    # ------------------------------------------------------------------

    def _buildStreamMetadata(self, station_name: str, station: Optional[Dict[str, Any]]) -> Dict[str, Any]:

        result = {field: "Unknown" for field in metadata.FIELDS}

        result["title"] = station_name
        result["source"] = "Internet Radio"
        result["bit_depth"] = "Unknown"
        result["duration_seconds"] = None
        result["file_size"] = None
        result["has_embedded_artwork"] = False

        if station:

            result["genre"] = station.get("tags", "Unknown") or "Unknown"

            result["comment"] = station.get("homepage", "Unknown") or "Unknown"

        return result

    # ------------------------------------------------------------------

    def isPlayingStream(self) -> bool:
        """
        Return True if the currently playing (or last played) media
        is an Internet Radio stream rather than a local file (Build
        0007).
        """

        return self._is_stream

# End of Part 1
    # ------------------------------------------------------------------

    def stop(self) -> bool:
        """
        Stop playback.
        """

        self._log("Stop requested.")

        if not self._service.stop():
            return False

        self._setState(self.STATE_STOPPED)

        self._position = None
        self._duration = None
        self._estimated_position = None

        self._log("Stopped")

        return True

    # ------------------------------------------------------------------

    def pause(self) -> bool:
        """
        Pause playback.
        """

        self._log("Pause requested.")

        if self._state != self.STATE_PLAYING:

            self._log("Pause ignored: not currently playing.")

            return False

        if not self._service.pause():
            return False

        self._setState(self.STATE_PAUSED)

        self._pause_wall_time = time.time()

        self._log("Paused")

        return True

    # ------------------------------------------------------------------

    def resume(self) -> bool:
        """
        Resume playback.
        """

        self._log("Resume requested.")

        if self._state != self.STATE_PAUSED:

            self._log("Resume ignored: not currently paused.")

            return False

        if not self._service.resume():
            return False

        self._setState(self.STATE_PLAYING)

        if self._pause_wall_time is not None:

            self._paused_seconds_total += time.time() - self._pause_wall_time

            self._pause_wall_time = None

        self._log("Resumed")

        return True

    # ------------------------------------------------------------------

    def togglePause(self) -> bool:
        """
        Toggle between pause and play.
        """

        if self._state == self.STATE_PLAYING:

            return self.pause()

        if self._state == self.STATE_PAUSED:

            return self.resume()

        return False

    # ------------------------------------------------------------------
    # Playback Queue (Build 0005 -- PLAYBACK_QUEUE_SPEC.md)
    # ------------------------------------------------------------------
    #
    # BrowserScreen scans the current directory, builds an ordered list
    # of supported media files, and hands it to playQueue() exactly
    # once when the user starts playback. From that point on,
    # PlaybackController owns the queue and all navigation within it;
    # BrowserScreen may be closed and playback continues independently
    # (PLAYBACK_QUEUE_SPEC.md "Queue Ownership").

    def setQueue(self, queue, start_index: int = 0) -> None:
        """
        Replace the current Playback Queue without starting playback.

        Mainly useful for tests/diagnostics; playQueue() is the normal
        entry point used by BrowserScreen.
        """

        self._queue = list(queue)

        self._queue_index = start_index if self._queue else -1

        self._log(f"Queue created: {len(self._queue)} item(s)")

        logger.verbose(
            "[Playback] Queue created\n\nItems: %s\n\nCurrent: %s\n\nNext: %s\n\nPrevious: %s\n",
            len(self._queue),
            self.getQueuePosition(),
            self._displayIndex(self._queue_index + 1),
            self._displayIndex(self._queue_index - 1),
        )

    # ------------------------------------------------------------------

    def playQueue(self, queue, start_index: int = 0) -> bool:
        """
        Replace the Playback Queue and start playback at `start_index`.

        Returns:
            True if playback of the starting track was requested
            successfully.
        """

        if not queue:

            self._log("playQueue() called with an empty queue.")

            return False

        if not (0 <= start_index < len(queue)):

            self._log(f"playQueue() start_index out of range: {start_index}")

            start_index = 0

        self.setQueue(queue, start_index)

        return self._playIndex(self._queue_index)

    # ------------------------------------------------------------------

    def _playIndex(self, index: int) -> bool:
        """
        Play the queue item at `index` and update the queue position.

        The queue position is only committed once play() actually
        succeeds -- a failed play() (e.g. file removed, service
        unavailable) must never leave getQueuePosition() pointing
        somewhere getCurrentTrack() doesn't agree with.
        """

        if not (0 <= index < len(self._queue)):
            return False

        filename = self._queue[index]

        logger.verbose(
            "[Playback] Track changed\n\nQueue position: %s\n\nFile: %s\n",
            index + 1,
            filename,
        )

        if not self.play(filename):
            return False

        self._queue_index = index

        return True

    # ------------------------------------------------------------------

    def jumpToQueueIndex(self, index: int) -> bool:
        """
        Build 0009, MAINSCREEN_SPEC.md "Playlist Panel" -- jumps
        directly to `index` within the CURRENT PlaybackQueue, without
        replacing the queue itself (unlike playQueue()). Used when the
        user selects a specific entry in MainScreen's Playlist Panel
        and presses OK: "The selected entry immediately becomes the
        new PlaybackQueue position. Playback continues normally
        through the remaining playlist."

        Returns:
            True if `index` was valid and playback was requested.
        """

        self._log(f"Jump to queue index requested: {index}")

        return self._playIndex(index)

    # ------------------------------------------------------------------

    def nextTrack(self) -> bool:
        """
        Advance to and play the next track in the Playback Queue.

        Returns:
            True if a next track existed and playback was requested.
        """

        self._log("Next track requested.")

        if not self.hasNext():

            self._log("Next track ignored: already at end of queue.")

            return False

        return self._playIndex(self._queue_index + 1)

    # ------------------------------------------------------------------

    def previousTrack(self) -> bool:
        """
        Return to and play the previous track in the Playback Queue.

        If already at the first track, this reports the beginning of
        the queue rather than restarting or wrapping
        (PLAYBACK_QUEUE_SPEC.md "Playback Navigation").

        Returns:
            True if a previous track existed and playback was
            requested.
        """

        self._log("Previous track requested.")

        if not self.hasPrevious():

            self._log("Already at beginning of queue.")

            return False

        return self._playIndex(self._queue_index - 1)

    # ------------------------------------------------------------------

    def hasNext(self) -> bool:
        """
        Return True if a next track exists in the Playback Queue.
        """

        return 0 <= self._queue_index < len(self._queue) - 1

    # ------------------------------------------------------------------

    def hasPrevious(self) -> bool:
        """
        Return True if a previous track exists in the Playback Queue.
        """

        return self._queue_index > 0

    # ------------------------------------------------------------------

    def getCurrentTrack(self):
        """
        Return the filename of the current queue item.

        Alias for getCurrentFile(), matching the public interface name
        used in PLAYBACK_CONTROLLER_SPEC.md section 6.
        """

        return self.getCurrentFile()

    # ------------------------------------------------------------------

    def getQueueSize(self) -> int:
        """
        Return the number of items in the current Playback Queue.
        """

        return len(self._queue)

    # ------------------------------------------------------------------

    def getQueuePosition(self) -> int:
        """
        Return the current 1-based queue position, or 0 when the
        queue is empty (matching PLAYBACK_QUEUE_SPEC.md's example,
        which numbers the queue starting at 1).
        """

        if not self._queue or self._queue_index < 0:
            return 0

        return self._queue_index + 1

    # ------------------------------------------------------------------

    def _displayIndex(self, index: int) -> str:
        """
        Return the filename at `index`, or "None" when out of range --
        used only for verbose queue-creation logging.
        """

        if 0 <= index < len(self._queue):
            return self._queue[index]

        return "None"

# End of Part 2
    # ------------------------------------------------------------------
    # State Queries
    # ------------------------------------------------------------------

    def isPlaying(self) -> bool:
        """
        Return True if playback is currently active.
        """

        return self._state == self.STATE_PLAYING

    # ------------------------------------------------------------------

    def isPaused(self) -> bool:
        """
        Return True if playback is currently paused.
        """

        return self._state == self.STATE_PAUSED

    # ------------------------------------------------------------------

    def isStopped(self) -> bool:
        """
        Return True if playback is currently stopped.
        """

        return self._state == self.STATE_STOPPED

    # ------------------------------------------------------------------

    def getCurrentService(self):
        """
        Return the current service object, as reported by
        ServiceController.
        """

        return self._current_service

    # ------------------------------------------------------------------

    def getCurrentFile(self):
        """
        Return the filename currently loaded for playback.
        """

        return self._current_file

    # ------------------------------------------------------------------

    def getAdjacentFiles(self):
        """
        Return (previous_filename, next_filename) for the current
        queue position, either being None when there is no such
        neighbour (queue empty, or at either end). Build 0008 --
        MainScreen's Previous/Next queue preview panel
        (BUILD_0008_PLAN.md "Previous / Next Preview").
        """

        if not self._queue or self._queue_index < 0:
            return None, None

        previous_filename = (
            self._queue[self._queue_index - 1] if self._queue_index - 1 >= 0 else None
        )

        next_filename = (
            self._queue[self._queue_index + 1] if self._queue_index + 1 < len(self._queue) else None
        )

        return previous_filename, next_filename

    # ------------------------------------------------------------------

    def getState(self) -> str:
        """
        Return the current playback state.
        """

        return self._state

    # ------------------------------------------------------------------

    def hasMedia(self) -> bool:
        """
        Return True if a media file is currently selected/loaded.

        Used by MainScreen to decide between its "no media selected"
        startup state and its normal playback display
        (MAINSCREEN_SPEC.md section 5).
        """

        return self._current_file is not None

    # ------------------------------------------------------------------

    def getElapsedTime(self):
        """
        Return elapsed playback time in seconds, or None when unknown.

        Value is refreshed by tick() -- see PLAYBACK_CONTROLLER_SPEC.md
        section 4 (Playback Progress). Callers that need a fresh value
        (e.g. MainScreen's periodic refresh) should call tick() first.
        """

        return self._position

    # ------------------------------------------------------------------

    def getEstimatedElapsedTime(self):
        """
        Build 0010, device test round 10 -- the wall-clock-based
        position estimate tick() computes on every call, independent
        of whichever value getElapsedTime() ends up returning. Intended
        specifically for time-synced lyrics (InformationPanel), which
        need a smoothly, monotonically advancing clock -- unlike
        getElapsedTime(), this never reflects GStreamer's own raw
        reading directly, so a small in-tolerance jump in that reading
        (see tick()'s own docstring) can't make synced lyrics visibly
        skip a line and skip back, even though the same jump is still
        fine for the once-a-second elapsed/remaining time display.

        Falls back to getElapsedTime()'s own value when no estimate is
        available yet (e.g. the very first tick after a track starts,
        before _track_start_wall_time-based estimation has run) --
        never worse than the pre-existing behaviour in that case.
        """

        if self._estimated_position is not None:
            return self._estimated_position

        return self._position

    # ------------------------------------------------------------------

    def getDuration(self):
        """
        Return total media duration in seconds, or None when unknown.

        Value is refreshed by tick() -- see PLAYBACK_CONTROLLER_SPEC.md
        section 4 (Playback Progress).
        """

        return self._duration

    # ------------------------------------------------------------------

    def getProgress(self):
        """
        Return playback progress as a 0.0-1.0 float, or None when
        position/duration are not (yet) available.
        """

        if self._position is None or not self._duration:
            return None

        try:
            return max(0.0, min(1.0, self._position / self._duration))

        except (TypeError, ZeroDivisionError):
            return None

    # ------------------------------------------------------------------

    def getStreamInfo(self):
        """
        Return best-effort stream information (codec, sample rate,
        bitrate, channels) for DeveloperScreen's Playback Statistics
        page. Delegates to ServiceController -- never queries
        compatibility.py directly.
        """

        return self._service.getStreamInfo()

    # ------------------------------------------------------------------

    def getMetadata(self):
        """
        Return the current file's cached tag metadata dict (Build
        0006 -- METADATA_SPEC.md), or None if nothing has been played
        yet or extraction failed entirely.

        The dict always has every key in metadata.FIELDS (each
        defaulting to "Unknown") plus "source", "bit_depth",
        "duration_seconds", "file_size" and "has_embedded_artwork" --
        see metadata.MetadataReader.read().
        """

        return self._metadata

    # ------------------------------------------------------------------

    def getEmbeddedArtwork(self):
        """
        Return (mime_type, image_bytes) for the current file's
        embedded artwork, or None if it has none (or nothing has been
        played yet).
        """

        if self._metadata is None:
            return None

        return metadata_reader.getEmbeddedArtwork(self._metadata)

    # ------------------------------------------------------------------

    def seekForward(self, seconds: int = 10) -> bool:
        """
        Seek forward within the current track by `seconds`.

        Build 0008, device test round 7: a device log proved seeking
        relative to GStreamer's own reported position
        (compatibility.seekRelative()) is unsafe when that position
        can itself be stale (rounds 1-6): GStreamer had gotten stuck
        reporting a position near the end of a 231s track while the
        track was genuinely only ~84s in. A "+30s" relative seek
        request landed at (stale)231 + 30 = 261 -- past the end of the
        track -- because it was computed from GStreamer's own wrong
        belief, not the true position. Seeking now targets an absolute
        position computed from THIS class's own trusted `_position`
        (compatibility.seekTo()) instead, which sidesteps the whole
        category of bug: it never depends on GStreamer's own current-
        position belief being correct in the first place. The
        wall-clock estimate is also re-baselined to treat the seek
        target as the new known-good reference point, rather than
        accumulating an offset on top of assumptions about where the
        track started.

        Build 0008, device test round 6: a live Internet Radio stream
        has no seekable timeline, so seeking is rejected outright
        while streaming -- unlike MainScreen's LEFT/RIGHT (context-
        sensitive: switches radio lists instead of seeking while
        streaming), the dedicated seek keys had no such check before.
        """

        if self._state not in (self.STATE_PLAYING, self.STATE_PAUSED):
            return False

        if self._is_stream:

            logger.verbose("[Playback] Seek forward ignored: not seekable while streaming.")

            return False

        current_position = self._position if self._position is not None else 0

        target = max(0, current_position + seconds)

        logger.verbose(
            "[Playback] Seek forward: %ss (current: %ss, target: %ss)",
            seconds,
            current_position,
            target,
        )

        succeeded = self._service.seekTo(target)

        if succeeded:
            self._rebaselineAfterSeek(target)

        return succeeded

    # ------------------------------------------------------------------

    def seekBackward(self, seconds: int = 10) -> bool:
        """
        Seek backward within the current track by `seconds`. See
        seekForward()'s docstring for why an absolute target is used
        and streams are rejected.
        """

        if self._state not in (self.STATE_PLAYING, self.STATE_PAUSED):
            return False

        if self._is_stream:

            logger.verbose("[Playback] Seek backward ignored: not seekable while streaming.")

            return False

        current_position = self._position if self._position is not None else 0

        target = max(0, current_position - seconds)

        logger.verbose(
            "[Playback] Seek backward: %ss (current: %ss, target: %ss)",
            seconds,
            current_position,
            target,
        )

        succeeded = self._service.seekTo(target)

        if succeeded:
            self._rebaselineAfterSeek(target)

        return succeeded

    # ------------------------------------------------------------------

    def _rebaselineAfterSeek(self, target_position) -> None:
        """
        After a successful seek to `target_position`, treat it as the
        new known-good reference point for the wall-clock estimate
        tick() uses (see seekForward()'s docstring for why this
        matters) -- rather than accumulating an offset on top of
        assumptions about where the track originally started, which
        would compound across repeated seeks.
        """

        self._track_start_wall_time = time.time() - target_position
        self._seek_offset_seconds = 0
        self._paused_seconds_total = 0
        self._position = target_position

    # ------------------------------------------------------------------
    # Progress Refresh / Automatic Next Track (Build 0005)
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """
        Refresh elapsed/duration and drive Automatic Next Track.

        Intended to be called about once per second by MainScreen's
        refresh timer (MAINSCREEN_SPEC.md "Screen Refresh"). A no-op
        whenever playback is not active, so calling it unconditionally
        every second is safe and cheap.

        Build 0008, device test rounds 1-4: device logs across four
        rounds (two images) showed GStreamer's own reported elapsed
        value is sometimes wildly wrong from the moment a track starts
        -- not a fixed offset, a different, essentially random value
        each time (confirmed real values: 0, 10, 12, 14, 15, 17, 18,
        41, 42, 49, 52 seconds, all within about a second of the track
        actually starting). compatibility.py's existing error_code
        check can't catch this -- GStreamer reports success (error_code
        0) together with a leftover PTS value from whatever played
        previously, before its own pipeline has reset position
        tracking, a known category of race condition on GStreamer-
        based Enigma2 audio playback.

        Round 3 rejected such a reading, but only within a short
        settling window after playback starts, on the assumption
        GStreamer would have corrected itself by then. Round 4's log
        disproved that assumption: one track's wrong baseline (~52s)
        was still present, completely unchanged, right as the 5-second
        window closed, and was then accepted as correct and carried
        for the rest of the track -- reproducing the exact "ends
        early" symptom this was meant to fix, just delayed by 5
        seconds instead of prevented. There is no way to distinguish a
        stable-but-wrong reading from a stable-and-correct one using
        the position stream alone, since both simply increment by
        roughly one second per second once "settled" -- only comparing
        against an independent reference (wall-clock time) can tell
        them apart, so round 5 checks that on every tick, indefinitely,
        instead of only within a start-up window.

        The invariant checked is: elapsed can never exceed real
        wall-clock time since the track started, minus any time spent
        paused, plus any net seek offset applied since then (plus a
        generous tolerance for buffering/imprecision). This holds at
        any point in a track, including after a seek or a pause/resume
        cycle, because _seek_offset_seconds and _paused_seconds_total
        are both updated the moment the user acts, before GStreamer's
        own position necessarily catches up -- unlike the round 3
        check, this one does not need to assume seeking only happens
        after some fixed point in the track. (Pause handling itself
        was round 5's other fix: real wall-clock time keeps advancing
        while paused even though the track's own position does not,
        so a track paused for any length of time would otherwise make
        every subsequent reading look implausible and be wrongly
        discarded -- caught by the user asking directly whether pause
        was accounted for.)
        """

        if self._state != self.STATE_PLAYING:
            return

        elapsed, duration = self._service.getPlaybackPosition()

        estimated_position = None

        if self._track_start_wall_time is not None:

            estimated_position = (
                (time.time() - self._track_start_wall_time)
                - self._paused_seconds_total
                + self._seek_offset_seconds
            )

            # Build 0008, device test round 4 -- requested diagnostic:
            # logged BEFORE the discard check below, so a device log
            # shows this comparison even for a reading that gets
            # rejected as implausible, which is the most useful case
            # to see it for. Neither value drives playback or the UI
            # on its own.
            logger.verbose(
                "[Playback] Estimated position: %ds (wall-clock - paused + seek offset) | "
                "GStreamer-reported: %s",
                int(estimated_position),
                elapsed if elapsed is not None else "Unknown",
            )

            # Build 0010, device test round 10 -- see this attribute's
            # own __init__ comment. Stored every tick, independent of
            # whichever value self._position ends up with below.
            self._estimated_position = max(0.0, estimated_position)

        tolerance = self.POSITION_SANITY_TOLERANCE_SECONDS

        if estimated_position is not None and estimated_position > 0:

            tolerance += estimated_position * self.POSITION_DRIFT_TOLERANCE_RATIO

        elapsed_is_implausible = (
            elapsed is not None
            and estimated_position is not None
            and elapsed > estimated_position + tolerance
        )

        if elapsed_is_implausible:

            # Build 0008, device test round 6: a device log showed
            # GStreamer's own reported elapsed getting stuck at one
            # wrong value (291s, on a 231s-duration track) for over
            # twenty consecutive ticks -- round 5's fix correctly kept
            # rejecting it the whole time, but the practical effect was
            # the displayed time going blank for that entire stretch,
            # which is a worse outcome for the user than a reading that
            # might be a little off. Falls back to the wall-clock
            # estimate for DISPLAY here -- it's already proven accurate
            # enough to judge GStreamer's own value implausible against
            # in the first place, so it's a reasonable stand-in -- but
            # this branch always returns before the end-of-track check
            # below, so a rejected GStreamer reading can never itself
            # trigger Automatic Next Track; only a GStreamer value this
            # method has actually trusted can do that.
            logger.verbose(
                "[Playback] Discarding implausible elapsed reading: "
                "%ss reported, estimated position is only %.1fs "
                "(tolerance: %.1fs). Falling back to the estimate for display.",
                elapsed,
                estimated_position,
                tolerance,
            )

            self._position = max(0, int(estimated_position))
            self._duration = duration

            return

        self._position = elapsed
        self._duration = duration

        logger.verbose(
            "[Playback] Position\n\nElapsed: %s\n\nDuration: %s\n",
            elapsed if elapsed is not None else "Unknown",
            duration if duration is not None else "Unknown",
        )

        if estimated_position is not None and duration and estimated_position >= duration - 0.5:

            # Device test round 71 -- real bug found from a device
            # log and a user-submitted fix: GStreamer's own reported
            # elapsed got stuck at a single value (here, exactly
            # matching duration) for many consecutive ticks while
            # estimated_position kept advancing correctly and
            # smoothly (256, 257, 258, 259...) -- the tolerance check
            # above kept correctly rejecting the stuck value as
            # implausible for a while, but that tolerance itself grows
            # with estimated_position (POSITION_DRIFT_TOLERANCE_RATIO),
            # so it eventually widened enough to accept the still-
            # stale, stuck reading. The moment that happened, it
            # exactly equalled duration, triggering the old elapsed>=
            # duration check below roughly 13 seconds before the track
            # had actually finished playing. Deciding "finished" from
            # estimated_position instead avoids this specific failure
            # mode entirely, since it's the value proven accurate
            # throughout the whole episode in the log that surfaced
            # this. The "duration -" guard (not in the originally
            # submitted patch) is needed because live radio streams
            # typically report no fixed duration (None) -- without it,
            # this check would raise a TypeError for every radio tick.

            self._handleTrackFinished()

        elif estimated_position is None and elapsed is not None and duration and elapsed >= duration:

            # Fallback for the brief window before estimated_position
            # is available at all (self._track_start_wall_time not
            # yet set). The "estimated_position is None" check here is
            # essential, not incidental: without it, this branch would
            # still fire whenever the primary check above was false
            # for ANY reason -- including the exact bug scenario this
            # round fixes (estimated_position available but below the
            # finished threshold) -- silently reintroducing the same
            # premature-finish bug through this fallback path. Caught
            # by testing the exact logged scenario directly before
            # trusting this fix, not assumed correct from the
            # structure alone.
            self._handleTrackFinished()

    # ------------------------------------------------------------------

    def _handleTrackFinished(self) -> None:
        """
        Handle end-of-track: Automatic Next Track when enabled, stop
        otherwise (PLAYBACK_QUEUE_SPEC.md "Automatic Next Track").
        """

        self._log("Track finished.")

        auto_next = bool(config_manager.get("playback.auto_play_next", False))

        logger.verbose(f"[Playback] Auto Next enabled: {auto_next}")

        if auto_next and self.hasNext():

            self._log("Auto Next: playing next track.")

            self.nextTrack()

            return

        # Round 98, per direct request: replaces the never-implemented
        # "Resume playback (future)" setting -- when Auto Next is on
        # but there's no next track (the playlist just finished), loop
        # back to the first track instead of stopping, if enabled.
        if auto_next and bool(config_manager.get("playback.loop_playlist", False)) and len(self._queue) > 0:

            self._log("Auto Next: looping back to the start of the playlist.")

            self._playIndex(0)

            return

        logger.verbose(
            "[Playback] End-of-file reason: "
            + ("Auto Next disabled" if not auto_next else "no next track in queue")
        )

        self._log("Auto Next: stopping (no next track or disabled).")

        self.stop()

# End of Part 3
    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _setState(self, state: str) -> None:
        """
        Update the internal playback state.
        """

        if state == self._state:
            return

        self._log(f"State: {self._state} -> {state}")

        self._state = state

    # ------------------------------------------------------------------

    def _reset(self) -> None:
        """
        Reset internal playback information.

        Does not stop an active service -- callers should call stop()
        first when a full reset is required.
        """

        self._current_file = None
        self._current_service = None
        self._position = None
        self._duration = None
        self._estimated_position = None
        self._error_state = None

        self._queue = []
        self._queue_index = -1

        self._metadata = None

        self._is_stream = False

    # ------------------------------------------------------------------

    def stopPreviousServiceNow(self) -> bool:
        """
        Stop whatever service is currently active (typically live TV)
        immediately, rather than waiting until the first track is
        played. Intended to be called once by MainScreen right at
        startup (Build 0006, device test round 3).

        Delegates to ServiceController -- never touches
        compatibility.py directly.
        """

        return self._service.stopPreviousServiceNow()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """
        Release PlaybackController and ServiceController resources.

        Called by Browser.closePlayer() during shutdown.
        """

        self._log("Closing")

        try:
            self.stop()

        except Exception as error:

            self._log(f"Error while stopping during cleanup: {error}")

        self._service._cleanup()

        self._reset()

        self._initialized = False

        self._log("Closed")


# ==============================================================================
# End of file
# ==============================================================================

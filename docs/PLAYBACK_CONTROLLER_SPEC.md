# PlaybackController Specification

Version: 0.5

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

PlaybackController is responsible for all playback operations within
MediaPlayer3.

Beginning with Build 0005, PlaybackController also owns Playback Queue
management.

PlaybackController operates independently of BrowserScreen after
playback has started.

---

# Responsibilities

PlaybackController shall:

- Start playback.
- Stop playback.
- Pause playback.
- Resume playback.
- Maintain playback state.
- Maintain Playback Queue.
- Maintain current queue position.
- Provide playback progress.
- Report playback statistics.
- Coordinate Automatic Next Track.

PlaybackController shall never implement user interface logic.

---

# Playback Queue

Playback Queue is received from BrowserScreen when playback begins.

PlaybackController stores:

- Queue
- Queue size
- Current index
- Current track
- Previous track
- Next track

BrowserScreen does not modify the queue after creation.

---

# Playback Progress

PlaybackController provides:

Current elapsed time

Current duration

Playback percentage

Current playback state

These values are updated continuously while playback is active.

---

# Public Interface

Typical public methods include:

play()

stop()

pause()

resume()

nextTrack()

previousTrack()

hasNext()

hasPrevious()

getCurrentTrack()

getQueueSize()

getQueuePosition()

getElapsedTime()

getDuration()

getProgress()

---

# Automatic Next Track

PlaybackController is responsible for Automatic Next Track.

When playback reaches the end of a track:

Track Finished

↓

Automatic Next enabled?

↓

Yes

↓

Load next queue item

↓

Start playback

If no next track exists, playback stops normally.

---

# Logging

PlaybackController follows LOGGER_SPEC.md.

Normal logging includes:

- Playback started
- Playback stopped
- Playback paused
- Playback resumed
- Track changed

Verbose logging additionally records:

- File path
- File name
- Queue size
- Queue position
- Codec
- Duration
- Playback percentage
- Current elapsed time
- Previous track
- Next track
- Automatic Next decision
- End-of-file reason

---

# Playback States

PlaybackController supports the following states:

Created

↓

Initializing

↓

Ready

↓

Playing

↓

Paused

↓

Stopped

↓

Closing

↓

Closed

All state transitions should be logged.

---

# Design Principles

PlaybackController owns playback.

BrowserScreen owns browsing.

MainScreen owns presentation.

PlaybackController shall never depend on BrowserScreen after playback
has started.

PlaybackController shall expose playback information through stable
public interfaces.

---

# Acceptance Criteria

PlaybackController implementation is complete when:

- Playback starts correctly.
- Playback stops correctly.
- Pause and Resume function correctly.
- Playback Queue is maintained correctly.
- Previous and Next navigation function correctly.
- Automatic Next operates correctly.
- Playback progress is continuously available.
- Playback statistics are available to other modules.
- Logging follows LOGGER_SPEC.md.

---

# Related Documentation

PLAYBACK_QUEUE_SPEC.md

MAINSCREEN_SPEC.md

LOGGER_SPEC.md

BUILD_0005_PLAN.md

ARCHITECTURE.md

---

# End of File

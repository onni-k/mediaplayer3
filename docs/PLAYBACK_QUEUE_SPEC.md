# MediaPlayer3

# Playback Queue Specification

Version: 0.5.0-dev

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

Playback Queue represents the ordered collection of playable media files
available within the currently selected Browser directory.

The queue is created by BrowserScreen when playback starts.

PlaybackController owns the queue during playback.

BrowserScreen never controls playback navigation.

---

# Responsibilities

BrowserScreen

- Scan current directory.
- Filter supported media files.
- Build playback queue.
- Determine selected track.
- Pass queue to PlaybackController.

PlaybackController

- Store playback queue.
- Maintain current queue position.
- Provide Previous Track.
- Provide Next Track.
- Handle Automatic Next Track.
- Report queue status.

MainScreen

- Display playback information.
- Display current queue position if required.

---

# Queue Contents

The queue contains playable media files only.

Directories are never included.

Unsupported files are ignored.

Hidden files are ignored.

The queue preserves BrowserScreen sorting order.

---

# Queue Creation

Queue creation begins when the user starts playback.

Example

Directory

Music/

    Album/

        01 Intro.flac
        02 Song.flac
        03 Finale.flac

Playback starts on

02 Song.flac

Queue

1 Intro.flac

2 Song.flac

3 Finale.flac

Current Position

2

---

# Queue Ownership

After queue creation, PlaybackController becomes the owner of the queue.

BrowserScreen may be closed.

Playback continues independently of BrowserScreen.

---

# Playback Navigation

PlaybackController provides queue navigation.

Supported operations:

- Current Track
- Previous Track
- Next Track
- First Track
- Last Track

If no previous track exists, Previous Track reports beginning of queue.

If no next track exists:

- Stop playback, or
- Continue according to playback settings.

---

# Automatic Next Track

When Automatic Next Track is enabled:

Track Finished

↓

PlaybackController requests Next Track

↓

Next track exists

↓

Start playback

If no next track exists, playback stops normally.

---

# Logging

Normal logging

- Queue created
- Queue destroyed
- Track changed

Verbose logging

- Queue contents
- Queue size
- Current queue position
- Current file
- Previous file
- Next file
- Navigation events
- Automatic Next decisions

Example

Queue created

Items: 12

Current: 4

Next: 5

Previous: 3

---

# Future Extensions

Playback Queue has been designed to support future functionality.

Possible future extensions include:

- Playlist playback
- Shuffle playback
- Repeat Track
- Repeat Queue
- Favorites
- Resume playback
- Smart playlists

These features should extend Playback Queue without requiring
architectural changes.

---

# Design Principles

Playback Queue must remain independent of the user interface.

PlaybackController owns all playback navigation.

BrowserScreen creates the queue only once.

MainScreen displays playback information only.

This separation keeps playback independent from screen navigation.

---

# Acceptance Criteria

Playback Queue implementation is complete when:

- Queue contains supported media files only.
- Queue preserves Browser ordering.
- Previous Track functions correctly.
- Next Track functions correctly.
- Automatic Next functions correctly.
- Queue survives BrowserScreen closing.
- Logging follows LOGGER_SPEC.md.

---

# Related Documentation

ARCHITECTURE.md

BUILD_0005_PLAN.md

PLAYBACK_CONTROLLER_SPEC.md

MAINSCREEN_SPEC.md

LOGGER_SPEC.md

---

# End of File

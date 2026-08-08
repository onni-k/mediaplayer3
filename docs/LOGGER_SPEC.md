# Logger Specification

Version: 0.6

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

Logger provides consistent diagnostic information throughout
MediaPlayer3.

Logging supports both normal application monitoring and detailed
developer diagnostics.

All modules shall use the common Logger interface.

---

# Logging Levels

Supported logging levels:

ERROR

Serious failures requiring attention.

WARNING

Unexpected situations that do not stop execution.

INFO

Normal application events.

VERBOSE

Detailed operational diagnostics intended for development and
troubleshooting.

---

# Module Lifecycle

All major modules follow a common lifecycle.

Created

↓

Initializing

↓

Ready

↓

Closing

↓

Closed

Lifecycle events are logged at INFO level.

---

# Playback Logging

PlaybackController provides dedicated playback logging.

INFO logging includes:

- Playback started
- Playback stopped
- Playback paused
- Playback resumed
- Track changed

VERBOSE logging additionally includes:

- File path
- File name
- Queue position
- Queue size
- Playback duration
- Current playback position
- Playback percentage
- Previous track
- Next track
- Auto Next decision
- End-of-file reason

---

# Browser Logging

INFO logging includes:

- Browser opened
- Directory entered
- Playback requested
- Browser closed

VERBOSE logging additionally includes:

- Current directory
- Directory contents
- Supported media files
- Selected item
- Item type
- Queue creation
---

# MainScreen Logging

INFO logging includes:

- Screen created
- Screen initialized
- Screen ready
- Browser opened
- Main menu opened
- Screen closing
- Screen closed

VERBOSE logging additionally includes:

- UI refresh
- Progress bar update
- Playback state update
- Metadata refresh
- Refresh interval

---

# Developer Logging

Developer Mode enables additional diagnostic information.

Typical Developer logging includes:

- Queue contents
- Playback statistics
- Configuration values
- Compatibility information
- System information
- Internal state transitions

Developer logging should not affect normal application behaviour.

---

# Customization Logging (Build 0006)

BUILD_0006_PLAN.md "Logging" defines additional categories, all
gated behind Developer Mode like the rest of Developer Logging above:

Metadata

- Metadata loaded
- Metadata unavailable
- Metadata source

Implemented as verbose-only ("[Metadata] Metadata loaded" /
"Metadata unavailable" blocks) in metadata.py, matching the
multi-line verbose block format established in Build 0004
(docs/log_example1.txt).

Artwork

- Embedded artwork
- External artwork
- Default artwork

Implemented as verbose-only ("[MainScreen] Artwork source: ...")
in MainScreen's artwork resolution.

Localization

- Selected language
- Translation loaded
- Missing translation
- Fallback language

Implemented at INFO level for language selection/loading (always
visible, not gated behind Developer Mode, since language selection is
a normal user-facing event) and verbose-only for individual missing-
translation lookups, in localization.py.

Skin

- Selected skin
- Selected theme
- Compatibility check
- Default skin fallback

Implemented at INFO level in skin.py, for the same reason as
Localization above -- skin/theme selection and fallback are normal
user-facing events, not purely diagnostic detail.

---

# Log Format

Each log entry should include:

- Timestamp
- Module name
- Log level
- Message

Example

2026-07-16 18:42:15

[Playback]

[INFO]

Playback started

Verbose example

2026-07-16 18:42:15

[Playback]

[VERBOSE]

File:
/media/hdd/music/flac/example.flac

Queue Position:
3 / 12

Elapsed:
00:00

---

# Design Principles

Logging should:

- Be consistent.
- Be readable.
- Be useful.
- Avoid unnecessary repetition.
- Minimise performance impact.

Verbose logging should contain enough information to reproduce playback
problems without requiring additional instrumentation.

---

# Acceptance Criteria

Logging implementation is complete when:

- All modules use the common Logger interface.
- Lifecycle logging is consistent.
- Playback logging follows this specification.
- Browser logging follows this specification.
- Developer Mode controls verbose output.
- Log output remains readable.
- Performance impact is minimal.

---

# Related Documentation

BUILD_0005_PLAN.md

PLAYBACK_CONTROLLER_SPEC.md

PLAYBACK_QUEUE_SPEC.md

MAINSCREEN_SPEC.md

DEVELOPMENT_GUIDE.md

---

# End of File

# MediaPlayer3

# PlaybackInfoScreen Specification

Version: 0.6

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

PlaybackInfoScreen displays detailed information about the currently
selected or currently playing media.

The screen is intended for information display only.

PlaybackInfoScreen never controls playback directly.

Build 0006 expands the displayed information into General/Technical/
File sections, using real tag metadata (metadata.py) and stream info
instead of filename-only placeholders. See BUILD_0006_PLAN.md
"Playback Information":

General -- Artist, Album, Title, Track Number, Genre, Year

Technical -- Codec, Bitrate, Sample Rate, Bit Depth, Channels,
Duration, File Size

File -- Full Path, File Name, Metadata Source

PlaybackInfoScreen remains read-only.

---

# 2. Responsibilities

PlaybackInfoScreen is responsible for:

- Displaying playback information
- Displaying media metadata
- Displaying playback state
- Displaying technical media information
- Presenting information in a readable format

PlaybackInfoScreen is NOT responsible for:

- Playback control
- Directory browsing
- Configuration
- Metadata extraction
- Platform specific functionality
- Enigma2 service control

---

# 3. Lifecycle

Standard lifecycle

Created

↓

Initializing

↓

Request playback information

↓

Request metadata

↓

Initialized

↓

Running

↓

Cleanup

↓

Closed

PlaybackInfoScreen follows the lifecycle defined in LOGGER_SPEC.md.

---

# 4. Displayed Information

PlaybackInfoScreen may display:

Filename

Directory

Artist

Album

Title

Genre

Track number

Playback state

Elapsed time

Remaining time

Total duration

Progress indicator

Codec (future)

Bitrate (future)

Sample rate (future)

File size (future)

Unavailable information shall be displayed as "Unknown" or omitted.

---

# 5. Behaviour

PlaybackInfoScreen is opened from:

Main Menu

or

INFO key

PlaybackInfoScreen never starts playback.

PlaybackInfoScreen automatically refreshes displayed information when
playback state changes.

---

# 6. Remote Control Mapping

PlaybackInfoScreen shall respond to the following remote control keys.

INFO

- Close PlaybackInfoScreen.

MENU

- Return to Main Menu.

EXIT

- Return to MainScreen.

UP / DOWN

Reserved for future scrolling support.

PlaybackInfoScreen does not process playback control keys.

---

# 7. Controller Interaction

PlaybackInfoScreen communicates only through public interfaces.

PlaybackController

Responsibilities:

- Current media
- Playback state
- Elapsed time
- Total duration
- Progress information

Metadata Provider (future)

Responsibilities:

- Artist
- Album
- Title
- Genre
- Track number

PlaybackInfoScreen shall never communicate directly with:

ServiceController

Compatibility

NavigationInstance

Enigma2 playback services

---

# 8. Metadata Priority

Displayed metadata shall follow the following priority.

Title

1. ID3 Title
2. Filename (without directory path)
3. "Unknown"

Artist

1. ID3 Artist
2. "Unknown"

Album

1. ID3 Album
2. "Unknown"

Genre

1. ID3 Genre
2. "Unknown"

Missing metadata shall never prevent playback.

---

# 9. Logging

PlaybackInfoScreen follows LOGGER_SPEC.md.

Typical lifecycle logging:

```
PlaybackInfoScreen created.

PlaybackInfoScreen initializing.

PlaybackInfoScreen initialized.

PlaybackInfoScreen running.

PlaybackInfoScreen closed.
```

Typical user interaction logging:

```
Playback information requested.

Metadata loaded.

Returning to MainScreen.
```

Developer Mode BASIC

- Screen lifecycle
- Metadata request

Developer Mode VERBOSE

Additionally:

- Metadata fields received
- Missing metadata fields
- Refresh operations

---

# 10. Future Extensions

PlaybackInfoScreen is designed for future expansion.

Possible future additions:

- Album artwork
- Embedded lyrics
- Audio codec
- Bitrate
- Sample rate
- Channels
- ReplayGain
- Cover artwork cache
- Audio technical information

These features should not require changes to the public interface of
PlaybackInfoScreen.

---

# 11. Acceptance Criteria

PlaybackInfoScreen is considered complete when:

- It opens from Main Menu or INFO.
- Playback information is displayed correctly.
- Available metadata is displayed.
- Filename is used as Title when ID3 Title is unavailable.
- Missing metadata does not generate errors.
- Logging follows LOGGER_SPEC.md.
- PlaybackInfoScreen contains no playback implementation.
- PlaybackInfoScreen contains no platform-specific code.

---

# End of File

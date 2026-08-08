# MediaPlayer3

# BrowserScreen Specification

Version: 0.7

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

BrowserScreen provides directory browsing and media file selection.

It is a temporary screen that is opened from MainScreen when the user
wants to browse available media.

BrowserScreen is not the primary application window.

After successful media selection BrowserScreen returns control to
MainScreen.

---

# 2. Responsibilities

BrowserScreen is responsible for:

- Directory browsing
- File selection
- Directory navigation
- Filtering supported media files
- Requesting playback
- Returning to MainScreen

BrowserScreen is NOT responsible for:

- Playback implementation
- Playback status
- Metadata extraction
- Configuration management
- Platform specific functionality
- NavigationInstance access

---

# 3. Lifecycle

Standard lifecycle

Created

↓

Initializing

↓

Load directory

↓

Initialize file list

↓

Initialized

↓

Running

↓

Cleanup

↓

Closed

BrowserScreen shall follow the lifecycle defined in
LOGGER_SPEC.md.

---

# 4. User Interface

BrowserScreen displays:

Current directory

Directory list

Media file list

Current selection

Supported file icons (future)

Hidden files (optional)

Directory navigation status

Playback information is not displayed.

---

# 5. Behaviour

BrowserScreen is opened only by explicit user request.

Typical entry points:

MainScreen

↓

OK

or

MainScreen

↓

PVR

BrowserScreen never starts automatically during application startup.

BrowserScreen closes automatically after successful file selection.

---

# 6. Remote Control Mapping

BrowserScreen shall respond to the following remote control keys.

OK

- Open selected directory.
- Select media file.
- Request playback from PlaybackController.
- Close BrowserScreen after successful playback request.

PLAY

- Start playback of the selected media file.

PVR

- Return to MainScreen without changing playback.

MENU

- Open Main Menu.

INFO

- Open the context menu (Build 0007 -- PLAYLIST_MANAGER_SPEC.md
  "Browser Integration"): folders get Play Folder/Add Folder to
  Playlist/Create Playlist, audio files get Play/Add to Playlist/
  Information, playlist files (.m3u/.m3u8) get Play Playlist/Import
  Playlist/Information. Deliberately not bound to OK, which keeps its
  existing descend/play behaviour unchanged.

EXIT

- Return to MainScreen.

---

# 7. Screen Navigation

BrowserScreen may be opened from:

MainScreen

BrowserScreen may open:

Main Menu

PlaybackInfoScreen (future)

BrowserScreen shall never open SettingsScreen directly.

Navigation to SettingsScreen is always performed through Main Menu.

---

# 8. Controller Interaction

BrowserScreen communicates only through public controller interfaces.

PlaybackController

Responsibilities:

- Request playback
- Query supported media types
- Obtain current playback state (optional)

BrowserScreen shall never communicate directly with:

ServiceController

Compatibility

NavigationInstance

Enigma2 playback services

---

# 9. Logging

BrowserScreen follows LOGGER_SPEC.md.

Typical lifecycle logging:

```
BrowserScreen created.

BrowserScreen initializing.

BrowserScreen initialized.

BrowserScreen running.

BrowserScreen cleanup.

BrowserScreen closed.
```

Typical user interaction logging:

```
Directory opened.

Media file selected.

Playback requested.

Returning to MainScreen.
```

Developer Mode BASIC

- Screen lifecycle
- Directory changes
- Playback requests

Developer Mode VERBOSE

Additionally:

- Current directory
- Selected filename
- Supported file type detection
- Directory refresh operations

---

# 10. Future Extensions

BrowserScreen is designed to support future functionality.

Possible future additions:

- Playlist selection
- Search
- Favorites
- Recently played
- Sorting options
- Filtering
- Thumbnail view
- Album artwork preview
- Network locations

These features should be implemented without changing the primary
responsibility of BrowserScreen.

---

# 11. Acceptance Criteria

BrowserScreen is considered complete when:

- It opens only on explicit user request.
- Directory browsing functions correctly.
- Supported media files can be selected.
- Playback requests are forwarded to PlaybackController.
- BrowserScreen closes after successful playback request.
- PVR returns to MainScreen.
- Logging follows LOGGER_SPEC.md.
- BrowserScreen contains no playback implementation.
- BrowserScreen contains no platform-specific code.

---

# End of File

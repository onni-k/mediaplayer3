# MediaPlayer3

# DeveloperScreen Specification

Version: 0.7

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

DeveloperScreen provides diagnostic and development tools for
MediaPlayer3.

It is intended primarily for developers and testers.

DeveloperScreen provides access to runtime information, system
information and debugging tools without affecting normal application
operation.

DeveloperScreen shall never modify playback unless explicitly requested
by the developer.

---

# 2. Responsibilities

DeveloperScreen is responsible for:

- Displaying runtime information
- Displaying controller status
- Displaying platform information
- Displaying logger status
- Displaying build information
- Providing developer utilities

DeveloperScreen is NOT responsible for:

- Playback implementation
- Directory browsing
- Configuration management
- Platform abstraction
- Enigma2 service control

---

# 3. Lifecycle

Standard lifecycle

Created

↓

Initializing

↓

Collect runtime information

↓

Collect system information

↓

Initialize developer pages

↓

Initialized

↓

Running

↓

Cleanup

↓

Closed

DeveloperScreen follows the lifecycle defined in LOGGER_SPEC.md.

---

# 3a. Page Scrolling (Build 0006, device test round 2)

Pages whose content is taller than the details area scroll manually
via UP/DOWN, rather than being cut off with no way to see the rest.

The page title shows a "(first-last / total)" indicator whenever a
page doesn't fully fit.

Scroll position resets to the top when switching pages (LEFT/RIGHT).

---

# 4. Developer Pages

DeveloperScreen contains the following pages.

Runtime Status

Metadata & Artwork (Build 0006)

Localization (Build 0006)

Storage (Build 0007)

Playlists (Build 0007)

Internet Radio (Build 0007)

Logger

System Information

Compatibility

Build Information

Future developer pages may be added without changing the public
interface.

---

# 4c. Storage / Playlists / Internet Radio Pages (Build 0007)

Storage displays StorageManager.getDiagnostics() -- working
directory, fallback-location status, and each subdirectory's
existence/writability.

Playlists displays PlaylistManager.getDiagnostics() -- playlists path,
playlist count and names.

Internet Radio displays InternetRadioManager.getDiagnostics() -- API
base URL, favorite list names/count, history count, radio storage
path.

These pages are intended for diagnostics only.

---

# 4a. Metadata & Artwork Page (Build 0006)

Displays the current file's tag metadata (every field defined in
METADATA_SPEC.md section 5) and embedded artwork status, read from
PlaybackController.getMetadata()/getEmbeddedArtwork().

This page is intended for diagnostics only.

---

# 4b. Localization Page (Build 0006)

Displays LocalizationManager.getTranslationStats(): current language,
fallback language, available languages, total lookups, missing
translation count and keys.

This page is intended for diagnostics only.

---

# 5. Runtime Status

Runtime Status displays the current application state.

Initial information includes:

PlaybackController state

Current media

Playback state

Elapsed time

Total duration

Current Screen

Current directory (if BrowserScreen is active)

Current selection

Build 0005 -- Playback Statistics

Queue position

Queue size

Remaining time

Codec

Sample rate

Bitrate

Channels

Playback Statistics are obtained from PlaybackController's public
interface only (getQueuePosition(), getQueueSize(), getStreamInfo(),
etc.) -- DeveloperScreen never queries ServiceController or
compatibility.py directly.

Runtime Status is read-only.

---

# 6. Logger Page

Logger page displays current logging status.

Information includes:

Current log level

Developer Mode

Current log file

Log file location

Log message count (future)

Available actions:

- Export log
- Open log directory (future)
- Clear current log (future)

Changing logging options shall use the public Logger interface only.

---

# 7. System Information Page

Displays information provided by SystemInfo.

Information includes:

Platform

Distribution

Python version

Enigma2 version

Image version

Available features

System uptime (future)

Memory information (future)

System information is read-only.

---

# 8. Compatibility Page

Displays information provided by Compatibility.

Information includes:

Detected platform

Platform capabilities

Compatibility features

Enabled workarounds

Platform abstraction status

Build 0006 also displays Skin & Theme information here (current
skin/theme, version, compatibility requirement, author, available
skins/themes), sourced from SkinManager.getCompatibilityReport().

This page is intended for diagnostics only.

---

# 9. Build Information Page

Displays build-related information.

Information includes:

Application name

Version

Build number

Architecture version

Build date (future)

Git revision (future)

License

This information is read-only.

---

# 10. Controller Interaction

DeveloperScreen communicates only through public interfaces.

PlaybackController

- Runtime status
- Playback state
- Current media

Logger

- Logging status
- Developer mode
- Export log

SystemInfo

- Platform information
- Runtime information

Compatibility

- Platform detection
- Supported features
- Compatibility status

DeveloperScreen shall never communicate directly with:

ServiceController

NavigationInstance

Enigma2 playback services

---

# 11. Logging

DeveloperScreen follows LOGGER_SPEC.md.

Typical lifecycle logging:

```
DeveloperScreen created.

DeveloperScreen initializing.

DeveloperScreen initialized.

DeveloperScreen running.

DeveloperScreen cleanup.

DeveloperScreen closed.
```

Typical user interaction logging:

```
Opening Runtime Status.

Opening Logger page.

Opening System Information.

Opening Compatibility page.

Exporting log.
```

Developer Mode BASIC

- Screen lifecycle
- Page navigation

Developer Mode VERBOSE

Additionally:

- Refresh operations
- Runtime updates
- Export operations
- Diagnostic requests

---

# 12. Future Extensions

DeveloperScreen is designed to support future development tools.

Possible future additions:

- Architecture status
- Active timers
- Thread information
- Performance statistics
- Memory allocation
- Loaded modules
- Configuration dump
- Service history
- Screen history
- Diagnostic report export

Future additions should not require changes to the public interface of
DeveloperScreen.

---

# 13. Acceptance Criteria

DeveloperScreen is considered complete when:

- It opens from Developer Settings.
- Runtime Status displays current application information.
- Logger page displays logging status.
- System Information page displays runtime environment.
- Compatibility page displays platform information.
- Build Information page displays application version.
- Logging follows LOGGER_SPEC.md.
- DeveloperScreen contains no playback implementation.
- DeveloperScreen contains no platform-specific code.

---

# End of File

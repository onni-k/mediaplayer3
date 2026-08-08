# MediaPlayer3

# Main Menu Specification

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

Main Menu provides a single, consistent navigation interface for
MediaPlayer3.

Every primary screen opens the same Main Menu implementation.

Main Menu is responsible only for navigation.

It never performs playback or platform specific operations.

---

# 2. Responsibilities

Main Menu is responsible for:

- Presenting application functions
- Opening secondary screens
- Providing a consistent navigation experience
- Dispatching menu selections

Main Menu is NOT responsible for:

- Playback
- Directory browsing
- Configuration editing
- Platform abstraction
- Service management

---

# 3. Design Principles

MediaPlayer3 contains exactly one Main Menu implementation.

Every Screen opens the same menu.

Main Menu shall not contain duplicate functionality.

Menu entries should remain stable between application versions whenever
possible.

---

# 4. Lifecycle

Standard lifecycle

Created

↓

Initializing

↓

Create menu entries

↓

Initialized

↓

Waiting for user selection

↓

Dispatch selected action

↓

Closed

Main Menu follows the lifecycle defined in LOGGER_SPEC.md.

---

# 5. Initial Menu Structure

Main Menu initially contains:

Browser

Playback Information

Settings

Developer Tools

About

Exit

Future menu entries should be appended whenever practical rather than
changing the existing order.

---

# 6. Navigation

Main Menu may be opened from:

MainScreen

BrowserScreen

PlaybackInfoScreen

SettingsScreen

DeveloperScreen

The same Main Menu implementation shall be used regardless of the
calling screen.

---

# 7. Remote Control Mapping

Main Menu shall respond to the following remote control keys.

UP / DOWN

- Move between menu entries.

OK

- Execute the selected menu action.

LEFT / RIGHT

Reserved for future use.

MENU

- Close Main Menu and return to the calling screen.

EXIT

- Close Main Menu and return to the calling screen.

Main Menu shall never consume playback control keys.

---

# 8. Controller Interaction

Main Menu does not communicate directly with Controllers.

Instead, it dispatches user selections to the calling screen.

Example

MainScreen

↓

Main Menu

↓

Settings

↓

MainScreen opens SettingsScreen

This keeps Main Menu independent of application logic.

---

# 9. Logging

Main Menu follows LOGGER_SPEC.md.

Typical lifecycle logging:

```
Main Menu created.

Main Menu initializing.

Main Menu initialized.

Main Menu opened.

Main Menu closed.
```

Typical user interaction logging:

```
Menu entry selected:

Browser

Menu entry selected:

Settings

Menu entry selected:

Developer Tools

Returning to calling screen.
```

Developer Mode BASIC

- Menu opened
- Menu closed
- Selected menu entry

Developer Mode VERBOSE

Additionally:

- Calling screen
- Target screen
- Navigation timing
- Invalid selections (future)

---

# 10. Future Extensions

Main Menu is designed for future expansion.

Possible future menu entries include:

- Playlist
- Favorites
- Recently Played
- Search
- Help
- Update Check
- Export Diagnostics
- Plugin Manager

New menu entries should be added without changing existing menu
behaviour whenever practical.

---

# 11. Acceptance Criteria

Main Menu is considered complete when:

- Every primary screen opens the same Main Menu.
- Menu navigation is consistent throughout the application.
- Menu actions are dispatched correctly.
- Logging follows LOGGER_SPEC.md.
- Main Menu contains no playback implementation.
- Main Menu contains no platform-specific code.
- Main Menu contains no duplicated functionality.

---

# 12. Architecture Notes

Main Menu belongs to the Screen Layer.

It communicates only with the calling screen.

Business logic remains inside Controllers.

Platform-specific functionality remains inside Compatibility.

Main Menu shall remain a reusable navigation component shared by the
entire application.

---

# End of File

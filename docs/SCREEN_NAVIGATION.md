# MediaPlayer3

# Screen Navigation

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

This document defines the navigation flow between all user interface
screens.

Its purpose is to provide a single overview of the Screen Layer.

Detailed behaviour is defined in the individual Screen specifications.

---

# 2. Design Principles

MediaPlayer3 uses a screen-based architecture.

Every screen has a clearly defined responsibility.

Navigation shall remain simple and predictable.

Business logic belongs to Controllers.

Platform specific functionality belongs to the Core Layer.

---

# 3. Screen Hierarchy

Application

↓

MainScreen

↓

Main Menu

↓

Secondary Screens

The MainScreen is always considered the application's primary screen.

---

# 4. Primary Screens

MainScreen

Primary playback interface.

BrowserScreen

Directory browsing and media selection.

SettingsScreen

Application configuration.

PlaybackInfoScreen

Playback information and metadata.

DeveloperScreen

Developer tools and diagnostics.

---

# 5. Main Navigation

Application Start

↓

MainScreen

↓

MENU

↓

Main Menu

↓

Select Function

↓

Requested Screen

↓

Return

↓

MainScreen

This navigation flow shall remain consistent throughout the application.

---

# 6. Browser Navigation

MainScreen

↓

OK (No media selected)

or

PVR

↓

BrowserScreen

↓

Media Selected

↓

PlaybackController

↓

MainScreen

BrowserScreen is always temporary.

---

# 7. Main Menu Navigation

Main Menu may be opened from any primary screen.

Calling Screen

↓

Main Menu

↓

Selected Function

↓

Target Screen

↓

Calling Screen or MainScreen

Main Menu is always implemented as a single reusable component.

---

# 8. Screen Transition Matrix

| From | Action | To |
|------|--------|----|
| MainScreen | OK (no media) | BrowserScreen |
| MainScreen | PVR | BrowserScreen |
| MainScreen | MENU | Main Menu |
| BrowserScreen | OK (media selected) | MainScreen |
| BrowserScreen | EXIT | MainScreen |
| BrowserScreen | MENU | Main Menu |
| Main Menu | Browser | BrowserScreen |
| Main Menu | Settings | SettingsScreen |
| Main Menu | Playback Information | PlaybackInfoScreen |
| Main Menu | Developer Tools | DeveloperScreen |
| Main Menu | About | AboutScreen (future) |
| Main Menu | Exit | MainScreen |
| SettingsScreen | EXIT | MainScreen |
| PlaybackInfoScreen | EXIT | MainScreen |
| DeveloperScreen | EXIT | MainScreen |

---

# 9. Screen Responsibilities

MainScreen

- Playback interface
- Playback status
- Navigation entry point
- Playback control keys (Play/Pause/Stop/Previous/Next), forwarded to
  PlaybackController without changing screens (Build 0005)

BrowserScreen

- Directory browsing
- File selection

SettingsScreen

- User configuration

PlaybackInfoScreen

- Playback information
- Metadata display

DeveloperScreen

- Diagnostics
- Runtime information
- System information

Main Menu

- Navigation only

---

# 10. Navigation Rules

Navigation shall follow these rules.

- Every Screen has a single primary responsibility.
- BrowserScreen is temporary.
- MainScreen is the application's home screen.
- Main Menu is shared by every Screen.
- PlaybackController performs playback.
- Controllers never display user interface.
- Core modules never perform navigation.

These rules define the navigation architecture of MediaPlayer3.

---

# 11. Future Extensions

Future screens may include:

PlaylistScreen

FavoritesScreen

SearchScreen

HelpScreen

AboutScreen

Additional screens should integrate into the existing navigation model
without changing the role of MainScreen as the primary application
window.

---

# 12. Acceptance Criteria

Screen navigation is considered complete when:

- MainScreen is the primary application window.
- BrowserScreen is opened only by user request.
- Every Screen has a clearly defined responsibility.
- Main Menu is shared throughout the application.
- Navigation follows this document.
- Navigation logic remains independent of platform-specific code.
- Screen transitions remain predictable and consistent.

---

# End of File

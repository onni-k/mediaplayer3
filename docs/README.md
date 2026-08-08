# MediaPlayer3

Modern Media Player for Enigma2

Version: 0.7.0-dev

Current Build: 0007

Status: CONFIRMED COMPLETE -- device tested across four Enigma2 images (OpenViX, OpenATV, openPLI, OpenBH), 13 rounds

---

# Overview

MediaPlayer3 is a modern media player designed for Enigma2-based
receivers.

The project focuses on:

- Modular architecture
- Platform abstraction
- Maintainable code
- Clear separation of responsibilities
- Long-term extensibility
- Comprehensive documentation

MediaPlayer3 is designed to support multiple Enigma2 distributions
through a common architecture.

---

# Current Project Status

Build 0007 focuses on:

- Playlist management (PlaylistManager, PlaylistScreen)
- Internet Radio via RadioBrowser (InternetRadioManager,
  RadioBrowserScreen)
- Application storage management (StorageManager)
- BrowserScreen playlist context menu
- MainScreen Internet Radio navigation
- Developer diagnostics (storage/playlists/radio)

Implementation follows the documentation contained in the **docs/**
directory.

---

# Documentation Overview

The documentation is organised into several groups.

Architecture

ARCHITECTURE.md

Overall software architecture.

PROJECT_STRUCTURE.md

Project directory structure.

SCREEN_NAVIGATION.md

Screen navigation model.

---

Specifications

Core

CONFIG_SPEC.md

LOGGER_SPEC.md

SYSTEMINFO_SPEC.md

COMPATIBILITY_SPEC.md

LOCALIZATION_MANAGER_SPEC.md

SKIN_MANAGER_SPEC.md

THEME_SPEC.md

METADATA_SPEC.md

STORAGE_MANAGER_SPEC.md

PLAYLIST_MANAGER_SPEC.md

INTERNETRADIO_MANAGER_SPEC.md

Controllers

PLAYBACK_CONTROLLER_SPEC.md

PLAYBACK_QUEUE_SPEC.md

SERVICE_CONTROLLER_SPEC.md

Screens

MAINSCREEN_SPEC.md

MAINMENU_SPEC.md

BROWSERSCREEN_SPEC.md

PLAYLISTSCREEN_SPEC.md

RADIOBROWSER_SCREEN_SPEC.md

SETTINGSSCREEN_SPEC.md

PLAYBACKINFO_SPEC.md

DEVELOPER_SCREEN_SPEC.md

---

Project Documentation

BUILD_0007_PLAN.md

CHANGELOG.md

HISTORY.md

RELEASE_CHECKLIST.md

NAMING_CONVENTIONS.md

DEVELOPMENT_GUIDE.md

---

# Development Workflow

Recommended development process:

Idea

↓

Architecture Review

↓

Specification Update

↓

Implementation

↓

Testing

↓

Documentation Update

↓

Release Checklist

↓

Build Freeze

The project follows the development practices described in
DEVELOPMENT_GUIDE.md.

---

# Build History

| Build | Version | Status |
|--------|---------|--------|
| 0001 | 0.1.0-dev | Initial prototype |
| 0002 | 0.2.0-dev | Architecture planning |
| 0003 | 0.3.0-dev | Stable controller architecture |
| 0004 | 0.4.0-dev | Screen architecture redesign |
| 0005 | 0.5.0-dev | Playback experience: queue, progress bar, Auto Next |
| 0006 | 0.6.0-dev | Customization & rich metadata: localization, skins/themes, tag metadata, artwork |
| 0007 | 0.7.0-dev | Media collections: playlists, Internet Radio (RadioBrowser), storage management |

Refer to CHANGELOG.md and HISTORY.md for detailed project history.

---

# Design Principles

MediaPlayer3 is built around the following principles:

- Modular architecture
- One responsibility per module
- Clear separation between Screens, Controllers and Core modules
- Platform abstraction through Compatibility
- Public interfaces remain stable whenever practical
- Documentation evolves together with the implementation

These principles guide all future development.

---

# License

MediaPlayer3 is released under the GNU General Public License (GPL).

Some implementation ideas are inspired by existing Enigma2 projects.
Where source code is derived from existing GPL software, original
copyright notices and license terms shall be preserved.

---

# Acknowledgements

MediaPlayer3 builds upon the Enigma2 ecosystem and benefits from ideas
and experience gained from existing open source projects.

Special thanks to the Enigma2 community and the developers of OpenViX,
OpenATV and related projects for making their work available under open
source licenses.

---

# Getting Started

For new developers, the recommended reading order is:

1. README.md
2. ARCHITECTURE.md
3. PROJECT_STRUCTURE.md
4. SCREEN_NAVIGATION.md
5. DEVELOPMENT_GUIDE.md
6. Relevant *_SPEC.md documents
7. RELEASE_CHECKLIST.md

Following this order provides a complete overview of the project before
implementation begins.

---

# End of File

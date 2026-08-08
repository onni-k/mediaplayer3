# ARCHITECTURE.md

MediaPlayer3

Architecture Overview

Updated for Build 0007

---

# Purpose

This document describes the overall software architecture of
MediaPlayer3.

It explains how the major application components interact and how
responsibilities are separated between managers, controllers and user
interface screens.

The architecture follows a modular, layered design intended to simplify
maintenance, testing and future expansion.

---

# Design Principles

MediaPlayer3 follows these design principles:

- Single Responsibility Principle
- Layered Architecture
- Manager-based design
- User Interface separated from business logic
- Centralized storage management
- Platform abstraction through Compatibility layer
- Future extensibility without breaking existing interfaces

Each module should have one clearly defined responsibility.

---

# High-Level Architecture

```
                     MediaPlayer3

                            │

        ┌────────────────────────────────────┐
        │            User Interface          │
        │                                    │
        │ MainScreen                         │
        │ BrowserScreen                      │
        │ PlaylistScreen                     │
        │ RadioBrowserScreen                 │
        │ SettingsScreen                     │
        │ PlaybackInfoScreen                 │
        │ DeveloperScreen                    │
        └────────────────────────────────────┘
                            │
                            ▼
        ┌────────────────────────────────────┐
        │         PlaybackController         │
        └────────────────────────────────────┘
                            │
                            ▼
        ┌────────────────────────────────────┐
        │         ServiceController          │
        └────────────────────────────────────┘
                            │
                            ▼
        ┌────────────────────────────────────┐
        │       Compatibility Layer          │
        └────────────────────────────────────┘
                            │
                            ▼
                      Enigma2 Platform
```

---

# Manager Layer

The manager layer contains application services that are shared by
multiple components.

ConfigurationManager

Stores application settings.

LocalizationManager

Provides translated user interface strings.

SkinManager

Provides themes and skin compatibility.

StorageManager

Provides application storage services.

PlaylistManager

Provides playlist management.

InternetRadioManager

Provides Internet Radio management.

PlaybackController communicates with these managers whenever required,
but each manager remains independent from the others whenever possible.

---
# Storage Layer

StorageManager provides a centralized storage infrastructure for the
entire application.

No application component shall use hard coded filesystem paths.

StorageManager is responsible for:

- Working directory creation
- Directory validation
- Path services
- Storage diagnostics
- Recovery of missing directories

Application working directory:

```
/media/hdd/.mediaplayer3/

    playlists/
    radio/
    artwork/
    cache/
    logs/
    imports/
    exports/
    backups/
    userdata/
```

Future builds may extend this directory structure without affecting
other modules.

---

# Content Management

MediaPlayer3 separates media management into dedicated managers.

PlaylistManager

Responsible for:

- Playlist creation
- Playlist import/export
- Playlist validation
- Playback queue generation

InternetRadioManager

Responsible for:

- RadioBrowser communication
- Station search
- Favorite management
- Listening history
- Stream preparation

PlaybackController receives validated playback information from these
managers but never modifies their internal data.

---

# Dependency Rules

The following dependency rules shall always be followed.

User Interface

↓

Managers

↓

Controllers

↓

Compatibility Layer

↓

Enigma2

Managers shall never depend on user interface classes.

Controllers shall never modify user interface objects directly.

StorageManager shall remain independent from all application specific
logic.

---

# Future Architecture

The current architecture has been designed to support future expansion.

Planned manager classes include:

LibraryManager

Provides local music library indexing and search.

RecordingManager

Provides Internet Radio recording services.

LyricsManager

Provides synchronized (.lrc) and text (.txt) lyric handling.

These managers are planned for future builds and are intentionally kept
outside the Build 0007 implementation.

---

# Summary

MediaPlayer3 follows a modular architecture in which each component has
a clearly defined responsibility.

This separation provides:

- Easier maintenance
- Better testability
- Improved portability
- Cleaner implementation
- Future extensibility

The architecture has evolved incrementally from Build 0004 through
Build 0007 while maintaining backward compatibility between existing
components.

Future builds shall continue following the same modular design
principles.

---

End of ARCHITECTURE.md

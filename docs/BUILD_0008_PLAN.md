# BUILD_0008_PLAN.md

MediaPlayer3

Build 0008 Development Plan

Status

CONFIRMED COMPLETE -- 9 rounds of real device testing, confirmed by the user

Version

0.8.0-dev

---

# Purpose

Build 0008 focuses on improving the user experience by making local
music easier to browse, search and explore while providing richer
information during playback.

Rather than introducing new playback technologies, this build extends
the existing playback system with music library functionality,
lyrics support, information views and integrated help.

The overall goal is to make MediaPlayer3 behave more like a complete
music player while preserving the simple remote-control based user
interface established in previous builds.

---

# Primary Goals

Build 0008 introduces the following major components.

- Music Library
- LibraryManager
- MusicLibraryScreen
- LyricsManager
- HelpManager
- HelpScreen
- MainScreen information views
- Dynamic Playback Queue

These additions are designed to integrate with the architecture
introduced in Build 0007 without changing existing playback logic.

---

# Design Principles

Build 0008 follows the same architectural principles as previous
versions.

- Small independent modules
- One responsibility per manager
- Reusable user interface components
- Consistent navigation
- Playback independent of content source
- Documentation before implementation

Whenever possible, existing managers should remain unchanged.

---

# Music Library

Music Library becomes a new top-level function.

Main Menu

Browser

Playlists

Music Library

Internet Radio

Settings

Developer

Music Library is intentionally separated from Browser.

Browser continues to provide filesystem navigation while Music Library
provides metadata-based browsing and searching.

---

# Music Library Goals

Music Library shall support browsing by:

- Artist
- Album
- Track
- Genre
- Year

The interface shall also provide fast searching across the music
collection.

The music library is generated from metadata and is independent of the
physical directory structure whenever possible.

---
# LibraryManager

Build 0008 introduces LibraryManager.

LibraryManager is responsible for:

- Building the music library
- Reading metadata
- Maintaining the library index
- Providing search services
- Returning artists
- Returning albums
- Returning tracks
- Returning genres
- Returning years

LibraryManager never performs playback.

Playback always remains the responsibility of PlaybackController.

---

# MusicLibraryScreen

MusicLibraryScreen provides metadata based browsing.

The initial layout consists of three navigation panels.

```
Artists

Albums

Tracks
```

Future versions may optionally allow replacing the first panel with:

- Genres
- Years
- Search Results

Navigation follows the same model already established by
RadioBrowserScreen.

LEFT / RIGHT

Change active panel.

UP / DOWN

Move inside the active list.

OK

Open item or start playback.

MENU

Music Library functions.

HELP

Open context sensitive help.

EXIT

Return to previous screen.

---

# Dynamic Playback Queue

One of the primary architectural goals of Build 0008 is to unify
playback behavior.

PlaybackController shall receive a PlaybackQueue regardless of the
content source.

Possible queue sources include:

- Browser
- Playlist
- Music Library
- Artist
- Album
- Genre
- Search Results

Internetradio similarly provides a StationQueue.

PlaybackController shall never need to know how the queue was created.

This guarantees identical playback behavior regardless of where
playback started.

---

# Search

Music Library provides fast searching.

Initial search fields include:

- Artist
- Album
- Track
- Genre
- Year

Search results behave exactly like any other playlist.

Selecting the first track creates a temporary PlaybackQueue containing
all matching tracks.

Playback automatically continues through the remaining search results.

---
# Lyrics

Build 0008 introduces integrated lyrics support.

LyricsManager is responsible for locating, loading and presenting
available lyrics for the currently playing track.

Supported lyric sources are searched in the following order.

1. Embedded Lyrics

2. External .lrc

3. External .txt

4. Lyrics not available

Embedded lyrics always take precedence when available.

Future builds may extend LyricsManager with online lyric providers
without changing the user interface.

---

# MainScreen Information Views

The MainScreen gains an information panel in the lower right corner.

TEXT cycles through available views.

Lyrics

↓

Metadata

↓

Codec Information

↓

Lyrics...

The current view is indicated by a small status label.

Examples

Ⓛ Lyrics

Ⓜ Metadata

Ⓒ Codec

The interface remains unchanged while only the information panel
changes.

---

# Previous / Next Preview

The lower left corner displays the surrounding PlaybackQueue items.

Example

Previous

Juice Leskinen

──────────────

Next

J. Karjalainen

Internet Radio behaves identically.

The preview shows the previous and next stations from the current
StationQueue.

This provides better awareness of the current playback context.

---

# Help System

Every user interface screen provides context sensitive help.

Pressing HELP opens HelpScreen.

HelpScreen automatically displays the documentation matching the
currently active screen.

Examples

MainScreen

BrowserScreen

PlaylistScreen

MusicLibraryScreen

RadioBrowserScreen

SettingsScreen

DeveloperScreen

This allows users to learn application features without leaving the
current workflow.

---
# Documentation

Build 0008 introduces the following documentation.

Planning

- BUILD_0008_PLAN.md

Manager Specifications

- LIBRARY_MANAGER_SPEC.md
- LYRICS_MANAGER_SPEC.md
- HELP_MANAGER_SPEC.md

Screen Specifications

- MUSICLIBRARY_SCREEN_SPEC.md
- HELP_SCREEN_SPEC.md

Updated Documents

- ARCHITECTURE.md
- PROJECT_STRUCTURE.md
- HISTORY.md
- CHANGELOG.md

All documentation shall be completed before implementation whenever
possible.

---

# Deferred Features

The following features have intentionally been postponed to later
builds.

- Internet Radio recording
- RecordingManager
- Scheduled recordings
- Podcast support
- Online lyrics providers
- Smart playlists
- Advanced library indexing
- Automatic duplicate detection
- Remote media sources

These features remain compatible with the architecture introduced in
Build 0008.

---

# Summary

Build 0008 focuses on helping users find, browse and understand their
music collection while preserving the simple remote-control oriented
workflow established in previous builds.

The introduction of Music Library, LyricsManager and HelpManager
extends MediaPlayer3 beyond a traditional file browser into a complete
music player environment.

A unified Dynamic Playback Queue ensures identical playback behavior
regardless of whether playback begins from Browser, Playlist,
Music Library, Search Results or Internet Radio.

Context-sensitive help improves usability without requiring external
documentation.

Embedded lyrics, synchronized lyrics, metadata and codec information
provide a richer listening experience while maintaining a clean and
consistent MainScreen.

The modular architecture introduced in previous builds remains
unchanged, allowing future features to be added with minimal impact on
existing components.

---

End of BUILD_0008_PLAN.md

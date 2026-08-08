# MUSICLIBRARY_SCREEN_SPEC.md

MediaPlayer3

MusicLibraryScreen Specification

Status

Build 0008 CONFIRMED COMPLETE -- 9 rounds of real device testing, confirmed by the user

---

# Purpose

MusicLibraryScreen provides metadata-based browsing of the user's music
collection.

Unlike BrowserScreen, which follows the physical filesystem,
MusicLibraryScreen organizes music using LibraryManager.

The screen is optimized for remote-control navigation and follows the
same interaction model already established by RadioBrowserScreen.

---

# Responsibilities

MusicLibraryScreen is responsible for:

- Displaying artists
- Displaying albums
- Displaying tracks
- Displaying search results
- Navigating library contents
- Requesting PlaybackQueues from LibraryManager

MusicLibraryScreen shall not:

- Read media files directly
- Build the library index
- Decode media
- Control playback

---

# Screen Layout

The initial layout consists of three navigation panels.

```
Artists

Albums

Tracks
```

The currently active panel is highlighted.

Changing the selected artist updates the album list.

Changing the selected album updates the track list.

Selecting a track allows playback or additional actions.

---

# Navigation

LEFT / RIGHT

Move between panels.

UP / DOWN

Move inside the active panel.

OK

Open the selected item or start playback.

MENU

Open Music Library functions.

HELP

Open context-sensitive help.

EXIT

Return to the previous screen.

The navigation model intentionally matches RadioBrowserScreen.

---

# Playback

Selecting a track does not start playback directly.

Instead, MusicLibraryScreen requests a PlaybackQueue from
LibraryManager.

The PlaybackQueue contains all tracks represented by the current
selection.

Examples

Artist

↓

All tracks by the selected artist

Album

↓

All tracks from the selected album

Search Result

↓

All matching tracks

PlaybackController always receives a PlaybackQueue regardless of the
selection type.

---
# Search

MusicLibraryScreen provides integrated library searching.

Initial search fields include:

- Artist
- Album
- Track
- Genre
- Year

Search results are displayed using the same interface as normal library
views.

Selecting the first matching track creates a PlaybackQueue containing
all matching tracks.

Playback continues automatically through the remaining search results.

---

# Information Display

The currently selected item may display additional information.

Examples include:

- Album artwork
- Artist
- Album
- Year
- Genre
- Track count
- Duration

The displayed information depends on the selected panel.

Future versions may extend this area without changing the screen
layout.

---

# Error Handling

If the library contains no music, MusicLibraryScreen displays an
informative message.

Example:

```
No music library available.

Use Library Update from the menu
after adding music files.
```

Library loading errors are reported through the application log but
never terminate the application.

---

# Future Extensions

Possible future additions include:

- Genre panel
- Year panel
- Recently Added
- Most Played
- Recently Played
- Ratings
- Favorites
- Smart collections
- Library statistics
- Multiple sort modes

These additions are designed to integrate into the existing navigation
model without requiring major interface changes.

---

# Summary

MusicLibraryScreen provides a metadata-oriented alternative to
filesystem browsing.

Together with LibraryManager it allows users to browse, search and play
music using artists, albums and other metadata while preserving the
consistent navigation model already used throughout MediaPlayer3.

Dynamic PlaybackQueue generation ensures identical playback behavior
regardless of whether music is started from a library view, search
result or traditional BrowserScreen.

---

End of MUSICLIBRARY_SCREEN_SPEC.md

# LIBRARY_MANAGER_SPEC.md

MediaPlayer3

LibraryManager Specification

Status

Build 0008 CONFIRMED COMPLETE -- 9 rounds of real device testing, confirmed by the user

---

# Purpose

LibraryManager provides a metadata-based view of the user's music
collection.

Unlike BrowserScreen, which follows the physical filesystem,
LibraryManager organizes music using information stored in media files.

LibraryManager never performs playback.

Its responsibility is to discover music, maintain an indexed library,
perform searches and generate PlaybackQueues for PlaybackController.

---

# Responsibilities

LibraryManager is responsible for:

- Scanning configured music directories
- Reading media metadata
- Building the library index
- Updating the library when requested
- Providing search services
- Returning artists
- Returning albums
- Returning tracks
- Returning genres
- Returning years
- Creating PlaybackQueues from library selections

LibraryManager shall not:

- Decode media
- Control playback
- Manage playlists
- Display user interface

---

# Supported Media

LibraryManager supports every media format supported by
PlaybackController.

Typical formats include:

- FLAC
- MP3
- OGG
- WAV
- AAC
- M4A

Support automatically follows PlaybackController capabilities.

---

# Metadata

LibraryManager attempts to read all available metadata.

Typical fields include:

- Artist
- Album
- Album Artist
- Title
- Track Number
- Disc Number
- Genre
- Year
- Composer
- Comment
- Duration
- Bitrate
- Sample Rate
- Channels

Missing metadata never prevents a file from being added to the
library.

---

# Library Index

The library is represented by an internal index.

The index allows fast access to:

- Artists
- Albums
- Tracks
- Genres
- Years

The physical directory structure is not exposed to the user unless
explicitly requested through BrowserScreen.

---
# Search

LibraryManager provides metadata-based searching.

Supported search fields include:

- Artist
- Album
- Track
- Genre
- Year

Future versions may extend searching with:

- Composer
- Album Artist
- Comment
- Folder

Search results are returned as temporary library views.

Selecting any track creates a PlaybackQueue containing all matching
tracks.

Playback automatically continues through the remaining search results.

---

# PlaybackQueue Generation

LibraryManager never starts playback directly.

Instead it creates a PlaybackQueue which is passed to
PlaybackController.

Possible queue sources include:

- Artist
- Album
- Genre
- Year
- Search Result

PlaybackController treats every queue identically.

This guarantees consistent playback behavior throughout the
application.

---

# Library Updates

The library may be refreshed manually.

Future versions may optionally support:

- Automatic rescanning
- Background indexing
- Incremental updates

These features are intentionally outside the scope of Build 0008.

---

# Error Handling

LibraryManager ignores unreadable files.

Files with incomplete metadata remain visible whenever playback is
possible.

Scanning errors are written to the application log but never terminate
the application.

---

# Future Extensions

Possible future additions include:

- Rating support
- Play count
- Last played
- Recently added
- Most played
- Duplicate detection
- Smart collections
- Folder statistics

The architecture reserves space for these features without affecting
existing interfaces.

---

# Summary

LibraryManager provides a unified metadata-based view of the local music
collection.

It separates library organization from the physical filesystem and
creates PlaybackQueues that integrate seamlessly with the existing
PlaybackController.

This architecture allows BrowserScreen and MusicLibraryScreen to
coexist while serving different purposes.

---

End of LIBRARY_MANAGER_SPEC.md

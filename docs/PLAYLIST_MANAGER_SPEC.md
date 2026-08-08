# PLAYLIST_MANAGER_SPEC.md

MediaPlayer3

Build 0007

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

PlaylistManager is responsible for all playlist management inside
MediaPlayer3.

PlaylistManager owns playlist creation, loading, saving, importing,
exporting and modification.

PlaybackController is responsible only for playback.

PlaylistManager prepares playlist data for PlaybackController.

---

# Responsibilities

PlaylistManager shall provide:

- Playlist creation
- Playlist deletion
- Playlist renaming
- Playlist loading
- Playlist saving
- Playlist validation
- Playlist import
- Playlist export
- Track insertion
- Track removal
- Track movement
- Folder expansion
- Queue generation

PlaylistManager shall never perform media playback.

---

# Playlist Format

PlaylistManager stores playlists using Extended M3U.

Example:

#EXTM3U

#EXTINF:355,Queen - Bohemian Rhapsody
/media/hdd/music/Rock/Queen/Bohemian Rhapsody.flac

#EXTINF:285,Europe - The Final Countdown
/media/hdd/music/Rock/Europe/The Final Countdown.flac

Absolute paths shall be used.

PlaylistManager shall accept both:

- Standard M3U

and

- Extended M3U

All exported playlists shall use Extended M3U.

---

# Playlist Storage

Default directory:

/media/hdd/.mediaplayer3/playlists/

Each playlist is stored as an individual M3U file.

Example:

Favorites.m3u

Rock.m3u

Jazz.m3u

Christmas.m3u

Workout.m3u

Playlist names shall be unique.

Invalid filename characters shall automatically be removed or replaced.

---

# Playlist Object

PlaylistManager internally represents playlists as:

Playlist

↓

Track

↓

Track

↓

Track

Each Track contains:

- Full path
- File name
- Title
- Artist
- Album
- Duration

Metadata may be unavailable until loaded by PlaybackController.

---

# Playlist Operations

PlaylistManager shall support:

CreatePlaylist()

DeletePlaylist()

RenamePlaylist()

LoadPlaylist()

SavePlaylist()

ImportPlaylist()

ExportPlaylist()

ValidatePlaylist()

GeneratePlaybackQueue()

All operations shall return success or failure.

Errors shall never terminate the application.

---
# Folder Handling

PlaylistManager supports adding complete folders.

When a folder is added:

- Audio files are collected recursively.
- Supported file types only.
- Folder structure is not stored.
- Individual tracks are written into the playlist.

The original music directory shall never be modified.

---

# Browser Integration

BrowserScreen communicates directly with PlaylistManager.

Folder menu:

- Play Folder
- Add Folder to Playlist
- Create Playlist
- Cancel

Audio file menu:

- Play
- Add to Playlist
- Information
- Cancel

Playlist file menu:

- Play Playlist
- Import Playlist
- Information
- Cancel

PlaylistManager performs all playlist modifications.

---

# Playback Queue

PlaybackController never reads playlist files directly.

PlaylistManager prepares an ordered playback queue.

Example:

Playlist

↓

GeneratePlaybackQueue()

↓

Playback Queue

↓

PlaybackController

PlaybackController receives only validated playlist entries.

---

# Validation

PlaylistManager validates playlists before playback.

Validation includes:

- File exists
- Supported media type
- Duplicate handling
- Invalid path detection

Missing files shall be skipped.

Validation failures shall be written to the application log.

Playlist playback shall continue whenever possible.

---

# Logging

PlaylistManager shall provide structured logging.

Typical events:

INFO

Playlist created

Playlist renamed

Playlist deleted

Playlist loaded

Playlist saved

Playlist imported

Playlist exported

Track added

Track removed

Folder added

WARNING

Playlist validation failed

Missing file

ERROR

Playlist loading failed

Playlist saving failed

Verbose logging additionally records:

- Playlist parsing
- Playlist validation
- Queue generation
- Playlist statistics

---

# Future Extensions

The following features are outside the scope of Build 0007.

Possible future additions:

- Dynamic playlists
- Smart playlists
- Playlist folders
- Automatic duplicate removal
- Playlist search
- Playlist sorting
- Playlist merging
- Playlist synchronization
- Cloud playlist support

The current PlaylistManager architecture shall allow future expansion
without incompatible interface changes.

---

# Dependencies

PlaylistManager depends on:

- StorageManager
- Logger
- ConfigurationManager

PlaybackController depends on PlaylistManager only for playback queue
generation.

PlaylistManager shall not depend on BrowserScreen,
MainScreen or PlaybackController implementation details.

---

# Summary

PlaylistManager provides a dedicated playlist subsystem.

Responsibilities include:

- Playlist management
- Playlist storage
- Playlist validation
- Playback queue generation

Playback remains the responsibility of PlaybackController.

This separation follows the MediaPlayer3 architecture introduced in
Build 0004 and extended during Builds 0005, 0006 and 0007.

---

End of PLAYLIST_MANAGER_SPEC.md

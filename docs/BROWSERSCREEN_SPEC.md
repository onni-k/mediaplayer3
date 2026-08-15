# MediaPlayer3

# BrowserScreen Specification

Version: 1.0

Status: Build 0010 CONFIRMED COMPLETE (device test rounds 6, 7, 8, 9,
10 -- OpenViX, Vu+ Duo2)

---

# 1. Purpose

BrowserScreen provides local directory browsing and playlist building.

It is a temporary screen that is opened from MainScreen when the user
wants to browse local storage.

BrowserScreen is not the primary application window.

After playback starts, or on EXIT/MENU, BrowserScreen returns control
to MainScreen.

This is a full redesign from Build 0007's single-column, INFO-context-
menu-based browser (see HISTORY.md/CHANGELOG.md for that design) to
the three-column model below, following the same column-focus pattern
PodcastScreen already established (PODCAST_SCREEN_SPEC.md).

---

# 2. Layout

BrowserScreen uses a three-column layout.

```text
Directories | Files | Playlist
```

## Directories

The Directories column lists the subdirectories of the current root
(".." first, unless the current root is the filesystem root).

Moving the selection within Directories does not itself change what
the column displays -- only "Open directory" (see section 5) descends
into the selected entry, replacing the Directories column's own list
with that subdirectory's own subdirectories.

## Files

The Files column previews the supported audio files inside whichever
directory is currently *selected* (not necessarily opened) in the
Directories column -- it updates live as the Directories selection
moves, the same way PodcastScreen's Episodes column already tracks
the selected podcast, without requiring the directory to be opened
first.

## Playlist

The Playlist column shows the current working playlist -- the target
for every "add to playlist" action described in section 5. If none has
been chosen yet, INFO (section 6) opens the playlist picker; the first
"Add" action also opens it automatically if needed.

---

# 3. Responsibilities

BrowserScreen is responsible for:

- Directory browsing (Directories column)
- File preview and selection (Files column)
- Playlist building (Playlist column, via the OK menus in section 5)
- Forwarding playback requests to the shared PlaybackController
- Returning to MainScreen

BrowserScreen is NOT responsible for:

- Playback implementation
- Playback status display (MainScreen's own display handles that)
- Metadata extraction
- Configuration management
- Platform-specific functionality
- NavigationInstance access

---

# 4. Lifecycle

Standard lifecycle:

Created -> Initializing -> Load startup directory -> Initialize
Directories/Files/Playlist columns -> Initialized -> Running -> Closed.

BrowserScreen follows the lifecycle defined in LOGGER_SPEC.md.

An unavailable configured startup directory (e.g. a disconnected USB
drive or unmounted network share) does not crash BrowserScreen -- it
falls back to "/" (always present on any Linux-based system).

---

# 5. Column Actions (OK)

OK opens an action menu for the current selection. The exact contents
depend on which column has focus.

## Directories

- Play -- creates (or replaces) the fixed, reserved "Files" playlist
  (see section 5.1) with exactly that folder's supported audio files,
  recursive, and starts playing it.
- Open directory -- descends into the selected subdirectory (or ".."
  to go up), replacing the Directories column's own list.
- Add entire directory to playlist -- recursively adds every
  supported audio file under the selected directory to the current
  working playlist.
- Cancel

"Play" and "Add entire directory to playlist" are not offered for
"..".

## Files

- Play -- creates (or replaces) the fixed, reserved "Files" playlist
  with just that one file, and starts playing it.
- Add this file -- adds just the selected file to the current working
  playlist.
- Add this file and remaining files in directory -- adds the selected
  file and every file that sorts after it alphabetically in the same
  directory (non-recursive).
- Add all files from directory -- adds every supported audio file in
  the same directory (non-recursive).
- Cancel

## Playlist

- Play -- starts playing the current working playlist from the
  selected track onward.
- Remove -- removes the selected track from the current working
  playlist.
- Move up / Move down -- reorders the selected track within the
  current working playlist.
- Cancel

## 5.1 The reserved "Files" playlist

Directories/Files "Play" always targets one fixed, reserved playlist
(the existing, already-translated "Files" string) rather than a name
derived from the folder or file -- deliberately, to avoid ever
silently overwriting a playlist the user named themselves (device
test round 6). Only this one playlist is ever created/replaced by
"Play"; every other "Add ..." action in section 5 targets whichever
playlist is currently the working playlist (section 2, Playlist
column), never this reserved one implicitly.

---

# 6. Remote Control Mapping

BrowserScreen responds to the following remote control keys.

LEFT / RIGHT

- Switch the active column (Directories / Files / Playlist).

UP / DOWN

- Move the selection within the active column.
- Moving within Directories live-updates the Files column's preview
  (section 2).

CH+ / CH-

- Move 10 entries at a time within the active column (may not work on
  every remote/image).

OK

- Open the action menu for the current selection (section 5).

PLAY

- Directories: play the previewed directory directly (recursive,
  ephemeral queue -- does not create or modify any stored playlist,
  unlike OK's own "Play").
- Files: play the previewed directory directly, starting at the
  selected file (same ephemeral-queue behaviour as above).
- Playlist: play the current working playlist from the selected track
  onward (this one is backed by the stored playlist, same as OK's own
  "Play" for this column).

INFO

- Open the playlist picker (existing playlists, or create a new one)
  to choose the current working playlist.

MENU

- Open Main Menu.

HELP

- Show BrowserScreen's own help documentation.

EXIT / PVR

- Return to MainScreen without changing playback.

---

# 7. Screen Navigation

BrowserScreen may be opened from:

- MainScreen (OK/PVR startup chooser -> Local Music)

BrowserScreen may open:

- Main Menu
- The playlist picker (ChoiceBox, INFO or the first "Add" action)
- A new-playlist-name prompt (VirtualKeyBoard)

BrowserScreen shall never open SettingsScreen directly. Navigation to
SettingsScreen is always performed through Main Menu.

Closing BrowserScreen:

- EXIT/MENU-without-playing: `close(None)`.
- Directories/Files PLAY, or a directory/file "Play" action's
  resulting playback: `close("played")` -- a bare string, since this
  is ephemeral or reserved-playlist playback, not a genuinely
  user-named stored playlist.
- Playlist column playback (OK "Play" or PLAY): `close(("played",
  playlist_name))` -- a tuple, matching PlaylistScreen's own
  convention, so MainScreen's "Back" (MAINSCREEN_SPEC.md "MainScreen
  OK Menu") returns here correctly and LEFT/RIGHT favorites-view
  playlist cycling picks up the right playlist.

---

# 8. Controller Interaction

BrowserScreen communicates only through public controller/manager
interfaces:

- PlaybackController -- request playback, query playback state.
- playlist_manager -- load/save/add/remove/reorder playlist tracks,
  create playlists, list playlist names.

BrowserScreen shall never communicate directly with:

- ServiceController
- Compatibility
- NavigationInstance
- Enigma2 playback services

---

# 9. Logging

BrowserScreen follows LOGGER_SPEC.md.

Typical lifecycle logging:

```
[BrowserScreen] Created
[BrowserScreen] Initializing
[BrowserScreen] Ready
[BrowserScreen] Closing
```

Developer Mode BASIC

- Screen lifecycle
- Directory changes (open/ascend)
- Playback requests
- Playlist add/remove/reorder operations

Developer Mode VERBOSE

Additionally:

- LEFT/RIGHT/OK/PLAY/INFO key presses
- Directory scan failures (falls back gracefully, never crashes)

---

# 10. Error Handling

BrowserScreen remains usable when:

- The configured startup directory is unavailable (falls back to
  "/", section 4).
- A directory scan fails partway (logged, the rest of the listing
  still renders).
- An add/play action targets a directory with no supported audio
  files (a message is shown; the screen stays open).

---

# 11. Future Extensions

Possible future additions, without changing BrowserScreen's primary
responsibility:

- Search within the current directory tree
- Sorting options
- Thumbnail/album-artwork preview
- Network locations

---

# 12. Acceptance Criteria

BrowserScreen is considered complete when:

- It opens only on explicit user request.
- Directory browsing (Directories column) functions correctly,
  including a graceful fallback for an unavailable startup directory.
- The Files column correctly previews the directory currently
  selected in Directories, live.
- All Directories/Files/Playlist OK-menu actions in section 5 work as
  specified, including the reserved "Files" playlist's overwrite
  behaviour (section 5.1).
- Playback requests are forwarded to the shared PlaybackController;
  BrowserScreen never talks to lower-level playback machinery
  directly.
- Playlist changes are forwarded to playlist_manager; BrowserScreen
  never reads or writes playlist storage directly.
- BrowserScreen closes with the correct result (section 7) for every
  exit path, so MainScreen's "Back" and favorites-view playlist
  cycling both work correctly afterward.
- EXIT/PVR return to MainScreen without changing playback.
- Logging follows LOGGER_SPEC.md.
- BrowserScreen contains no playback implementation.
- BrowserScreen contains no platform-specific code.

---

# End of File

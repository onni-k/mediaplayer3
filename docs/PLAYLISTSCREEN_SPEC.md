# PLAYLISTSCREEN_SPEC.md

MediaPlayer3

Build 0007

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

PlaylistScreen provides a dedicated user interface for playlist
management.

PlaylistScreen allows users to browse, create, modify and play
playlists.

PlaylistScreen communicates with PlaylistManager.

PlaylistScreen never modifies playlist files directly.

---

# Responsibilities

PlaylistScreen shall provide:

- Playlist browsing
- Playlist selection
- Track browsing
- Playlist creation
- Playlist deletion
- Playlist renaming
- Playlist playback
- Playlist import
- Playlist export
- Context menus

Playback remains the responsibility of PlaybackController.

---

# Screen Layout

PlaylistScreen consists of two primary panels.

Left panel:

Local PlaylistManager playlists, followed by Internet Radio favorite
lists (Build 0007, device test round 3 -- "Ohjelman soittolistanäkymässä
voisi olla paikalliset soittolistat ja internetradiosoittolistat
nähtävilä. Vasemmassa listassa ensin paikalliset soittolistat ja
sitten internetradiolistat."). Radio entries are shown with a
"(Radio)" suffix to disambiguate from a local playlist that happens to
share the same name.

Right panel:

The selected entry's tracks (local playlist) or stations (radio
list).

Playlist-level and track-level context menus both branch on entry
type: radio lists get a leaner menu than local playlists (no Export,
no Move Up/Down for stations -- those don't apply); "Play" on a radio
list plays its first station.

Example:

Playlists

↓

Favorites

Rock

Jazz

Christmas

Workout

↓

Tracks

01 Queen - Bohemian Rhapsody

02 Europe - The Final Countdown

03 Roxette - Listen To Your Heart

04 Toto - Africa

...

---

# Navigation

PlaylistScreen follows the standard MediaPlayer3 navigation model.

LEFT

Move to left panel.

RIGHT

Move to right panel.

UP

Move selection upward.

DOWN

Move selection downward.

OK

Open context menu.

MENU

Open PlaylistScreen options.

EXIT

Return to previous screen.

Color buttons shall not be required.

---

# Playlist Selection

Selecting a playlist automatically loads its contents.

Track list updates immediately.

Playback is not started automatically.

Only the selected playlist changes.

---

# Track Selection

Selecting a track updates the current selection.

Playback begins only after the user selects:

Play

from the context menu.

Track selection never modifies the playlist.

---

# Playlist Context Menu

Available operations:

Play

Rename

Delete

Export

Information

Cancel

Operations are performed through PlaylistManager.

---
# Track Context Menu

Available operations:

Play

Remove from Playlist

Move Up

Move Down

Information

Cancel

Playlist modifications are delegated to PlaylistManager.

---

# Playlist Creation

Users may create playlists from:

- Empty playlist
- Current folder
- Existing M3U playlist

Playlist names shall be validated before creation.

Duplicate playlist names shall not be allowed.

---

# Playlist Import

PlaylistScreen supports importing playlists.

Supported formats:

- Extended M3U
- Standard M3U

Imported playlists are stored inside:

/media/hdd/.mediaplayer3/playlists/

Original playlist files remain unchanged.

---

# Playlist Export

PlaylistScreen supports playlist export.

Default destination:

/media/hdd/.mediaplayer3/exports/

Export format:

Extended M3U

Export operations are performed by PlaylistManager.

---

# Information Dialog

Playlist information may include:

- Playlist name
- Number of tracks
- Total duration
- File location
- Last modified

Track information may include:

- Title
- Artist
- Album
- Duration
- File path

Information is read from PlaylistManager whenever possible.

---

# Logging

PlaylistScreen shall provide user interface logging.

Typical events:

INFO

Playlist selected

Track selected

Context menu opened

Playlist import requested

Playlist export requested

WARNING

Invalid playlist selected

ERROR

Playlist loading failed

Verbose logging additionally records:

- Navigation events
- Panel changes
- Menu selections

Playlist modifications are logged by PlaylistManager.

---

# Dependencies

PlaylistScreen depends on:

- PlaylistManager
- PlaybackController
- Logger
- SkinManager
- LocalizationManager

PlaylistScreen shall not access playlist files directly.

All playlist operations are delegated to PlaylistManager.

---

# Future Extensions

The following features are outside the scope of Build 0007.

Possible future additions:

- Playlist search
- Playlist sorting
- Drag-and-drop style track reordering
- Dynamic playlists
- Smart playlists
- Playlist artwork
- Playlist statistics

The current screen layout shall allow future expansion without major
navigation changes.

---

# Summary

PlaylistScreen provides a dedicated playlist management interface.

Responsibilities include:

- Playlist browsing
- Track browsing
- Playlist playback
- Playlist import
- Playlist export

All playlist management is delegated to PlaylistManager.

Playback remains the responsibility of PlaybackController.

PlaylistScreen follows the common MediaPlayer3 navigation model used by
BrowserScreen, RadioBrowserScreen and MainScreen.

---

End of PLAYLISTSCREEN_SPEC.md

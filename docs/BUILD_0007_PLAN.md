# BUILD_0007_PLAN.md

MediaPlayer3

Build 0007

Status: Planning

Target Platform:
Enigma2 (OpenViX primary)

Python:
3.13

---

# Overview

Build 0007 focuses on media collections and Internet Radio.

The primary objectives are:

- Playlist management
- Internet Radio support
- Unified media navigation
- Storage management
- Consistent user interface
- Improved user workflow

Build 0007 extends the architecture introduced during Builds 0004,
0005 and 0006 without changing the existing playback model.

PlaybackController remains responsible only for playback.

Media management is delegated to dedicated manager classes.

---

# Design Goals

Build 0007 shall introduce:

- PlaylistManager
- InternetRadioManager
- StorageManager

The user experience shall remain consistent across all media types.

Local music

↓

Playlists

↓

Internet Radio

shall all use the same navigation model.

The application shall remain fully operable using only:

- Direction keys
- OK
- MENU
- EXIT

Color buttons shall not be required for normal operation.

---

# Architecture

Core Layer

- PlaybackController
- PlaylistManager
- InternetRadioManager
- StorageManager
- ConfigurationManager
- LocalizationManager
- SkinManager
- Logger

Screen Layer

- BrowserScreen
- PlaylistScreen
- RadioBrowserScreen
- MainScreen
- PlaybackInfoScreen
- SettingsScreen
- DeveloperScreen

StorageManager provides all application paths.

PlaylistManager owns playlist handling.

InternetRadioManager owns all radio functionality.

PlaybackController owns playback only.

---

# StorageManager

Build 0007 introduces StorageManager.

Responsibilities:

- Create application working directory
- Create required subdirectories
- Validate directory structure
- Recover missing directories
- Verify write permissions
- Provide application paths
- Storage diagnostics

Other modules shall never use hard coded paths.

Example interface:

StorageManager.getPlaylistsPath()

StorageManager.getRadioPath()

StorageManager.getArtworkPath()

StorageManager.getCachePath()

StorageManager.getLogsPath()

StorageManager.getImportsPath()

StorageManager.getExportsPath()

StorageManager.getBackupsPath()

StorageManager.getUserDataPath()

---

# Working Directory

MediaPlayer3 stores all application data inside a dedicated hidden
working directory.

Default location:

/media/hdd/.mediaplayer3/

Directory layout:

.mediaplayer3/

    playlists/

    radio/

    artwork/

    cache/

    logs/

    imports/

    exports/

    backups/

    userdata/

The working directory shall be created automatically during the first
application startup.

Missing directories shall be recreated automatically whenever required.

Application startup shall never fail because a directory is missing.

The userdata directory is reserved for future application features and
is created during initialization although it is not actively used in
Build 0007.

---
# PlaylistManager

Build 0007 introduces PlaylistManager.

PlaylistManager owns all playlist management.

Responsibilities:

- Create playlists
- Delete playlists
- Rename playlists
- Import playlists
- Export playlists
- Load playlists
- Save playlists
- Add folders
- Add tracks
- Remove tracks
- Move tracks
- Validate playlist entries

PlaybackController shall never modify playlists directly.

PlaylistManager prepares playback queues for PlaybackController.

---

# Playlist Storage

MediaPlayer3 stores playlists inside the application working directory.

Default location:

/media/hdd/.mediaplayer3/playlists/

Playlist format:

Extended M3U

Example:

#EXTM3U

#EXTINF:355,Queen - Bohemian Rhapsody
/media/hdd/music/Rock/Queen/Bohemian Rhapsody.flac

#EXTINF:285,Europe - The Final Countdown
/media/hdd/music/Rock/Europe/The Final Countdown.flac

Absolute file paths shall be used.

Extended M3U provides maximum compatibility with external music
players.

---

# Browser Integration

BrowserScreen integrates directly with PlaylistManager.

Folders:

OK

↓

Play Folder

Add Folder to Playlist

Create Playlist

Cancel

Audio files:

OK

↓

Play

Add to Playlist

Information

Cancel

Playlist files:

OK

↓

Play Playlist

Import Playlist

Information

Cancel

Playlist creation shall never modify the original music directory.

---

# PlaylistScreen

PlaylistScreen provides playlist management.

Screen layout:

Playlists

↓

Tracks

LEFT / RIGHT

Switch active panel.

UP / DOWN

Move inside active panel.

OK

Open context menu.

MENU

Playlist options.

EXIT

Return to previous screen.

PlaylistScreen follows the same navigation model used by
BrowserScreen and RadioBrowserScreen.

---

# Playlist Context Menu

Playlist:

- Play
- Rename
- Delete
- Export
- Information
- Cancel

Track:

- Play
- Remove
- Move Up
- Move Down
- Information
- Cancel

Folder:

- Play Folder
- Add Folder to Playlist
- Create Playlist
- Cancel

All playlist operations shall be available through the OK button.

---

# Playlist Collections

MediaPlayer3 supports multiple playlists.

Examples:

Favorites

Rock

Jazz

Classical

Christmas

Workout

Travel

Users may freely create, rename and delete playlists.

The number of playlists is not limited by the application.

---

# Playlist Import

PlaylistManager supports importing existing playlists.

Supported formats:

- Extended M3U
- Standard M3U

Imported playlists are copied into:

/media/hdd/.mediaplayer3/playlists/

Original playlists remain unchanged.

---

# Playlist Export

Playlists may be exported.

Export destination:

/media/hdd/.mediaplayer3/exports/

Export format:

Extended M3U

Exported playlists remain fully compatible with external media players.

---
# InternetRadioManager

Build 0007 introduces InternetRadioManager.

InternetRadioManager owns all Internet Radio functionality.

Responsibilities:

- RadioBrowser API communication
- Station search
- Station filtering
- Favorites management
- History management
- Playback preparation
- Station metadata
- Stream information
- Search caching

PlaybackController receives only the final stream URL.

All RadioBrowser communication shall remain internal to
InternetRadioManager.

---

# RadioBrowser Integration

MediaPlayer3 uses the RadioBrowser API.

RadioBrowser provides:

- Station database
- Search
- Country information
- Language information
- Tags
- Codec
- Bitrate
- Homepage
- Station metadata

MediaPlayer3 shall not maintain its own online station database.

Only user generated data shall be stored locally.

---

# RadioBrowserScreen

RadioBrowserScreen provides Internet Radio browsing.

Screen layout:

Stations

↓

Region

↓

Language

LEFT / RIGHT

Switch active panel.

UP / DOWN

Move inside active panel.

OK

Open context menu.

MENU

Screen options.

EXIT

Return to previous screen.

All screen navigation follows the same model used by BrowserScreen
and PlaylistScreen.

---

# Search

Station search supports:

- Station name
- Country
- Language
- Tags

Region and Language panels provide additional search filters.

Search results are automatically filtered using the currently selected
Region and Language.

Search filters may be configured from application settings.

Default values should follow the receiver language and region whenever
possible.

---

# Station Information

Selecting a station displays detailed information in the information
panel.

Typical information:

- Station name
- Country
- Language
- Tags
- Codec
- Bitrate
- Homepage
- Votes
- Last check status

The information panel updates automatically when the selected station
changes.

---

# Station Context Menu

OK

↓

Play

Add to Favorites

Create Favorite List

Station Information

Cancel

All station operations shall be available through the OK button.

---

# Favorite Lists

MediaPlayer3 supports multiple favorite lists.

Examples:

General

Finnish

Rock

Jazz

Classical

Christmas

Users may freely create, rename and delete favorite lists.

Favorites are stored locally.

---

# History

InternetRadioManager maintains a listening history.

History stores recently played stations.

History is independent from favorite lists.

History may be cleared from Settings.

History navigation may be selected as the default channel navigation
mode.

---

# MainScreen Navigation

Internet Radio playback supports navigation directly from MainScreen.

LEFT / RIGHT

Switch favorite list or history list.

UP / DOWN

Previous station

Next station

The selected navigation mode is configurable from Settings.

RadioBrowserScreen is not required during normal listening.

---
# Logging

Build 0007 extends application logging.

The following components shall provide structured logging:

- PlaylistManager
- InternetRadioManager
- StorageManager

Typical logged events:

Playlist

- Playlist created
- Playlist renamed
- Playlist deleted
- Playlist imported
- Playlist exported
- Track added
- Track removed

Internet Radio

- Search started
- Search completed
- Station selected
- Playback started
- Playback stopped
- Favorite added
- Favorite removed
- History updated

Storage

- Working directory created
- Missing directory recovered
- Import completed
- Export completed

Verbose logging additionally records:

- RadioBrowser requests
- Playlist loading
- Playlist saving
- Search filters
- Station metadata
- Storage diagnostics

---

# User Interface Principles

MediaPlayer3 shall provide a consistent user interface across all
screens.

BrowserScreen

↓

PlaylistScreen

↓

RadioBrowserScreen

↓

MainScreen

↓

SettingsScreen

All screens shall use identical navigation principles.

LEFT / RIGHT

Switch active panel.

UP / DOWN

Move inside current panel.

OK

Open context menu.

MENU

Open screen specific options.

EXIT

Return to previous screen.

Color buttons shall not be required for normal application use.

---

# Acceptance Criteria

Build 0007 is complete when:

✓ Multiple playlists are supported.

✓ Playlist import is functional.

✓ Playlist export is functional.

✓ Folder based playlist creation works.

✓ Track based playlist creation works.

✓ Playlist playback works.

✓ Internet Radio search works.

✓ Region filtering works.

✓ Language filtering works.

✓ Favorite lists work.

✓ History works.

✓ MainScreen station navigation works.

✓ StorageManager creates all required directories.

✓ Application recovers automatically from missing directories.

✓ BrowserScreen, PlaylistScreen and RadioBrowserScreen share a common
navigation model.

✓ Structured logging covers all new components.

---

# Documentation

New documents:

BUILD_0007_PLAN.md

PLAYLIST_MANAGER_SPEC.md

INTERNETRADIO_MANAGER_SPEC.md

STORAGE_MANAGER_SPEC.md

PLAYLISTSCREEN_SPEC.md

RADIOBROWSER_SCREEN_SPEC.md

Updated documents:

ARCHITECTURE.md

LOGGER_SPEC.md

CONFIG_SPEC.md

DEVELOPMENT_GUIDE.md

PROJECT_STRUCTURE.md

HISTORY.md

CHANGELOG.md

---

# Build 0008 Preview

Possible future features:

- Dynamic playlists
- Lyrics integration
- Online artwork providers
- Podcast support
- UPnP media sources
- DLNA browsing
- Cloud playlist synchronization
- Advanced playlist search
- Smart playlists
- Storage migration support (versioned working directory)

Build 0008 planning begins after Build 0007 has been completed and
stabilized.

---

End of Build 0007 Plan

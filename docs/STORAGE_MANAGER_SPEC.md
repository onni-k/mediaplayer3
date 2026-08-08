# STORAGE_MANAGER_SPEC.md

MediaPlayer3

Build 0007

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

StorageManager is responsible for all MediaPlayer3 application storage.

StorageManager provides a centralized interface for application
directories and storage related operations.

Other modules shall never use hard coded filesystem paths.

StorageManager is initialized during application startup before other
manager classes.

---

# Responsibilities

StorageManager shall provide:

- Working directory creation
- Directory validation
- Missing directory recovery
- Write permission verification
- Application path services
- Storage diagnostics

StorageManager shall never store application specific data.

Its responsibility is limited to storage infrastructure.

---

# Working Directory

MediaPlayer3 stores all application data inside a dedicated hidden
working directory.

Default location:

/media/hdd/.mediaplayer3/

Directory structure:

playlists/

radio/

artwork/

cache/

logs/

imports/

exports/

backups/

userdata/

StorageManager shall automatically create missing directories.

Application startup shall continue whenever recovery is possible.

---

# Directory Initialization

During initialization StorageManager shall:

1. Verify working directory.

2. Create working directory if missing.

3. Verify required subdirectories.

4. Create missing subdirectories.

5. Verify write permissions.

6. Report initialization status.

Initialization failures shall be written to the application log.

---

# Public Interface

StorageManager provides path accessors.

Typical interface:

getWorkingDirectory()

getPlaylistsPath()

getRadioPath()

getArtworkPath()

getCachePath()

getLogsPath()

getImportsPath()

getExportsPath()

getBackupsPath()

getUserDataPath()

Returned paths shall always be validated before use.

---

# Directory Responsibilities

playlists/

Stores user playlist files.

radio/

Stores Internet Radio favorites, history and cache.

artwork/

Stores downloaded artwork cache.

cache/

Stores temporary application cache.

logs/

Stores application log files.

imports/

Temporary location for imported playlists.

exports/

Default location for exported playlists.

backups/

Stores automatic and manual backups.

userdata/

Reserved for future user specific application data.

---
# Storage Recovery

StorageManager shall automatically recover missing directories.

Example:

Application startup

↓

Missing cache/

↓

Create cache/

↓

Write log entry

↓

Continue startup

Application startup shall not fail because a recoverable directory is
missing.

---

# Validation

StorageManager validates:

- Working directory exists
- Required directories exist
- Directory permissions
- Read access
- Write access

Validation failures shall be reported through Logger.

Whenever possible StorageManager shall recover automatically.

---

# Logging

StorageManager shall provide structured logging.

Typical events:

INFO

Working directory created

Directory created

Directory verified

Initialization completed

WARNING

Directory missing

Directory recreated

Write permission limited

ERROR

Working directory unavailable

Directory creation failed

Initialization failed

Verbose logging additionally records:

- Path validation
- Permission checks
- Directory recovery
- Storage diagnostics

---

# Dependencies

StorageManager depends on:

- Logger

StorageManager shall not depend on:

- BrowserScreen
- PlaylistScreen
- RadioBrowserScreen
- PlaybackController
- PlaylistManager
- InternetRadioManager

Other managers may depend on StorageManager.

---

# Future Extensions

The following features are outside the scope of Build 0007.

Possible future additions:

- Storage version management
- Automatic storage migration
- Multiple storage locations
- External storage selection
- Storage usage statistics
- Automatic cleanup policies
- Cache size management
- Backup scheduling

Storage version information shall not be introduced until a future
build requires directory structure migration.

Systems without version information shall be interpreted as using the
original Build 0007 storage layout.

---

# Summary

StorageManager provides the storage infrastructure used by
MediaPlayer3.

Responsibilities include:

- Working directory management
- Directory creation
- Directory validation
- Path services
- Storage diagnostics

StorageManager never stores application specific data.

This separation keeps storage management independent from playback,
playlists and Internet Radio functionality.

---

End of STORAGE_MANAGER_SPEC.md

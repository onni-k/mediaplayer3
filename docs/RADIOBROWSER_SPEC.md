# RADIOBROWSER_SPEC.md

MediaPlayer3

RadioBrowser Specification

Status: Build 0010 CONFIRMED COMPLETE (device test rounds 11, 12, 14
-- OpenViX, Vu+ Duo2)

---

# Purpose

RadioBrowser provides access to Internet Radio station information and
local station storage for MediaPlayer3.

The RadioBrowser implementation separates external RadioBrowser service
communication from local station management and presentation.

---

# Local Station Database

MediaPlayer3 shall maintain a local copy of available radio stations.

The local database is used to:

- Provide stations when the network is unavailable.
- Reduce unnecessary requests to the external RadioBrowser service.
- Preserve the user's available station list between sessions.
- Provide predictable browser behaviour.

The local database shall contain the station information required by
MediaPlayer3 for browsing and playback.

---

# Database Update

The local station database shall be updated when:

- No stations are available.
- The user selects "Update database".
- The configured automatic update interval has expired.

The default automatic update interval may be seven days.

A normal update shall not remove existing stations before new station
data has been successfully obtained.

If an update fails, the existing local station database shall remain
available.

---

# Manual Update

The user shall be able to start a database update manually.

Reachable via RadioBrowserScreen's own Stations-column OK menu
("Update stations" -- device test round 12, moved there from
SettingsScreen's colour buttons per direct user request, since
RADIOBROWSER_SCREEN_SPEC.md's own "Color buttons shall not be
required" already applied). "Clear station list" (see "Database
Integrity" below) lives in the same menu.

The update operation shall:

1. Contact the configured RadioBrowser service.
2. Retrieve available station information.
3. Validate the received data.
4. Update the local database.
5. Preserve the existing database if the update fails.

The user shall receive appropriate feedback about the result of the
operation.

---
# Automatic Updates

The RadioBrowser database may be updated automatically.

The update interval shall be configurable where appropriate.

The default interval may be seven days.

An automatic update shall not interrupt active playback.

If the update fails, the current local station database shall remain
unchanged.

Automatic updates shall not repeatedly retry in a tight loop.

---

# Station Data

The local station database may contain:

- Station name
- Station UUID
- Stream URL
- Homepage URL
- Favicon
- Country
- Country code
- Region
- Language
- Tags
- Codec
- Bitrate
- Station status

Not all fields are required for a station to be usable.

A station shall be considered playable when a valid stream URL is
available.

Missing optional station information shall not prevent playback.

---

# Language and Region Filters

The Radio browser shall allow the user to filter stations by:

- Language
- Region

The selected filter values shall be used when presenting available
stations.

Filters shall not modify or delete the underlying local station
database.

Clearing a filter shall restore the broader station list.

---

# Station Selection

Selecting a station shall make it the current radio station.

The station may then be:

- Played
- Added to Favorites

Radio stations are added to Favorites, never to the local file
playlist system (device test round 14 -- correcting an earlier
Build 0010 draft that briefly added a station's stream URL to a local
playlist instead; "General" and any other favorite list a user creates
are the correct, and only, target).

Playback shall use the existing MediaPlayer3 playback architecture.

RadioBrowser shall not implement audio playback.

---

# Favorites

Favorites shall be managed separately from the RadioBrowser station
database.

Updating RadioBrowser data shall not automatically remove user
favorites.

If a favorite station is no longer present in the external RadioBrowser
database, the favorite may remain locally stored until the user removes
it.

---
# Error Handling

RadioBrowser shall handle external service and local database failures
without terminating MediaPlayer3.

Possible conditions include:

- Network unavailable
- RadioBrowser service unavailable
- Request timeout
- Invalid response
- Invalid station data
- Database read failure
- Database write failure
- Empty station list

Errors shall be logged through the existing MediaPlayer3 logging
system.

The user shall receive an appropriate message where user action is
required.

---

# Empty Database

If no local stations are available, MediaPlayer3 shall inform the user.

The user may be offered the option to download the RadioBrowser station
database again.

If the download fails, MediaPlayer3 shall remain operational.

---

# Database Integrity

A failed database update shall not leave the existing station database
in an unusable state.

Updates should preferably be written to a temporary location before
replacing the active database.

If the new database cannot be validated or written successfully, the
previous valid database shall remain available.

---

# Service Selection

The implementation may use an available RadioBrowser API server.

The selected server shall be configurable where appropriate.

Temporary failure of one server should not automatically result in loss
of the local station database.

---

# Logging

RadioBrowser operations shall use the MediaPlayer3 logging system.

Useful diagnostic information may include:

- Operation
- Server
- Request result
- Number of stations received
- Database operation
- Error type
- Error description
- Timestamp

Sensitive information shall not be written to normal logs.

---

# Design Principles

RadioBrowser separates:

- External station service communication
- Local station database
- Station filtering
- Favorites
- User interface
- Playback

RadioBrowser shall provide station data to the appropriate MediaPlayer3
components.

It shall not:

- Implement audio playback.
- Directly manipulate MainScreen.
- Directly manipulate BrowserScreen presentation.
- Remove Favorites as a side effect of database updates.

The local station database is a cache and operational data source, not
the source of truth for user Favorites.

This separation allows Internet Radio to remain usable even when the
external RadioBrowser service is temporarily unavailable.

---

End of RADIOBROWSER_SPEC.md

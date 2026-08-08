# INTERNETRADIO_MANAGER_SPEC.md

MediaPlayer3

Build 0007

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

InternetRadioManager is responsible for all Internet Radio functionality
inside MediaPlayer3.

InternetRadioManager manages station discovery, favorites, history,
stream preparation and RadioBrowser communication.

PlaybackController is responsible only for media playback.

InternetRadioManager prepares radio streams for PlaybackController.

---

# Responsibilities

InternetRadioManager shall provide:

- RadioBrowser communication
- Station search
- Station filtering
- Station metadata
- Favorite list management
- Listening history
- Stream URL preparation
- Search caching
- Station validation

InternetRadioManager shall never perform media playback.

---

# RadioBrowser Integration

MediaPlayer3 uses the public RadioBrowser API.

InternetRadioManager encapsulates all API communication.

Other application components shall never access the RadioBrowser API
directly.

Server Discovery (confirmed on a real device, Build 0007 test round 1)

The plain "api.radio-browser.info" hostname does not serve API
requests directly -- every request against it returns HTTP 404.

RadioBrowser requires resolving "all.api.radio-browser.info" via DNS
and reverse-resolving each returned IP to an actual mirror hostname
(e.g. "de1.api.radio-browser.info"), then calling one of those
mirrors. This matches the official API documentation, the pyradios
reference project, and the serverlist_python3.py example script
(checked per user request after the real-device failure).

InternetRadioManager discovers mirrors once per process lifetime and
retries each discovered mirror in turn if one fails, caching whichever
mirror last answered successfully so subsequent requests try it
first.

Supported API functionality includes:

- Station search
- Country information
- Language information
- Tags
- Codec
- Bitrate
- Homepage
- Votes
- Stream URL
- Station metadata

InternetRadioManager may cache search results locally.

---

# Local Storage

Internet Radio data is stored inside:

/media/hdd/.mediaplayer3/radio/

Typical files:

favorites.json

history.json

search_cache.json

Only user generated information is stored locally.

Station information is always obtained from RadioBrowser.

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

Users may:

- Create lists
- Rename lists
- Delete lists
- Reorder stations

Favorite lists are independent from RadioBrowser.

---

# History

InternetRadioManager maintains listening history.

History stores:

- Station name
- Stream URL
- Timestamp
- Favorite list (optional)

History size is configurable.

History may be cleared from Settings.

---
# Search

InternetRadioManager supports searching by:

- Station name
- Country
- Language
- Tags

Search filters may be combined.

Example:

Station Name

↓

rock

+

Country

↓

Finland

+

Language

↓

Finnish

↓

Filtered search results

Default Country and Language values should follow receiver settings
whenever possible.

---

# Stream Preparation

InternetRadioManager prepares playback streams.

Preparation includes:

- Validate station
- Obtain stream URL
- Retrieve station metadata
- Verify stream availability (optional)

PlaybackController receives only the final validated stream URL.

---

# Favicon (Build 0007, device test round 3)

InternetRadioManager.downloadFavicon(favicon_url) downloads and
caches a station's favicon image, for MainScreen to display as cover
art while that station plays ("MainScreen -näkymässä Voisi laittaa
kuvakkeeksi radiokanavan kuvakkeen, jos on saatavilla").

Cached under StorageManager.getCachePath(), keyed by a hash of the
URL so the same station's icon isn't re-downloaded every time it
plays.

Never raises; returns None on any failure (empty URL, network error,
write failure, or a "null"-ish sentinel string -- see Device test
round 4 below), so MainScreen falls through to the next artwork
priority level exactly the same way a missing embedded/folder artwork
already does for local files.

Not yet verified against a real network connection -- favicon URLs
are hosted by individual stations rather than RadioBrowser itself, so
their reachability/format can vary far more widely than RadioBrowser's
own API endpoints (which device test round 1 already confirmed do
work).

Device test round 4: a real device log captured an actual CRASH here
(the whole enigma2 process exited). RadioBrowser returned the literal
string "null" for a station's favicon field, rather than JSON
null/empty -- that string is truthy in Python, so it passed a plain
`if not favicon_url` check and reached urllib.request.Request(),
which raised an uncaught ValueError ("unknown url type: 'null'").
Fixed with a shared _cleanUrlField() helper that rejects
"null"/"none"/"n/a" (case-insensitive) in addition to empty values,
applied to downloadFavicon() and, as defense in depth, to
prepareStream()'s url/url_resolved fields too, since they come from
the same API and could plausibly have the same quirk.

---

# Validation

InternetRadioManager validates stations before playback.

Validation includes:

- Stream URL available
- Station metadata available
- Supported protocol
- Duplicate handling

Invalid stations shall be skipped whenever possible.

Validation failures shall be written to the application log.

---

# Logging

InternetRadioManager shall provide structured logging.

Typical events:

INFO

Search started

Search completed

Station selected

Playback requested

Favorite added

Favorite removed

Favorite list created

Favorite list deleted

History updated

WARNING

Station unavailable

Stream validation failed

ERROR

RadioBrowser request failed

Station playback preparation failed

Verbose logging additionally records:

- RadioBrowser requests
- API responses
- Search filters
- Metadata loading
- Cache operations
- Stream preparation

---

# Dependencies

InternetRadioManager depends on:

- StorageManager
- Logger
- ConfigurationManager

PlaybackController depends on InternetRadioManager only for validated
stream preparation.

InternetRadioManager shall not depend on BrowserScreen,
RadioBrowserScreen or PlaybackController implementation details.

---

# Future Extensions

The following features are outside the scope of Build 0007.

Possible future additions:

- Podcast support
- User defined stations
- Multiple RadioBrowser servers
- Automatic station quality selection
- Station logo download
- Online artwork
- Sleep timer integration
- Cloud synchronized favorites

The current architecture shall allow future expansion without
incompatible interface changes.

---

# Summary

InternetRadioManager provides a dedicated Internet Radio subsystem.

Responsibilities include:

- RadioBrowser communication
- Station search
- Favorite management
- Listening history
- Stream preparation

Playback remains the responsibility of PlaybackController.

This separation follows the MediaPlayer3 architecture introduced in
Build 0004 and extended during Builds 0005, 0006 and 0007.

---

End of INTERNETRADIO_MANAGER_SPEC.md

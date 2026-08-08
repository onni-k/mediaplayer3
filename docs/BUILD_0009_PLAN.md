# BUILD_0009_PLAN.md

MediaPlayer3

Build 0009 Development Plan

Status

Planning

Target Version

0.9.0-dev

---

# Theme

MainScreen 2.0 and Radio EPG

Build 0009 focuses on improving usability while preserving the modular
architecture introduced during previous builds.

Rather than introducing major new playback functionality, this build
concentrates on making existing features easier to access through a
single unified MainScreen.

The same user interface shall support:

- Local music
- Playlists
- Music Library
- Internet Radio

Only the Information Panel content changes according to the currently
playing media.

---

# Primary Goals

The primary objectives of Build 0009 are:

- Redesign MainScreen
- Introduce Information Panel
- Improve playlist navigation
- Integrate Radio EPG
- Improve remote-control usability
- Preserve compatibility with all supported Enigma2 distributions

No major architectural redesign is planned.

Existing managers remain responsible for their respective functional
areas.

---

# MainScreen 2.0

The MainScreen will be reorganized into three primary areas.

```
+------------------------------------------------------------+
| Album Art | Artist - Album                                 |
|           | Current Song                                   |
+-----------+------------------------------------------------+
| Playlist  | Information                                    |
|           |                                                |
| Previous  |                                                |
| Current   |                                                |
| Next      |                                                |
|           |                                                |
|           |                                                |
|           |                                                |
|           |                                                |
+------------------------------------------------------------+
| Progress Bar                                               |
+------------------------------------------------------------+
```

The redesigned layout provides significantly more vertical space for
the Information Panel while maintaining a compact overview of the
currently playing media.

Album Art remains permanently visible.

Progress Bar is moved to the bottom of the screen.

---
# Playlist Panel

The Playlist Panel becomes an active navigation area rather than a
simple preview.

The panel displays:

- Previous
- Current
- Next

The currently playing item remains highlighted.

Playlist mode allows the user to browse the active playlist without
opening PlaylistScreen.

Controls:

UP / DOWN

Move between playlist entries.

LEFT / RIGHT

Change active playlist.

OK

Begin playback from the selected entry.

The selected entry immediately becomes the new PlaybackQueue position.

Playback continues normally through the remaining playlist.

---

# Information Panel

The previous Lyrics area is replaced by a generic Information Panel.

The Information Panel dynamically displays available information
depending on the current playback source.

Possible information types include:

- Lyrics LRC
- Lyrics Embedded
- Lyrics TXT
- Metadata
- Codec
- Now Playing
- Radio EPG
- Station Information

Only information types containing useful data are included.

Empty information pages are never shown.

The title always identifies the current information source.

Examples:

Information: Lyrics LRC

Information: Lyrics Embedded

Information: Metadata

Information: Codec

Information: Radio EPG

Information: Station

This provides a consistent user experience regardless of the playback
source.

---

# Player Mode

Player Mode remains optimized for playback control.

The Progress Bar becomes the active control.

LEFT / RIGHT

Seek backward / forward.

UP / DOWN

Previous / Next track.

CH+ / CH-

Previous / Next track.

The playback controls remain identical for local music and Internet
Radio whenever applicable.

---
# Active Panel Navigation

The EPG / INFO button selects the active panel.

The active panel cycles in the following order:

Player

↓

Playlist

↓

Information

↓

Player

Only one panel is active at a time.

The active panel title is highlighted using the current skin's active
selection color.

Each panel receives its own navigation controls.

---

# Information Panel Behaviour

The Information Panel automatically builds its list of available pages.

Unavailable information types are omitted.

Example:

Local music with synchronized lyrics:

- Information: Lyrics LRC
- Information: Metadata
- Information: Codec

Local music without lyrics:

- Information: Metadata
- Information: Codec

Internet Radio:

- Information: Radio EPG
- Information: Now Playing
- Information: Station
- Information: Codec

LEFT / RIGHT switches between available information pages.

UP / DOWN scrolls the currently displayed information.

The user never encounters empty information pages.

---

# Help System

HELP always opens context-sensitive documentation.

Examples:

Player Panel

↓

PLAYER_HELP.md

Playlist Panel

↓

PLAYLIST_HELP.md

Information Panel

↓

INFORMATION_HELP.md

BrowserScreen

↓

BROWSER_HELP.md

MusicLibraryScreen

↓

MUSICLIBRARY_HELP.md

The HelpManager automatically selects the appropriate documentation
according to the currently active screen and panel.

---

# Radio EPG

Build 0009 introduces Radio EPG integration.

EPGManager remains provider-based.

Initially supported providers include:

- YLE Radio
- Bauer Media Finland

Additional providers may be added without modifying MainScreen.

The Information Panel displays Radio EPG whenever programme information
is available.

When programme information is unavailable, Information Panel
automatically falls back to other available information.

---
# Architecture

Build 0009 preserves the architecture introduced in previous builds.

No redesign of PlaybackController is planned.

Existing managers continue to operate independently.

New functionality is introduced through:

- MainScreen enhancements
- Information Panel
- EPGManager integration

The Information Panel acts as a unified presentation layer for playback
information regardless of the underlying data source.

---

# Documentation

New documentation:

- BUILD_0009_PLAN.md
- INFORMATION_PANEL_SPEC.md

Updated documentation:

- MAINSCREEN_SPEC.md
- EPG_MANAGER_SPEC.md
- ARCHITECTURE.md
- PROJECT_STRUCTURE.md
- HISTORY.md
- CHANGELOG.md

Documentation continues to be completed before implementation whenever
practical.

---

# Deferred

The following features remain outside the scope of Build 0009:

- RecordingManager
- Internet Radio recording
- Podcast support
- Online lyrics providers
- Smart playlists
- Listening statistics

These features remain compatible with the current architecture and may
be implemented in future builds without requiring major structural
changes.

---

# Design Philosophy

Build 0009 focuses on improving usability rather than increasing
complexity.

Every new information source should integrate through the Information
Panel whenever practical.

The same MainScreen shall provide a consistent user experience for:

- Local music
- Music Library
- Playlists
- Internet Radio

Only the Information Panel content changes according to the currently
available information.

This approach keeps navigation simple while allowing MediaPlayer3 to
grow through independent managers and providers.

---

End of BUILD_0009_PLAN.md

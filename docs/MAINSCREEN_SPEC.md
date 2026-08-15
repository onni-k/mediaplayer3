# MAINSCREEN_SPEC.md

MediaPlayer3

MainScreen Specification

Status: Build 0010 -- CONFIRMED COMPLETE (OK Menu/PVR changes: device
test rounds 7, 9, 12, 14, on OpenViX and Vu+ Duo2; see
Claude_notes_build0010.txt for the full record). Everything from
Build 0009 below this point remains accurate except where this
document's own "OK" sections (Player Panel) note a Build 0010 change.

---

# Purpose

MainScreen is the primary playback interface of MediaPlayer3.

It provides immediate access to playback controls, playlist navigation
and playback-related information without requiring the user to switch
between multiple screens.

The same MainScreen is used for:

- Local music
- Internet Radio
- Music Library playback
- Playlist playback

Only the Information Panel content changes according to the currently
playing media.

---

# Design Goals

MainScreen shall:

- Present the most important playback information.
- Support remote-control operation using a minimal number of buttons.
- Keep playback controls immediately available.
- Provide direct playlist navigation.
- Display only useful playback information.
- Support future information providers without redesign.

---

# Layout

MainScreen is divided into three primary areas.

```
+------------------------------------------------------------+
| Album Art | Artist - Album                                 |
|           | Song                                           |
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

Album Art remains permanently visible.

Artist and Album share a single line.

Song title occupies the second line.

The complete right side of the screen is reserved for the
Information Panel.

The Progress Bar occupies the bottom of MainScreen.

---

# Active Panels

MainScreen contains three selectable panels.

- Player
- Playlist
- Information

Only one panel is active at any time.

The active panel title is highlighted using the active selection
colour provided by the current Enigma2 skin.

---
# Remote Control

Build 0009 simplifies MainScreen navigation by removing the dependency
on the TEXT button.

The TEXT button is no longer used.

All previous TEXT button functionality has been removed.

The active panel is now selected exclusively using the EPG / INFO
button.

The active panel cycles as follows:

Player

↓

Playlist

↓

Information

↓

Player

Only the currently active panel responds to navigation keys.

This behaviour provides consistent operation across supported Enigma2
receivers, including receivers where the TEXT button is unavailable or
does not generate key events.

---

# Player Panel

Player Panel is responsible for playback control.

When Player Panel is active:

LEFT / RIGHT

Seek backward / forward.

UP / DOWN

Previous / Next track.

CH+ / CH-

Previous / Next track.

OK

Build 0010, BUILD_0010_PLAN.md "MainScreen OK Menu" (device test
rounds 7, 9, 12, 14) -- replaced the previous direct Play/Pause
toggle:

If nothing is currently loaded, opens the startup chooser (Internet
Radio / Local Music / Music Library / Playlists / Podcasts) -- the
same chooser PVR opens (see below).

If something is loaded, opens a small action menu instead:

- Back -- always first. Returns to whichever screen playback was
  started from (Internet Radio / File Browser / Playlists / Podcasts
  / Music Library), tracked internally per source screen; falls back
  to Main Menu if no origin is known yet this session.
- Clear history, Add to Favorites, Remove from Favorites -- only
  while Internet Radio is playing (RADIOBROWSER_SCREEN_SPEC.md
  "MainScreen Integration"). These use the same Favorites mechanism
  as RadioBrowserScreen's own Station Context Menu, never the local
  playlist system.
- Stop/Resume -- a single item whose label and action depend on
  current state (Stop while playing, Resume while paused/stopped).
  Pausing on its own is still handled directly by the dedicated PAUSE
  key, unaffected by this menu.
- Cancel

PVR opens the same startup chooser OK does when nothing is loaded,
regardless of current playback state -- it no longer opens
BrowserScreen directly.

HELP

Open Player Help.

The Progress Bar remains active only while Player Panel is selected.

---

# Playlist Panel

Playlist Panel allows browsing of the current playlist directly from
MainScreen.

Displayed items:

Previous

Current

Next

When Playlist Panel is active:

UP / DOWN

Move playlist selection.

LEFT / RIGHT

Switch active playlist.

OK

Start playback from selected item.

HELP

Open Playlist Help.

The selected playlist entry immediately becomes the current playback
position.

Playback continues through the remaining playlist whenever possible.

---

# Information Panel

Information Panel displays playback-related information supplied by
independent managers.

Examples include:

- Lyrics
- Metadata
- Codec information
- Radio EPG
- Now Playing
- Station information
When Information Panel is active:

LEFT / RIGHT

Switch between available information pages.

UP / DOWN

Scroll the current information page.

HELP

Open Information Panel Help.

OK

No action.

Only information pages containing actual content are available.

Empty information pages are never presented.

---

# Information Sources

Information Panel may present information supplied by:

LyricsManager

- Lyrics LRC
- Lyrics Embedded
- Lyrics TXT

MetadataReader

- Artist
- Album
- Title
- Genre
- Year
- Composer
- Publisher

CodecReader

- Codec
- Bitrate
- Sample Rate
- Channels
- Bit Depth

EPGManager

- Radio EPG
- Now Playing
- Station Information

Additional providers may be integrated without modifying MainScreen.

---

# Help Integration

The HELP button always opens documentation related to the currently
active panel.

Player Panel

↓

PLAYER_HELP.md

Playlist Panel

↓

PLAYLIST_HELP.md

Information Panel

↓

INFORMATION_HELP.md

This behaviour provides consistent context-sensitive help throughout
MediaPlayer3.

---

# Design Principles

MainScreen serves as the central user interface for MediaPlayer3.

Rather than introducing additional windows, new playback-related
information should integrate through the Information Panel whenever
practical.

This approach provides a consistent user experience for:

- Local music
- Internet Radio
- Music Library
- Playlists

while preserving the modular architecture of the application.

---

End of MAINSCREEN_SPEC.md

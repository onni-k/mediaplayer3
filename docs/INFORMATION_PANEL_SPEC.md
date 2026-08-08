# INFORMATION_PANEL_SPEC.md

MediaPlayer3

Information Panel Specification

Status: Build 0009 -- CONFIRMED COMPLETE (13 rounds of real device
testing across OpenViX, OpenPLI, OpenATV and OpenBH; see
CHANGELOG.md's "BUILD 0009 -- CONFIRMED COMPLETE" and
Claude_notes_build0009.txt for the full record).

---

# Purpose

The Information Panel provides a unified area for displaying playback-
related information.

Instead of creating separate user interface areas for lyrics, metadata,
codec information and Radio EPG, all information is presented through a
single reusable panel.

The panel dynamically adapts to the currently playing media.

---

# Design Goals

The Information Panel shall:

- Present only useful information.
- Never display empty pages.
- Remain independent from playback source.
- Support scrolling when required.
- Integrate with MainScreen.
- Support future information providers.

---

# Layout

The Information Panel occupies the complete right side of MainScreen.

```
+-----------------------------------------+
| Information: Lyrics LRC                 |
+-----------------------------------------+
|                                         |
|  Lyrics / Metadata / Codec / EPG        |
|                                         |
|                                         |
|                                         |
|                                         |
|                                         |
|                                         |
|                                         |
+-----------------------------------------+
```

The panel title always indicates the currently displayed information
type.

Examples:

Information: Lyrics LRC

Information: Lyrics Embedded

Information: Lyrics TXT

Information: Metadata

Information: Codec

Information: Radio EPG

Information: Now Playing

Information: Station

---

# Supported Information Types

The Information Panel may display:

Lyrics

- Embedded lyrics
- LRC lyrics
- TXT lyrics

Metadata

- Artist
- Album
- Title
- Genre
- Year
- Composer
- Publisher

Codec Information

- Codec
- Sample rate
- Bitrate
- Channels
- Bit depth

Internet Radio

- Radio EPG
- Now Playing
- Station information

Only information containing actual content is presented.

---
# Page Selection

The Information Panel automatically builds its list of available pages.

Unavailable information types are excluded.

Examples:

Local music with synchronized lyrics:

- Information: Lyrics LRC
- Information: Metadata
- Information: Codec

Local music with embedded lyrics:

- Information: Lyrics Embedded
- Information: Metadata
- Information: Codec

Local music without lyrics:

- Information: Metadata
- Information: Codec

Internet Radio with programme information:

- Information: Radio EPG
- Information: Now Playing
- Information: Station
- Information: Codec

Internet Radio without programme information:

- Information: Now Playing
- Information: Station
- Information: Codec

The user never encounters empty information pages.

---

# Navigation

The Information Panel becomes active when selected using the
EPG / INFO button.

Controls:

UP / DOWN

Scroll current page.

LEFT / RIGHT

Switch between available information pages.

HELP

Open Information Panel help.

OK

No action.

---

# Providers

Information is supplied by independent managers.

Examples:

LyricsManager

- Lyrics

MetadataReader

- Metadata

CodecReader

- Codec Information

EPGManager

- Radio EPG
- Now Playing
- Station Information

The Information Panel remains independent from the implementation of
individual providers.

---

# Design Principles

The Information Panel provides a single presentation layer for all
playback-related information.

Whenever practical, new information sources should integrate through
the Information Panel rather than introducing additional user interface
components.

This approach preserves a consistent user experience while allowing the
application to grow through independent managers and providers.

---

End of INFORMATION_PANEL_SPEC.md

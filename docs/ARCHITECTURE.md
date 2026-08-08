# ARCHITECTURE.md

MediaPlayer3

Architecture Overview

---

# Overview

MediaPlayer3 follows a modular architecture where each component has a
single well-defined responsibility.

Core modules are responsible for business logic.

Controllers coordinate application behaviour.

Screens present information to the user.

Providers retrieve information from external sources.

This separation keeps components independent and simplifies future
development.

Note (Build 0009): this document originally used illustrative naming
("YLE Provider", "Bauer Provider") from the planning stage. It now
reflects the actual implemented module names.

---

# High-Level Architecture

```
                           User Interface

    BrowserScreen      PlaylistScreen      MainScreen
            |                |                 |
            +----------------+-----------------+
                             |
                     PlaybackController
                             |
                      ServiceController
                             |
     +--------------+---------+-----------+--------------+
     |              |         |           |              |
PlaylistManager  LyricsManager LibraryManager InternetRadioManager
     |              |         |           |
     |              |         |           |
 metadata.py    metadata.py   |      EPGManager
 (codec info)   (tags)        |           |
                              |    finland_radio_epg_registry
                              |           |
                              |     Provider Layer
                              |           |
                              |   +-------+--------+
                              |   |                |
                              | Yle Teksti-TV   Bauer/Rayo
                              | (EPGScheduleProvider) (NowPlayingProvider)
                              |
                         Storage (StorageManager)
```

Every Core module performs one specific task.

Communication occurs only through defined interfaces.

No Core module directly manipulates another's internal state.

---

# Layer Responsibilities

## Screens

Screens present information and receive user input.

Screens contain no business logic.

Primary screens include:

- BrowserScreen
- PlaylistScreen
- MainScreen
- MusicLibraryScreen
- RadioBrowserScreen
- SettingsScreen
- DeveloperScreen
- HelpScreen
- PlaybackInfoScreen
- MainMenu

MainScreen serves as the primary playback interface.

---

## Controllers

PlaybackController coordinates playback behaviour.

Responsibilities include:

- Playback state
- Track changes
- Queue progression
- Elapsed/duration tracking (including reconciling a stream's own
  reported position against a wall-clock estimate, when the two
  disagree by more than the stream's own natural drift)
- Communication between screens and Core modules

ServiceController wraps the underlying Enigma2 service reference and
playback primitives (play/pause/resume/stop/seek). It is the only
module that talks to `enigma`/`NavigationInstance` directly for actual
playback control -- everything else that needs to know about the
platform goes through Compatibility instead.

Controllers do not implement user interface functionality.

---

## Core Modules

Core modules implement application business logic.

Current Core modules include:

- PlaylistManager
- LibraryManager
- LyricsManager
- InternetRadioManager
- EPGManager
- finland_radio_epg_registry (Build 0009 -- see Providers, below)
- InformationPanel (Build 0009 -- see MainScreen, below)
- HelpManager
- Storage (StorageManager)
- SkinManager, Logger, Localization, Compatibility (cross-cutting)

Each Core module is responsible for a single functional area.

Core modules communicate only through defined public interfaces --
never by reaching into another module's internals, and never by a
Screen talking to an external data source (a file, a network request,
a config value) directly instead of going through the Core module
that owns it.

---

## Providers

Providers retrieve information from external services.

Current providers (`epg_providers/Finland_radio_epg/`):

- Yle Teksti-TV (`yle_teletext_provider.py`) -- implements
  `EPGScheduleProvider`: current + upcoming programmes, for Yle Radio
  1/YleX/Radio Suomi/Vega/X3M. The only Yle API still open to the
  public (their purpose-built programme API was deprecated in 2021).
- Bauer Media/Rayo (`bauer_nowplaying_provider.py`) -- implements
  `NowPlayingProvider`: current track only (no official API exists;
  reads a station's own rayo.fi page's embedded state instead), for
  all 18 of Bauer's published Finnish stations.

Providers are accessed exclusively through EPGManager, which exposes
two provider interfaces -- `EPGScheduleProvider` (schedule/upcoming
programmes) and `NowPlayingProvider` (current track) -- a station may
have either, both, or neither registered; EPGManager falls back to
generic ICY stream tags for now-playing when no `NowPlayingProvider`
is registered.

`finland_radio_epg_registry` sits between a real, playing
RadioBrowser station and the providers above: RadioBrowser identifies
stations by an opaque stationuuid known only once a station is
actually selected, so this module matches by normalized station name
instead (best-effort -- see EPG_MANAGER_SPEC.md's own notes on
matching reliability) and registers the right provider(s) for that
station's real stationuuid.

Additional providers (for other broadcasters, or other countries) may
be added without affecting MainScreen, InformationPanel or EPGManager
-- following the same pattern, in their own subfolder under
`epg_providers/`.

---

# Information Flow

Playback information flows through independent Core modules before
reaching the user interface.

```
Internet Radio station selected
        |
        v
InternetRadioManager (resolves/prepares the stream)
        |
        v
finland_radio_epg_registry (matches station -> provider, by name)
        |
        v
    EPGManager (holds the registered provider(s))
        |
        v
  InformationPanel (builds the Radio EPG / Now Playing pages)
        |
        v
   MainScreen
```

Local playback follows a similar structure: LyricsManager and
PlaybackController's own metadata/codec accessors feed
InformationPanel directly (no EPGManager or provider involved, since
there's no external service to query for a local file).

---

# MainScreen

MainScreen acts as the central playback interface of MediaPlayer3.

Rather than creating separate user interface areas for individual
information sources, MainScreen delegates presentation to the
Information Panel (`information_panel.py`, InformationPanel).

The MainScreen is divided into three functional panels:

- Player (default)
- Playlist
- Information

The active panel is selected using the EPG / INFO button. While
playing Internet Radio specifically, the Playlist panel is skipped in
this cycle (Player <-> Information only) -- LEFT/RIGHT on the Player
panel covers switching favourite lists for radio instead, since
seeking never applied to a live stream anyway. The Playlist panel's
own display (Previous/Current/Next) still keeps updating in the
background regardless of whether it's reachable via the cycle.

Navigation keys operate only on the currently active panel, and their
meaning changes with it (e.g. LEFT/RIGHT seeks on the Player panel for
local files, but switches pages on the Information panel).

InformationPanel builds its page list dynamically -- Lyrics/Metadata/
Codec for local files, Radio EPG/Now Playing/Station/Codec for
Internet Radio -- showing only pages that actually have content,
rather than a fixed set of views.

This approach provides a consistent remote-control experience while
keeping the interface compact.

---

# Design Principles

MediaPlayer3 follows several architectural principles.

Single Responsibility

Each Core module performs one clearly defined task.

Separation of Concerns

Business logic remains inside Core modules.

Presentation remains inside screens.

Loose Coupling

Core modules communicate only through public interfaces.

Extensibility

New providers and Core modules may be added without redesigning
existing components.

Unified Information Presentation

Playback-related information is presented through the Information
Panel whenever practical rather than introducing additional user
interface elements.

Documentation First

Architecture and specifications are completed before implementation
whenever practical; finalized once a build is confirmed complete
across real device testing.

Prefer the Provably Reliable Over the Merely Elegant

When an Enigma2 API's exact behaviour can't be verified without real
hardware, prefer whatever mechanism is already confirmed working
elsewhere in this codebase over a technically cleaner but unverified
alternative. Two real, confirmed examples from Build 0009: an
Enigma2-standard `onLayoutFinish` callback (the textbook-correct way
to defer a widget-instance access until a screen's skin is applied)
caused a startup crash, root-caused via a real device log's exact
timing match and fixed by falling back to the project's own
already-proven `eTimer`-based deferral pattern instead. Separately,
MainScreen's own generated skin XML must be parsed with
`xml.etree.ElementTree` before shipping any change to it -- a
malformed-XML Python f-string compiles and runs perfectly well from
Python's own point of view (a second real, confirmed startup crash:
two skin comments used "--", which is illegal anywhere inside an XML
comment except its own closing "-->", and nothing in this project's
own stub-based testing could have caught it).

---

# Summary

The Build 0009 architecture extends the modular design introduced in
earlier builds while preserving compatibility with existing playback
components.

The introduction of the Information Panel and provider-based Radio EPG
support improves usability without increasing architectural complexity.

Future functionality can be integrated through additional Core modules
or providers while maintaining the same user interface principles.

---

End of ARCHITECTURE.md

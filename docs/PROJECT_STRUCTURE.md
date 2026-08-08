# PROJECT_STRUCTURE.md

MediaPlayer3

Project Structure

---

# Design Philosophy

The project is organised according to functional responsibility rather
than physical file location whenever practical.

Each manager owns one functional area.

Screens remain responsible only for user interface presentation.

Providers isolate external information sources.

This separation simplifies testing, maintenance and future
development.

Note (Build 0009): this document originally described an idealized,
planning-stage structure (e.g. `playbackcontroller.py`,
`providers/yle_provider.py`). It now reflects the actual, implemented
file names and layout -- real names differ in a few places
(underscored, e.g. `playback_controller.py`; providers nested one
level deeper, under `epg_providers/Finland_radio_epg/`, to leave room
for future non-Finnish provider groups without renaming these).

---

# High-Level Structure

```
MediaPlayer3/

    plugin.py
    project.py
    version.py

    browserscreen.py
    mainscreen.py
    playlistscreen.py
    musiclibraryscreen.py
    radiobrowserscreen.py
    settingsscreen.py
    developer_screen.py
    help_screen.py
    playbackinfo_screen.py
    mainmenu.py

    playback_controller.py
    service_controller.py
    information_panel.py

    playlist_manager.py
    library_manager.py
    lyrics_manager.py
    internetradio_manager.py
    epg_manager.py
    finland_radio_epg_registry.py
    help_manager.py
    storage.py

    epg_providers/
        __init__.py
        Finland_radio_epg/
            __init__.py
            yle_teletext_provider.py
            bauer_nowplaying_provider.py
            README.md

    metadata.py
    compatibility.py
    skin.py
    config.py
    localization.py
    logger.py
    statusbar.py
    constants.py
    features.py
    paths.py
    systeminfo.py

    resources/
        help/
        icons/
        themes/
        locale/

docs/
```

The physical directory structure may evolve while preserving the same
logical architecture.

---

# Screens

BrowserScreen

Browse storage devices and create playback queues.

MainScreen

Primary playback interface -- three navigable panels (Player/
Playlist/Information), see MAINSCREEN_SPEC.md and
INFORMATION_PANEL_SPEC.md (Build 0009).

PlaylistScreen

Playlist management.

MusicLibraryScreen

Music Library navigation.

RadioBrowserScreen

Internet Radio station search and favourites (RadioBrowser API).

SettingsScreen

Application configuration.

DeveloperScreen

Diagnostics and internal state inspection.

HelpScreen

Context-sensitive documentation -- generic scrollable document
viewer, reused by every screen's own HELP key.

PlaybackInfoScreen

Detailed current-track information (reachable from Main Menu).

MainMenu

Application entry point / top-level navigation.

---

# Controllers

PlaybackController coordinates playback behaviour (queue position,
elapsed/duration tracking, seeking, Automatic Next Track).

ServiceController wraps the underlying Enigma2 service reference and
playback primitives (play/pause/resume/stop/seek) -- the only module
that talks to `enigma`/`NavigationInstance` directly for actual
playback control; everything else goes through `compatibility.py`.

Controllers contain no presentation logic.

---

# Core Modules

Core modules implement application business logic, independent of any
specific Screen.

Current Core modules:

- PlaybackController / ServiceController (playback)
- InformationPanel (Build 0009 -- builds MainScreen's Information
  Panel page list; see below)
- PlaylistManager
- LibraryManager
- LyricsManager
- InternetRadioManager
- EPGManager
- HelpManager
- Storage (StorageManager)
- SkinManager (`skin.py`)
- Logger, Localization, Compatibility (cross-cutting)

Core modules remain independent and communicate only through public
interfaces -- a Screen never talks to an external data source (a file,
a network API, a config file) directly; it always goes through the
Core module that owns that responsibility.

---

# InformationPanel (Build 0009)

Owns MainScreen's Information Panel: builds a list of "pages" from
whatever the current track or station actually has (never an empty
page), tracks which page is selected and how far it's scrolled, and
formats each page's content. Consumes existing Core modules
(LyricsManager, PlaybackController's own metadata/codec accessors,
EPGManager) -- it originates no data of its own.

See INFORMATION_PANEL_SPEC.md for the full specification.

---

# EPG Providers (Build 0009)

Providers retrieve radio schedule/now-playing information from
external services, each isolated behind EPGManager's own
`EPGScheduleProvider`/`NowPlayingProvider` interfaces so EPGManager
and MainScreen never depend on a specific provider's own
implementation details.

Current providers (`epg_providers/Finland_radio_epg/`):

- `yle_teletext_provider.py` -- Yle's Teksti-TV API (schedule data:
  current + upcoming programmes). Covers Yle Radio 1/YleX/Radio
  Suomi/Vega/X3M.
- `bauer_nowplaying_provider.py` -- Bauer Media/Rayo Finland (now-
  playing only, read from each station's own web page). Covers all 18
  of Bauer's published Finnish stations.

`finland_radio_epg_registry.py` is the piece that matches a real,
playing RadioBrowser station to one of the providers above (by
normalized station name -- RadioBrowser's own stationuuid can't be
known in advance) and registers it with EPGManager. New provider
groups for other countries/broadcasters would follow the same pattern:
their own subfolder under `epg_providers/`, their own registry module.

Future providers may be added without modifying EPGManager,
MainScreen or InformationPanel.

---

# Information Flow

```
External Service (Yle Teksti-TV / Bauer's own page / RadioBrowser)
        |
        v
   EPG Provider (epg_providers/Finland_radio_epg/*)
        |
        v
  finland_radio_epg_registry (matches a played station to a provider)
        |
        v
     EPGManager
        |
        v
  InformationPanel
        |
        v
    MainScreen
```

Local playback follows the same principle: LyricsManager/
PlaybackController's own metadata and codec accessors feed
InformationPanel directly, without EPGManager or a provider being
involved.

---

# Documentation

Project documentation is maintained within the `docs/` directory.

Major documentation includes:

- ARCHITECTURE.md
- PROJECT_STRUCTURE.md (this file)
- HISTORY.md
- CHANGELOG.md
- MAINSCREEN_SPEC.md
- INFORMATION_PANEL_SPEC.md
- EPG_MANAGER_SPEC.md
- Other per-module *_SPEC.md files (one per Core module/Screen)
- Claude_notes_build*.txt (session-by-session development record,
  one per build)

Documentation is completed before implementation whenever practical;
finalized (this pass) once a build is confirmed complete across real
device testing.

---

# Design Principles

The project structure reflects logical responsibilities rather than
implementation details.

Business logic remains inside Core modules.

External services remain isolated within providers.

Screens remain focused on user interaction.

This organisation allows MediaPlayer3 to grow without requiring major
architectural changes.

---

End of PROJECT_STRUCTURE.md

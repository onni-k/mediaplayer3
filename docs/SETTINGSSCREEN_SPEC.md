# SettingsScreen Specification

Version: 0.7

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

SettingsScreen provides user configurable application settings.

Settings are grouped into logical categories.

SettingsScreen modifies configuration values only.

Application behaviour is implemented by the responsible modules.

---

# Responsibilities

SettingsScreen shall:

- Display current settings.
- Allow settings to be modified.
- Save configuration changes.
- Restore default values when requested.
- Display setting descriptions where appropriate.
- Apply Language/Skin/Theme changes immediately to
  LocalizationManager/SkinManager (Build 0006), not only on save.

SettingsScreen shall never implement playback logic.

---

# Setting Categories

General (Language, Startup directory, Hidden files)

Appearance (Skin, Theme -- Build 0006)

Playback

User Interface

Logging

Developer

System

---

# Appearance Settings (Build 0006)

Language

Selects LocalizationManager's active language. Applied immediately;
see LOCALIZATION_MANAGER_SPEC.md.

Device test round 66: added a "System" choice (the new default) that
resolves dynamically, at every point the language is actually applied
(startup, and again whenever this setting itself changes), to the
receiver's own current Enigma2 OSD language -- see config.py's own
resolveLanguageCode(). Falls back to English if the receiver's own
language isn't one MediaPlayer3 ships a catalog for. Choosing "Suomi"
or "English" explicitly still pins that language regardless of what
the receiver's own OSD language is or later becomes.

Skin

Selects SkinManager's active skin. Falls back to the default skin if
the selection is incompatible; see SKIN_MANAGER_SPEC.md.

Theme

Selects SkinManager's active theme (colour palette). Applied
immediately to newly-opened Screens; MainScreen itself picks up the
change on its next creation (see THEME_SPEC.md section 6 for why).

---

# Radio Settings (Build 0007)

Radio default country / Radio default language

Default search filters applied when opening RadioBrowserScreen
(INTERNETRADIO_MANAGER_SPEC.md). Left blank by default -- MediaPlayer3
cannot reliably detect the receiver's actual region/language.

Radio station limit (0 = unlimited)

Device test round 68: caps how many stations a single search's own
local-database filter returns (INTERNETRADIO_MANAGER_SPEC.md
"Search"). 100 by default -- raising it (or setting 0, meaning no
cap at all) shows more of the local database's own matches per
search, at the cost of a longer list to scroll through.

Device test round 69: this same setting (renamed from "Radio search
result limit" to reflect the wider scope) now also governs how many
stations updateStationDatabase() fetches from RadioBrowser itself,
via proper offset-based pagination in DATABASE_DOWNLOAD_PAGE_SIZE-
sized pages rather than one single request. 0 means the database
update fetches RadioBrowser's entire real catalogue (confirmed
against a live comparison: a user reported RadioBrowser's own website
showing 58362 total stations / 88 Finnish, while MediaPlayer3's own
database had stalled at exactly the old hardcoded 20000-station
download cap regardless of this setting -- that hardcoded cap
(DATABASE_DOWNLOAD_LIMIT) is now only an ultimate safety ceiling,
not the actual per-update target).

Unlimited results for own language

Device test round 68: when on, a search whose Language filter matches
the app's own current UI language (general.language, resolved through
config.py's own resolveLanguageCode()) ignores the result limit above
entirely for that one search, regardless of its own value -- letting
a user see every station in their own language without raising the
general limit for every other search too. Off by default.

Radio navigation mode

Selects whether MainScreen's LEFT/RIGHT/UP/DOWN Internet Radio
navigation (MAINSCREEN_SPEC.md "Internet Radio Navigation") defaults
to the favorites list or the history list.

Radio history size

Maximum number of entries kept in the listening history.

Resume radio station on start (Build 0007, device test round 3)

Opt-in (off by default): auto-resumes the last-played Internet Radio
station whenever MediaPlayer3 is launched through its own normal
Extensions/Plugin menu entry -- part of "power-radio-radio" launch-
and-resume behaviour. Does NOT cover launching MediaPlayer3 itself via
a global hardware RADIO key press from outside the plugin; see
docs/Claude_notes_build0007.txt for why.

YELLOW: Clear radio history

Clears InternetRadioManager's listening history after a Yes/No
confirmation. A deliberate, limited use of a colour button for a
genuinely occasional, optional action -- SettingsScreen has no other
colour button bindings.

---

# Playback Settings

Build 0005 introduces playback related settings.

Playback

☐ Automatically play next track

When enabled:

PlaybackController automatically starts the next track in the current
Playback Queue.

When disabled:

Playback stops after the current track finishes.

Seek step (seconds) -- Build 0006, device test round 3

Controls the FASTFORWARD/REWIND seek step. Default 60 seconds.
LEFT/RIGHT's shorter seek step (10 seconds) is fixed, not
configurable.

---

# Startup Directory Selection (Build 0006, device test round 3)

Startup directory is selected via a directory browser
(Screens.LocationBox.LocationBox, a standard Enigma2 core screen)
rather than typed as plain text, matching how files are selected in
BrowserScreen. Pressing OK on the Startup directory entry opens the
browser instead of ConfigListScreen's normal text-edit behaviour;
cancelling leaves the previous value unchanged.

---

# User Interface

MainScreen related options.

Examples include:

- Show progress bar
- Show elapsed time
- Show remaining time
- Show playback state

User interface settings affect presentation only.

---

# Logging Settings

Logging configuration is managed through ConfigurationManager.

Available options include:

Logging

☐ Enable logging

☐ Enable verbose logging

Verbose logging records additional playback and browser diagnostics.

---

# Developer Settings

Developer Mode enables additional diagnostic functionality.

Examples include:

- Show System Information
- Show Playback Statistics
- Enable Verbose Logging
- Enable Developer Screen

Developer settings are intended for testing and troubleshooting.

---

# Configuration

SettingsScreen reads and writes configuration through
ConfigurationManager.

Settings are applied without requiring architectural changes.

Each module reads only the settings relevant to its responsibilities.

---

# Logging

SettingsScreen follows LOGGER_SPEC.md.

INFO logging includes:

- Screen created
- Screen initialized
- Screen ready
- Setting changed
- Configuration saved
- Screen closing
- Screen closed

VERBOSE logging additionally includes:

- Previous value
- New value
- Configuration category
- Configuration key
- Save operation timing

---

# Design Principles

SettingsScreen owns configuration editing only.

ConfigurationManager owns configuration storage.

PlaybackController reads playback settings.

MainScreen reads presentation settings.

Logger reads logging settings.

This separation preserves the layered architecture introduced during
Build 0004.

---

# Acceptance Criteria

SettingsScreen implementation is complete when:

- Settings are displayed correctly.
- Settings can be modified.
- Configuration is saved correctly.
- Playback settings affect PlaybackController.
- User Interface settings affect MainScreen.
- Logging settings affect Logger.
- Developer settings affect Developer Mode.
- Logging follows LOGGER_SPEC.md.

---

# Related Documentation

CONFIG_SPEC.md

LOGGER_SPEC.md

PLAYBACK_CONTROLLER_SPEC.md

MAINSCREEN_SPEC.md

BUILD_0005_PLAN.md

---

# End of File

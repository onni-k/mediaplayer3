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

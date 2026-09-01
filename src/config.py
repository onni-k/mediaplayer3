# ==============================================================================
# MediaPlayer3
#
# File        : config.py
# Description : Centralized configuration management for MediaPlayer3.
#
# Author      : MediaPlayer3 Project
# Copyright   : (C) 2026 MediaPlayer3 Project
# License     : GNU General Public License v2 (GPL-2.0)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Compatible  : OpenViX 6.8+, OpenATV (planned)
# Python      : 3.13+
#
# Implements  : CONFIG_SPEC.md v0.1
# Architecture: ARCHITECTURE.md v0.3
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-07-05  Build 0002
#   - Initial version (config.py).
#
# 2026-07-10  Build 0003
#   - Renamed to configuration.py to match module name used in
#     ARCHITECTURE.md section 6 at the time (Settings wrapper).
#
# 2026-07-12  Build 0004
#   - Renamed back to config.py per PROJECT_STRUCTURE.md section 7 and
#     CHANGELOG.md ("Configuration module renamed to config.py").
#   - Replaced the plain Settings static wrapper with ConfigurationManager,
#     implementing the public interface required by CONFIG_SPEC.md
#     section 4: load(), save(), get(), set(), validate(),
#     reset_defaults(), get_version().
#   - Configuration entries reorganised into the categories defined in
#     CONFIG_SPEC.md section 5 (General, Playback, Logging, Developer).
#   - "Restore TV service on Exit" added as a Developer-only entry,
#     always enabled by default and not shown in normal Settings, per
#     SETTINGSSCREEN_SPEC.md section 5.
#
# 2026-07-14  Build 0005
#   - "playback.auto_play_next" is now actually read by
#     PlaybackController (previously stored but unused).
#   - Added the "ui" category: show_progress_bar, show_elapsed_time,
#     show_remaining_time, show_playback_state -- MainScreen
#     presentation toggles, per SETTINGSSCREEN_SPEC.md section 6
#     ("User Interface").
#
# 2026-07-19  Build 0006
#   - Added the "appearance" category: skin, theme -- read by
#     SkinManager (skin.py), not by ConfigurationManager itself.
#     "general.language" (already existed since Build 0004) is now
#     also read by LocalizationManager (localization.py).
#
# 2026-07-19  Build 0006 (device test round 1)
#   - Added "custom" to appearance.theme's choices and
#     appearance.custom_background_color (hex text entry), requested
#     after a real device test.
#
# 2026-07-19  Build 0006 (device test round 3)
#   - Added playback.seek_step_seconds (default 60, was a hardcoded
#     30 in mainscreen.py), requested after a real device test.
#
# 2026-07-19  Build 0006 (device test round 4)
#   - seek_step_seconds default reconsidered back to 30 (was briefly
#     60 in round 3).
#
# 2026-07-19  Build 0007
#   - Added the "radio" category: default_country, default_language
#     (search filter defaults), navigation_mode (favorites/history for
#     MainScreen's station navigation), history_size -- read by
#     InternetRadioManager (internetradio_manager.py), not by
#     ConfigurationManager itself.
#
# 2026-07-24  Build 0007 (device test round 3)
#   - Added radio.resume_on_start (default off): opt-in auto-resume of
#     the last-played station whenever MediaPlayer3 is launched.
#
# 2026-07-25  Build 0007 (device test round 8)
#   - Added "gray" to appearance.theme's choices and made it the
#     default (was "default") -- requested: a new Gray theme with
#     background colour #A0A0A0.
#
# 2026-07-26  Build 0007 (device test round 10)
#   - appearance.custom_background_color's default changed from pure
#     black (#000000) to near-black (#0A0A0A) -- avoids a known
#     chroma-key issue on many DVB/Enigma2 receivers where the video
#     plane shows through pure black instead of a solid pixel.
#
# 2026-07-28  Build 0008
#   - Added library.scan_directory (LIBRARY_MANAGER_SPEC.md) --
#     LibraryManager's own scan root, intentionally independent of
#     general.startup_directory even though it defaults to the same
#     folder.
#
# 2026-07-29  Build 0008 (device test round 2)
#   - Fixed a real bug confirmed by a device log ("[Config] Unknown
#     configuration key: library.scan_directory"): the setting was
#     declared on cfg but never added to _ENTRIES, the flat registry
#     ConfigurationManager.get()/set() actually look keys up in --
#     declaring a cfg.* attribute alone was never enough on its own.
#     This made LibraryManager.scan() always read an empty directory
#     regardless of what the user picked in Settings. Cross-checked
#     every other declared cfg.* setting against _ENTRIES; this was
#     the only one missing.
#
# 2026-08-24  Build 0010 (device test round 46)
#   - Added "light"/"dark" to appearance.skin's own choices (was
#     "default" only, placeholder from Build 0006). Deliberately
#     separate from appearance.theme, which every OTHER screen still
#     uses for its own colours -- appearance.skin is read only by
#     MusicLibraryScreen for now (the one screen using the new
#     background-image UI, see musiclibraryscreen.py's own change
#     history), not yet a general replacement. Reusing this
#     already-declared cfg key instead of adding a new one, since it
#     was created for exactly this purpose and never used.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 configuration.

All access to Enigma2 configuration should go through this module.
Other modules should never access config.plugins.mediaplayer3 directly --
they should use the shared `config_manager` (ConfigurationManager)
instance instead, per CONFIG_SPEC.md section 3 (Architecture).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from Components.config import (
    config,
    ConfigSubsection,
    ConfigYesNo,
    ConfigText,
    ConfigSelection,
    ConfigInteger,
)

from .compatibility import compatibility
from .logger import (
    logger,
    DEVELOPER_MODE_OFF,
    DEVELOPER_MODE_BASIC,
    DEVELOPER_MODE_VERBOSE,
)
from .paths import default_media_directory, ensure_trailing_slash

# ------------------------------------------------------------------------------
# Configuration version
# ------------------------------------------------------------------------------
#
# See CONFIG_SPEC.md section 8. Bump this whenever the meaning or shape of
# a stored entry changes, so a future migration step has something to key
# off. Build 0004 introduces the version but does not yet need to migrate
# anything.
#
CONFIG_VERSION = 1

# ------------------------------------------------------------------------------
# Enigma2 configuration section
# ------------------------------------------------------------------------------

if not hasattr(config.plugins, "mediaplayer3"):
    config.plugins.mediaplayer3 = ConfigSubsection()

cfg = config.plugins.mediaplayer3


# Device test round 65 -- guards against a language MediaPlayer3
# doesn't actually ship a catalog for; round 66's own resolveLanguageCode()
# below is the only place this list is consulted now.
_AVAILABLE_LANGUAGE_CODES = ("en", "fi")


def resolveLanguageCode(configured_value: str) -> str:
    """
    Device test round 66 -- resolves cfg.general.language's own
    configured value ("fi", "en", or "system") to an actual 2-letter
    language code LocalizationManager can load. "system" is resolved
    fresh every time this is called (at plugin startup, and again
    whenever Settings applies a language change live) rather than
    baked into a config default once -- so if the receiver's own OSD
    language changes later, MediaPlayer3 picks that up on its own
    next start too, without the user needing to re-select anything
    here. Replaces round 65's own _defaultLanguageCode(), which only
    computed the system language once, at config-creation time.
    """

    if configured_value != "system":
        return configured_value

    system_language = compatibility.getSystemLanguage(fallback_language_code="en")

    if system_language in _AVAILABLE_LANGUAGE_CODES:
        return system_language

    return "en"


# ------------------------------------------------------------------------------
# Build 0008 -- Library (LIBRARY_MANAGER_SPEC.md)
# ------------------------------------------------------------------------------

cfg.library = ConfigSubsection()

# ------------------------------------------------------------------------------
# General (CONFIG_SPEC.md section 5 / SETTINGSSCREEN_SPEC.md section 5)
# ------------------------------------------------------------------------------

cfg.general = ConfigSubsection()

cfg.general.language = ConfigSelection(
    default="system",
    choices=[
        ("system", "Järjestelmä"),
        ("fi", "Suomi"),
        ("en", "English"),
    ],
)

cfg.general.startup_directory = ConfigText(
    default=default_media_directory()
)

cfg.general.hidden_files = ConfigYesNo(
    default=False
)

# Build 0010, BUILD_0010_PLAN.md "Main Menu Integration": "Settings
# shall provide an option to add MediaPlayer3 to the Enigma2 main
# menu." Read directly by plugin.py's own Plugins() function, which
# Enigma2 calls once at plugin-list load time (startup, or a plugin-
# list rescan) -- not re-evaluated live, so toggling this in Settings
# needs a GUI restart (or a full reboot) before the main menu entry
# actually appears/disappears, same as most other Enigma2 plugins'
# own menu-visibility toggles. MediaPlayer3's own Extensions/Plugin
# menu entry (WHERE_PLUGINMENU) is unaffected either way -- this only
# adds or removes the additional WHERE_MENU entry.
cfg.general.show_in_main_menu = ConfigYesNo(
    default=False
)

# Build 0008 -- LibraryManager's own scan root, intentionally
# independent of general.startup_directory (BUILD_0008_PLAN.md "Music
# Library is intentionally separated from Browser."). Defaults to the
# same folder for convenience, but can be pointed elsewhere.
cfg.library.scan_directory = ConfigText(
    default=default_media_directory()
)

# ------------------------------------------------------------------------------
# Playback (SETTINGSSCREEN_SPEC.md section 6)
# ------------------------------------------------------------------------------

cfg.playback = ConfigSubsection()

cfg.playback.resume_playback = ConfigYesNo(
    default=False
)

# Automatic Next Track (Build 0005 -- PLAYBACK_QUEUE_SPEC.md /
# BUILD_0005_PLAN.md). Read by PlaybackController._handleTrackFinished()
# every time a track ends.
cfg.playback.auto_play_next = ConfigYesNo(
    default=False
)

# Seek step in seconds, used by MainScreen's FASTFORWARD/REWIND
# handling (Build 0006, device test round 3 -- made configurable).
# Default was briefly changed to 60s in round 3, then reconsidered
# back to the original 30s in round 4. LEFT/RIGHT's short seek step
# stays a fixed 10s -- only the long (FF/RW) step is configurable.
cfg.playback.seek_step_seconds = ConfigInteger(
    default=30,
    limits=(5, 300),
)

# Build 0009, device test round 7 -- step size (seconds) for the
# Information Panel's synchronized-lyrics offset adjustment (UP/DOWN
# while viewing synchronized lyrics), per user request to make this
# configurable instead of the fixed 0.5s it started as (round 7
# shipped with a 1s default; round 8 confirmed 5s worked well in
# practice and became the new default). Whole seconds only
# (ConfigInteger, matching seek_step_seconds's own pattern).
cfg.playback.lyrics_offset_step_seconds = ConfigInteger(
    default=5,
    limits=(1, 10),
)

# Device test round 27 -- ffprobe_helper.py provides real, measured
# codec info (where the ffprobe binary is present -- confirmed on at
# least one real device, not guaranteed on every image) instead of
# the existing extension-guess/station-metadata fallbacks
# (information_panel.py's own _buildCodecPage()). On by default;
# this toggle exists for anyone on an image/box where ffprobe
# misbehaves or isn't wanted (it does briefly block the interface --
# see ffprobe_helper.probe()'s own docstring -- while viewing the
# Codec information page, or while radiobrowserscreen.py's own
# opt-in codec logging, cfg.logging.log_station_codecs, is enabled).
cfg.playback.enable_ffprobe = ConfigYesNo(
    default=True
)

# ------------------------------------------------------------------------------
# User Interface (Build 0005 -- SETTINGSSCREEN_SPEC.md section 6)
# ------------------------------------------------------------------------------
#
# MainScreen presentation toggles -- affect what MainScreen displays
# only, never playback itself (SETTINGSSCREEN_SPEC.md "Design
# Principles": "MainScreen reads presentation settings").

cfg.ui = ConfigSubsection()

cfg.ui.show_progress_bar = ConfigYesNo(
    default=True
)

cfg.ui.show_elapsed_time = ConfigYesNo(
    default=True
)

cfg.ui.show_remaining_time = ConfigYesNo(
    default=True
)

cfg.ui.show_playback_state = ConfigYesNo(
    default=True
)

# ------------------------------------------------------------------------------
# Appearance (Build 0006 -- SKIN_MANAGER_SPEC.md / THEME_SPEC.md)
# ------------------------------------------------------------------------------

cfg.appearance = ConfigSubsection()

cfg.appearance.skin = ConfigSelection(
    default="default",
    choices=[
        ("default", "Default"),
        ("light", "Light"),
        ("dark", "Dark"),
    ],
)

cfg.appearance.theme = ConfigSelection(
    default="gray",
    choices=[
        ("gray", "Gray"),
        ("light", "Light"),
        ("dark", "Dark"),
        ("default", "Default"),
        ("highcontrast", "High Contrast"),
        ("custom", "Custom"),
    ],
)

# Only meaningful when appearance.theme == "custom" -- see
# skin.SkinManager.setCustomColor(). A plain hex string, validated by
# SkinManager before being applied (an invalid entry is rejected,
# leaving the previous colour in place, rather than breaking the
# theme).
cfg.appearance.custom_background_color = ConfigText(
    default="#0A0A0A",
    fixed_size=False,
)

# ------------------------------------------------------------------------------
# Internet Radio (Build 0007 -- INTERNETRADIO_MANAGER_SPEC.md)
# ------------------------------------------------------------------------------

cfg.radio = ConfigSubsection()

# Default search filters (BUILD_0007_PLAN.md "Search filters may be
# configured from application settings." / "Default values should
# follow the receiver language and region whenever possible.").
# Left blank by default -- MediaPlayer3 has no reliable way to detect
# the receiver's actual region/language on its own; the user sets
# these once in Settings if they want a default filter applied.
cfg.radio.default_country = ConfigText(
    default="",
    fixed_size=False,
)

cfg.radio.default_language = ConfigText(
    default="",
    fixed_size=False,
)

# Device test round 68 -- per direct request, after a user noticed
# the Language filter's own "Any" search only ever returned 100
# stations even though the local database itself had 20000: that 100
# was never a RadioBrowser API limit (updateStationDatabase() already
# downloads the full DATABASE_DOWNLOAD_LIMIT worth locally) -- it's
# InternetRadioManager.search()'s own DEFAULT_SEARCH_LIMIT, applied
# every time a search's own local-database filter is sliced down to a
# result count, regardless of how many of the locally-stored stations
# actually matched. 0 means "no limit" (return every match); see
# internetradio_manager.py's own search() for why slicing with a
# limit of 0 needed its own explicit check rather than relying on
# Python's own list[:0] (which means "give me zero", the opposite of
# what a "0 = unlimited" setting needs).
cfg.radio.search_limit = ConfigInteger(
    default=100,
    limits=(0, 20000),
)

# Device test round 68 -- per direct request ("hae käytössä olevan
# kielen kaikki kanavat"): when on, a search whose own Language filter
# matches the app's own current UI language (general.language,
# resolved through config.py's own resolveLanguageCode()) ignores
# radio.search_limit entirely for that one search, returning every
# matching station regardless of the general cap -- letting a user
# browse their own language's full station list without needing to
# raise radio.search_limit for every OTHER search too (a plain "Any"
# search across every language in the database is a very different,
# much larger result set than "just my own language"). Off by
# default, since a very large local-language station count could
# otherwise surprise a user who never asked for it.
cfg.radio.unlimited_for_own_language = ConfigYesNo(
    default=False
)

# MainScreen's LEFT/RIGHT/UP/DOWN station navigation
# (BUILD_0007_PLAN.md "MainScreen Navigation") switches between
# favorites or history depending on this setting.
cfg.radio.navigation_mode = ConfigSelection(
    default="favorites",
    choices=[
        ("favorites", "Favorites"),
        ("history", "History"),
    ],
)

cfg.radio.history_size = ConfigInteger(
    default=50,
    limits=(5, 200),
)

# Opt-in: resume the last-played Internet Radio station automatically
# whenever MediaPlayer3 itself is launched (Build 0007, device test
# round 3 -- "kun painaa power-radio-radio, niin tv-aukeaa ja
# edellinen radiokanava lähtee soimaan"). Off by default, since
# auto-playing audio the moment the plugin opens could otherwise be
# surprising. See docs/Claude_notes_build0007.txt for what this does
# and does NOT cover -- it only resumes on MediaPlayer3's own normal
# launch, not via a global hardware key from outside the plugin.
cfg.radio.resume_on_start = ConfigYesNo(
    default=False
)

# Build 0009, device test round 11 -- use ExtEplayer3 (FFmpeg-based)
# instead of the default GStreamer-based service for Internet Radio
# playback specifically (never affects local file playback). Off by
# default: not every image has ExtEplayer3/FFmpeg installed. See
# compatibility.py's createServiceReference() for the original
# reasoning (independent evidence this class of GStreamer stream-
# reconnect failure is often fixed by this exact switch elsewhere).
#
# Build 0009, device test rounds 12-13: tested against real hardware
# for the two stations that motivated this (Radio Nova, Radio
# SuomiRock) -- did NOT fix them. A full device log showed
# ExtEplayer3 failing the same way GStreamer did (stopping itself
# ~1s after "PLAYBACK_OPEN", no user interaction involved), just with
# a quieter failure mode (clean exit, no error message) instead of
# GStreamer's explicit "Not Found" errors -- strong evidence the
# underlying issue is server/stream-side for these two stations
# specifically, not something either playback backend can route
# around. ExtEplayer3 additionally introduced a new problem of its
# own on this hardware: STOP took roughly 10 seconds to actually
# silence the audio (confirmed not a MediaPlayer3-side delay -- the
# software stop command itself completed in milliseconds; the lag
# was ExtEplayer3/ServiceApp's own audio buffer draining) and
# affected LOCAL file playback too, not just radio. Switching back to
# GStreamer (this setting off) restored immediate, correct STOP
# behaviour for both. Left available as a per-installation option
# (it's still the documented fix for this general class of issue
# elsewhere) but no longer expected to help on this specific
# hardware/stream combination -- kept off by default.
cfg.radio.use_exteplayer3 = ConfigYesNo(
    default=False
)

# Build 0010, BUILD_0010_PLAN.md "RadioBrowser Database" /
# RADIOBROWSER_SPEC.md "Automatic Updates": "The update interval
# shall be configurable where appropriate. The default interval may
# be seven days." database_auto_update is the on/off switch;
# database_update_interval_days is that interval, only consulted
# when auto-update is on. See internetradio_manager.py's
# shouldAutoUpdateDatabase() for how these are used together.
cfg.radio.database_auto_update = ConfigYesNo(
    default=True
)

cfg.radio.database_update_interval_days = ConfigInteger(
    default=7,
    limits=(1, 90),
)

# ------------------------------------------------------------------------------
# Radio EPG (EPG_MANAGER_SPEC.md, Build 0009)
# ------------------------------------------------------------------------------

cfg.epg = ConfigSubsection()

# Yle's Teksti-TV API (yle_teletext_provider.py, confirmed working
# against real Yle radio schedule data) requires the user's own
# app_id/app_key, registered at tunnus.yle.fi/api-avaimet -- these are
# the user's personal credentials, never something MediaPlayer3 could
# ship with built in. Left blank by default; Yle Radio schedule
# lookups are simply skipped (not an error) until both are set.
cfg.epg.yle_app_id = ConfigText(
    default="",
    fixed_size=False,
)

cfg.epg.yle_app_key = ConfigText(
    default="",
    fixed_size=False,
)

# ------------------------------------------------------------------------------
# Podcasts (Build 0010 -- PODCAST_PROVIDER_SPEC.md "Authentication")
# ------------------------------------------------------------------------------

cfg.podcast = ConfigSubsection()

# Podcast Index (podcastindex_provider.py) works out of the box using
# a bundled default key/secret (lightly obfuscated in that module, see
# its own header for why this isn't real security), but a user's own
# free key from https://api.podcastindex.org/signup here always takes
# priority when both fields are set -- the only genuinely private
# option, and avoids every MediaPlayer3 installation sharing the same
# bundled key's rate limit. Left blank by default.
cfg.podcast.podcastindex_api_key = ConfigText(
    default="",
    fixed_size=False,
)

cfg.podcast.podcastindex_api_secret = ConfigText(
    default="",
    fixed_size=False,
)

# ------------------------------------------------------------------------------
# Logging (SETTINGSSCREEN_SPEC.md section 6)
# ------------------------------------------------------------------------------

cfg.logging = ConfigSubsection()

cfg.logging.developer_level = ConfigSelection(
    default=DEVELOPER_MODE_OFF,
    choices=[
        (DEVELOPER_MODE_OFF, "Off"),
        (DEVELOPER_MODE_BASIC, "Basic"),
        (DEVELOPER_MODE_VERBOSE, "Verbose"),
    ],
)

cfg.logging.keep_log_files = ConfigInteger(
    default=10,
    limits=(1, 100),
)

# Device test round 27 -- user request: a log entry with the real
# (ffprobe-measured) codec for whatever station the user's selection
# settles on in RadioBrowserScreen's Stations column, building up
# real-world codec data across many stations/sessions over time (the
# stated goal: eventually being able to tell which stations use a
# codec MediaPlayer3/Enigma2 doesn't handle well, e.g. the two
# specific stations named as suspects, and warn generally about that
# class of station). Also now updates the info panel itself with the
# measured codec/bitrate, or a warning if the probe fails (device test
# round 29). On by default since round 29 -- confirmed useful and not
# problematic across real device testing, superseding round 27's own
# "off by default" reasoning.
cfg.logging.log_station_codecs = ConfigYesNo(
    default=True
)

# ------------------------------------------------------------------------------
# Developer (SETTINGSSCREEN_SPEC.md section 6 / DEVELOPER_SCREEN_SPEC.md)
# ------------------------------------------------------------------------------

cfg.developer = ConfigSubsection()

# Device test round 31 -- "Disable Restore TV service on Exit" removed
# from the Settings UI (no longer shown, no longer settable that way)
# per direct request, but the underlying config entry and its actual
# exit-time behaviour are left completely untouched -- only its
# Settings-screen visibility changed, not what MediaPlayer3 actually
# does. Always defaults to False (restore TV, the everyday-safe
# behaviour) since it can no longer be turned on through the UI.
cfg.developer.disable_restore_tv_on_exit = ConfigYesNo(
    default=False
)

# ------------------------------------------------------------------------------
# Public entry registry
# ------------------------------------------------------------------------------
#
# Maps dotted CONFIG_SPEC.md-style keys ("category.name") to the
# underlying ConfigElement, so ConfigurationManager.get()/set() can stay
# generic instead of growing one method per setting.

_ENTRIES: Dict[str, Any] = {
    "general.language": cfg.general.language,
    "general.startup_directory": cfg.general.startup_directory,
    "general.hidden_files": cfg.general.hidden_files,
    "general.show_in_main_menu": cfg.general.show_in_main_menu,

    "library.scan_directory": cfg.library.scan_directory,

    "playback.resume_playback": cfg.playback.resume_playback,
    "playback.auto_play_next": cfg.playback.auto_play_next,
    "playback.seek_step_seconds": cfg.playback.seek_step_seconds,
    "playback.lyrics_offset_step_seconds": cfg.playback.lyrics_offset_step_seconds,
    "playback.enable_ffprobe": cfg.playback.enable_ffprobe,

    "ui.show_progress_bar": cfg.ui.show_progress_bar,
    "ui.show_elapsed_time": cfg.ui.show_elapsed_time,
    "ui.show_remaining_time": cfg.ui.show_remaining_time,
    "ui.show_playback_state": cfg.ui.show_playback_state,

    "appearance.skin": cfg.appearance.skin,
    "appearance.theme": cfg.appearance.theme,
    "appearance.custom_background_color": cfg.appearance.custom_background_color,

    "radio.default_country": cfg.radio.default_country,
    "radio.default_language": cfg.radio.default_language,
    "radio.search_limit": cfg.radio.search_limit,
    "radio.unlimited_for_own_language": cfg.radio.unlimited_for_own_language,
    "radio.navigation_mode": cfg.radio.navigation_mode,
    "radio.history_size": cfg.radio.history_size,
    "radio.resume_on_start": cfg.radio.resume_on_start,
    "radio.use_exteplayer3": cfg.radio.use_exteplayer3,
    "radio.database_auto_update": cfg.radio.database_auto_update,
    "radio.database_update_interval_days": cfg.radio.database_update_interval_days,

    "epg.yle_app_id": cfg.epg.yle_app_id,
    "epg.yle_app_key": cfg.epg.yle_app_key,
    "podcast.podcastindex_api_key": cfg.podcast.podcastindex_api_key,
    "podcast.podcastindex_api_secret": cfg.podcast.podcastindex_api_secret,

    "logging.developer_level": cfg.logging.developer_level,
    "logging.keep_log_files": cfg.logging.keep_log_files,
    "logging.log_station_codecs": cfg.logging.log_station_codecs,

    "developer.disable_restore_tv_on_exit": cfg.developer.disable_restore_tv_on_exit,
}


class ConfigurationManager:
    """
    Centralized configuration management for MediaPlayer3.

    Implements the public interface required by CONFIG_SPEC.md section 4.
    ConfigurationManager never depends on Screen classes -- Screens and
    Controllers access configuration only through this class.
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.3"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self.load()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Config] %s", message)

# End of Part 1
    # ------------------------------------------------------------------
    # Public interface (CONFIG_SPEC.md section 4)
    # ------------------------------------------------------------------

    def load(self) -> None:
        """
        Load configuration.

        Enigma2's config system parses the on-disk configuration file at
        boot; every ConfigElement above already pulled its stored value
        (or its default) from that parsed structure when it was created.
        load() therefore validates the currently active values and logs
        the outcome, rather than re-reading the file itself.
        """

        self._log("Loading configuration.")

        self.validate()

        self._log("Configuration loaded.")

    # ------------------------------------------------------------------

    def save(self) -> None:
        """
        Save configuration.
        """

        self._log("Saving configuration.")

        try:
            cfg.save()

        except Exception as error:

            self._log(f"Unable to save configuration: {error}")

            return

        self._log("Configuration saved.")

    # ------------------------------------------------------------------

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Return the current value for `key` (e.g. "general.hidden_files").

        Returns `default` when `key` is unknown, so a missing/renamed
        entry never raises for a caller.
        """

        entry = _ENTRIES.get(key)

        if entry is None:

            self._log(f"Unknown configuration key: {key}")

            return default

        return entry.value

    # ------------------------------------------------------------------

    def set(self, key: str, value: Any) -> bool:
        """
        Set `key` to `value`.

        Returns True on success, False when the key is unknown or the
        value was rejected by validate(). Invalid values are never
        allowed to terminate the application (CONFIG_SPEC.md section 7).
        """

        entry = _ENTRIES.get(key)

        if entry is None:

            self._log(f"Unknown configuration key: {key}")

            return False

        if not self.validateValue(key, value):

            self._log(
                f"Invalid configuration value for {key}: {value!r} "
                "(using default)"
            )

            return False

        previous = entry.value

        entry.value = value

        if self._developerVerbose():
            self._log(f"{key}: {previous!r} -> {value!r}")

        return True

    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """
        Validate every known configuration entry.

        ConfigSelection/ConfigYesNo/ConfigInteger already clamp or reject
        out-of-range values at assignment time, so validate() mainly
        exists as an explicit, loggable checkpoint per CONFIG_SPEC.md
        section 7, and as a hook for future cross-field validation.
        """

        valid = True

        for key, entry in _ENTRIES.items():

            try:
                # Touching .value forces evaluation of the stored value;
                # ConfigInteger raises here if it was corrupted on disk.
                _ = entry.value

            except Exception as error:

                self._log(f"Invalid configuration entry: {key} ({error})")

                valid = False

        return valid

    # ------------------------------------------------------------------

    def validateValue(self, key: str, value: Any) -> bool:
        """
        Validate a single candidate value for `key` before it is applied.

        Build 0004 performs basic, type-appropriate checks; ConfigSpec's
        underlying ConfigElement still performs the final clamping.
        """

        entry = _ENTRIES.get(key)

        if entry is None:
            return False

        if isinstance(entry, ConfigYesNo):
            return isinstance(value, bool)

        if isinstance(entry, ConfigInteger):

            try:
                low, high = entry.limits[0]

                return low <= int(value) <= high

            except Exception:
                return False

        if isinstance(entry, ConfigSelection):
            return value in [choice[0] for choice in entry.choices]

        if isinstance(entry, ConfigText):
            return isinstance(value, str)

        return True

# End of Part 2
    # ------------------------------------------------------------------

    def reset_defaults(self) -> None:
        """
        Restore every configuration entry to its documented default value.
        """

        self._log("Restoring default configuration.")

        for key, entry in _ENTRIES.items():

            try:
                entry.setValue(entry.default)

            except Exception as error:

                self._log(f"Unable to reset {key}: {error}")

        self.save()

        self._log("Default configuration restored.")

    # ------------------------------------------------------------------

    def get_version(self) -> int:
        """
        Return the internal configuration version (CONFIG_SPEC.md
        section 8).
        """

        return CONFIG_VERSION

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------
    #
    # Thin, readable wrappers around get()/set() for the entries other
    # modules need most often. These are convenience only -- the generic
    # get()/set() interface above remains the canonical public API.

    def isDeveloperMode(self) -> bool:
        """
        Device test round 31 -- "Developer Mode" as a separate toggle
        removed; this now derives directly from the Logging Level
        setting instead ("siirtaa developer moden toiminnot suoraan
        logging level verbose alle") -- Developer Mode is considered
        on exactly when Logging Level is Verbose, nothing else drives
        it anymore.
        """

        from .logger import DEVELOPER_MODE_OFF, DEVELOPER_MODE_VERBOSE

        return self.get("logging.developer_level", DEVELOPER_MODE_OFF) == DEVELOPER_MODE_VERBOSE

    def isRestoreTvServiceEnabled(self) -> bool:
        return not bool(self.get("developer.disable_restore_tv_on_exit", False))

    def getDeveloperLogLevel(self) -> str:
        return self.get("logging.developer_level", DEVELOPER_MODE_OFF)

    def getStartupDirectory(self) -> str:
        return ensure_trailing_slash(
            self.get("general.startup_directory", default_media_directory())
        )

    def setStartupDirectory(self, directory: str) -> bool:
        return self.set("general.startup_directory", ensure_trailing_slash(directory))

    def _developerVerbose(self) -> bool:
        return self.getDeveloperLogLevel() == DEVELOPER_MODE_VERBOSE

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            "ConfigurationManager("
            f"initialized={self._initialized}, "
            f"version={CONFIG_VERSION})"
        )


# ----------------------------------------------------------------------
# Global ConfigurationManager instance
# ----------------------------------------------------------------------

config_manager = ConfigurationManager()


# ==============================================================================
#
# Build Notes
#
# Build 0004 replaces the Build 0003 Settings static wrapper with
# ConfigurationManager, matching the public interface required by
# CONFIG_SPEC.md section 4 (load/save/get/set/validate/reset_defaults/
# get_version).
#
# Future builds may extend this module with:
#
#   - Configuration import / export
#   - Automatic backup
#   - Multiple user profiles
#   - Configuration migration (using CONFIG_VERSION)
#   - Configuration checksum
#
# The public ConfigurationManager interface should remain backward
# compatible whenever practical.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

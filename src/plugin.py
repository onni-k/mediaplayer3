# ==============================================================================
# MediaPlayer3
#
# File        : plugin.py
# Description : MediaPlayer3 plugin entry point.
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
# ------------------------------------------------------------------------------
# Change history
#
# 2026-07-04  Build 0001
#   - Initial version.
#
# 2026-07-12  Build 0004
#   - Opens MainScreen instead of Browser (now BrowserScreen), per
#     ARCHITECTURE.md section 3 and MAINSCREEN_SPEC.md section 1.
#   - Applies the saved Developer Mode / debug logging configuration to
#     the shared logger instance at startup.
#
# 2026-07-19  Build 0006
#   - Applies the saved language (LocalizationManager) and skin/theme
#     (SkinManager) configuration at startup, alongside the existing
#     logging configuration.
#
# 2026-07-19  Build 0006 (device test round 4)
#   - Added plugin.png: the icon= "plugin.png" reference in
#     Plugins() below previously had no matching file. Confirmed
#     showing correctly in the plugin menu on a real device.
#
# 2026-07-19  Build 0007
#   - Imports storage_manager/playlist_manager/internetradio_manager
#     explicitly so their startup logging appears in a predictable
#     order before MainScreen's own "Created" line -- each is already
#     a self-initializing module-level singleton (same pattern as
#     SkinManager/LocalizationManager), so no additional setup call is
#     needed here beyond that.
#
# 2026-07-24  Build 0007 (device test round 3)
#   - Added opt-in auto-resume of the last-played Internet Radio
#     station on launch (radio.resume_on_start, default off) --
#     requested as part of "power-radio-radio" launch-and-resume
#     behaviour. This covers only MediaPlayer3's own normal launch
#     (Extensions/Plugin menu); launching the whole plugin from a
#     GLOBAL hardware RADIO key press (i.e. from outside the plugin,
#     e.g. from live TV) is NOT implemented -- see
#     docs/Claude_notes_build0007.txt for why.
#
# 2026-07-25  Build 0007 (device test round 8)
#   - appearance.theme's fallback default (used only if
#     config_manager.get() somehow can't find the key) updated to
#     "gray", matching config.py's new default.
#
# 2026-07-26  Build 0007 (device test round 10)
#   - custom_background_color's own fallback default updated to
#     near-black (#0A0A0A), matching config.py's new default.
#
# 2026-08-01  Build 0008 (device test round 3)
#   - Added device/system identification to the startup log (receiver
#     model, image name/version, platform) -- requested purely for
#     troubleshooting (matching a user-reported log against the
#     receiver/image it came from), even though nothing in the
#     application currently reads this back. compatibility.py already
#     had getImageName()/getImageVersion()/getReceiverModel(), unused
#     anywhere until now.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 plugin entry point.
"""

import platform
import traceback

from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox

from .compatibility import compatibility
from .config import config_manager
from .internetradio_manager import internetradio_manager
from .localization import localization_manager
from .localization import _
from .logger import logger
from .mainscreen import MainScreen
from .playlist_manager import playlist_manager
from .skin import skin_manager
from .storage import storage_manager
from .version import get_version_string

# ------------------------------------------------------------------------------
# Plugin entry point
# ------------------------------------------------------------------------------

def main(session, **kwargs):
    """
    Start MediaPlayer3.
    """

    logger.info("============================================================")
    logger.info(get_version_string())
    logger.info("Starting MediaPlayer3")
    logger.info("============================================================")

    #
    # Build 0008 -- device/system identification, logged unconditionally
    # at every startup purely for troubleshooting (e.g. matching a user-
    # reported log against the receiver/image it came from) -- nothing
    # in the application currently reads this back. Each lookup already
    # falls back to "Unknown" on its own (compatibility.py), so this can
    # never prevent startup.
    #
    try:
        logger.info(
            "Device: %s | Image: %s %s | Platform: %s %s",
            compatibility.getReceiverModel(),
            compatibility.getImageName(),
            compatibility.getImageVersion(),
            platform.system(),
            platform.release(),
        )

    except Exception as error:

        logger.warning("Unable to log device/system identification: %s", error)

    #
    # Apply saved Logging Level configuration to the shared logger
    # before MainScreen is created, so lifecycle logging for
    # MainScreen's own startup already reflects the user's setting.
    # Device test round 31: the separate "Enable debug logging" toggle
    # is gone -- Logging Level alone drives this now.
    #
    try:
        logger.setDeveloperMode(config_manager.getDeveloperLogLevel())

    except Exception as error:

        logger.warning("Unable to apply logging configuration: %s", error)

    #
    # Apply saved language, skin and theme configuration (Build 0006).
    # Each call falls back safely on its own if the saved value is no
    # longer valid, so a bad/removed skin or theme can never prevent
    # startup.
    #
    try:
        localization_manager.setLanguage(config_manager.get("general.language", "fi"))

    except Exception as error:

        logger.warning("Unable to apply language configuration: %s", error)

    try:
        skin_manager.loadSkin(config_manager.get("appearance.skin", "default"))

        skin_manager.loadTheme(config_manager.get("appearance.theme", "gray"))

        if skin_manager.getThemeName() == "custom":

            skin_manager.setCustomColor(
                "background",
                config_manager.get("appearance.custom_background_color", "#0A0A0A"),
            )

    except Exception as error:

        logger.warning("Unable to apply skin/theme configuration: %s", error)

    logger.info("Storage working directory: %s", storage_manager.getWorkingDirectory())

    logger.info("Playlists available: %d", len(playlist_manager.getPlaylistNames()))

    logger.info("Radio favorite lists: %s", ", ".join(internetradio_manager.getFavoriteListNames()) or "None")

    # Build 0010 -- identified during the Build 0009 exception audit:
    # this call had no top-level exception guard at all. Two real
    # device crashes during Build 0009 (a malformed XML skin comment,
    # an unverified onLayoutFinish API used to work around the first
    # fix) both propagated straight to Enigma2's own crash handler
    # because nothing here caught them -- every individual startup
    # step *before* this point was already wrapped defensively, but
    # MainScreen's own construction/layout was not. This does not
    # prevent bugs in MainScreen itself; it only ensures that if one
    # slips through despite everything MainScreen's own code already
    # does defensively, the person sees a clear MediaPlayer3 error
    # dialog instead of an uncontrolled Enigma2 traceback, and the
    # failure is fully logged for diagnosis.
    try:
        main_screen = session.open(MainScreen)

    except Exception as error:

        logger.warning("MainScreen failed to start: %s\n%s", error, traceback.format_exc())

        session.open(
            MessageBox,
            _("MediaPlayer3 could not start:\n%s") % error,
            MessageBox.TYPE_ERROR,
        )

        return

    #
    # Opt-in: resume the last-played Internet Radio station
    # automatically (Build 0007, device test round 3 --
    # radio.resume_on_start, default off). Reconstructs a station-like
    # dict from the most recent history entry (name/stream_url/
    # stationuuid -- see InternetRadioManager.addHistoryEntry()) and
    # hands it to MainScreen exactly the same way picking a station in
    # RadioBrowserScreen would. Never allowed to prevent or delay
    # normal startup -- wrapped defensively, and only attempted after
    # MainScreen has already opened successfully.
    #
    try:
        if config_manager.get("radio.resume_on_start", False) and main_screen is not None:

            history = internetradio_manager.getHistory()

            if history:

                last_entry = history[0]

                station = {
                    "stationuuid": last_entry.get("stationuuid"),
                    "name": last_entry.get("name", "Internet Radio"),
                    "url": last_entry.get("stream_url", ""),
                    "url_resolved": last_entry.get("stream_url", ""),
                }

                logger.info("Resuming last radio station: %s", station["name"])

                main_screen.playRadioStation(station)

    except Exception as error:

        logger.warning("Unable to resume last radio station: %s", error)

# ------------------------------------------------------------------------------
# Plugin registration
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Main menu hook (Build 0010, BUILD_0010_PLAN.md "Main Menu
# Integration")
# ------------------------------------------------------------------------------

def mainMenu(menuid, **kwargs):
    """
    WHERE_MENU's own calling convention -- different from
    WHERE_PLUGINMENU's `fnc`, which Enigma2 calls directly when the
    user selects the plugin. This one is called for every menu
    Enigma2 builds (menuid identifies which one), and must return a
    list of (name, function, unique_id, weight) tuples to contribute
    an entry to that specific menu, or [] to contribute nothing --
    getting this wrong (e.g. treating it like WHERE_PLUGINMENU's fnc)
    either crashes menu construction or silently never shows an entry
    anywhere, so this checks menuid explicitly rather than assuming
    it's always called for the main menu.
    """

    if menuid != "mainmenu":
        return []

    return [("MediaPlayer3", main, "mediaplayer3", 50)]


def Plugins(**kwargs):
    """
    Register plugin.

    Build 0010, BUILD_0010_PLAN.md "Main Menu Integration": "Settings
    shall provide an option to add MediaPlayer3 to the Enigma2 main
    menu." Enigma2 calls this function once when the plugin list is
    loaded (startup, or an explicit plugin-list rescan) -- not
    something this file can re-trigger itself when the Settings value
    changes later, so config_manager.get() here reads whatever was
    saved the LAST time Enigma2 loaded plugins, meaning a GUI restart
    (or reboot) is needed after toggling this Settings entry before
    the main menu entry actually appears or disappears -- documented
    directly in the Settings entry's own label ("restart required")
    rather than left as a surprise.

    The Extensions/Plugin menu entry (WHERE_PLUGINMENU) is always
    registered regardless of this setting -- this only adds an
    additional, optional WHERE_MENU entry alongside it.
    """

    descriptors = [
        PluginDescriptor(
            name="MediaPlayer3",
            description="Modern audio player for Enigma2",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main,
        ),
    ]

    if config_manager.get("general.show_in_main_menu", False):

        descriptors.append(
            PluginDescriptor(
                name="MediaPlayer3",
                description="Modern audio player for Enigma2",
                where=PluginDescriptor.WHERE_MENU,
                fnc=mainMenu,
            )
        )

    return descriptors


#end_of_file

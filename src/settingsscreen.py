# ==============================================================================
#
# MediaPlayer3
#
# File        : settingsscreen.py
#
# Description :
#
#     SettingsScreen
#
#     User configurable settings. Never performs playback, directory
#     browsing or Enigma2 service control -- it talks only to
#     ConfigurationManager (config.py) and Logger.
#
# Implements :
#
#     SETTINGSSCREEN_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md v0.3
#
# Project :
#
#     MediaPlayer3
#
# License :
#
#     GPL-2.0-or-later
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-07-12  Build 0004
#   - Initial version.
#
# 2026-07-14  Build 0005
#   - "Automatically play next track" is now a real, active setting
#     (previously listed as "(future)").
#   - Added User Interface category: Show progress bar / elapsed time /
#     remaining time / playback state -- MainScreen presentation
#     toggles (SETTINGSSCREEN_SPEC.md section 6).
#   - _wasDeveloperModeVisible() no longer hardcodes the base entry
#     count, so future entries don't silently break Developer Mode's
#     show/hide rebuild logic.
#
# 2026-07-19  Build 0006
#   - Added Language, Skin and Theme entries (SKIN_MANAGER_SPEC.md /
#     LOCALIZATION_MANAGER_SPEC.md). Changes apply immediately to
#     LocalizationManager/SkinManager -- newly-opened Screens (e.g.
#     Main Menu) reflect the change right away since they read
#     colors/translations at their own open time; MainScreen's own
#     already-built skin (fixed once per Screen.__init__ by Enigma2)
#     picks up the change on its next creation (app restart), not
#     while it stays open -- this is a real Enigma2 Screen/skin
#     limitation, not something SettingsScreen can work around from
#     outside MainScreen (see docs/Claude_notes_build0006.txt).
#
# 2026-07-19  Build 0006 (device test round 1)
#   - Added "Custom background color" entry, shown only when Theme is
#     set to "custom" -- requested after a real device test.
#   - Visibility bookkeeping (which conditional entries are shown)
#     replaced with an explicit (developer_mode, is_custom_theme)
#     tuple comparison instead of a fragile "list length changed"
#     check, now that there are two independent conditional entries
#     instead of one.
#
# 2026-07-19  Build 0006 (device test round 3)
#   - Startup directory is now picked via LocationBox (a directory
#     browser), instead of typed as plain text -- requested after a
#     real device test.
#   - Added "Seek step (seconds)" entry (playback.seek_step_seconds).
#
# 2026-07-19  Build 0006 (device test round 4)
#   - Directory browser now shows a clear on-screen instruction
#     ("Browse to the desired directory, then press GREEN...")
#     confirming how to confirm a selection, per user feedback that
#     GREEN worked but wasn't documented on screen.
#
# 2026-07-19  Build 0007
#   - Added Radio default country/language, navigation mode, history
#     size entries. Added YELLOW: "Clear radio history"
#     (BUILD_0007_PLAN.md "History may be cleared from Settings.") --
#     a deliberate, limited use of a colour button for a genuinely
#     occasional, optional action, per user guidance.
#
# 2026-07-24  Build 0007 (device test round 3)
#   - Added "Resume radio station on start" (radio.resume_on_start).
#
# 2026-07-24  Build 0007 (device test round 5)
#   - Added INFO handling: SettingsScreen previously had no
#     "InfoActions" context at all, showing Enigma2's "unhandled key"
#     indicator (same audit that found PlaylistScreen missing it,
#     confirmed on OpenATV). Shows the currently selected entry's name
#     and value.
#
# 2026-07-24  Build 0007 (device test round 6)
#   - INFO handling now uses compatibility.getInfoKeyActionNames()
#     instead of a hardcoded "info"/"showEventInfo" pair: OpenATV on a
#     VU+ remote has no physical INFO button at all -- EPG substitutes
#     for it, generating KEY_EPG rather than KEY_INFO, resolving (per
#     a device log's static context dump) to action
#     "showEventInfoPlugin" via the "InfobarEPGActions" context, which
#     no screen previously included.
#
# 2026-07-25  Build 0007 (device test round 8)
#   - Fullscreen skin (position=0,0, scaled from a design canvas,
#     theme background colour), matching MainScreen's own approach
#     since Build 0005 -- requested so the box's own background never
#     shows through and the theme's background colour (e.g. the new
#     Gray theme, #A0A0A0) fills the whole display consistently.
#
# 2026-07-26  Build 0007 (device test round 9)
#   - Fixed a real bug confirmed by device screenshots: every text
#     Label widget showed a solid black backdrop instead of the
#     theme's background colour (visible as black boxes around all
#     text against the new Gray theme's #A0A0A0 background) -- and,
#     per the user, would show the box's own live video/background
#     bleeding through instead of solid colour if TV were playing
#     underneath. Root cause: Enigma2 Label widgets paint an opaque
#     backdrop by default (the exact issue MainScreen itself hit and
#     fixed back in Build 0005 -- see this file's own July 2026
#     Build 0005 entry) -- MainScreen's widgets already had
#     transparent="1" + foregroundColor set, but this screen's own
#     Build 0007 round 8 fullscreen conversion never added it. Added
#     transparent="1" and foregroundColor="{text_color}" to every
#     Label-type widget, matching MainScreen's own working pattern.
#
# 2026-07-26  Build 0007 (device test round 10)
#   - Replaced every pure-black (#000000) background default with a
#     near-black grey (#0A0A0A) -- requested per user hypothesis after
#     device testing showed the box's own video/background still
#     bleeding through wherever a screen's background was pure black,
#     even with backgroundColor/transparent set correctly (round 9).
#     Pure black (RGB 0,0,0) is a well-known chroma-key value on many
#     DVB/Enigma2 receivers, where the OSD plane treats exact black as
#     "show the video plane instead" rather than painting a solid
#     black pixel; #0A0A0A is visually indistinguishable from black
#     but numerically avoids the exact-match key.
#
# 2026-07-26  Build 0007 (device test round 11)
#   - Round 10's near-black fix (#0A0A0A) still didn't stop the box's
#     own video/background showing through, confirmed by a device
#     screenshot (Main Menu). The user provided the real cause and the
#     device's own skin.xml as evidence: Enigma2 skin colours are
#     8-digit "#AARRGGBB", and a bare 6-digit "#RRGGBB" value leaves
#     the alpha channel to be read unpredictably rather than reliably
#     opaque -- this device's own skin.xml defines "black" as
#     "#00000000", not "#000000". background_color (and any other
#     colour used as a backgroundColor attribute) is now passed
#     through skin.to_opaque_skin_color(), which prepends an explicit
#     "00" (opaque, in Enigma2's inverted alpha convention) alpha
#     byte -- foregroundColor/text is untouched, since that isn't
#     where this failure mode occurs.
#
# 2026-07-27  Build 0007 (device test round 12)
#   - Round 11's 8-digit opaque-alpha fix still didn't stop the box's
#     own video/background showing through behind text (confirmed by
#     a further device screenshot). The user found, empirically, that
#     a WHITE background reliably avoids the issue where gray/near-
#     black backgrounds don't (visible directly in the screenshot:
#     Main Menu's first rows render on a solid opaque white bar while
#     the rest of the list shows the background through). Every text-
#     bearing widget (Label AND List types) now uses a fixed white
#     background + near-black text (skin.PANEL_BACKGROUND_COLOR /
#     PANEL_TEXT_COLOR) instead of the active theme's own background/
#     text colours -- the outer screen background (edges) still uses
#     the theme colour ("Reunat saavat jäädä harmaiksi").
#
# 2026-07-28  Build 0008
#   - Added HELP key handling: opens HelpScreen with this screen's own
#     context-sensitive help document via HelpManager.getHelp(). HELP
#     key action names are PROVISIONAL/unverified on real hardware --
#     see compatibility.py's HELP_KEY_ACTIONS.
#
# 2026-07-29  Build 0008 (device test round 1)
#   - Added "Music Library directory" (cfg.library.scan_directory),
#     using the exact same LocationBox directory browser as Startup
#     directory -- requested after real device testing ("Asetuksissa
#     voisi olla music library kansion valinta samalla tavalla kuin on
#     browserilla"). Generalized _openDirectoryPicker()/
#     _directoryPicked() to work with either directory setting instead
#     of only Startup directory.
# ------------------------------------------------------------------------------

from __future__ import annotations

from Components.ActionMap import ActionMap
from Components.config import getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from .compatibility import compatibility
from .help_manager import help_manager
from .help_screen import HelpScreen
from .config import cfg, config_manager
from .internetradio_manager import internetradio_manager
from .localization import _, localization_manager
from .logger import logger
from .mainmenu import MainMenu
from .paths import ensure_trailing_slash
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)


class SettingsScreen(Screen, ConfigListScreen):
    """
    User configuration screen.

    Settings are grouped into the categories defined in
    SETTINGSSCREEN_SPEC.md section 4: General, Playback, Logging,
    Developer. "Restore TV service on Exit" is only shown once
    Developer Mode is enabled, and is not part of normal Settings
    (SETTINGSSCREEN_SPEC.md section 5).
    """

    SPECIFICATION_VERSION = "0.7"
    ARCHITECTURE_VERSION = "0.3"

    DESIGN_WIDTH = 600
    DESIGN_HEIGHT = 450

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build SettingsScreen's skin for an exact `width` x `height`
        window, scaling from the 600x450 design resolution above --
        see BrowserScreen._buildSkin() for the pattern this follows
        (Build 0007, device test round 8).
        """

        sx = width / SettingsScreen.DESIGN_WIDTH
        sy = height / SettingsScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3SettingsScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Settings">

            <widget name="config"
                    {rect(20, 20, 560, 380)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="hint"
                    {rect(20, 410, 560, 30)}
                    {font(14)}
                    halign="center"
                    valign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

        </screen>
        """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, session):

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        self.session = session

        self._directory_picker_target = None

        self._initialized = False

        self._log("Created")

        self._log("Initializing")

        self._log("Configuration loaded.")

        self.list = []

        ConfigListScreen.__init__(self, self.list, session=session)

        self["hint"] = self._makeHint()

        actions = {
            "ok": self.keyOK,
            "cancel": self.exitPressed,
            "left": self.keyLeft,
            "right": self.keyRight,
            "menu": self.menuPressed,
            "yellow": self.clearRadioHistoryPressed,
        }

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.infoPressed

        for action_name in compatibility.getHelpKeyActionNames():
            actions[action_name] = self.helpPressed

        self["actions"] = ActionMap(
            ["SetupActions", "MenuActions", "ColorActions", "InfoActions", "InfobarEPGActions", "HelpActions"],
            actions,
            -1,
        )

        self._buildList()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[SettingsScreen] %s", message)

    # ------------------------------------------------------------------

    def _makeHint(self):

        from Components.Label import Label

        return Label(
            "OK: Edit   LEFT/RIGHT: Change   YELLOW: Clear Radio History   MENU: Menu   EXIT: Save & Back"
        )

# End of Part 1
    # ------------------------------------------------------------------
    # Configuration Entries (SETTINGSSCREEN_SPEC.md sections 4-6)
    # ------------------------------------------------------------------

    def _buildList(self) -> None:
        """
        (Re)build the visible configuration entry list.

        Rebuilt whenever Developer Mode or the custom theme selection
        is toggled, since "Disable Restore TV service on Exit"
        (SETTINGSSCREEN_SPEC.md section 5) and "Custom background
        color" (Build 0006) are each only shown under their own
        condition.
        """

        entries = [
            getConfigListEntry("Startup directory", cfg.general.startup_directory),
            getConfigListEntry("Music Library directory", cfg.library.scan_directory),
            getConfigListEntry("Hidden files", cfg.general.hidden_files),
            getConfigListEntry("Language", cfg.general.language),
            getConfigListEntry("Skin", cfg.appearance.skin),
            getConfigListEntry("Theme", cfg.appearance.theme),
        ]

        if cfg.appearance.theme.value == "custom":

            entries.append(
                getConfigListEntry("Custom background color", cfg.appearance.custom_background_color)
            )

        entries += [
            getConfigListEntry("Resume playback (future)", cfg.playback.resume_playback),
            getConfigListEntry("Automatically play next track", cfg.playback.auto_play_next),
            getConfigListEntry("Seek step (seconds)", cfg.playback.seek_step_seconds),
            getConfigListEntry("Lyrics offset step (seconds)", cfg.playback.lyrics_offset_step_seconds),
            getConfigListEntry("Radio default country", cfg.radio.default_country),
            getConfigListEntry("Radio default language", cfg.radio.default_language),
            getConfigListEntry("Radio navigation mode", cfg.radio.navigation_mode),
            getConfigListEntry("Radio history size", cfg.radio.history_size),
            getConfigListEntry("Resume radio station on start", cfg.radio.resume_on_start),
            getConfigListEntry(
                "Use ExtEplayer3 for radio"
                + (" (asennettu)" if compatibility.isExtEplayer3Available() else " (EI asennettu)"),
                cfg.radio.use_exteplayer3,
            ),
            getConfigListEntry("Yle EPG app_id", cfg.epg.yle_app_id),
            getConfigListEntry("Yle EPG app_key", cfg.epg.yle_app_key),
            getConfigListEntry("Show progress bar", cfg.ui.show_progress_bar),
            getConfigListEntry("Show elapsed time", cfg.ui.show_elapsed_time),
            getConfigListEntry("Show remaining time", cfg.ui.show_remaining_time),
            getConfigListEntry("Show playback state", cfg.ui.show_playback_state),
            getConfigListEntry("Enable debug logging", cfg.logging.debug_logging),
            getConfigListEntry("Developer logging level", cfg.logging.developer_level),
            getConfigListEntry("Developer Mode", cfg.developer.developer_mode),
        ]

        if cfg.developer.developer_mode.value:

            entries.append(
                getConfigListEntry(
                    "Disable Restore TV service on Exit",
                    cfg.developer.disable_restore_tv_on_exit,
                )
            )

        self.list = entries

        self["config"].setList(self.list)

        self._last_visibility_state = (cfg.developer.developer_mode.value, cfg.appearance.theme.value == "custom")

    # ------------------------------------------------------------------
    # Event Handlers (SETTINGSSCREEN_SPEC.md section 7)
    # ------------------------------------------------------------------

    def keyLeft(self) -> None:

        logger.verbose("[SettingsScreen] LEFT pressed.")

        ConfigListScreen.keyLeft(self)

        self._afterChange()

    # ------------------------------------------------------------------

    def keyRight(self) -> None:

        logger.verbose("[SettingsScreen] RIGHT pressed.")

        ConfigListScreen.keyRight(self)

        self._afterChange()

    # ------------------------------------------------------------------

    def keyOK(self) -> None:

        logger.verbose("[SettingsScreen] OK pressed.")

        # Build 0006 (device test round 3) -- Startup directory is
        # picked via a directory browser instead of typed text,
        # requested after real device feedback ("Voisiko settings -
        # startup directory valita browserilla, kuten tiedostot?").
        # Build 0008 -- Music Library directory uses the exact same
        # picker, requested the same way ("Asetuksissa voisi olla
        # music library kansion valinta samalla tavalla kuin on
        # browserilla").
        directory_config = self._directoryPickerTarget()

        if directory_config is not None:

            self._openDirectoryPicker(directory_config)

            return

        current = self.getCurrentEntry()

        previous_value = self.getCurrentValue()

        ConfigListScreen.keyOK(self)

        self._log(f"Configuration updated: {current}")

        if self._developerVerbose():

            self._log(f"Previous value: {previous_value}")

        self._afterChange()

    # ------------------------------------------------------------------

    def _directoryPickerTarget(self):
        """
        Return the ConfigText element the directory browser should
        edit, if the currently selected entry is one of the
        directory-valued settings (Startup directory / Music Library
        directory) -- otherwise None.
        """

        try:
            current = self["config"].getCurrent()

            if current is None or len(current) <= 1:
                return None

            element = current[1]

            if element is cfg.general.startup_directory or element is cfg.library.scan_directory:
                return element

            return None

        except Exception as error:

            logger.verbose(f"[SettingsScreen] Unable to check current entry: {error}")

            return None

    # ------------------------------------------------------------------

    def infoPressed(self) -> None:
        """
        Build 0007, device test round 5 -- SettingsScreen previously
        had no INFO handling at all, showing Enigma2's "unhandled
        key" indicator (same audit that found PlaylistScreen missing
        it, confirmed on OpenATV). Shows the currently selected
        entry's name and value.
        """

        logger.verbose("[SettingsScreen] INFO pressed.")

        current = self.getCurrentEntry()

        value = self.getCurrentValue()

        if current is None:
            return

        self.session.open(MessageBox, f"{current}\n\n{value}", MessageBox.TYPE_INFO)

    # ------------------------------------------------------------------

    def helpPressed(self) -> None:
        """
        Build 0008 -- opens HelpScreen with SettingsScreen's own
        context-sensitive help document.
        """

        logger.verbose("[SettingsScreen] HELP pressed.")

        title, content = help_manager.getHelp("settingsscreen")

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------

    def clearRadioHistoryPressed(self) -> None:
        """
        Build 0007 -- BUILD_0007_PLAN.md "History may be cleared from
        Settings." Bound to YELLOW: a genuinely occasional, optional
        action, unlike core navigation, so a colour button is a
        reasonable fit here.
        """

        logger.verbose("[SettingsScreen] YELLOW pressed.")

        self.session.openWithCallback(
            self._radioHistoryClearConfirmed,
            MessageBox,
            _("Clear Internet Radio listening history?"),
            MessageBox.TYPE_YESNO,
        )

    # ------------------------------------------------------------------

    def _radioHistoryClearConfirmed(self, confirmed) -> None:

        if not confirmed:
            return

        internetradio_manager.clearHistory()

        self._log("Radio history cleared.")

    # ------------------------------------------------------------------

    def _openDirectoryPicker(self, target_config) -> None:

        try:
            from Screens.LocationBox import LocationBox

        except ImportError as error:

            self._log(f"Directory browser unavailable: {error}")

            return

        self._directory_picker_target = target_config

        current_directory = ensure_trailing_slash(target_config.value)

        label = _("Startup directory") if target_config is cfg.general.startup_directory else _("Music Library directory")

        self._log(f"Opening directory browser for {label}.")

        self.session.openWithCallback(
            self._directoryPicked,
            LocationBox,
            text=_("Browse to the desired directory, then press GREEN to set it as the {0}").format(label),
            currDir=current_directory,
        )

    # ------------------------------------------------------------------

    def _directoryPicked(self, path=None) -> None:

        if not path:

            self._log("Directory browser closed without a selection.")

            return

        path = ensure_trailing_slash(path)

        self._directory_picker_target.value = path

        self._log(f"Startup directory changed via browser: {path}")

        self._buildList()

    # ------------------------------------------------------------------

    def _afterChange(self) -> None:

        # Build 0006 -- apply language/skin/theme changes immediately,
        # rather than waiting for a restart, so the user can see the
        # effect right away. Each call falls back safely on its own
        # if the new value turns out to be invalid.
        if cfg.general.language.value != localization_manager.getLanguage():

            localization_manager.setLanguage(cfg.general.language.value)

        if cfg.appearance.skin.value != skin_manager.getSkinName():

            skin_manager.loadSkin(cfg.appearance.skin.value)

        if cfg.appearance.theme.value != skin_manager.getThemeName():

            skin_manager.loadTheme(cfg.appearance.theme.value)

        if skin_manager.getThemeName() == "custom":

            skin_manager.setCustomColor("background", cfg.appearance.custom_background_color.value)

        # Developer Mode and the custom theme each show/hide their own
        # extra entry -- rebuild only when that visibility actually
        # changed, so a plain value edit doesn't reset the list
        # widget's cursor position on every keypress.
        visibility_state = (cfg.developer.developer_mode.value, cfg.appearance.theme.value == "custom")

        if visibility_state != self._last_visibility_state:

            self._buildList()

    # ------------------------------------------------------------------

    def menuPressed(self) -> None:
        """
        Open Main Menu (SETTINGSSCREEN_SPEC.md section 7).
        """

        logger.verbose("[SettingsScreen] MENU pressed.")

        self._saveConfiguration()

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "settings"):
            return

        # Any other destination is handled by MainScreen: close this
        # screen and forward the chosen action so MainScreen can open
        # the requested Screen next.
        self._log("Returning to Main Menu.")

        self._close(action_id)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:
        """
        Save changes and return to the previous screen
        (SETTINGSSCREEN_SPEC.md section 7).
        """

        logger.verbose("[SettingsScreen] EXIT pressed.")

        self._saveConfiguration()

        self._log("Returning to Main Menu.")

        self._close(None)

    # ------------------------------------------------------------------

    def _close(self, result=None) -> None:
        """
        Standard lifecycle close: logs Closing/Closed and returns to
        the previous screen with `result`.
        """

        self._log("Closing")

        self._log("Closed")

        self.close(result)

# End of Part 2
    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _saveConfiguration(self) -> None:

        self._log("Saving configuration.")

        config_manager.save()

        self._log("Configuration saved.")

    # ------------------------------------------------------------------

    def _developerVerbose(self) -> bool:

        from .logger import DEVELOPER_MODE_VERBOSE

        return config_manager.getDeveloperLogLevel() == DEVELOPER_MODE_VERBOSE

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"SettingsScreen(initialized={self._initialized})"


# ==============================================================================
#
# Build Notes
#
# SettingsScreen communicates only with ConfigurationManager (config.py)
# and Logger. It never talks to PlaybackController, ServiceController,
# Compatibility or NavigationInstance directly, per
# SETTINGSSCREEN_SPEC.md section 8.
#
# "Restore TV service on Exit" always defaults to enabled
# (disable_restore_tv_on_exit == False) and is only ever shown while
# Developer Mode is on, per SETTINGSSCREEN_SPEC.md section 5.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

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

import os

from enigma import ePicLoad, eTimer

from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.config import getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
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
from .paths import ensure_trailing_slash, SKIN_PATH
from .skin import skin_manager, to_opaque_skin_color

# Device test round 59 -- background-image variant/tier system, a
# copy of MusicLibraryScreen's own (round 39/46). Simpler than every
# other converted screen: SettingsScreen has a single always-focused
# list (no multiple panels to switch between), so there's only ONE
# background image per variant/tier -- no per-state swapping, no
# normal/active header pair, the header is always shown in its own
# "active" colour.
SETTINGS_SKIN_VARIANTS = ("light", "dark")

SETTINGS_DEFAULT_SKIN_VARIANT = "light"

SETTINGS_SKIN_PALETTES = {
    "light": {
        "panel_background_color": "#F9F9F9",
        "list_background_color": "#EAEAEA",
        "panel_text_color": "#1A1A1A",
        "header_fg": "#036DFA",
        "hint_fg": "#036DFA",
        "info_label_fg": "#036DFA",
        "selected_row_bg": "#A491FB",
        "selected_row_fg": "#1A1A1A",
    },
    "dark": {
        "panel_background_color": "#1C202B",
        "list_background_color": "#161922",
        "panel_text_color": "#F0F0F0",
        "header_fg": "#FFFFFF",
        "hint_fg": "#F0F0F0",
        "info_label_fg": "#7B9FE0",
        "selected_row_bg": "#2B2F39",
        "selected_row_fg": "#C7AC4E",
    },
}


def _resolveSettingsSkinVariant() -> str:

    variant = config_manager.get("appearance.skin", SETTINGS_DEFAULT_SKIN_VARIANT)

    if variant not in SETTINGS_SKIN_VARIANTS:
        return SETTINGS_DEFAULT_SKIN_VARIANT

    return variant


def _resolveSettingsResolutionTier(screen_width: int) -> str:

    return "hd" if screen_width >= 1000 else "sd"


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

    # Device test round 59 -- changed from 600x465 to 1672x941,
    # matching MusicLibraryScreen's own round 39 reasoning.
    DESIGN_WIDTH = 1672
    DESIGN_HEIGHT = 941

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Device test round 59 -- reuses MusicLibraryScreen's own
        background-image approach (per direct request), simplified
        for a single always-focused list: one header (a gear icon,
        always shown "active"), one wide config list, an info area
        showing the currently selected setting's own help text (new
        this round), and a 5-item hint row (including a fixed-colour
        YELLOW remote-button icon, unrecoloured unlike every other
        hint icon -- see the background image generation script's own
        comment for why).
        """

        sx = width / SettingsScreen.DESIGN_WIDTH
        sy = height / SettingsScreen.DESIGN_HEIGHT

        self._screen_width = width

        self._screen_height = height

        self._skin_variant = _resolveSettingsSkinVariant()

        palette = SETTINGS_SKIN_PALETTES[self._skin_variant]

        panel_background_color = to_opaque_skin_color(palette["panel_background_color"])
        panel_text_color = palette["panel_text_color"]

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Bold;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3SettingsScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{panel_background_color}"
                title="MediaPlayer3 - Settings">

            <widget name="background"
                    position="0,0"
                    size="{width},{height}"
                    alphatest="blend"/>

            <widget name="header_title"
                    {rect(88, 80, 1500, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_fg']}"
                    transparent="1"/>

            <widget name="config"
                    {rect(40, 138, 1590, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="info"
                    {rect(60, 702, 1550, 130)}
                    {font(26)}
                    halign="center"
                    valign="center"
                    foregroundColor="{palette['info_label_fg']}"
                    backgroundColor="{panel_background_color}"/>

            <widget name="hint_text_ok"
                    {rect(72, 874, 156, 63)}
                    font="Bold;{max(10, int(21 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_leftright"
                    {rect(274, 874, 255, 63)}
                    font="Bold;{max(10, int(21 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_yellow"
                    {rect(575, 874, 378, 63)}
                    font="Bold;{max(10, int(21 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_menu"
                    {rect(999, 874, 171, 63)}
                    font="Bold;{max(10, int(21 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_exit"
                    {rect(1216, 874, 296, 63)}
                    font="Bold;{max(10, int(21 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

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

        # Device test round 63 -- moved to BEFORE ConfigListScreen.
        # __init__() below, which creates "config" internally: this
        # project's own Round 7 paint-order rule (earlier self[name]=
        # ... insertion paints underneath) means "background" must be
        # inserted first. It was backwards here -- ConfigListScreen.
        # __init__() ran first, so "config" was inserted before
        # "background", and the background image painted ON TOP of
        # the list once decoded. Confirmed directly: disabling the
        # background entirely (round 62's own diagnostic) fixed the
        # list's own text rendering completely, and the user's own
        # description ("kuva latautui tekstin päälle ja kuulsi vähän
        # läpi") matches this exactly.
        self["background"] = Pixmap()

        self._background_picload = ePicLoad()

        compatibility.connectPictureDataSignal(self._background_picload, self._onBackgroundImageDecoded)

        ConfigListScreen.__init__(self, self.list, session=session)

        self["header_title"] = Label(_("Settings"))

        # Device test round 59 -- new: shows the currently selected
        # setting's own short help text, per direct request
        # ("Info-ikkunassa voisi olla asetuskohtainen ohje"). Didn't
        # exist before this round.
        self["info"] = Label("")

        self["hint_text_ok"] = Label(_("OK: Edit"))
        self["hint_text_leftright"] = Label(_("LEFT/RIGHT: Change"))
        self["hint_text_yellow"] = Label(_("YELLOW: Clear Radio History"))
        self["hint_text_menu"] = Label(_("MENU: Menu"))
        self["hint_text_exit"] = Label(_("EXIT: Save & Back"))

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

        # Device test round 62's own diagnostic (temporarily disabling
        # this call) confirmed the background image was the cause of
        # the reported "list flashes then fades" symptom -- round 63
        # found and fixed the real root cause (a widget insertion-
        # order bug: "background" was being created AFTER
        # ConfigListScreen.__init__() had already created "config"
        # internally, so the background painted on top of the list
        # once decoded, instead of underneath it). Re-enabled now that
        # the actual fix is in place.
        self._decodeBackgroundImage()

        self._updateSettingInfo()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[SettingsScreen] %s", message)

    # ------------------------------------------------------------------

# End of Part 1
    # ------------------------------------------------------------------
    # Configuration Entries (SETTINGSSCREEN_SPEC.md sections 4-6)
    # ------------------------------------------------------------------

    def _buildList(self) -> None:
        """
        (Re)build the visible configuration entry list.

        Rebuilt whenever the custom theme selection is toggled, since
        "Custom background color" (Build 0006) is only shown under
        its own condition. Device test round 31: "Disable Restore TV
        service on Exit" / "Developer Mode" no longer exist as
        separate concepts (Developer Mode now derives directly from
        Logging Level -- see config_manager.isDeveloperMode()), so
        rebuilding no longer needs to react to either.
        """

        entries = [
            getConfigListEntry(_("Startup directory"), cfg.general.startup_directory),
            getConfigListEntry(_("Music Library directory"), cfg.library.scan_directory),
            getConfigListEntry(_("Hidden files"), cfg.general.hidden_files),
            getConfigListEntry(_("Show in main menu (restart required)"), cfg.general.show_in_main_menu),
            # Device test round 31: deliberately NOT translated
            # ("Language saa olla kaantamatta, niin sen loytaa vaikka
            # tulisi joskus erikoisempiakin kielia kayttoon") -- this
            # entry must stay findable by its English label regardless
            # of which language is currently active, including a
            # future one nobody has added a translation for yet.
            getConfigListEntry("Language", cfg.general.language),
            getConfigListEntry(_("Skin"), cfg.appearance.skin),
            getConfigListEntry(_("Theme"), cfg.appearance.theme),
        ]

        if cfg.appearance.theme.value == "custom":

            entries.append(
                getConfigListEntry(_("Custom background color"), cfg.appearance.custom_background_color)
            )

        entries += [
            getConfigListEntry(_("Resume playback (future)"), cfg.playback.resume_playback),
            getConfigListEntry(_("Automatically play next track"), cfg.playback.auto_play_next),
            getConfigListEntry(_("Seek step (seconds)"), cfg.playback.seek_step_seconds),
            getConfigListEntry(_("Lyrics offset step (seconds)"), cfg.playback.lyrics_offset_step_seconds),
            getConfigListEntry(_("Use ffprobe for codec info"), cfg.playback.enable_ffprobe),
            getConfigListEntry(_("Radio default country"), cfg.radio.default_country),
            getConfigListEntry(_("Radio default language"), cfg.radio.default_language),
            getConfigListEntry(_("Radio navigation mode"), cfg.radio.navigation_mode),
            getConfigListEntry(_("Radio history size"), cfg.radio.history_size),
            getConfigListEntry(_("Resume radio station on start"), cfg.radio.resume_on_start),
            getConfigListEntry(
                _("Use ExtEplayer3 for radio")
                + (_(" (installed)") if compatibility.isExtEplayer3Available() else _(" (NOT installed)")),
                cfg.radio.use_exteplayer3,
            ),
            getConfigListEntry(_("Yle EPG app_id"), cfg.epg.yle_app_id),
            getConfigListEntry(_("Yle EPG app_key"), cfg.epg.yle_app_key),
            getConfigListEntry(_("Podcast Index API key"), cfg.podcast.podcastindex_api_key),
            getConfigListEntry(_("Podcast Index API secret"), cfg.podcast.podcastindex_api_secret),
            getConfigListEntry(_("Show progress bar"), cfg.ui.show_progress_bar),
            getConfigListEntry(_("Show elapsed time"), cfg.ui.show_elapsed_time),
            getConfigListEntry(_("Show remaining time"), cfg.ui.show_remaining_time),
            getConfigListEntry(_("Show playback state"), cfg.ui.show_playback_state),
            getConfigListEntry(_("Log station codec info (Internet Radio)"), cfg.logging.log_station_codecs),
            getConfigListEntry(_("Logging level"), cfg.logging.developer_level),
        ]

        self.list = entries

        self["config"].setList(self.list)

        self._last_visibility_state = (cfg.appearance.theme.value == "custom",)

    # ------------------------------------------------------------------

    # Device test round 59 -- one short help line per setting, shown
    # in the new "info" widget as the selection moves. Keyed by the
    # exact translated label text used above in _buildList() (matches
    # what self["config"].getCurrent()[0] returns for the selected
    # row) -- one entry ("Use ExtEplayer3 for radio") has a dynamic
    # "(installed)"/"(NOT installed)" suffix appended at build time,
    # so it's matched by prefix instead of exact equality below.
    _SETTING_DESCRIPTIONS = {
        _("Startup directory"): _("Folder the file Browser opens in by default."),
        _("Music Library directory"): _("Folder scanned for the Music Library."),
        _("Hidden files"): _("Show files and folders starting with a dot."),
        _("Show in main menu (restart required)"): _("Add MediaPlayer3 to the main menu."),
        "Language": _("Interface language."),
        _("Skin"): _("Light or dark background style for the redesigned screens."),
        _("Theme"): _("Colour theme for screens not yet using the new skin."),
        _("Custom background color"): _("Background colour used when Theme is set to Custom."),
        _("Resume playback (future)"): _("Resume the last track on startup (not yet implemented)."),
        _("Automatically play next track"): _("Play the next track when one finishes."),
        _("Seek step (seconds)"): _("How far each seek key press moves playback."),
        _("Lyrics offset step (seconds)"): _("How far each lyrics-offset key press shifts timing."),
        _("Use ffprobe for codec info"): _("Detect the real codec/bitrate instead of guessing from the file extension."),
        _("Radio default country"): _("Country filter Internet Radio starts with."),
        _("Radio default language"): _("Language filter Internet Radio starts with."),
        _("Radio navigation mode"): _("Whether CH+/CH- browses favourites or history."),
        _("Radio history size"): _("How many recently played stations to remember."),
        _("Resume radio station on start"): _("Reopen the last playing station automatically."),
        _("Use ExtEplayer3 for radio"): _("Use the ExtEplayer3 backend for Internet Radio playback."),
        _("Yle EPG app_id"): _("API app_id for Yle radio programme data."),
        _("Yle EPG app_key"): _("API app_key for Yle radio programme data."),
        _("Podcast Index API key"): _("API key for searching podcasts."),
        _("Podcast Index API secret"): _("API secret for searching podcasts."),
        _("Show progress bar"): _("Show the playback progress bar on the Player screen."),
        _("Show elapsed time"): _("Show elapsed time on the Player screen."),
        _("Show remaining time"): _("Show remaining time on the Player screen."),
        _("Show playback state"): _("Show Playing/Paused status on the Player screen."),
        _("Log station codec info (Internet Radio)"): _("Write detected station codec info to the log."),
        _("Logging level"): _("How much detail is written to the log file."),
    }

    def _updateSettingInfo(self) -> None:

        try:
            current = self["config"].getCurrent()

        except Exception:

            current = None

        if not current:

            self["info"].setText("")

            return

        label = current[0]

        description = self._SETTING_DESCRIPTIONS.get(label)

        if description is None:

            # The one dynamic-suffix entry ("Use ExtEplayer3 for
            # radio (installed)"/"(NOT installed)") won't match the
            # dict's own exact key -- match by prefix instead.
            for key, value in self._SETTING_DESCRIPTIONS.items():

                if label.startswith(key):

                    description = value

                    break

        self["info"].setText(description or "")

    # ------------------------------------------------------------------

    def selectionChanged(self) -> None:

        ConfigListScreen.selectionChanged(self)

        self._updateSettingInfo()

    # ------------------------------------------------------------------
    # Background image (device test round 59 -- simpler than every
    # other converted screen: a single state, decoded once, no
    # per-focus swapping needed.)
    # ------------------------------------------------------------------

    def _decodeBackgroundImage(self) -> None:

        if self["background"].instance is None:

            logger.verbose("[SettingsScreen] background widget not ready yet, retrying decode shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(self._decodeBackgroundImage)

            retry_timer.start(100, True)

            self._pending_background_retry_timer = retry_timer

            return

        image_path = os.path.join(
            SKIN_PATH,
            self._skin_variant,
            _resolveSettingsResolutionTier(self._screen_width),
            "settings_background.png",
        )

        try:
            width, height = self._screen_width, self._screen_height

            aspect = AVSwitch().getFramebufferScale()

            self._background_picload.setPara((width, height, aspect[0], aspect[1], False, 1, "#00000000"))

            if self._background_picload.startDecode(image_path) != 0:
                raise RuntimeError("startDecode() reported failure")

        except Exception as error:

            logger.verbose(f"[SettingsScreen] Unable to decode background image {image_path}: {error}")

    # ------------------------------------------------------------------

    def _onBackgroundImageDecoded(self, picture_info=None) -> None:

        try:
            pixmap = self._background_picload.getData()

            if pixmap is None:
                return

            self["background"].instance.setPixmap(pixmap)

            self["background"].show()

        except Exception as error:

            logger.verbose(f"[SettingsScreen] Unable to apply decoded background image: {error}")

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
        visibility_state = (cfg.appearance.theme.value == "custom",)

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

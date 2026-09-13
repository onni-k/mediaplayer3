# ==============================================================================
#
# MediaPlayer3
#
# File        : browserscreen.py
#
# Description :
#
#     BrowserScreen
#
#     Local file browsing and playlist building. BrowserScreen is a
#     *temporary* screen: it is opened from MainScreen when the user
#     wants to browse local storage, and it returns to MainScreen
#     either after playback has started or on EXIT/MENU.
#
#     Build 0010 -- three-column browsing model (BUILD_0010_PLAN.md
#     "Local File Browser" / "File Browser Actions"), structurally
#     following PodcastScreen's own three-column pattern (same
#     LEFT/RIGHT column-focus model, ChoiceBox action menus, two-tier
#     column header highlighting):
#
#         Directories | Files | Playlist
#
#     The left column browses the directory tree (subdirectories of
#     the current root, plus ".." to go up). The middle column
#     previews the supported audio files inside whichever directory is
#     currently *selected* in the left column (auto-updates on
#     selection change, exactly like PodcastScreen's Episodes column
#     already does for the podcast selected in Available/Subscribed --
#     BUILD_0010_PLAN.md: "The middle column contains files in the
#     selected directory."). The right column shows the current
#     working playlist, which OK's per-column action menus add to.
#
#     BUILD_0010_PLAN.md's own "File Browser Actions" section lists
#     OK's per-column action menu contents but -- confirmed with the
#     user directly, since LEFT/RIGHT is already committed to column
#     switching and LEFT/RIGHT/OK is otherwise fully accounted for --
#     does not say how a directory is actually *entered* (descended).
#     Fixed by adding one extra item, "Open directory", to the
#     Directories column's OK menu alongside the plan's own "Add
#     entire directory to playlist" -- deliberately a small, explicit
#     deviation from the plan's literal wording rather than a silent
#     one. Two further small, equally-flagged additions for the same
#     "this literally cannot function without it" reason:
#
#       - PLAY (existing hardware key, used throughout this project)
#         still starts playback directly -- from Directories (queue =
#         entire previewed directory, like Build 0007's "Play Folder"),
#         Files (queue = previewed directory, starting at the selected
#         file) or Playlist (the current playlist, starting at the
#         selected track). BUILD_0010_PLAN.md's OK-menu lists never
#         include a "Play" item themselves (this screen becomes
#         primarily a playlist-building tool, per the plan's own
#         framing), so without this, nothing in the new design could
#         ever actually start playback -- and the plan is explicit
#         that "the existing playback and playlist handling shall
#         remain unchanged".
#       - INFO opens a "Select Playlist" picker (existing playlist,
#         or create new), settable at any time, not just implicitly on
#         first Add. Without this there would be no way to switch the
#         Playlist column to a different existing playlist once one
#         had been chosen.
#
#     BrowserScreen receives MainScreen's shared PlaybackController
#     instance and forwards playback requests to it -- it never talks
#     to ServiceController, Compatibility or Enigma2 playback services
#     directly (BROWSERSCREEN_SPEC.md section 8).
#
# Implements :
#
#     BROWSERSCREEN_SPEC.md v0.7 (three-column redesign pending a
#     matching spec revision -- see docs/Claude_notes_build0010.txt,
#     Round 6)
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
# 2026-07-04  Build 0001
#   - Initial version (as browser.py, application's primary screen).
#
# 2026-07-10  Build 0003 Revision 1
#   - Layered architecture: playback delegated to PlaybackController.
#
# 2026-07-12  Build 0004
#   - Renamed from browser.py to browserscreen.py.
#   - No longer the primary application window -- MainScreen is.
#   - No longer creates its own PlaybackController; receives the shared
#     instance from MainScreen so playback state survives navigation.
#
# 2026-07-19  Build 0007
#   - Added an INFO context menu for folder/file/playlist-file actions.
#
# 2026-07-28  Build 0008
#   - Added HELP key handling.
#
# 2026-08-09  Build 0010 (round 6)
#   - Full redesign: single-column file list + INFO context menu
#     replaced with the three-column Directories | Files | Playlist
#     model described above. Old single-column implementation is kept
#     in source control history (not reproduced here) rather than
#     inline, per this project's own convention of not carrying dead
#     code forward across a full-screen rewrite.
# ------------------------------------------------------------------------------

"""
browserscreen -- three-column local file browser (Directories | Files |
Playlist), per BUILD_0010_PLAN.md "Local File Browser" / "File Browser
Actions".
"""

from __future__ import annotations

import os
from typing import List, Optional

from enigma import ePicLoad, eTimer

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from .compatibility import compatibility
from .config import cfg, config_manager
from .constants import PLAYLIST_FILE_EXTENSIONS, SUPPORTED_AUDIO_EXTENSIONS
from .guide_manager import guide_manager
from .guide_screen import GuideScreen
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .paths import ensure_trailing_slash
from .coverart_manager import coverart_manager
from .lrclib_manager import lrclib_manager
from .playlist_manager import playlist_manager
from .skin import resolve_skin_asset_path, to_opaque_skin_color

COLUMNS = ("directories", "files", "playlist")

# Device test round 55 -- background-image variant/tier system,
# a copy of MusicLibraryScreen's own (round 39/46) with the same
# light palette values, per the same "reuse Music Library's images
# and colours" request already used for RadioBrowserScreen (round
# 54).
BROWSER_SKIN_VARIANTS = ("light", "dark", "test_skin", "vintage_radio")

BROWSER_DEFAULT_SKIN_VARIANT = "light"

BROWSER_SKIN_PALETTES = {
    "light": {
        "panel_background_color": "#F9F9F9",
        "list_background_color": "#EAEAEA",
        "panel_text_color": "#1A1A1A",
        "header_inactive_fg": "#1E2334",
        "header_active_fg": "#036DFA",
        "hint_fg": "#036DFA",
        "info_label_fg": "#036DFA",
        "selected_row_bg": "#A491FB",
        "selected_row_fg": "#1A1A1A",
    },
    "dark": {
        "panel_background_color": "#1C202B",
        "list_background_color": "#161922",
        "panel_text_color": "#F0F0F0",
        "header_inactive_fg": "#F0F0F0",
        "header_active_fg": "#FFFFFF",
        "hint_fg": "#F0F0F0",
        "info_label_fg": "#7B9FE0",
        "selected_row_bg": "#2B2F39",
        "selected_row_fg": "#C7AC4E",
    },
}

# Round 112, per direct request (a real device crash: KeyError
# 'test_skin' -- round 110 added "test_skin" to this screen's own
# SKIN_VARIANTS whitelist, letting it become the active variant,
# but never added a matching entry HERE, in the separate dict that
# actually supplies its colour palette) -- test_skin starts out
# visually identical to Dark (matches its own bundled template,
# which starts as an exact copy of Dark's PNGs too), and stays in
# sync with any future change to Dark's own palette automatically,
# since this is a reference to the same dict, not a copy of it.

# Round 149, per direct request ("test_skinin muiden ikkunoiden
# väriteema mainscreenin mukaiseksi" -- test_skin's own colours on
# every OTHER window should match MainScreen's): round 112's own
# crash-fix aliased this to Dark's own palette (a plain blue/white
# theme) since test_skin's own PNGs started as Dark copies -- but
# MainScreen's own test_skin has since become a warm amber/brass
# vintage-radio look (round 113 onward) that this alias was never
# updated to follow. Colours only, matching the direct request's own
# scope -- these screens' own background images/icons are untouched,
# so panel_background_color/list_background_color are kept close to
# Dark's own tone, just warmed slightly toward brown for consistency
# with the new amber text sitting on them. Text/accent colours copied
# directly from MainScreen's own test_skin palette (panel_text_color,
# header_inactive_fg, header_active_fg, hint_fg all identical values)
# so a user moving between screens sees one consistent amber, not a
# slightly-different shade per screen.
BROWSER_SKIN_PALETTES["test_skin"] = {
    "panel_background_color": "#1C1610",
    "list_background_color": "#161108",
    "panel_text_color": "#E8A24C",
    "header_inactive_fg": "#C08A45",
    "header_active_fg": "#FFC978",
    "hint_fg": "#FFC978",
    "info_label_fg": "#FFC978",
    "selected_row_bg": "#C08A45",
    "selected_row_fg": "#1A1206",
}

# Round 155, per direct request: an independent copy (not a
# reference) of test_skin's own palette above -- see mainscreen.py's
# own round 155 comment for the full reasoning.
BROWSER_SKIN_PALETTES["vintage_radio"] = {
    "panel_background_color": "#1C1610",
    "list_background_color": "#161108",
    "panel_text_color": "#E8A24C",
    "header_inactive_fg": "#C08A45",
    "header_active_fg": "#FFC978",
    "hint_fg": "#FFC978",
    "info_label_fg": "#FFC978",
    "selected_row_bg": "#C08A45",
    "selected_row_fg": "#1A1206",
}


def _resolveBrowserSkinVariant() -> str:

    variant = config_manager.get("appearance.skin", BROWSER_DEFAULT_SKIN_VARIANT)

    if variant not in BROWSER_SKIN_VARIANTS:
        return BROWSER_DEFAULT_SKIN_VARIANT

    return variant


def _resolveBrowserResolutionTier(screen_width: int) -> str:

    return "hd" if screen_width >= 1000 else "sd"


# CHANNEL UP/DOWN page-step, matching RadioBrowserScreen/PodcastScreen's
# own PAGE_STEP convention for long lists.
PAGE_STEP = 15


def _defaultPlayPlaylistName() -> str:
    """
    Build 0010, device test round 6 -- user request: "Ylikirjoitus-
    riskin voi välttää luomalla suosikin Tiedostot, jota muokataan
    oletuksena." Directories/Files columns' "Play" action (Round 8)
    originally named the created/overwritten playlist after the
    folder or file itself -- risking a silent overwrite of an
    existing, unrelated, hand-curated playlist that happened to share
    that name. Fixed: always use this one fixed, reserved playlist
    name instead (the existing "Files"/"Tiedostot" translation,
    reused rather than inventing a new string) -- only this single
    dedicated playlist is ever touched by quick-play, never anything
    the user named themselves. Kept as a function (not a module-level
    constant) for consistency with how every other default-with-
    translation elsewhere in this codebase is expressed, even though
    round 140's own localization.py rewrite means _() itself no
    longer needs any prior initialization step to be safe to call.
    """

    return _("Files")


class BrowserScreen(Screen, HelpableScreen):
    """
    Local file browsing and playlist building
    (BUILD_0010_PLAN.md "Local File Browser").

    BrowserScreen is temporary: it is always opened from MainScreen and
    always returns to it.
    """

    SPECIFICATION_VERSION = "0.7"
    ARCHITECTURE_VERSION = "0.3"

    # Device test round 55 -- changed from 700x540 to 1672x941,
    # matching MusicLibraryScreen's own round 39 reasoning.
    DESIGN_WIDTH = 1672
    DESIGN_HEIGHT = 941

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Device test round 55 -- reuses MusicLibraryScreen's own
        background-image approach exactly (per direct request: same
        pattern already used for RadioBrowserScreen in round 54).
        Icons: directories->folder, files->track (music note,
        already used for MusicLibraryScreen's own Tracks column),
        playlist->playlist (the list-with-dots icon from the original
        icon sheet). A new "info" text widget was added this round
        (didn't exist before) showing the current playlist's own name
        and track count, per direct request.
        """

        sx = width / BrowserScreen.DESIGN_WIDTH
        sy = height / BrowserScreen.DESIGN_HEIGHT

        self._screen_width = width

        self._screen_height = height

        self._skin_variant = _resolveBrowserSkinVariant()

        palette = BROWSER_SKIN_PALETTES[self._skin_variant]

        panel_background_color = to_opaque_skin_color(palette["panel_background_color"])
        panel_text_color = palette["panel_text_color"]

        # Round 151, per direct request/device photos: two real,
        # pre-existing mismatches only became obvious once test_skin's
        # own colours genuinely diverged from Dark's (round 149) --
        # scrollbarBackgroundColor was hardcoded light grey (#E0E0E0)
        # for every variant, never part of any palette at all, so it
        # never matched Dark's own dark tones either; and the "info"
        # status widget's own opaque panel_background_color fill,
        # fine while it matched Light/Dark's own background image body
        # colour exactly, no longer matches test_skin's own warm brown
        # image at all -- letting a visible seam show at that widget's
        # own edges, the same class of bug round 150 already fixed for
        # LyricsFullscreenScreen. Both scoped to test_skin only, same
        # as round 150's own approach -- Light/Dark keep their
        # existing appearance unchanged.
        if self._skin_variant in ("test_skin", "vintage_radio"):

            scrollbar_bg = "#3A2E1A"

            info_background_attr = 'transparent="1"'

        else:

            scrollbar_bg = "#E0E0E0"

            info_background_attr = f'backgroundColor="{panel_background_color}"'

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Bold;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3BrowserScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{panel_background_color}"
                title="MediaPlayer3 - Browser">

            <!-- Round 96: same zPosition fix as MainMenu/
                 LyricsFullscreenScreen's own round 95/96 fix for a
                 title flashing then hiding behind this background
                 once its own async decode completes; explicit,
                 permanent z-order pin, immune to decode timing. -->
            <widget name="background"
                    position="0,0"
                    size="{width},{height}"
                    zPosition="-1"
                    alphatest="blend"/>

            <widget name="status"
                    {rect(60, 19, 1550, 55)}
                    {font(34)}
                    halign="center"
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="directories_title_normal"
                    {rect(135, 80, 383, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="directories_title_active"
                    {rect(135, 80, 383, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="files_title_normal"
                    {rect(652, 80, 422, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="files_title_active"
                    {rect(652, 80, 422, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="playlist_title_normal"
                    {rect(1207, 80, 403, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="playlist_title_active"
                    {rect(1207, 80, 403, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="directories_list"
                    {rect(40, 138, 498, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="{scrollbar_bg}"
                    scrollbarMode="showOnDemand"/>

            <widget name="files_list"
                    {rect(557, 138, 537, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="{scrollbar_bg}"
                    scrollbarMode="showOnDemand"/>

            <widget name="playlist_list"
                    {rect(1112, 138, 518, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="{scrollbar_bg}"
                    scrollbarMode="showOnDemand"/>

            <widget name="info"
                    {rect(60, 702, 1550, 90)}
                    {font(24)}
                    foregroundColor="{palette['info_label_fg']}"
                    {info_background_attr}/>

            <widget name="hint_text_leftright"
                    {rect(67, 874, 207, 63)}
                    font="Bold;{max(10, int(17 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_updown"
                    {rect(313, 874, 170, 63)}
                    font="Bold;{max(10, int(17 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_ok"
                    {rect(522, 874, 135, 63)}
                    font="Bold;{max(10, int(17 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_play"
                    {rect(696, 874, 108, 63)}
                    font="Bold;{max(10, int(17 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_info"
                    {rect(843, 874, 227, 63)}
                    font="Bold;{max(10, int(17 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_help"
                    {rect(1109, 874, 106, 63)}
                    font="Bold;{max(10, int(17 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_menu"
                    {rect(1254, 874, 138, 63)}
                    font="Bold;{max(10, int(17 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_exit"
                    {rect(1431, 874, 132, 63)}
                    font="Bold;{max(10, int(17 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

        </screen>
        """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, session, playback_controller=None):
        """
        `playback_controller` is MainScreen's shared PlaybackController
        instance -- BrowserScreen never creates its own
        (BROWSERSCREEN_SPEC.md section 8).

        Round 99, per direct request: now Optional -- SettingsScreen
        opens this screen as a plain directory picker (Startup/Music
        Library directory, "Aseta oletushakemistoksi"/"Aseta
        musiikkikirjaston hakemistoksi"), where nothing is actually
        playing and there's nothing to pass. Play/"Add to playlist"
        are left out of both the directory and file OK menus whenever
        self._playback is None (see _directoryMenu()/_fileMenu()'s own
        choice-building) rather than guarded at each individual call
        site, so this is the only place that needs to know a picker
        might have no playback controller at all.
        """

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        # Round 131: registers this screen with Enigma2's own native
        # help mechanism (see the HelpableActionMap construction
        # further down) -- required alongside HelpableScreen's own
        # base-class mixin above; a missing call here is a documented
        # real-world way to leave a screen's own HELP button inactive
        # even with HelpableActionMaps present.
        HelpableScreen.__init__(self)

        self.session = session

        self._playback = playback_controller

        self._focus = "directories"

        # Build 0010 -- identified during the Build 0009 exception
        # audit: an unavailable configured startup directory must
        # never crash this screen outright (a disconnected USB drive
        # or unmounted network share is a normal, expected situation,
        # not a bug). Falls back to "/" (always exists on any
        # Linux-based system).
        startup_directory = config_manager.getStartupDirectory()

        if not os.path.isdir(startup_directory):

            logger.warning(f"[BrowserScreen] Startup directory unavailable, falling back to '/': {startup_directory}")

            startup_directory = "/"

        self._current_root = startup_directory

        self._directory_entries: List[str] = []  # display names, ".." first if present

        self._current_playlist_name: Optional[str] = None

        self._playlist_tracks: List[dict] = []

        self._files_in_preview: List[str] = []

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[BrowserScreen] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["background"] = Pixmap()

        self._background_picload = ePicLoad()

        compatibility.connectPictureDataSignal(self._background_picload, self._onBackgroundImageDecoded)

        self._background_pixmap_cache = {}

        # Device test round 62 -- guards against starting a second
        # concurrent decode while one is already running.
        self._background_decode_in_progress = False

        self["status"] = Label("")

        for column_name in COLUMNS:

            self[f"{column_name}_title_normal"] = Label("")
            self[f"{column_name}_title_active"] = Label("")
            self[f"{column_name}_title_active"].hide()
            self[f"{column_name}_list"] = MenuList([])

        # Device test round 55 -- new: shows the current playlist's
        # own name and track count, per direct request. Didn't exist
        # before this round.
        self["info"] = Label("")

        # Device test round 55 -- 8 icon+text pairs replacing the old
        # single "hint" Label, matching the pattern already used for
        # MusicLibraryScreen/RadioBrowserScreen. Recomputed spacing
        # from scratch for 8 items (one more than RadioBrowserScreen's
        # own 7) -- see _buildSkin()'s own docstring.
        self["hint_text_leftright"] = Label(_("LEFT/RIGHT: Column"))
        self["hint_text_updown"] = Label(_("UP/DOWN: Move"))
        self["hint_text_ok"] = Label(_("OK: Actions"))
        self["hint_text_play"] = Label(_("PLAY: Play"))
        self["hint_text_info"] = Label(_("GREEN: Add/Select"))
        self["hint_text_help"] = Label(_("HELP: Help"))
        self["hint_text_menu"] = Label(_("MENU: Menu"))
        self["hint_text_exit"] = Label(_("EXIT: Back"))

        # Round 134, per direct programmer feedback (see
        # playlistscreen.py's own round 134 comment for the full
        # reasoning): the correct StaticText()/key_red component and
        # naming for colour-button hints, created here for round 133's
        # own GREEN/RED additions. No skin <widget source="key_green"
        # .../> entry yet -- this screen's own hint bar has the same
        # kind of tight remaining width playlistscreen.py's own does,
        # and GREEN's own text would need to change dynamically with
        # focus (Playlist column: "Select Playlist"; Directories/
        # Files: "Add to Playlist") once it does get a skin position,
        # which the existing hint_text_info Label already handles with
        # a static "GREEN: Add/Select" compromise -- left as-is for
        # now rather than duplicating that logic here too.
        self["key_green"] = StaticText(_("Add/Select"))
        self["key_red"] = StaticText(_("Remove"))

        self._reloadDirectoryColumn()

        actions = {
            "ok": self.okPressed,
            "cancel": self.exitPressed,
            "play": self.playPressed,
            "left": self.focusPrevious,
            "right": self.focusNext,
            "up": self.moveUp,
            "down": self.moveDown,
            "menu": self.menuPressed,
            # Round 132/133, per direct request: EPG/INFO used to open
            # the playlist picker directly (round 132: moved to GREEN,
            # freeing EPG/INFO for help); round 133 gave GREEN a
            # second, context-dependent job (add to playlist in
            # Directories/Files, still selectPlaylistPressed() in the
            # Playlist column itself -- see greenPressed()'s own
            # docstring), and added RED for the inverse (remove from
            # playlist).
            "green": self.greenPressed,
            "red": self.redPressed,
            # Round 146, per direct request (colour-button audit):
            # YELLOW/BLUE move the Playlist column's own selected
            # track up/down -- direct shortcuts to _playlistItemMenu()'s
            # own existing "Move up"/"Move down" choices.
            "yellow": self.yellowPressed,
            "blue": self.bluePressed,
        }

        for action_name in compatibility.getChannelUpKeyActionNames():
            actions[action_name] = self.pageUp

        for action_name in compatibility.getChannelDownKeyActionNames():
            actions[action_name] = self.pageDown

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.infoPressed

        for action_name in compatibility.getHelpKeyActionNames():

            # Round 131: "displayHelp" specifically excluded -- see
            # mainscreen.py's own round 130 comment on this exact
            # exclusion for the full reasoning: it's the action name
            # Enigma2's own native help mechanism listens for
            # internally, and binding it here too would silently beat
            # that mechanism to it every time.
            # Round 156, per direct request/device log: "displayHelpLong"
            # is excluded the same way as "displayHelp" -- a real device
            # log showed both registered on the same HelpActions context
            # for the same physical HELP key on some images, so leaving
            # it bound here let it win that key over the native handler.
            # See mainscreen.py's own round 156 comment for the full story.
            if action_name in ("displayHelp", "displayHelpLong"):

                continue

            actions[action_name] = self.infoPressed

        for action_name in compatibility.getPvrKeyActionNames():
            actions[action_name] = self.exitPressed

        contexts = [
            "OkCancelActions",
            "ColorActions",
            "DirectionActions",
            "MediaPlayerActions",
            "MenuActions",
            "InfoActions",
            "InfobarActions",
            "InfobarBouquetActions",
            "InfobarEPGActions",
            "HelpActions",
        ]

        help_text_by_handler = {
            self.okPressed: _("open the actions menu"),
            self.exitPressed: _("go back"),
            self.playPressed: _("play the selected file"),
            self.focusPrevious: _("move to the previous column"),
            self.focusNext: _("move to the next column"),
            self.moveUp: _("move up"),
            self.moveDown: _("move down"),
            self.menuPressed: _("open the menu"),
            self.pageUp: _("page up"),
            self.pageDown: _("page down"),
            self.greenPressed: _("add to playlist (or select playlist in the Playlist column)"),
            self.redPressed: _("remove from playlist"),
            self.yellowPressed: _("move the selected playlist track up"),
            self.bluePressed: _("move the selected playlist track down"),
            self.infoPressed: _("show information about this screen"),
        }

        # Round 131: see mainscreen.py's own round 130 comment for the
        # full reasoning behind this try/except -- HelpableActionMap's
        # own multi-context list support isn't universal across the
        # Enigma2 builds this project targets, so this never risks any
        # actual key binding, only the native help text if unsupported.
        try:

            helpable_actions = {
                action_name: (handler, help_text_by_handler.get(handler, ""))
                for action_name, handler in actions.items()
            }

            self["actions"] = HelpableActionMap(self, contexts, helpable_actions, -1)

        except Exception as error:

            logger.warning(f"[BrowserScreen] HelpableActionMap unavailable, falling back to plain ActionMap: {error}")

            self["actions"] = ActionMap(contexts, actions, -1)

        self._updateDisplay()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Directory Handling
    # ------------------------------------------------------------------

    def _reloadDirectoryColumn(self) -> None:
        """
        Populate the Directories column with the subdirectories of
        self._current_root, ".." first if not at the filesystem root.
        """

        entries = [".."] if self._current_root not in ("/", "") else []

        try:
            for entry in sorted(os.listdir(self._current_root), key=str.lower):

                if entry.startswith("."):
                    continue

                if os.path.isdir(os.path.join(self._current_root, entry)):

                    entries.append(entry)

        except OSError as error:

            self._log(f"Unable to scan directory: {self._current_root} ({error})")

        self._directory_entries = entries

    # ------------------------------------------------------------------

    def _selectedDirectoryPath(self) -> Optional[str]:
        """
        Full path corresponding to the currently selected entry in the
        Directories column, or None if nothing usable is selected.
        ".." resolves to the parent of the current root.
        """

        index = self["directories_list"].getSelectedIndex()

        if not (0 <= index < len(self._directory_entries)):
            return None

        entry = self._directory_entries[index]

        if entry == "..":

            return os.path.dirname(self._current_root.rstrip("/")) or "/"

        return os.path.join(self._current_root, entry)

    # ------------------------------------------------------------------

    def _openSelectedDirectory(self) -> None:
        """
        Descend into (or go up out of) the selected Directories entry
        -- the "Open directory" action added to the OK menu (see this
        file's own header comment for why).
        """

        target = self._selectedDirectoryPath()

        if target is None or not os.path.isdir(target):

            self.session.open(MessageBox, _("Directory not available."), MessageBox.TYPE_ERROR)

            return

        self._current_root = target

        self._reloadDirectoryColumn()

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _updateDisplay(self) -> None:

        self["directories_list"].setList(self._directory_entries)

        preview_directory = self._previewDirectory()

        files = playlist_manager.listDirectoryAudioFiles(preview_directory) if preview_directory else []

        self._files_in_preview = files

        self["files_list"].setList([os.path.basename(path) for path in files])

        self["playlist_list"].setList(
            [self._formatTrackEntry(track) for track in self._playlist_tracks]
        )

        # Device test round 55 -- titles simplified to their own
        # static names; the Playlist column's own dynamic name+count
        # (previously baked into this title) moved to the new "info"
        # widget below instead, per direct request.
        titles = {
            "directories": _("Directories"),
            "files": _("Files"),
            "playlist": _("Playlist"),
        }

        for column_name, title_text in titles.items():

            # Device test round 57 -- the "> " marker removed: the
            # background image's own colour already distinguishes the
            # active column, and the marker's extra characters were
            # causing the title to wrap onto two lines when selected.

            self[f"{column_name}_title_normal"].setText(title_text)

            self[f"{column_name}_title_active"].setText(title_text)

        if self._current_playlist_name:

            self["info"].setText(
                f"{_('Playlist')}: {self._current_playlist_name}\n"
                f"{len(self._playlist_tracks)} {_('track(s)')}"
            )

        else:

            self["info"].setText(_("No playlist selected"))

        self._updateColumnHighlighting()

        self["status"].setText(self._current_root)

    # ------------------------------------------------------------------

    def _formatTrackEntry(self, track: dict) -> str:

        artist = track.get("artist", "Unknown")
        title = track.get("title", track.get("file_name", "Unknown"))

        if artist and artist != "Unknown":

            return f"{artist} - {title}"

        return title

    # ------------------------------------------------------------------

    def _previewDirectory(self) -> Optional[str]:
        """
        The directory whose files the Files column currently previews
        -- BUILD_0010_PLAN.md "The middle column contains files in the
        selected directory": tracks the Directories column's current
        *selection*, live, the same way PodcastScreen's Episodes
        column already tracks the selected podcast, without requiring
        "Open directory" first.
        """

        index = self["directories_list"].getSelectedIndex()

        if not (0 <= index < len(self._directory_entries)):

            return self._current_root

        entry = self._directory_entries[index]

        if entry == "..":

            return os.path.dirname(self._current_root.rstrip("/")) or "/"

        return os.path.join(self._current_root, entry)

    # ------------------------------------------------------------------

    def _updateColumnHighlighting(self) -> None:
        """
        Device test round 55 -- the active/inactive column-header
        colouring now lives in one of three pre-rendered background
        images (resources/skins/{variant}/{tier}/browser_{focus}_
        active.png), swapped here instead of toggling individual bg
        widgets, matching MusicLibraryScreen's own round 39/45 and
        RadioBrowserScreen's own round 54. Header TEXT stays real,
        translatable normal/active widget pairs, toggled here too.
        """

        self._decodeBackgroundImage(self._focus)

        for column_name in COLUMNS:

            is_active = column_name == self._focus

            try:
                self[f"{column_name}_title_normal"].hide() if is_active else self[f"{column_name}_title_normal"].show()

                self[f"{column_name}_title_active"].show() if is_active else self[f"{column_name}_title_active"].hide()

            except Exception as error:

                logger.verbose(f"[BrowserScreen] Unable to set column highlight visibility: {error}")

    # ------------------------------------------------------------------
    # Background image (device test round 55 -- mirrors
    # MusicLibraryScreen's own _decodeBackgroundImage()/
    # _onBackgroundImageDecoded() exactly, including the per-state
    # cache and stale-decode guard; see that file's own docstrings for
    # the full reasoning, not repeated here.)
    # ------------------------------------------------------------------

    def _decodeBackgroundImage(self, focus_state: str) -> None:

        if focus_state in self._background_pixmap_cache:

            if self["background"].instance is not None:

                self["background"].instance.setPixmap(self._background_pixmap_cache[focus_state])

                self["background"].show()

            return

        # Device test round 62 -- real bug found from a device log on
        # MainScreen (a slow decode, likely worsened by a concurrent
        # "gAccel alloc failed" the same log showed, left this
        # method's own cache check above still empty when another
        # call arrived before the first decode finished, causing a
        # second concurrent startDecode() on the same ePicLoad
        # instance -- confirmed directly as "startDecode() reported
        # failure" in the log). Same guard applied here defensively:
        # ePicLoad only supports one decode at a time per instance;
        # this simply skips starting a new one while one is already
        # running.
        if getattr(self, "_background_decode_in_progress", False):
            return

        if self["background"].instance is None:

            logger.verbose("[BrowserScreen] background widget not ready yet, retrying decode shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(lambda: self._decodeBackgroundImage(focus_state))

            retry_timer.start(100, True)

            self._pending_background_retry_timer = retry_timer

            return

        image_path = resolve_skin_asset_path(
            self._skin_variant,
            _resolveBrowserResolutionTier(self._screen_width),
            f"browser_{focus_state}_active.png",
        )

        self._pending_background_focus_state = focus_state

        try:
            width, height = self._screen_width, self._screen_height

            aspect = AVSwitch().getFramebufferScale()

            self._background_picload.setPara((width, height, aspect[0], aspect[1], False, 1, "#00000000"))

            self._background_decode_in_progress = True

            if self._background_picload.startDecode(image_path) != 0:
                raise RuntimeError("startDecode() reported failure")

        except Exception as error:

            self._background_decode_in_progress = False

            logger.verbose(f"[BrowserScreen] Unable to decode background image {image_path}: {error}")

    # ------------------------------------------------------------------

    def _onBackgroundImageDecoded(self, picture_info=None) -> None:

        # Device test round 62 -- cleared in a finally below so every
        # branch (including early returns) reliably clears it once
        # the decode has genuinely finished.
        try:
            pixmap = self._background_picload.getData()

            if pixmap is None:
                return

            state = getattr(self, "_pending_background_focus_state", None)

            if state is not None:

                self._background_pixmap_cache[state] = pixmap

            if state != self._focus:
                return

            self["background"].instance.setPixmap(pixmap)

            self["background"].show()

        except Exception as error:

            logger.verbose(f"[BrowserScreen] Unable to apply decoded background image: {error}")

        finally:

            self._background_decode_in_progress = False

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def focusPrevious(self) -> None:

        logger.verbose("[BrowserScreen] LEFT pressed.")

        self._focus = COLUMNS[(COLUMNS.index(self._focus) - 1) % len(COLUMNS)]

        self._updateDisplay()

    # ------------------------------------------------------------------

    def focusNext(self) -> None:

        logger.verbose("[BrowserScreen] RIGHT pressed.")

        self._focus = COLUMNS[(COLUMNS.index(self._focus) + 1) % len(COLUMNS)]

        self._updateDisplay()

    # ------------------------------------------------------------------

    def moveUp(self) -> None:

        self[f"{self._focus}_list"].up()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def moveDown(self) -> None:

        self[f"{self._focus}_list"].down()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageUp(self) -> None:

        widget = self[f"{self._focus}_list"]

        steps = min(PAGE_STEP, widget.getSelectedIndex())

        for _step in range(steps):

            widget.up()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageDown(self) -> None:

        widget = self[f"{self._focus}_list"]

        entries = widget.list or []

        steps = min(PAGE_STEP, max(0, len(entries) - 1 - widget.getSelectedIndex()))

        for _step in range(steps):

            widget.down()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def _onSelectionChanged(self) -> None:
        """
        Moving within Directories live-updates the Files preview
        (BUILD_0010_PLAN.md, see _previewDirectory()). Moving within
        Files or Playlist doesn't reload anything else.
        """

        if self._focus != "directories":
            return

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Playback (PLAY key -- see this file's own header comment)
    # ------------------------------------------------------------------

    def playPressed(self) -> None:

        logger.verbose("[BrowserScreen] PLAY pressed.")

        if self._focus == "directories":

            self._playSelectedDirectory()

        elif self._focus == "files":

            self._playSelectedFile()

        elif self._focus == "playlist":

            self._playCurrentPlaylist()

    # ------------------------------------------------------------------

    def _playSelectedDirectory(self) -> None:
        """
        Recursively play every supported audio file under the
        previewed directory (Build 0007's "Play Folder", carried
        forward unchanged in behaviour).
        """

        directory = self._previewDirectory()

        if not directory or not os.path.isdir(directory):

            self.session.open(MessageBox, _("Directory not available."), MessageBox.TYPE_ERROR)

            return

        collected = []

        try:
            for root, _directories, files in os.walk(directory):

                for entry in sorted(files, key=str.lower):

                    if entry.startswith("."):
                        continue

                    if entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):

                        collected.append(os.path.join(root, entry))

        except OSError as error:

            self._log(f"Unable to scan directory for playback: {directory} ({error})")

        if not collected:

            self.session.open(MessageBox, _("No playable files found."), MessageBox.TYPE_ERROR)

            return

        self._log(f"Play directory: {directory} ({len(collected)} track(s))")

        if self._playback.playQueue(collected, 0):

            self.close("played")

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------

    def _playSelectedFile(self) -> None:

        index = self["files_list"].getSelectedIndex()

        if not (0 <= index < len(self._files_in_preview)):

            return

        queue = self._files_in_preview

        self._log(f"Play file: {queue[index]}")

        if self._playback.playQueue(queue, index):

            self.close("played")

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------

    def _playCurrentPlaylist(self) -> None:

        if not self._current_playlist_name:

            self.session.open(MessageBox, _("No playlist selected."), MessageBox.TYPE_INFO, timeout=3)

            return

        index = self["playlist_list"].getSelectedIndex()

        if index < 0:
            index = 0

        queue = playlist_manager.generatePlaybackQueue(self._current_playlist_name)

        if not queue:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        start_index = index if index < len(queue) else 0

        self._log(f"Play playlist: {self._current_playlist_name} ({len(queue)} track(s))")

        if self._playback.playQueue(queue, start_index):

            self.close(("played", self._current_playlist_name))

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------
    # Actions (OK -- BUILD_0010_PLAN.md "File Browser Actions")
    # ------------------------------------------------------------------

    def okPressed(self) -> None:

        logger.verbose("[BrowserScreen] OK pressed.")

        if self._focus == "directories":

            self._directoryMenu()

        elif self._focus == "files":

            self._fileMenu()

        elif self._focus == "playlist":

            self._playlistItemMenu()

    # ------------------------------------------------------------------

    def _directoryMenu(self) -> None:

        target = self._selectedDirectoryPath()

        if target is None:
            return

        index = self["directories_list"].getSelectedIndex()

        label = self._directory_entries[index] if 0 <= index < len(self._directory_entries) else "?"

        # ".." only makes sense to open, not to bulk-add/play -- "play/
        # add the entire parent directory" isn't a meaningful action
        # here and would recurse back into this browser's own current
        # directory a second time.
        if label == "..":

            choices = [(_("Open directory"), "open"), (_("Cancel"), "cancel")]

        else:

            # Device test round 30 -- user request: when the previewed
            # directory (self._files_in_preview, already tracking
            # whatever's currently selected here -- see
            # _previewDirectory()'s own docstring) actually has
            # playable files, "Play" leads (the more likely action);
            # otherwise "Open directory" leads (current/previous
            # behaviour) since there's nothing to play here directly
            # anyway.
            #
            # Round 99, per direct request: "Set as X directory"
            # always offered (writes straight to config, needs no
            # playback controller); "Play"/"Add entire directory to
            # playlist" only offered when self._playback is actually
            # available -- None when this screen is opened as a plain
            # directory picker from SettingsScreen (round 99), where
            # attempting to play anything would have nothing to play
            # through.
            #
            # Round 147, per direct request/device confirmation
            # ("jos hakemistossa ei ole soitettavia kappaleita, niin
            # saisi ensimmäisenä vaihtoehtona olla avaa hakemisto"):
            # round 30's own comment above already described this
            # exact "Play leads when there are playable files,
            # otherwise Open directory leads" intent, but the code
            # underneath it never actually implemented that
            # distinction -- the first branch unconditionally put
            # "Play" first whenever self._playback was available,
            # regardless of self._files_in_preview, and the second
            # "if self._files_in_preview" block below just re-assigned
            # the exact same list again, a no-op duplicate that never
            # touched the genuinely broken case (playback available,
            # but no files directly in this directory). Fixed here:
            # self._files_in_preview now genuinely decides the order.
            if self._playback is None:

                playback_choices = [(_("Open directory"), "open")]

            elif self._files_in_preview:

                playback_choices = [
                    (_("Play"), "play"),
                    (_("Open directory"), "open"),
                    (_("Add entire directory to playlist"), "add"),
                ]

            else:

                playback_choices = [
                    (_("Open directory"), "open"),
                    (_("Play"), "play"),
                    (_("Add entire directory to playlist"), "add"),
                ]

            choices = (
                playback_choices
                + [
                    (_("Download lyrics"), "download_lyrics"),
                    (_("Download cover art"), "download_coverart"),
                    (_("Set as startup directory"), "set_startup_directory"),
                    (_("Set as Music Library directory"), "set_library_directory"),
                    (_("Cancel"), "cancel"),
                ]
            )

        self.session.openWithCallback(
            lambda choice: self._directoryMenuChosen(choice, target),
            ChoiceBox,
            title=label,
            list=choices,
        )

    # ------------------------------------------------------------------

    def _directoryMenuChosen(self, choice, target: str) -> None:

        if choice is None or choice[1] == "cancel":
            return

        if choice[1] == "open":

            self._openSelectedDirectory()

        elif choice[1] == "play":

            self._playDirectoryAsPlaylist(target)

        elif choice[1] == "add":

            self._requireCurrentPlaylist(lambda name: self._addDirectoryToPlaylist(name, target))

        elif choice[1] == "download_lyrics":

            self._offerLyricsDownload(target)

        elif choice[1] == "download_coverart":

            self._offerCoverArtDownload(target)

        elif choice[1] == "set_startup_directory":

            self._setConfigDirectory(cfg.general.startup_directory, _("Startup directory"), target)

        elif choice[1] == "set_library_directory":

            self._setConfigDirectory(cfg.library.scan_directory, _("Music Library directory"), target)

    # ------------------------------------------------------------------

    def _setConfigDirectory(self, target_config, label: str, directory: str) -> None:
        """
        Round 99, per direct request: lets "Set as startup directory"/
        "Set as Music Library directory" write straight to config from
        wherever the user already is in the Browser, instead of only
        being settable from SettingsScreen. Writes directly to the
        same config_manager both SettingsScreen's own directory picker
        (round 98) and this screen's own normal operation already
        share -- no callback needed, since both screens read the same
        live ConfigText object.
        """

        target_config.value = ensure_trailing_slash(directory)

        target_config.save()

        self._log(f"{label} set to: {target_config.value}")

        self.session.open(
            MessageBox,
            _("{0} set to: {1}").format(label, target_config.value),
            MessageBox.TYPE_INFO,
            timeout=3,
        )

    # ------------------------------------------------------------------

    def _playDirectoryAsPlaylist(self, directory: str) -> None:
        """
        Build 0010, device test round 5 -- Directories column's "Play"
        action: "Jos valitsee kansion kohdalla soita, niin se voisi
        luoda suoraan soittolistan koko kansiosta ja alkaa
        soittamaan." Round 6: uses the fixed default playlist name
        (_defaultPlayPlaylistName(), "Files"/"Tiedostot") rather than
        the folder's own name, after a real overwrite-risk concern --
        see that function's own docstring, and
        playlist_manager.createPlaylistFromFolder()'s, for the
        overwrite-by-design reasoning this still relies on.
        """

        playlist_name = _defaultPlayPlaylistName()

        count = playlist_manager.createPlaylistFromFolder(playlist_name, directory)

        if count <= 0:

            self.session.open(MessageBox, self._describeAddFailure(), MessageBox.TYPE_ERROR)

            return

        self._startPlaylistPlayback(playlist_name)

    # ------------------------------------------------------------------

    def _describeAddFailure(self) -> str:
        """
        Build 0010, device test round 20 (OpenPLI, disk-full test box):
        a folder/file add or "Play" action returning 0/False can mean
        either "genuinely nothing to add" or "found files, but saving
        the playlist itself failed" (disk full, permissions, ...) --
        these need different messages, or a real write failure looks
        identical to an empty folder and the actual, fixable problem
        (device out of storage) never reaches the user. Checks
        playlist_manager's own getLastSaveError() (set on any
        savePlaylist() failure, which every "add"/"Play" action here
        eventually goes through) to tell them apart.
        """

        error = playlist_manager.getLastSaveError()

        if error:

            return _("Save failed: %s") % error

        return _("No playable files found.")

    # ------------------------------------------------------------------

    def _addDirectoryToPlaylist(self, playlist_name: str, directory: str) -> None:

        count = playlist_manager.addFolder(playlist_name, directory)

        self._afterAdd(playlist_name, count)

    # ------------------------------------------------------------------

    def _fileMenu(self) -> None:

        index = self["files_list"].getSelectedIndex()

        if not (0 <= index < len(self._files_in_preview)):
            return

        filepath = self._files_in_preview[index]

        # Round 99: Play/"Add..." need a real PlaybackController/
        # playlist target to do anything useful with -- left out when
        # this screen is a plain directory picker (self._playback is
        # None), same reasoning as _directoryMenu()'s own choices.
        choices = (
            [(_("Play"), "play")] if self._playback is not None else []
        ) + (
            [
                (_("Add this file"), "add_one"),
                (_("Add this file and remaining files in directory"), "add_remaining"),
                (_("Add all files from directory"), "add_all"),
            ]
            if self._playback is not None
            else []
        ) + [
            (_("Download lyrics"), "download_lyrics"),
            (_("Download cover art"), "download_coverart"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._fileMenuChosen(choice, filepath),
            ChoiceBox,
            title=os.path.basename(filepath),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _fileMenuChosen(self, choice, filepath: str) -> None:

        if choice is None or choice[1] == "cancel":
            return

        directory = os.path.dirname(filepath)

        if choice[1] == "play":

            self._playFileAsPlaylist(filepath)

        elif choice[1] == "add_one":

            self._requireCurrentPlaylist(
                lambda name: self._afterAdd(name, 1 if playlist_manager.addTrack(name, filepath) else 0)
            )

        elif choice[1] == "add_remaining":

            self._requireCurrentPlaylist(
                lambda name: self._afterAdd(
                    name, playlist_manager.addFilesInDirectory(name, directory, from_filename=filepath)
                )
            )

        elif choice[1] == "add_all":

            self._requireCurrentPlaylist(
                lambda name: self._afterAdd(name, playlist_manager.addFilesInDirectory(name, directory))
            )

        elif choice[1] == "download_lyrics":

            self._offerLyricsDownload(filepath)

        elif choice[1] == "download_coverart":

            self._offerCoverArtDownload(filepath)

    # ------------------------------------------------------------------

    def _offerLyricsDownload(self, target: str) -> None:
        """
        First step of the LRCLIB lyrics-download feature (round 83).
        Round 92, per direct request: replaced the original plain
        yes/no confirmation with a choice of which kind of lyrics to
        download -- deliberately its own small method rather than
        folded into a bigger dialog, so a later round can add further
        questions as additional steps in this same chain without
        having to restructure a combined one-shot dialog (this is
        exactly that later round). `target` is either a directory or
        a single file path.
        """

        choices = [
            (_("Download all"), "all"),
            (_("Download synced lyrics only (LRC)"), "synced_only"),
            (_("Download plain text lyrics only (TXT)"), "plain_only"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._lyricsDownloadModeChosen(choice, target),
            ChoiceBox,
            title=_("Download lyrics?"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _lyricsDownloadModeChosen(self, choice, target: str) -> None:

        if choice is None or choice[1] == "cancel":
            return

        mode = choice[1]

        # Round 85, per direct request: if the target is a directory
        # that itself contains subdirectories, ask a second, separate
        # question before starting -- kept as its own step in the
        # same chain round 83 set up for exactly this kind of
        # follow-up question, not folded into the first one.
        if os.path.isdir(target) and lrclib_manager.hasSubdirectories(target):

            self.session.openWithCallback(
                lambda recursive: self._startLyricsDownload(target, recursive, mode),
                MessageBox,
                _("Also download lyrics for subdirectories?"),
                MessageBox.TYPE_YESNO,
            )

        else:

            self._startLyricsDownload(target, False, mode)

    # ------------------------------------------------------------------

    def _startLyricsDownload(self, target: str, recursive: bool, mode: str) -> None:

        # Same deferred please-wait pattern as RadioBrowserScreen's own
        # _updateStationDatabase() -- a real, potentially slow network
        # operation (worse here for a whole directory, one request per
        # track), so paint the status message before the blocking call
        # actually runs.
        self["status"].setText(_("Downloading lyrics, please wait..."))

        self._lyrics_download_timer = eTimer()

        self._lyrics_download_timer.callback.append(lambda: self._performLyricsDownload(target, recursive, mode))

        self._lyrics_download_timer.start(10, True)

    # ------------------------------------------------------------------

    def _performLyricsDownload(self, target: str, recursive: bool, mode: str) -> None:

        if os.path.isdir(target):

            counts = lrclib_manager.downloadForDirectory(target, recursive=recursive, mode=mode)

            message = self._describeLyricsDownloadTally(counts)

        else:

            result = lrclib_manager.downloadForFile(target, mode=mode)

            message = self._describeLyricsDownloadResult(result)

        self["status"].setText(self._current_root)

        logger.info(f"[BrowserScreen] Lyrics download finished for '{target}': {message}")

        self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

    # ------------------------------------------------------------------

    def _describeLyricsDownloadResult(self, result: str) -> str:

        return {
            "saved_synced": _("Synced lyrics downloaded."),
            "saved_plain": _("Lyrics downloaded (plain text -- LRCLIB has no synced version for this track)."),
            "instrumental": _("LRCLIB has this track marked as instrumental -- no lyrics to download."),
            "not_found": _("No lyrics found on LRCLIB for this track."),
            "already_has_lyrics": _("This track already has lyrics -- nothing downloaded."),
            "missing_tags": _("Missing artist/title tags -- can't search LRCLIB for this track."),
            "rate_limited": _("LRCLIB is temporarily busy. Try again in a moment."),
            "error": _("Lyrics download failed. Check your network connection."),
        }.get(result, _("Lyrics download failed. Check your network connection."))

    # ------------------------------------------------------------------

    def _describeLyricsDownloadTally(self, counts: dict) -> str:

        if not counts:
            return _("No audio files found in this directory.")

        labels = {
            "saved_synced": _("synced"),
            "saved_plain": _("plain text"),
            "instrumental": _("instrumental"),
            "not_found": _("not found"),
            "already_has_lyrics": _("already had lyrics"),
            "missing_tags": _("missing tags"),
            "rate_limited": _("temporarily busy, try again shortly"),
            "error": _("failed"),
        }

        parts = [f"{count} {labels.get(result, result)}" for result, count in counts.items() if count > 0]

        return _("Lyrics download finished: %s.") % ", ".join(parts)

    # ------------------------------------------------------------------

    def _offerCoverArtDownload(self, target: str) -> None:
        """
        Cover art's own version of _offerLyricsDownload()/
        _lyricsDownloadConfirmed() (round 88, mirrors rounds 83 and 85
        exactly, per direct request: "kuvien lataus samalla tavalla
        kuin sanoituksiin").
        """

        self.session.openWithCallback(
            lambda confirmed: self._coverArtDownloadConfirmed(confirmed, target),
            MessageBox,
            _("Download cover art?"),
            MessageBox.TYPE_YESNO,
        )

    # ------------------------------------------------------------------

    def _coverArtDownloadConfirmed(self, confirmed, target: str) -> None:

        if not confirmed:
            return

        if os.path.isdir(target) and coverart_manager.hasSubdirectories(target):

            self.session.openWithCallback(
                lambda recursive: self._startCoverArtDownload(target, recursive),
                MessageBox,
                _("Also download cover art for subdirectories?"),
                MessageBox.TYPE_YESNO,
            )

        else:

            self._startCoverArtDownload(target, False)

    # ------------------------------------------------------------------

    def _startCoverArtDownload(self, target: str, recursive: bool) -> None:

        # Same deferred please-wait pattern as _startLyricsDownload()/
        # RadioBrowserScreen's own _updateStationDatabase().
        self["status"].setText(_("Downloading cover art, please wait..."))

        self._coverart_download_timer = eTimer()

        self._coverart_download_timer.callback.append(lambda: self._performCoverArtDownload(target, recursive))

        self._coverart_download_timer.start(10, True)

    # ------------------------------------------------------------------

    def _performCoverArtDownload(self, target: str, recursive: bool) -> None:

        if os.path.isdir(target):

            counts = coverart_manager.downloadForDirectory(target, recursive=recursive)

            message = self._describeCoverArtDownloadTally(counts)

        else:

            result = coverart_manager.downloadForFile(target)

            message = self._describeCoverArtDownloadResult(result)

        self["status"].setText(self._current_root)

        logger.info(f"[BrowserScreen] Cover art download finished for '{target}': {message}")

        self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

    # ------------------------------------------------------------------

    def _describeCoverArtDownloadResult(self, result: str) -> str:

        return {
            "saved": _("Cover art downloaded."),
            "already_has_cover": _("This album already has cover art -- nothing downloaded."),
            "not_found": _("No matching cover art found."),
            "missing_tags": _("Missing artist/album tags -- can't search for cover art."),
            "rate_limited": _("MusicBrainz is temporarily busy. Try again in a moment."),
            "error": _("Cover art download failed. Check your network connection."),
        }.get(result, _("Cover art download failed. Check your network connection."))

    # ------------------------------------------------------------------

    def _describeCoverArtDownloadTally(self, counts: dict) -> str:

        if not counts:
            return _("No audio files found in this directory.")

        labels = {
            "saved": _("saved"),
            "already_has_cover": _("already had cover art"),
            "not_found": _("not found"),
            "missing_tags": _("missing tags"),
            "rate_limited": _("temporarily busy, try again shortly"),
            "error": _("failed"),
        }

        parts = [f"{count} {labels.get(result, result)}" for result, count in counts.items() if count > 0]

        return _("Cover art download finished: %s.") % ", ".join(parts)

    # ------------------------------------------------------------------

    def _afterAdd(self, playlist_name: str, count: int) -> None:

        self._log(f"Added {count} track(s) to playlist: {playlist_name}")

        if count <= 0:

            box_type = MessageBox.TYPE_ERROR if playlist_manager.getLastSaveError() else MessageBox.TYPE_INFO

            self.session.open(MessageBox, self._describeAddFailure(), box_type, timeout=3)

        elif count == 1:

            self.session.open(
                MessageBox,
                _("Added to playlist: %s") % playlist_name,
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        else:

            self.session.open(
                MessageBox,
                _("Added %d tracks to playlist: %s") % (count, playlist_name),
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        if self._current_playlist_name == playlist_name:

            self._playlist_tracks = playlist_manager.loadPlaylist(playlist_name)

            self._updateDisplay()

    # ------------------------------------------------------------------

    def greenPressed(self) -> None:
        """
        Round 133, per direct request ("Mainscreen, browser,(hakemisto
        ja tiedosto)... vihreä lisää soittolistaan"): GREEN's own
        direct shortcut to this screen's own existing "Add" menu
        options -- adds the currently focused directory (Directories
        column) or file (Files column) to the current/target playlist,
        prompting for one first if none is set yet (same
        _requireCurrentPlaylist() flow the OK menu's own "add" choices
        already use).

        In the Playlist column itself, "add to playlist" has no
        meaning (there's nothing outside a playlist to add from) --
        GREEN keeps its own round 132 behaviour there instead
        (selectPlaylistPressed(), choosing which playlist this column
        displays), so the one key still does the single most useful
        thing for whichever column is actually focused.
        """

        if self._focus == "playlist":

            self.selectPlaylistPressed()

            return

        if self._focus == "directories":

            target = self._selectedDirectoryPath()

            if target is None:

                return

            self._requireCurrentPlaylist(lambda name: self._addDirectoryToPlaylist(name, target))

        elif self._focus == "files":

            index = self["files_list"].getSelectedIndex()

            if not (0 <= index < len(self._files_in_preview)):

                return

            filepath = self._files_in_preview[index]

            self._requireCurrentPlaylist(
                lambda name: self._afterAdd(name, 1 if playlist_manager.addTrack(name, filepath) else 0)
            )

    # ------------------------------------------------------------------

    def redPressed(self) -> None:
        """
        Round 133, per direct request ("punainen poista soittolistasta"):
        RED's own direct shortcut to remove the currently focused
        directory's own tracks (Directories column, via
        playlist_manager.removeTracksInDirectory()) or the currently
        focused file's own single entry (Files column, via
        playlist_manager.removeTrackByPath()) from the current/target
        playlist -- the inverse of greenPressed() above, targeting the
        exact same playlist concept. A no-op in the Playlist column
        itself, which already has its own dedicated remove action.
        """

        if self._focus == "directories":

            target = self._selectedDirectoryPath()

            if target is None:

                return

            self._requireCurrentPlaylist(
                lambda name: self._afterRemove(name, playlist_manager.removeTracksInDirectory(name, target))
            )

        elif self._focus == "files":

            index = self["files_list"].getSelectedIndex()

            if not (0 <= index < len(self._files_in_preview)):

                return

            filepath = self._files_in_preview[index]

            self._requireCurrentPlaylist(
                lambda name: self._afterRemove(name, 1 if playlist_manager.removeTrackByPath(name, filepath) else 0)
            )

    # ------------------------------------------------------------------

    def yellowPressed(self) -> None:
        """
        Round 146, per direct request (colour-button audit): direct
        shortcut to the Playlist column's own existing "Move up" menu
        choice (_playlistItemMenu()) -- moves the currently selected
        track one position earlier in the current playlist. A no-op
        outside the Playlist column, and when nothing is actually
        selected there.
        """

        self._moveSelectedPlaylistTrack(-1)

    # ------------------------------------------------------------------

    def bluePressed(self) -> None:
        """
        Round 146, per direct request: the same shortcut as
        yellowPressed() above, for "Move down" instead.
        """

        self._moveSelectedPlaylistTrack(1)

    # ------------------------------------------------------------------

    def _moveSelectedPlaylistTrack(self, direction: int) -> None:

        if self._focus != "playlist" or not self._current_playlist_name:

            return

        index = self["playlist_list"].getSelectedIndex()

        if not (0 <= index < len(self._playlist_tracks)):

            return

        playlist_manager.moveTrack(self._current_playlist_name, index, direction)

        self._playlist_tracks = playlist_manager.loadPlaylist(self._current_playlist_name)

        self._updateDisplay()

    # ------------------------------------------------------------------

    def _afterRemove(self, playlist_name: str, count: int) -> None:

        self._log(f"Removed {count} track(s) from playlist: {playlist_name}")

        if count <= 0:

            self.session.open(
                MessageBox,
                _("Not found in playlist: %s") % playlist_name,
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        elif count == 1:

            self.session.open(
                MessageBox,
                _("Removed from playlist: %s") % playlist_name,
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        else:

            self.session.open(
                MessageBox,
                _("Removed %d tracks from playlist: %s") % (count, playlist_name),
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        if self._current_playlist_name == playlist_name:

            self._playlist_tracks = playlist_manager.loadPlaylist(playlist_name)

            self._updateDisplay()

    # ------------------------------------------------------------------

    def _playFileAsPlaylist(self, filepath: str) -> None:
        """
        Build 0010, device test round 5 -- Files column's "Play"
        action: "Tiedoston kohdalla voisi luoda soittolistan vain
        siitä tiedostosta ja alkaa soittamaan." Round 6: uses the
        fixed default playlist name (_defaultPlayPlaylistName(),
        "Files"/"Tiedostot") rather than the file's own basename --
        see that function's own docstring for why (same overwrite-risk
        concern as the Directories column's "Play").
        """

        playlist_name = _defaultPlayPlaylistName()

        if not playlist_manager.createPlaylistFromFile(playlist_name, filepath):

            self.session.open(MessageBox, self._describeAddFailure(), MessageBox.TYPE_ERROR)

            return

        self._startPlaylistPlayback(playlist_name)

    # ------------------------------------------------------------------

    def _startPlaylistPlayback(self, playlist_name: str) -> None:
        """
        Shared by both new "Play" actions (Directories/Files columns):
        loads `playlist_name` fresh and starts playback from the
        beginning, closing with ("played", playlist_name) -- same
        convention as the Playlist column's own PLAY/OK handling, so
        MainScreen's "Back" (BUILD_0010_PLAN.md "MainScreen OK Menu")
        returns here to BrowserScreen, and LEFT/RIGHT favorites-view
        playlist cycling picks it up too.
        """

        queue = playlist_manager.generatePlaybackQueue(playlist_name)

        if not queue or not self._playback.playQueue(queue, 0):

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        self._log(f"Play: {playlist_name} ({len(queue)} track(s))")

        self.close(("played", playlist_name))

    # ------------------------------------------------------------------

    def _playlistItemMenu(self) -> None:

        if not self._current_playlist_name:

            self.selectPlaylistPressed()

            return

        index = self["playlist_list"].getSelectedIndex()

        if not (0 <= index < len(self._playlist_tracks)):
            return

        choices = [
            (_("Play"), "play"),
            (_("Remove"), "remove"),
            (_("Move up"), "up"),
            (_("Move down"), "down"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._playlistItemMenuChosen(choice, index),
            ChoiceBox,
            title=self._formatTrackEntry(self._playlist_tracks[index]),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _playlistItemMenuChosen(self, choice, index: int) -> None:

        if choice is None or choice[1] == "cancel":
            return

        name = self._current_playlist_name

        if choice[1] == "play":

            # Build 0010, device test round 5: "Soittolistanäkymässä
            # soita voisi alkaa suoraan soittamaan listalla olevat
            # kappaleet valitusta kappaleesta eteenpäin." Same queue-
            # from-selected-index logic PLAY already used
            # (_playCurrentPlaylist()) -- just reachable from OK too
            # now, with the selection already known from this menu.
            self._playCurrentPlaylist()

            return

        elif choice[1] == "remove":

            playlist_manager.removeTrack(name, index)

        elif choice[1] == "up":

            playlist_manager.moveTrack(name, index, -1)

        elif choice[1] == "down":

            playlist_manager.moveTrack(name, index, 1)

        self._playlist_tracks = playlist_manager.loadPlaylist(name)

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Current playlist selection (INFO -- see this file's own header
    # comment for why this exists)
    # ------------------------------------------------------------------

    def selectPlaylistPressed(self) -> None:

        logger.verbose("[BrowserScreen] INFO pressed.")

        self._requireCurrentPlaylist(self._setCurrentPlaylist, force_prompt=True)

    # ------------------------------------------------------------------

    def _requireCurrentPlaylist(self, callback, force_prompt: bool = False) -> None:
        """
        Ensure a current playlist is set before running `callback(name)`.
        If one is already set and force_prompt is False, calls back
        immediately; otherwise opens the picker first.
        """

        if self._current_playlist_name and not force_prompt:

            callback(self._current_playlist_name)

            return

        names = playlist_manager.getPlaylistNames()

        choices = [(name, name) for name in names]

        choices.append((_("Create new playlist..."), "__new__"))
        choices.append((_("Cancel"), "__cancel__"))

        self.session.openWithCallback(
            lambda choice: self._playlistPickerChosen(choice, callback),
            ChoiceBox,
            title=_("Select playlist"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _playlistPickerChosen(self, choice, callback) -> None:

        if choice is None or choice[1] == "__cancel__":
            return

        if choice[1] == "__new__":

            self.session.openWithCallback(
                lambda text: self._newPlaylistNameEntered(text, callback),
                VirtualKeyBoard,
                title=_("New playlist name"),
                text="",
            )

            return

        self._setCurrentPlaylist(choice[1])

        callback(choice[1])

    # ------------------------------------------------------------------

    def _newPlaylistNameEntered(self, text, callback) -> None:

        if not text:
            return

        playlist_manager.createPlaylist(text)

        self._setCurrentPlaylist(text)

        callback(text)

    # ------------------------------------------------------------------

    def _setCurrentPlaylist(self, name: str) -> None:

        self._current_playlist_name = name

        self._playlist_tracks = playlist_manager.loadPlaylist(name)

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def infoPressed(self) -> None:

        logger.verbose("[BrowserScreen] INFO pressed.")

        title, content = guide_manager.getGuide("browserscreen")

        self.session.open(GuideScreen, title, content)

    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[BrowserScreen] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "browser"):
            return

        self._log("Returning to MainScreen.")

        self.close(action_id)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[BrowserScreen] EXIT/PVR pressed.")

        self._log("Closing")

        self.close(None)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"BrowserScreen(initialized={self._initialized})"


# ==============================================================================
#
# Build Notes
#
# BrowserScreen responsibilities:
#
#   - Directory browsing (Directories column)
#   - File preview and selection (Files column)
#   - Playlist building (Playlist column, via OK's per-column menus)
#   - Forwarding playback requests to the shared PlaybackController
#   - Returning to MainScreen
#
# BrowserScreen is intentionally NOT responsible for:
#
#   - Playback implementation
#   - Playback status display (MainScreen's StatusBar handles that)
#   - Enigma2 service handling
#   - Platform compatibility
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

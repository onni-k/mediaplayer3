# ==============================================================================
#
# MediaPlayer3
#
# File        : playlistscreen.py
#
# Description :
#
#     PlaylistScreen
#
#     Dual-panel playlist management: left panel lists local
#     PlaylistManager playlists AND InternetRadioManager favorite
#     lists together (local first, then radio); right panel lists the
#     selected entry's tracks or stations. All modifications are
#     delegated to PlaylistManager/InternetRadioManager -- PlaylistScreen
#     only displays and dispatches user choices.
#
# Implements :
#
#     PLAYLISTSCREEN_SPEC.md v0.2
#
# Architecture :
#
#     ARCHITECTURE.md (Build 0007)
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
# 2026-07-19  Build 0007
#   - Initial version (local playlists only).
#
# 2026-07-24  Build 0007 (device test round 3)
#   - Combined local playlists and Internet Radio favorite lists in
#     the left panel (local first, then radio -- "Vasemmassa listassa
#     ensin paikalliset soittolistat ja sitten internetradiolistat"),
#     requested after real device testing. Each entry tracked as
#     ("local", name)/("radio", name); context menus, playback and
#     information dialogs all branch on entry type. Radio-list "Play"
#     plays the first station in that favorite list; radio entries
#     have a leaner menu (no Export/Move Up/Move Down, which don't
#     apply to stations).
#
# 2026-07-24  Build 0007 (device test round 5)
#   - Added INFO handling (infoPressed()): PlaylistScreen previously
#     had no "InfoActions" context or "info"/"showEventInfo" binding
#     at all, showing Enigma2's "unhandled key" indicator on OpenATV.
#     Shows Information for whichever panel/entry currently has focus.
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
# ------------------------------------------------------------------------------

from __future__ import annotations

import os

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
from .config import config_manager
from .guide_manager import guide_manager
from .guide_screen import GuideScreen
from .internetradio_manager import internetradio_manager
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .playlist_manager import playlist_manager
from .skin import resolve_skin_asset_path, to_opaque_skin_color

# Device test round 58 -- background-image variant/tier system, a
# copy of MusicLibraryScreen's own (round 39/46), matching the same
# "reuse Music Library's images and colours" pattern already used for
# RadioBrowserScreen/BrowserScreen/PodcastScreen (rounds 54-56). Two
# columns instead of three this time, per direct request.
PLAYLIST_SKIN_VARIANTS = ("light", "dark", "test_skin", "vintage_radio")

PLAYLIST_DEFAULT_SKIN_VARIANT = "light"

PLAYLIST_SKIN_PALETTES = {
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
# väriteema mainscreenin mukaiseksi"): see browserscreen.py's own
# round 149 comment for the full reasoning.
PLAYLIST_SKIN_PALETTES["test_skin"] = {
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

# Round 155, per direct request: independent copy, see mainscreen.py's
# own round 155 comment for the full reasoning.
PLAYLIST_SKIN_PALETTES["vintage_radio"] = {
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


def _resolvePlaylistSkinVariant() -> str:

    variant = config_manager.get("appearance.skin", PLAYLIST_DEFAULT_SKIN_VARIANT)

    if variant not in PLAYLIST_SKIN_VARIANTS:
        return PLAYLIST_DEFAULT_SKIN_VARIANT

    return variant


def _resolvePlaylistResolutionTier(screen_width: int) -> str:

    return "hd" if screen_width >= 1000 else "sd"

# Build 0010, device test round 6 -- named for _updateColumnHighlighting()'s
# loop, matching RadioBrowserScreen/MusicLibraryScreen/PodcastScreen's own
# PANELS/COLUMNS convention (this screen previously used the "playlists"/
# "tracks" string literals directly everywhere else, which is unaffected).
PANELS = ("playlists", "tracks")

# CHANNEL UP/DOWN jump this many entries at once in the focused panel,
# matching BrowserScreen/MusicLibraryScreen/PodcastScreen/
# RadioBrowserScreen's own PAGE_STEP convention for long lists
# (added round 79, per direct request -- this screen never had CH+/
# CH- paging before this round).
PAGE_STEP = 15


def _formatPlaylistDuration(total_seconds: int) -> str:
    """
    Device test round 58 -- formats a playlist's total duration as
    "H:MM:SS" or "M:SS", matching PodcastScreen's own _formatDuration()
    pattern. Returns "" when there's nothing usable (e.g. every track
    was missing duration data) rather than showing "0:00", which would
    misleadingly imply the playlist itself is empty.
    """

    if total_seconds <= 0:
        return ""

    hours, remainder = divmod(total_seconds, 3600)

    minutes, secs = divmod(remainder, 60)

    if hours:

        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"



class PlaylistScreen(Screen, HelpableScreen):
    """
    Dual-panel playlist management (Build 0007).
    """

    SPECIFICATION_VERSION = "0.1"

    # Device test round 58 -- changed from 700x500 to 1672x941,
    # matching MusicLibraryScreen's own round 39 reasoning.
    DESIGN_WIDTH = 1672
    DESIGN_HEIGHT = 941

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Device test round 58 -- reuses MusicLibraryScreen's own
        background-image approach exactly (per direct request: same
        pattern already used for RadioBrowserScreen/BrowserScreen/
        PodcastScreen), but with two wider columns instead of three
        ("täytyy jakaa vain kuva 2 sarakkeeseen"). Icons: playlists->
        playlist (the list-with-dots icon), tracks->track (music
        note, already used elsewhere). New "info" widget shows the
        current playlist's own track count and total duration, per
        direct request -- this screen never had a description/info
        display before.
        """

        sx = width / PlaylistScreen.DESIGN_WIDTH
        sy = height / PlaylistScreen.DESIGN_HEIGHT

        self._screen_width = width

        self._screen_height = height

        self._skin_variant = _resolvePlaylistSkinVariant()

        palette = PLAYLIST_SKIN_PALETTES[self._skin_variant]

        panel_background_color = to_opaque_skin_color(palette["panel_background_color"])
        panel_text_color = palette["panel_text_color"]

        # Round 151, per direct request: see browserscreen.py's own
        # round 151 comment for the full reasoning -- same fix, same
        # scope (test_skin only).
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
        <screen name="MediaPlayer3PlaylistScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{panel_background_color}"
                title="MediaPlayer3 - Playlists">

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

            <widget name="playlists_title_normal"
                    {rect(104, 80, 700, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="playlists_title_active"
                    {rect(104, 80, 700, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="tracks_title_normal"
                    {rect(919, 80, 700, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="tracks_title_active"
                    {rect(919, 80, 700, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="playlists"
                    {rect(40, 138, 775, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="{scrollbar_bg}"
                    scrollbarMode="showOnDemand"/>

            <widget name="tracks"
                    {rect(855, 138, 775, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="{scrollbar_bg}"
                    scrollbarMode="showOnDemand"/>

            <widget name="info"
                    {rect(60, 702, 1550, 130)}
                    {font(28)}
                    halign="center"
                    valign="center"
                    foregroundColor="{palette['info_label_fg']}"
                    {info_background_attr}/>

            <widget name="hint_text_leftright"
                    {rect(82, 874, 299, 63)}
                    font="Bold;{max(10, int(24 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_updown"
                    {rect(447, 874, 240, 63)}
                    font="Bold;{max(10, int(24 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_ok"
                    {rect(753, 874, 169, 63)}
                    font="Bold;{max(10, int(24 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_menu"
                    {rect(988, 874, 196, 63)}
                    font="Bold;{max(10, int(24 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_exit"
                    {rect(1250, 874, 186, 63)}
                    font="Bold;{max(10, int(24 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

        </screen>
        """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, session, playback_controller=None):

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        HelpableScreen.__init__(self)

        self.session = session

        self._playback = playback_controller

        self._focus = "playlists"

        # Combined local playlists + radio favorite lists (Build 0007,
        # device test round 3), each entry ("local", name) or
        # ("radio", name) -- see _reloadPlaylists().
        self._entries = []
        self._current_entry_type = None

        self._current_playlist = None
        self._current_tracks = []

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Playlist] %s", message)

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

        for panel_name in PANELS:

            self[f"{panel_name}_title_normal"] = Label("")
            self[f"{panel_name}_title_active"] = Label("")
            self[f"{panel_name}_title_active"].hide()

        self["playlists"] = MenuList([])
        self["tracks"] = MenuList([])

        # Device test round 58 -- new: shows the current playlist's
        # own track count and total duration, per direct request.
        # Didn't exist before this round.
        self["info"] = Label("")

        self["hint_text_leftright"] = Label(_("LEFT/RIGHT: Panel"))
        self["hint_text_updown"] = Label(_("UP/DOWN: Move"))
        self["hint_text_ok"] = Label(_("OK: Options"))
        self["hint_text_menu"] = Label(_("MENU: Menu"))
        self["hint_text_exit"] = Label(_("EXIT: Back"))

        # Round 134, per direct programmer feedback ("For colour
        # buttons use StaticText() and use the standard names, i.e.
        # 'key_red', 'key_green', 'key_yellow', 'key_blue'"): the
        # correct Enigma2 component type/naming for colour-button
        # hints, confirmed against real stock Enigma2 and enigma2-
        # plugins source (e.g. HdmiCEC's own setup screen, Emission's
        # own EmissionOverview.py) -- Label()+a made-up widget name
        # (this project's own earlier pattern, e.g. hint_text_yellow
        # elsewhere in this codebase) works but isn't what any other
        # Enigma2 screen or skin actually expects. Created here so the
        # correct component exists from round 133's own red/green/
        # yellow additions onward; deliberately NOT given a skin
        # <widget source="key_red".../> entry yet -- this screen's own
        # hint bar (5 existing slots) has only ~200px of its own
        # 1672px design width left unused, not enough room for three
        # more full-width hints without redesigning the background
        # artwork and widget geometry the way MainScreen's own hint
        # bar needed (rounds 113-129) -- a well-scoped follow-up, not
        # attempted here. An Enigma2 Source component created without
        # a matching skin entry is simply invisible, never an error
        # (the same tolerant behaviour this project's own hint_text_*
        # widgets already rely on).
        self["key_red"] = StaticText(_("Clear"))
        self["key_green"] = StaticText(_("New"))
        self["key_yellow"] = StaticText(_("Rename"))

        actions = {
            "ok": self.okPressed,
            "cancel": self.exitPressed,
            "left": self.focusLeft,
            "right": self.focusRight,
            "up": self.moveUp,
            "down": self.moveDown,
            "menu": self.menuPressed,
            # Round 133, per direct request ("Soittolistalla punainen
            # voi tyhjentää soittolistan ja vihreä luo uuden, Keltainen
            # voi nimetä uudelleen" -- RED clears, GREEN creates a new
            # one, YELLOW renames): direct colour-key shortcuts for
            # three actions that already existed behind the OK/Options
            # menu (rename, create) or needed a genuinely new
            # capability (clear -- see playlist_manager.clearPlaylist()'s
            # own docstring for why this is deliberately distinct from
            # the existing "Delete" menu option, which removes the
            # playlist entry itself, not just its own tracks).
            #
            # Round 147, per direct request: RED is now context-
            # dependent (delete playlist / remove track -- see
            # redPressed()'s own docstring); YELLOW/BLUE became Move
            # Up/Move Down, matching BrowserScreen's own Playlist
            # column shortcuts, since Rename is reachable from the OK
            # menu alone and no longer needs a colour key of its own.
            "red": self.redPressed,
            "green": self.createNewPlaylistPressed,
            "yellow": self.yellowPressed,
            "blue": self.bluePressed,
        }

        # Round 132, per direct request: EPG/INFO used to show
        # information already visible in this screen's own hint bar
        # (redundant); now opens this screen's own help content
        # instead, matching every other screen.
        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.infoPressed

        for action_name in compatibility.getChannelUpKeyActionNames():
            actions[action_name] = self.pageUp

        for action_name in compatibility.getChannelDownKeyActionNames():
            actions[action_name] = self.pageDown

        for action_name in compatibility.getHelpKeyActionNames():

            # Round 156, per direct request/device log: "displayHelpLong"
            # is excluded the same way as "displayHelp" -- a real device
            # log showed both registered on the same HelpActions context
            # for the same physical HELP key on some images, so leaving
            # it bound here let it win that key over the native handler.
            # See mainscreen.py's own round 156 comment for the full story.
            if action_name in ("displayHelp", "displayHelpLong"):

                continue

            actions[action_name] = self.infoPressed

        contexts = [
            "OkCancelActions",
            "ColorActions",
            "DirectionActions",
            "MediaPlayerActions",
            "MenuActions",
            "InfoActions",
            "InfobarEPGActions",
            "HelpActions",
        ]

        help_text_by_handler = {
            self.okPressed: _("open the actions menu"),
            self.exitPressed: _("go back"),
            self.focusLeft: _("move to the left panel"),
            self.focusRight: _("move to the right panel"),
            self.moveUp: _("move up"),
            self.moveDown: _("move down"),
            self.menuPressed: _("open the menu"),
            self.pageUp: _("page up"),
            self.pageDown: _("page down"),
            self.infoPressed: _("show information about this screen"),
            self.redPressed: _("delete the selected playlist, or remove the selected track"),
            self.createNewPlaylistPressed: _("create a new playlist"),
            self.yellowPressed: _("move the selected track up"),
            self.bluePressed: _("move the selected track down"),
        }

        try:

            helpable_actions = {
                action_name: (handler, help_text_by_handler.get(handler, ""))
                for action_name, handler in actions.items()
            }

            self["actions"] = HelpableActionMap(self, contexts, helpable_actions, -1)

        except Exception as error:

            logger.warning(f"[PlaylistScreen] HelpableActionMap unavailable, falling back to plain ActionMap: {error}")

            self["actions"] = ActionMap(contexts, actions, -1)

        self._reloadPlaylists()

        self._updateFocusIndicator()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Panel / list management
    # ------------------------------------------------------------------

    def _reloadPlaylists(self) -> None:
        """
        Build the combined left-panel list: local PlaylistManager
        playlists first, then InternetRadioManager favorite lists
        (Build 0007, device test round 3 -- "Vasemmassa listassa
        ensin paikalliset soittolistat ja sitten internetradiolistat").
        Each entry is ("local", name) or ("radio", name); radio
        entries are shown with a "(Radio)" suffix to disambiguate from
        a local playlist that happens to share the same name.
        """

        local_names = playlist_manager.getPlaylistNames()

        radio_names = internetradio_manager.getFavoriteListNames()

        self._entries = [("local", name) for name in local_names] + [("radio", name) for name in radio_names]

        display = local_names + [f"{name} ({_('Radio')})" for name in radio_names]

        self["playlists"].setList(display)

        if self._entries:

            self._selectEntry(0)

        else:

            self._current_playlist = None

            self._current_entry_type = None

            self._current_tracks = []

            self["tracks"].setList([])

    # ------------------------------------------------------------------

    def _selectEntry(self, index: int) -> None:

        if not (0 <= index < len(self._entries)):
            return

        self._current_entry_type, self._current_playlist = self._entries[index]

        self._reloadTracks()

    # ------------------------------------------------------------------

    def _reloadTracks(self) -> None:

        if not self._current_playlist:

            self["tracks"].setList([])

            self._updatePlaylistInfo()

            return

        if self._current_entry_type == "radio":

            self._current_tracks = internetradio_manager.getFavorites(self._current_playlist)

            display = [entry.get("name", "Unknown") for entry in self._current_tracks]

        else:

            self._current_tracks = playlist_manager.loadPlaylist(self._current_playlist)

            display = [
                track.get("title") or track.get("file_name", "Unknown")
                for track in self._current_tracks
            ]

        self["tracks"].setList(display)

        self._updatePlaylistInfo()

        logger.verbose(
            f"[Playlist] Track list updated\n\n"
            f"List: {self._current_playlist} ({self._current_entry_type})\n\n"
            f"Entries: {len(display)}\n"
        )

    # ------------------------------------------------------------------

    def _updateFocusIndicator(self) -> None:
        """
        Build 0010, device test round 7 -- see MusicLibraryScreen's
        identical fix/reasoning.
        """

        self["status"].setText(_("Playlists"))

        # Device test round 58 -- titles are static (never change
        # dynamically, unlike Podcast/BrowserScreen's own titles), but
        # now need setting explicitly since the normal/active pair
        # widgets start out empty (Label("")) rather than being
        # constructed with their final text directly, matching how
        # every other converted screen sets its own titles.
        self["playlists_title_normal"].setText(_("Playlists"))

        self["playlists_title_active"].setText(_("Playlists"))

        self["tracks_title_normal"].setText(_("Tracks"))

        self["tracks_title_active"].setText(_("Tracks"))

        self._updateColumnHighlighting()

        self._updatePlaylistInfo()

    # ------------------------------------------------------------------

    def _updateColumnHighlighting(self) -> None:
        """
        Device test round 58 -- the active/inactive column-header
        colouring now lives in one of two pre-rendered background
        images (resources/skins/{variant}/{tier}/playlist_{focus}_
        active.png), swapped here instead of toggling individual bg
        widgets, matching MusicLibraryScreen's own round 39/45 and
        RadioBrowserScreen's/BrowserScreen's/PodcastScreen's own
        rounds 54-56. Header TEXT stays real, translatable normal/
        active widget pairs, toggled here too.
        """

        self._decodeBackgroundImage(self._focus)

        for panel_name in PANELS:

            is_active = panel_name == self._focus

            try:
                self[f"{panel_name}_title_normal"].hide() if is_active else self[f"{panel_name}_title_normal"].show()

                self[f"{panel_name}_title_active"].show() if is_active else self[f"{panel_name}_title_active"].hide()

            except Exception as error:

                logger.verbose(f"[Playlist] Unable to set column highlight visibility: {error}")

    # ------------------------------------------------------------------
    # Background image (device test round 58 -- mirrors
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

            logger.verbose("[Playlist] background widget not ready yet, retrying decode shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(lambda: self._decodeBackgroundImage(focus_state))

            retry_timer.start(100, True)

            self._pending_background_retry_timer = retry_timer

            return

        image_path = resolve_skin_asset_path(
            self._skin_variant,
            _resolvePlaylistResolutionTier(self._screen_width),
            f"playlist_{focus_state}_active.png",
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

            logger.verbose(f"[Playlist] Unable to decode background image {image_path}: {error}")

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

            logger.verbose(f"[Playlist] Unable to apply decoded background image: {error}")

        finally:

            self._background_decode_in_progress = False

    # ------------------------------------------------------------------

    def _updatePlaylistInfo(self) -> None:
        """
        Device test round 58 -- shows the current playlist's own
        track count and total duration in the new "info" widget, per
        direct request. Radio-favourites lists have no duration data
        (they're live streams, not fixed-length tracks), so only the
        track count is shown for those; regular playlists show both.
        Falls back to a translated placeholder when nothing is
        selected.
        """

        if not self._current_playlist:

            self["info"].setText(_("No playlist selected"))

            return

        count = len(self._current_tracks)

        if self._current_entry_type == "radio":

            self["info"].setText(_("%d station(s)") % count)

            return

        total_seconds = 0

        for track in self._current_tracks:

            try:
                total_seconds += int(track.get("duration") or 0)

            except (TypeError, ValueError):

                pass

        duration_text = _formatPlaylistDuration(total_seconds)

        if duration_text:

            self["info"].setText(f"{count} {_('track(s)')} \u2022 {duration_text}")

        else:

            self["info"].setText(f"{count} {_('track(s)')}")

    # ------------------------------------------------------------------
    # Navigation (PLAYLISTSCREEN_SPEC.md "Navigation")
    # ------------------------------------------------------------------

    def focusLeft(self) -> None:

        logger.verbose("[Playlist] LEFT pressed.")

        self._focus = "playlists"

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def focusRight(self) -> None:

        logger.verbose("[Playlist] RIGHT pressed.")

        self._focus = "tracks"

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def moveUp(self) -> None:

        logger.verbose("[Playlist] UP pressed.")

        if self._focus == "playlists":

            self["playlists"].up()

            self._onPlaylistSelectionChanged()

        else:

            self["tracks"].up()

    # ------------------------------------------------------------------

    def moveDown(self) -> None:

        logger.verbose("[Playlist] DOWN pressed.")

        if self._focus == "playlists":

            self["playlists"].down()

            self._onPlaylistSelectionChanged()

        else:

            self["tracks"].down()

    # ------------------------------------------------------------------

    def pageUp(self) -> None:
        """
        CH+ -- jump PAGE_STEP entries up in the focused panel
        (round 79, matching BrowserScreen/MusicLibraryScreen/
        PodcastScreen/RadioBrowserScreen's own CH+/CH- convention).
        Clamped so it stops at the top of the list instead of
        wrapping around when fewer than PAGE_STEP entries remain
        (round 80, per direct request).
        """

        logger.verbose("[Playlist] CH+ pressed. focus=%s", self._focus)

        widget = self[self._focus]

        steps = min(PAGE_STEP, widget.getSelectedIndex())

        if self._focus == "playlists":

            for _step in range(steps):

                widget.up()

            self._onPlaylistSelectionChanged()

        else:

            for _step in range(steps):

                widget.up()

    # ------------------------------------------------------------------

    def pageDown(self) -> None:

        logger.verbose("[Playlist] CH- pressed. focus=%s", self._focus)

        widget = self[self._focus]

        entries = widget.list or []

        steps = min(PAGE_STEP, max(0, len(entries) - 1 - widget.getSelectedIndex()))

        if self._focus == "playlists":

            for _step in range(steps):

                widget.down()

            self._onPlaylistSelectionChanged()

        else:

            for _step in range(steps):

                widget.down()

    # ------------------------------------------------------------------

    def _onPlaylistSelectionChanged(self) -> None:
        """
        Selecting a playlist/list automatically loads its contents;
        playback is never started automatically
        (PLAYLISTSCREEN_SPEC.md "Playlist Selection").
        """

        self._selectEntry(self["playlists"].getSelectedIndex())

# End of Part 1
    # ------------------------------------------------------------------
    # Context Menus (PLAYLISTSCREEN_SPEC.md "Playlist Context Menu" /
    # "Track Context Menu")
    # ------------------------------------------------------------------

    def okPressed(self) -> None:

        logger.verbose("[Playlist] OK pressed.")

        if self._focus == "playlists":

            self._openPlaylistMenu()

        else:

            self._openTrackMenu()

    # ------------------------------------------------------------------

    def infoPressed(self) -> None:
        """
        Round 139 -- renamed from helpPressed(); opens GuideScreen
        with PlaylistScreen's own context-sensitive information
        document. This also replaces round 132's own dead infoPressed()
        (which showed a track/playlist's own context-menu Information
        instead -- unreachable since round 132 moved EPG/INFO to
        open help content here; removed as part of this rename rather
        than left in place any longer).
        """

        logger.verbose("[Playlist] INFO pressed.")

        title, content = guide_manager.getGuide("playlistscreen")

        self.session.open(GuideScreen, title, content)

    # ------------------------------------------------------------------

    def _openPlaylistMenu(self) -> None:

        if not self._current_playlist:

            self._openCreationMenu()

            return

        if self._current_entry_type == "radio":

            choices = [
                (_("Play"), "play"),
                (_("Rename"), "rename"),
                (_("Delete"), "delete"),
                (_("Information"), "information"),
                (_("Create New"), "create"),
                (_("Cancel"), "cancel"),
            ]

        else:

            choices = [
                (_("Play"), "play"),
                (_("Rename"), "rename"),
                (_("Delete"), "delete"),
                (_("Clear"), "clear"),
                (_("Export"), "export"),
                (_("Information"), "information"),
                (_("Create New"), "create"),
                (_("Cancel"), "cancel"),
            ]

        self.session.openWithCallback(
            self._playlistMenuChosen,
            ChoiceBox,
            title=self._current_playlist,
            list=choices,
        )

    # ------------------------------------------------------------------

    def _playlistMenuChosen(self, choice) -> None:

        if choice is None:
            return

        action = choice[1]

        if action == "play":

            self._playCurrentPlaylist()

        elif action == "rename":

            self._promptText(_("New playlist name"), self._current_playlist, self._renamePlaylist)

        elif action == "delete":

            self._confirmDeletePlaylist()

        elif action == "clear":

            # Round 147: "Clear" (emptying this local playlist's own
            # tracks while keeping the playlist itself, distinct from
            # "Delete" above) moved here from round 133's own RED
            # colour-key shortcut -- see redPressed()'s own docstring.
            # Local-only, matching "Export"'s own existing local-only
            # restriction in this same choice list.
            self.session.openWithCallback(
                self._clearPlaylistConfirmed,
                MessageBox,
                f"{_('Clear')} \"{self._current_playlist}\"?",
                MessageBox.TYPE_YESNO,
            )

        elif action == "export":

            path = playlist_manager.exportPlaylist(self._current_playlist)

            if path:

                self.session.open(MessageBox, f"{_('Exported')}: {path}", MessageBox.TYPE_INFO)

        elif action == "information":

            self._showPlaylistInformation()

        elif action == "create":

            self._openCreationMenu()

    # ------------------------------------------------------------------

    def _openTrackMenu(self) -> None:

        if not self._current_tracks:
            return

        index = self["tracks"].getSelectedIndex()

        if not (0 <= index < len(self._current_tracks)):
            return

        entry = self._current_tracks[index]

        if self._current_entry_type == "radio":

            choices = [
                (_("Play"), "play"),
                (_("Remove from Playlist"), "remove"),
                (_("Move Up"), "move_up"),
                (_("Move Down"), "move_down"),
                (_("Information"), "information"),
                (_("Cancel"), "cancel"),
            ]

            title = entry.get("name", "Unknown")

        else:

            choices = [
                (_("Play"), "play"),
                (_("Remove from Playlist"), "remove"),
                (_("Move Up"), "move_up"),
                (_("Move Down"), "move_down"),
                (_("Information"), "information"),
                (_("Cancel"), "cancel"),
            ]

            title = entry.get("title", entry.get("file_name", "Unknown"))

        self.session.openWithCallback(
            lambda choice: self._trackMenuChosen(choice, index, entry),
            ChoiceBox,
            title=title,
            list=choices,
        )

    # ------------------------------------------------------------------

    def _trackMenuChosen(self, choice, index, entry) -> None:

        if choice is None:
            return

        action = choice[1]

        is_radio = self._current_entry_type == "radio"

        if action == "play":

            self._playFromTrack(index)

        elif action == "remove":

            self._confirmRemoveTrack(index)

        elif action == "move_up":

            # Round 146, per direct follow-up request ("soittolistan-
            # ässä siirrä ylös/alas koskemaan myös radion suosikki-
            # listoja, nyt vaikuttaa vain paikallisiin tiedostoihin"):
            # previously excluded radio entries entirely (`and not
            # is_radio`), since internetradio_manager had no reorder
            # capability of its own at all until this round's own
            # moveFavorite() was added. Both branches now use the
            # exact same swap-based approach, just against a different
            # manager/list identifier.
            if is_radio:

                internetradio_manager.moveFavorite(self._current_playlist, index, -1)

            else:

                playlist_manager.moveTrack(self._current_playlist, index, -1)

            self._reloadTracks()

        elif action == "move_down":

            if is_radio:

                internetradio_manager.moveFavorite(self._current_playlist, index, 1)

            else:

                playlist_manager.moveTrack(self._current_playlist, index, 1)

            self._reloadTracks()

        elif action == "information":

            if is_radio:

                lines = [
                    entry.get("name", "Unknown"),
                    "",
                    f"{_('Codec')}: {entry.get('codec', 'Unknown')}",
                    f"{_('Country')}: {entry.get('country', 'Unknown')}",
                    f"{_('Tags')}: {entry.get('tags', 'Unknown')}",
                ]

            else:

                lines = [
                    entry.get("title", "Unknown"),
                    "",
                    f"Artist: {entry.get('artist', 'Unknown')}",
                    f"Path: {entry.get('path', 'Unknown')}",
                ]

            self.session.open(MessageBox, "\n".join(lines), MessageBox.TYPE_INFO)

# End of Part 2
    # ------------------------------------------------------------------
    # Playback (delegates to PlaybackController via MainScreen's shared
    # instance -- PlaylistScreen never talks to ServiceController)
    # ------------------------------------------------------------------

    def _playCurrentPlaylist(self) -> None:

        self._playFromTrack(0)

    # ------------------------------------------------------------------

    def _playFromTrack(self, start_index: int) -> None:

        if self._playback is None or not self._current_playlist:
            return

        if self._current_entry_type == "radio":

            self._playRadioListEntry(start_index)

            return

        queue = playlist_manager.generatePlaybackQueue(self._current_playlist)

        if not queue:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        start_index = min(start_index, len(queue) - 1)

        self._log(f"Play Playlist: {self._current_playlist} (starting at {start_index})")

        if self._playback.playQueue(queue, start_index):

            self.close(("played", self._current_playlist))

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------

    def _playRadioListEntry(self, index: int) -> None:
        """
        Play the station at `index` in the current radio favorite
        list (Build 0007, device test round 3). Mirrors
        RadioBrowserScreen._playStation() -- PlaylistScreen prepares
        and plays the stream itself rather than depending on
        MainScreen, matching how it already plays local queues
        directly.
        """

        stations = internetradio_manager.getFavorites(self._current_playlist)

        if not stations or not (0 <= index < len(stations)):

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        station = stations[index]

        result = internetradio_manager.prepareStream(station)

        if result is None or not self._playback.playStream(result["url"], result["station"]):

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        self._log(f"Play Radio List: {self._current_playlist} -> {station.get('name', '?')}")

        self.close(("played", None))

    # ------------------------------------------------------------------
    # Playlist Creation (PLAYLISTSCREEN_SPEC.md "Playlist Creation")
    # ------------------------------------------------------------------

    def _openCreationMenu(self) -> None:

        choices = [
            (_("Empty Playlist"), "empty"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            self._creationMenuChosen,
            ChoiceBox,
            title=_("Create playlist"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _creationMenuChosen(self, choice) -> None:

        if choice is None or choice[1] != "empty":
            return

        self._promptText(_("New playlist name"), "", self._createPlaylist)

    # ------------------------------------------------------------------

    def createNewPlaylistPressed(self) -> None:
        """
        Round 133: GREEN's own direct shortcut to "Create playlist" ->
        "Empty Playlist" -- the ChoiceBox this normally goes through
        (_openCreationMenu()) only ever offers that one real choice
        besides Cancel, so this skips straight to the name prompt
        rather than making the user confirm a single-option menu.
        """

        self._promptText(_("New playlist name"), "", self._createPlaylist)

    # ------------------------------------------------------------------

    def yellowPressed(self) -> None:
        """
        Round 147, per direct request: replaces round 133's own
        renamePlaylistPressed() shortcut -- Rename stays reachable via
        the OK menu only now ("nimeä uudelleen riittää kun on ok-napin
        takana käytettävissä"), freeing YELLOW for the same "Move Up"
        shortcut BrowserScreen's own Playlist column already has.
        Works for both local tracks and radio favourite entries.
        """

        self._moveSelectedTrack(-1)

    # ------------------------------------------------------------------

    def bluePressed(self) -> None:
        """
        Round 147: the same shortcut as yellowPressed() above, for
        "Move Down" instead -- replaces round 146's own single-track
        remove shortcut, which moved to RED (see redPressed()'s own
        docstring for the full reasoning).
        """

        self._moveSelectedTrack(1)

    # ------------------------------------------------------------------

    def _moveSelectedTrack(self, direction: int) -> None:

        if self._focus == "playlists" or not self._current_tracks:

            return

        index = self["tracks"].getSelectedIndex()

        if not (0 <= index < len(self._current_tracks)):

            return

        if self._current_entry_type == "radio":

            internetradio_manager.moveFavorite(self._current_playlist, index, direction)

        else:

            playlist_manager.moveTrack(self._current_playlist, index, direction)

        self._reloadTracks()

    # ------------------------------------------------------------------

    def redPressed(self) -> None:
        """
        Round 147, per direct request ("muutetaan soittolistan
        punaisen poista toiminto sen mukaan ollaanko soittolista- vai
        kappale/kanava sarakkeessa"): RED is now context-dependent --
        deletes the whole selected playlist (Playlists column, via the
        existing _confirmDeletePlaylist(), unchanged) or removes just
        the selected track/station (Tracks column, via the new
        _confirmRemoveTrack(), which round 146's own bluePressed()
        used to do without any confirmation at all -- now confirmed
        the same way, per the same direct request). Replaces round
        133's own clearPlaylistPressed() -- "Clear" (emptying a local
        playlist's own tracks while keeping the playlist itself) is
        still available, just moved into the playlist-level menu
        itself (_playlistMenuChosen()'s own new "clear" choice) rather
        than kept on a colour key, matching the same "menu is enough"
        reasoning yellowPressed() above already applies to Rename.
        """

        if self._focus == "playlists":

            if not self._current_playlist:

                return

            self._confirmDeletePlaylist()

            return

        if not self._current_tracks:

            return

        index = self["tracks"].getSelectedIndex()

        self._confirmRemoveTrack(index)

    # ------------------------------------------------------------------

    def _clearPlaylistConfirmed(self, confirmed) -> None:

        if not confirmed or not self._current_playlist:

            return

        playlist_manager.clearPlaylist(self._current_playlist)

        self._reloadPlaylists()

    # ------------------------------------------------------------------

    def _createPlaylist(self, name) -> None:
        """
        "Create New" always creates a LOCAL playlist -- radio favorite
        lists have their own creation flow in RadioBrowserScreen
        (Add to Favorites -> Create New), which also lets a station be
        added to the new list in the same step.
        """

        if not name:
            return

        if playlist_manager.createPlaylist(name):

            self._reloadPlaylists()

            self._selectEntryByTypeAndName("local", name)

        else:

            self.session.open(MessageBox, _("Playlist already exists"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------

    def _renamePlaylist(self, new_name) -> None:

        if not new_name or new_name == self._current_playlist:
            return

        if self._current_entry_type == "radio":

            ok = internetradio_manager.renameFavoriteList(self._current_playlist, new_name)

        else:

            ok = playlist_manager.renamePlaylist(self._current_playlist, new_name)

        if ok:

            entry_type = self._current_entry_type

            self._reloadPlaylists()

            self._selectEntryByTypeAndName(entry_type, new_name)

    # ------------------------------------------------------------------

    def _confirmDeletePlaylist(self) -> None:

        self.session.openWithCallback(
            self._deleteConfirmed,
            MessageBox,
            f"{_('Delete')} \"{self._current_playlist}\"?",
            MessageBox.TYPE_YESNO,
        )

    # ------------------------------------------------------------------

    def _deleteConfirmed(self, confirmed) -> None:

        if not confirmed or not self._current_playlist:
            return

        if self._current_entry_type == "radio":

            internetradio_manager.deleteFavoriteList(self._current_playlist)

        else:

            playlist_manager.deletePlaylist(self._current_playlist)

        self._reloadPlaylists()

    # ------------------------------------------------------------------

    def _confirmRemoveTrack(self, index: int) -> None:
        """
        Round 147, per direct request ("lisätään myös kysely haluatko
        poistaa" -- add a confirmation dialog too): removing a single
        track/station used to happen immediately, with no confirmation
        at all, from both the track menu's own "Remove from Playlist"
        choice and round 146's own direct BLUE shortcut. Both now go
        through this shared method instead, matching
        _confirmDeletePlaylist()'s own existing pattern for the
        whole-playlist case.
        """

        if not (0 <= index < len(self._current_tracks)):
            return

        entry = self._current_tracks[index]

        name = entry.get("name") if self._current_entry_type == "radio" else entry.get("title", entry.get("file_name", "?"))

        self.session.openWithCallback(
            lambda confirmed: self._removeTrackConfirmed(confirmed, index),
            MessageBox,
            f"{_('Remove')} \"{name}\"?",
            MessageBox.TYPE_YESNO,
        )

    # ------------------------------------------------------------------

    def _removeTrackConfirmed(self, confirmed, index: int) -> None:

        if not confirmed or not (0 <= index < len(self._current_tracks)):
            return

        entry = self._current_tracks[index]

        if self._current_entry_type == "radio":

            internetradio_manager.removeFavorite(entry.get("stationuuid"), self._current_playlist)

        else:

            playlist_manager.removeTrack(self._current_playlist, index)

        self._reloadTracks()

    # ------------------------------------------------------------------

    def _showPlaylistInformation(self) -> None:

        type_label = _("Internet Radio") if self._current_entry_type == "radio" else _("Playlists")

        lines = [
            self._current_playlist,
            "",
            f"{_('Type')}: {type_label}",
            f"{_('Tracks') if self._current_entry_type != 'radio' else _('Stations')}: {len(self._current_tracks)}",
        ]

        self.session.open(MessageBox, "\n".join(lines), MessageBox.TYPE_INFO)

    # ------------------------------------------------------------------

    def _selectEntryByTypeAndName(self, entry_type, name) -> None:

        if (entry_type, name) in self._entries:

            self._selectEntry(self._entries.index((entry_type, name)))

    # ------------------------------------------------------------------

    def _promptText(self, title, initial_text, callback) -> None:

        self.session.openWithCallback(
            lambda text: callback(text) if text else None,
            VirtualKeyBoard,
            title=title,
            text=initial_text,
        )

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[Playlist] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "playlists"):
            return

        self.close(action_id)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[Playlist] EXIT pressed.")

        self._log("Closing")

        self._log("Closed")

        self.close(None)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"PlaylistScreen(initialized={self._initialized})"


# ==============================================================================
# End of file
# ==============================================================================

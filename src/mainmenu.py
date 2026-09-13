# ==============================================================================
#
# MediaPlayer3
#
# File        : mainmenu.py
#
# Description :
#
#     MainMenu
#
#     Single, reusable navigation menu shared by every primary Screen
#     (MainScreen, BrowserScreen, SettingsScreen).
#
#     MainMenu is responsible only for navigation. It never performs
#     playback or platform specific operations, and it never
#     communicates directly with a Controller -- it dispatches the
#     user's selection back to the calling Screen, which decides what
#     to open next.
#
# Implements :
#
#     MAINMENU_SPEC.md v0.1
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
#   - Added "Music Library" entry, between Playlists and Internet
#     Radio (BUILD_0008_PLAN.md "Main Menu" ordering).
# ------------------------------------------------------------------------------

from __future__ import annotations

import os

from enigma import ePicLoad, eTimer

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen

from .compatibility import compatibility
from .config import config_manager
from .guide_manager import guide_manager
from .guide_screen import GuideScreen
from .localization import _
from .logger import logger
from .skin import resolve_skin_asset_path, skin_manager, to_opaque_skin_color

# Device test round 64 -- background-image variant/tier system, a
# copy of SettingsScreen's own simpler single-image pattern (round
# 59): MainMenu has no multi-panel focus either, so no per-state
# swapping is needed here, matching Settings rather than the more
# complex 6-screen pattern.
MAINMENU_SKIN_VARIANTS = ("light", "dark", "test_skin", "vintage_radio")

MAINMENU_DEFAULT_SKIN_VARIANT = "light"

MAINMENU_SKIN_PALETTES = {
    "light": {
        "panel_background_color": "#F9F9F9",
        "panel_text_color": "#1A1A1A",
        "header_fg": "#036DFA",
        "hint_fg": "#036DFA",
        "selected_row_bg": "#A491FB",
        "selected_row_fg": "#1A1A1A",
    },
    "dark": {
        "panel_background_color": "#1C202B",
        "panel_text_color": "#F0F0F0",
        "header_fg": "#FFFFFF",
        "hint_fg": "#F0F0F0",
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
MAINMENU_SKIN_PALETTES["test_skin"] = {
    "panel_background_color": "#1C1610",
    "panel_text_color": "#E8A24C",
    "header_fg": "#FFC978",
    "hint_fg": "#FFC978",
    "selected_row_bg": "#C08A45",
    "selected_row_fg": "#1A1206",
}

# Round 155, per direct request: independent copy, see mainscreen.py's
# own round 155 comment for the full reasoning.
MAINMENU_SKIN_PALETTES["vintage_radio"] = {
    "panel_background_color": "#1C1610",
    "panel_text_color": "#E8A24C",
    "header_fg": "#FFC978",
    "hint_fg": "#FFC978",
    "selected_row_bg": "#C08A45",
    "selected_row_fg": "#1A1206",
}


def _resolveMainMenuSkinVariant() -> str:

    variant = config_manager.get("appearance.skin", MAINMENU_DEFAULT_SKIN_VARIANT)

    if variant not in MAINMENU_SKIN_VARIANTS:
        return MAINMENU_DEFAULT_SKIN_VARIANT

    return variant


def _resolveMainMenuResolutionTier(screen_width: int) -> str:

    return "hd" if screen_width >= 1000 else "sd"

# ------------------------------------------------------------------------------
# Menu entries (MAINMENU_SPEC.md section 5)
# ------------------------------------------------------------------------------
#
# Each entry is (display_text, action_id). Future menu entries should be
# appended to this list rather than reordering the existing ones, per
# MAINMENU_SPEC.md section 5.

MENU_ENTRIES = [
    ("Browser", "browser"),
    ("Playlists", "playlists"),
    ("Music Library", "music_library"),
    ("Internet Radio", "radio"),
    ("Podcasts", "podcast"),
    ("Settings", "settings"),
    ("Exit", "exit"),
]


class MainMenu(Screen, HelpableScreen):
    """
    Shared navigation menu.

    Usage (from any primary Screen):

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

        def _mainMenuCallback(self, action_id):
            if action_id is None:
                return  # menu closed without a selection
            ...
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.3"

    # Device test round 64 -- changed from 440x360 to 1672x941,
    # matching MusicLibraryScreen's own round 39 reasoning.
    DESIGN_WIDTH = 1672
    DESIGN_HEIGHT = 941

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Device test round 64 -- reuses SettingsScreen's own simpler
        single-image background approach (round 59): MainMenu has no
        multi-panel focus either, so no per-state swapping is needed.
        Header icon is the menu/hamburger icon rather than Settings'
        own gear, matching what this screen actually represents.
        """

        sx = width / MainMenu.DESIGN_WIDTH
        sy = height / MainMenu.DESIGN_HEIGHT

        self._screen_width = width

        self._screen_height = height

        self._skin_variant = _resolveMainMenuSkinVariant()

        palette = MAINMENU_SKIN_PALETTES[self._skin_variant]

        panel_background_color = to_opaque_skin_color(palette["panel_background_color"])
        panel_text_color = palette["panel_text_color"]

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Bold;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3MainMenu"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{panel_background_color}"
                title="{_('Main Menu')}">
            <!-- Round 97, per direct request: the screen's own
                 title= attribute (not the "title" widget below) is
                 what actually renders "MediaPlayer3 - Main Menu" on
                 the left, redundant now that "MediaPlayer3" reads
                 centered in its own new widget (round 96); narrowed
                 to just the translated "Main Menu" string. -->

            <!-- Round 95, per direct request: the "title" widget's
                 own text ("MediaPlayer3") was flashing briefly on
                 open, then disappearing behind this background once
                 its own ePicLoad decode finished ("Mainmenussa
                 otsikko välähtää näytössä, mutta jää siten
                 taustakuvan taakse piiloon"). Being created first in
                 Python (self["background"] = ...) only sets the
                 INITIAL paint order; Enigma2's own async
                 setPixmap() on an already-shown widget can still
                 restack it visually above widgets added later,
                 which is exactly what a background image whose own
                 decode finishes after the screen's first paint can
                 do. zPosition explicitly and permanently pins this
                 widget behind everything else regardless of decode
                 timing, the same technique already used for
                 MainScreen's own cover-art-as-background widget
                 (Build 0005, "zPosition -1, behind all text"). -->
            <widget name="background"
                    position="0,0"
                    size="{width},{height}"
                    zPosition="-1"
                    alphatest="blend"/>

            <!-- Round 96, per direct request: split into "Main Menu"
                 on the left (this widget, narrowed) and "MediaPlayer3"
                 centered (a new widget below); previously one wide
                 box just said "MediaPlayer3" on its own. -->
            <widget name="title"
                    {rect(88, 80, 500, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_fg']}"
                    transparent="1"/>

            <widget name="app_branding"
                    {rect(600, 80, 608, 57)}
                    font="Bold;{max(10, int(36 * sx))}"
                    halign="center"
                    valign="center"
                    foregroundColor="{palette['header_fg']}"
                    transparent="1"/>

            <widget name="menu"
                    {rect(40, 138, 1590, 622)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarMode="showOnDemand"/>

            <widget name="hint_text_ok"
                    {rect(82, 792, 149, 63)}
                    font="Bold;{max(10, int(24 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_exit"
                    {rect(297, 792, 233, 63)}
                    font="Bold;{max(10, int(24 * sx))}"
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

        HelpableScreen.__init__(self)

        self.session = session

        self._entries = [(_(label), action_id) for label, action_id in MENU_ENTRIES]

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[MainMenu] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["background"] = Pixmap()

        self._background_picload = ePicLoad()

        compatibility.connectPictureDataSignal(self._background_picload, self._onBackgroundImageDecoded)

        self["title"] = Label(_("Main Menu"))

        self["app_branding"] = Label("MediaPlayer3")

        self["hint_text_ok"] = Label(_("OK: Select"))
        self["hint_text_exit"] = Label(_("MENU/EXIT: Close"))

        self["menu"] = MenuList([entry[0] for entry in self._entries])

        actions = {
            "ok": self._select,
            "cancel": self._closeMenu,
            "menu": self._closeMenu,
            "up": self["menu"].up,
            "down": self["menu"].down,
        }

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

        contexts = ["OkCancelActions", "DirectionActions", "MenuActions", "HelpActions"]

        help_text_by_handler = {
            self._select: _("select the highlighted entry"),
            self._closeMenu: _("close the menu"),
            self["menu"].up: _("move up"),
            self["menu"].down: _("move down"),
            self.infoPressed: _("show information about this screen"),
        }

        try:

            helpable_actions = {
                action_name: (handler, help_text_by_handler.get(handler, ""))
                for action_name, handler in actions.items()
            }

            self["actions"] = HelpableActionMap(self, contexts, helpable_actions, -1)

        except Exception as error:

            logger.warning(f"[MainMenu] HelpableActionMap unavailable, falling back to plain ActionMap: {error}")

            self["actions"] = ActionMap(contexts, actions, -1)

        self._decodeBackgroundImage()

        self._log("Ready")

    # ------------------------------------------------------------------
    # Background image (device test round 64 -- mirrors
    # SettingsScreen's own single-state _decodeBackgroundImage()/
    # _onBackgroundImageDecoded() exactly; see that file's own
    # docstrings for the full reasoning, not repeated here.)
    # ------------------------------------------------------------------

    def _decodeBackgroundImage(self) -> None:

        if self["background"].instance is None:

            logger.verbose("[MainMenu] background widget not ready yet, retrying decode shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(self._decodeBackgroundImage)

            retry_timer.start(100, True)

            self._pending_background_retry_timer = retry_timer

            return

        image_path = resolve_skin_asset_path(
            self._skin_variant,
            _resolveMainMenuResolutionTier(self._screen_width),
            "mainmenu_background.png",
        )

        try:
            width, height = self._screen_width, self._screen_height

            aspect = AVSwitch().getFramebufferScale()

            self._background_picload.setPara((width, height, aspect[0], aspect[1], False, 1, "#00000000"))

            if self._background_picload.startDecode(image_path) != 0:
                raise RuntimeError("startDecode() reported failure")

        except Exception as error:

            logger.verbose(f"[MainMenu] Unable to decode background image {image_path}: {error}")

    # ------------------------------------------------------------------

    def _onBackgroundImageDecoded(self, picture_info=None) -> None:

        try:
            pixmap = self._background_picload.getData()

            if pixmap is None:
                return

            self["background"].instance.setPixmap(pixmap)

            self["background"].show()

        except Exception as error:

            logger.verbose(f"[MainMenu] Unable to apply decoded background image: {error}")

# End of Part 1
    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def _select(self) -> None:
        """
        Dispatch the currently highlighted entry back to the calling
        Screen.
        """

        index = self["menu"].getSelectedIndex()

        if index is None or index < 0 or index >= len(self._entries):

            self._closeMenu()

            return

        label, action_id = self._entries[index]

        self._log(f"Menu entry selected: {label}")

        self._log("Closing")

        self._log("Closed")

        self.close(action_id)

    # ------------------------------------------------------------------

    def infoPressed(self) -> None:
        """
        Round 139 -- renamed from helpPressed(); opens GuideScreen
        with the Main Menu's own context-sensitive information
        document (this screen has no EPG/INFO key of its own, so
        this is reachable only via the HELP_KEY_ACTIONS fallback
        spellings -- see this file's own getHelpKeyActionNames() loop).
        """

        logger.verbose("[MainMenu] INFO pressed.")

        title, content = guide_manager.getGuide("mainmenu")

        self.session.open(GuideScreen, title, content)

    # ------------------------------------------------------------------

    def _closeMenu(self) -> None:
        """
        Close Main Menu without a selection and return to the calling
        Screen (MAINMENU_SPEC.md section 7 -- MENU/EXIT).
        """

        self._log("Returning to calling screen.")

        self._log("Closing")

        self._log("Closed")

        self.close(None)


# ==============================================================================
#
# Build Notes
#
# MainMenu belongs to the Screen Layer. It communicates only with the
# calling Screen via its close() return value -- never with a
# Controller directly, per MAINMENU_SPEC.md section 12 (Architecture
# Notes).
#
# Round 136, per direct request: "About" removed from this menu
# entirely (it only ever showed the version number, already visible
# in MainScreen's own header) -- see mainscreen.py's own round 136
# comment for the full removal.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

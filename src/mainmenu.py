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
#     (MainScreen, BrowserScreen, SettingsScreen, PlaybackInfoScreen,
#     DeveloperScreen).
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

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.Screen import Screen

from .compatibility import compatibility
from .help_manager import help_manager
from .help_screen import HelpScreen
from .localization import _
from .logger import logger
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)

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
    ("Playback Information", "playback_info"),
    ("Settings", "settings"),
    ("Developer Tools", "developer"),
    ("About", "about"),
    ("Exit", "exit"),
]


class MainMenu(Screen):
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

    DESIGN_WIDTH = 440
    DESIGN_HEIGHT = 360

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build MainMenu's skin for an exact `width` x `height` window,
        scaling from the 440x360 design resolution above (Build 0007,
        device test round 8).
        """

        sx = width / MainMenu.DESIGN_WIDTH
        sy = height / MainMenu.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3MainMenu"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Main Menu">

            <widget name="title"
                    {rect(20, 10, 400, 30)}
                    {font(22)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="menu"
                    {rect(20, 50, 400, 280)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="hint"
                    {rect(20, 330, 400, 25)}
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

        self._entries = [(_(label), action_id) for label, action_id in MENU_ENTRIES]

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[MainMenu] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["title"] = Label("MediaPlayer3")
        self["hint"] = Label(_("OK: Select   MENU/EXIT: Close"))

        self["menu"] = MenuList([entry[0] for entry in self._entries])

        actions = {
            "ok": self._select,
            "cancel": self._closeMenu,
            "menu": self._closeMenu,
            "up": self["menu"].up,
            "down": self["menu"].down,
        }

        for action_name in compatibility.getHelpKeyActionNames():
            actions[action_name] = self.helpPressed

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "MenuActions", "HelpActions"],
            actions,
            -1,
        )

        self._log("Ready")

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

    def helpPressed(self) -> None:
        """
        Build 0008 -- opens HelpScreen with the Main Menu's own
        context-sensitive help document.
        """

        logger.verbose("[MainMenu] HELP pressed.")

        title, content = help_manager.getHelp("mainmenu")

        self.session.open(HelpScreen, title, content)

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
# "About" currently opens a simple MessageBox from the calling Screen
# (see mainscreen.py._showAbout()) rather than a dedicated AboutScreen,
# since ARCHITECTURE.md section 10 lists AboutScreen as a *future*
# screen, outside the scope of Build 0004.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

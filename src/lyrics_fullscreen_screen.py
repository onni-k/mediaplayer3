# ==============================================================================
#
# MediaPlayer3
#
# File        : lyrics_fullscreen_screen.py
#
# Description :
#
#     LyricsFullscreenScreen
#
#     Shows lyrics for the currently playing track at full screen
#     size, opened from MainScreen's Information panel (round 87).
#     OK, EXIT, LEFT and RIGHT close it and return to MainScreen.
#
# Implements :
#
#     Round 87 -- new Screen (originally a static, non-live display).
#     Round 93 -- per direct request, rebuilt to live-update exactly
#     like MainScreen's own windowed Information panel display
#     (lyrics_manager.py's getScrollWindowData(), a fixed "current"
#     row that's always bigger/bold for synchronized lyrics, UP/DOWN
#     now adjusts the lyrics' timing offset instead of closing the
#     screen -- "kuten ikkunoidussa tilassa").
#
# Architecture :
#
#     ARCHITECTURE.md
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
# 2026-09-01  Build 0010 (device test round 87)
#   - Initial version: a single static Label showing the full lyrics
#     text once, no live updates. All of OK/EXIT/UP/DOWN/LEFT/RIGHT
#     closed the screen.
#
# 2026-09-02  Build 0010 (device test round 93)
#   - Rebuilt around a live, periodically-refreshed multi-widget
#     display, mirroring MainScreen's own lyrics_line_N rows exactly
#     (same LYRICS_WINDOW_ROWS shape, same runtime gFont() switch for
#     unsynchronized lyrics, same reasoning -- see MainScreen's own
#     change history for round 93 for the full explanation; this
#     screen's own version is a separate, fullscreen-sized set of
#     rows rather than shared code, since the two screens' widget
#     names, scaling and skin are otherwise unrelated).
#   - Takes the shared InformationPanel instance directly (the same
#     one MainScreen itself owns and keeps refreshing on its own
#     1-second tick even while this screen sits on top of it) rather
#     than a pre-resolved block of text, so this screen always shows
#     the current live line -- getCurrentLyricsWindowData() is the
#     single source of truth, never recomputed here.
#   - UP/DOWN now call InformationPanel.scroll() (round 93, per direct
#     request: "Muutetaan kokoruudun tilassa että nuoli ylos/alas ei
#     palauta takaisin vaan muuttaa sanoitusten ajoitusta, kuten
#     ikkunoidussa tilassa") -- the exact same method the windowed
#     panel's own UP/DOWN already calls, which itself already knows to
#     route to the lyrics timing offset instead of ordinary scrolling
#     while a live lyrics page is active (information_panel.py's own
#     scroll() docstring). OK/EXIT/LEFT/RIGHT still close the screen.
#   - Falls back to the original round-87 static full-text display
#     (the "content" widget) whenever getCurrentLyricsWindowData()
#     returns None -- no live position available (e.g. lyrics exist
#     but playback has no elapsed-time feed at all).
#
# 2026-09-03  Build 0010 (device test round 94)
#   - Added a background image and a live title (see mainscreen.py's
#     own round 94 entry for the parallel work there) -- reused
#     MainMenu's own mainmenu_background.png directly.
#
# 2026-09-03  Build 0010 (device test round 95)
#   - Round 94's reused mainmenu_background.png didn't fit: its own
#     baked-in hamburger/play/exit icons and card boundaries are
#     specific to MainMenu's own layout and hints, causing real
#     overlap with this screen's own title/lyrics rows ("Sanoitusten
#     alue menee liian ylos ja peittää otsikkoalueen") and a bottom
#     edge that ran too low. Generated a dedicated
#     lyrics_fullscreen_background.png instead (via PIL, sampling this
#     project's own existing card/highlight-bar colours from
#     mainmenu_background.png so the new image stays in the same
#     visual style, but with card boundaries computed to match this
#     file's own actual title/lyrics-row/hint positions exactly, and
#     no icons at all -- the icons baked into every other reused
#     background image in this project are specific to whichever
#     screen they were drawn for and don't carry over to a screen with
#     different key hints).
# ------------------------------------------------------------------------------

"""
LyricsFullscreenScreen -- shows lyrics at full screen size, live.
"""

from __future__ import annotations

import os

from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from enigma import ePicLoad, eTimer, gFont

from .compatibility import compatibility
from .config import config_manager
from .localization import _
from .logger import logger
from .paths import SKIN_PATH
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)

# Round 94, per direct request ("samantyylinen taustakuva kuin
# mainmenussa"): first tried reusing MainMenu's own
# mainmenu_background.png directly. Round 95, per direct request:
# that image's own baked-in decorations (hamburger icon, play/exit
# icons) are specific to MainMenu's own hints and didn't match this
# screen's own layout or key hints -- its header/content card
# boundaries also didn't line up with this screen's own title/lyrics-
# row/hint positions, causing real overlap ("Sanoitusten alue menee
# liian ylös ja peittää otsikkoalueen"). Replaced with a dedicated
# lyrics_fullscreen_background.png (generated to match this file's
# own widget positions exactly -- see this comment's own round 95
# entry in the change history above for the generation approach), in
# the same rounded-card visual style but with no icons and boundaries
# that actually line up with title/lyrics rows/hint here.
LYRICS_FULLSCREEN_SKIN_VARIANTS = ("light", "dark")

LYRICS_FULLSCREEN_DEFAULT_SKIN_VARIANT = "light"


def _resolveLyricsFullscreenSkinVariant() -> str:

    variant = config_manager.get("appearance.skin", LYRICS_FULLSCREEN_DEFAULT_SKIN_VARIANT)

    if variant not in LYRICS_FULLSCREEN_SKIN_VARIANTS:
        return LYRICS_FULLSCREEN_DEFAULT_SKIN_VARIANT

    return variant


def _resolveLyricsFullscreenResolutionTier(screen_width: int) -> str:

    return "hd" if screen_width >= 1000 else "sd"


class LyricsFullscreenScreen(Screen):
    """
    Full-screen lyrics viewer -- live-updating, matching MainScreen's
    own windowed Information panel display, scaled up.
    """

    SPECIFICATION_VERSION = "0.2"

    DESIGN_WIDTH = 1920
    DESIGN_HEIGHT = 1080

    # Round 93 -- same shape as MainScreen's own LYRICS_WINDOW_ROWS
    # (height, font_size, bold) per row, just sized for a full 1080p
    # canvas instead of squeezed into MainScreen's smaller info panel
    # box. 10 normal rows (55) + 2 bigger prev/next rows (70) + 1
    # biggest/bold current row (90) = 780, comfortably inside the
    # ~900-unit content area below (leaves headroom, same reasoning as
    # MainScreen's own row sizing -- see that file's own round 93
    # comment for the HelpScreen round-81 lesson this follows).
    LYRICS_WINDOW_ROWS = (
        (55, 34, False),
        (55, 34, False),
        (55, 34, False),
        (55, 34, False),
        (55, 34, False),
        (70, 42, False),
        (90, 54, True),
        (70, 42, False),
        (55, 34, False),
        (55, 34, False),
        (55, 34, False),
        (55, 34, False),
        (55, 34, False),
    )

    REFRESH_INTERVAL_MS = 1000

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Fullscreen skin, matching MainScreen/PlaybackInfoScreen's own
        approach: position=0,0, scaled from a design canvas, theme
        background colour so the box's own video/background never
        shows through.
        """

        sx = width / LyricsFullscreenScreen.DESIGN_WIDTH

        sy = height / LyricsFullscreenScreen.DESIGN_HEIGHT

        self._screen_width = width

        self._screen_height = height

        self._skin_variant = _resolveLyricsFullscreenSkinVariant()

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))

        # Round 103, per direct request (dark theme showed a mismatch:
        # the background image already had its own correct dark
        # colours -- round 95's own generation sampled them
        # separately for light/dark -- but these text/box colours were
        # still the fixed light-theme values, unlike "title" above,
        # which already went theme-aware in round 97). Same dark
        # values MainScreen's own MAINSCREEN_SKIN_PALETTES["dark"]
        # already uses, so every window agrees on what "dark theme"
        # actually looks like.
        if self._skin_variant == "dark":

            panel_background_color = to_opaque_skin_color("#1C202B")

            panel_text_color = "#F0F0F0"

        else:

            panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)

            panel_text_color = PANEL_TEXT_COLOR

        # Round 97, per direct request: the title should read in the
        # same blue tones the windowed Information panel's own title
        # already uses (MainScreen's info_title_active, "header_active_
        # fg") rather than the plain panel_text_color every other
        # widget here uses -- same light/dark values, duplicated here
        # rather than imported since this screen doesn't otherwise
        # depend on MainScreen's own palette dict.
        title_foreground_color = "#036DFA" if self._skin_variant == "light" else "#FFFFFF"

        font_family = skin_manager.getFont("Regular")

        self._lyrics_font_family = font_family

        self._lyrics_font_scale = sx

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="{font_family};{max(10, int(size * sx))}"'

        lyrics_window_widgets = []

        lyrics_row_y = 110

        for row_index, (row_height, row_font_size, row_bold) in enumerate(self.LYRICS_WINDOW_ROWS):

            row_font_family = "Bold" if row_bold else font_family

            lyrics_window_widgets.append(
                f'<widget name="lyrics_line_{row_index}"\n'
                f'        {rect(40, lyrics_row_y, 1840, row_height)}\n'
                f'        font="{row_font_family};{max(10, int(row_font_size * sx))}"\n'
                f'        halign="center"\n'
                f'        valign="center"\n'
                f'        backgroundColor="{panel_background_color}"\n'
                f'        foregroundColor="{panel_text_color}"/>'
            )

            lyrics_row_y += row_height

        lyrics_window_xml = "\n\n            ".join(lyrics_window_widgets)

        return f"""
        <screen name="MediaPlayer3LyricsFullscreenScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Lyrics">

            <!-- Round 96, per direct request: same fix as MainMenu's
                 own round 95 title-hiding bug (missed applying it
                 here too at the time); zPosition explicitly and
                 permanently pins this widget behind everything else,
                 immune to Enigma2's own async setPixmap() restacking
                 a widget above others regardless of creation order. -->
            <widget name="background"
                    position="0,0"
                    size="{width},{height}"
                    zPosition="-1"
                    alphatest="blend"/>

            <widget name="title"
                    {rect(40, 30, 1840, 60)}
                    font="Bold;{max(10, int(36 * sx))}"
                    halign="center"
                    valign="center"
                    transparent="1"
                    foregroundColor="{title_foreground_color}"/>

            <widget name="content"
                    {rect(40, 110, 1840, 900)}
                    {font(28)}
                    halign="center"
                    valign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            {lyrics_window_xml}

            <widget name="hint"
                    {rect(40, 1025, 1840, 40)}
                    {font(18)}
                    halign="center"
                    valign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

        </screen>
        """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, session, title: str, static_text: str, information_panel):

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        self.session = session

        self._title = title or _("Lyrics")

        self._static_text = static_text or _("No lyrics available.")

        self._information_panel = information_panel

        self._refresh_timer = eTimer()

        self._background_picload = ePicLoad()

        compatibility.connectPictureDataSignal(self._background_picload, self._onBackgroundImageDecoded)

        self._pending_background_retry_timer = None

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[LyricsFullscreenScreen] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        # Background must be created first -- earlier self[name] =
        # ... insertion paints underneath, later insertion paints on
        # top (this project's own established widget paint-order
        # rule; see MainMenu/SettingsScreen's own background widgets
        # for the same convention).
        self["background"] = Pixmap()

        self["title"] = Label(self._title)

        self["content"] = Label(self._static_text)

        self["hint"] = Label(_("OK / EXIT / LEFT / RIGHT: Close -- UP / DOWN: Adjust timing"))

        for row_index in range(len(self.LYRICS_WINDOW_ROWS)):

            self[f"lyrics_line_{row_index}"] = Label("")

            self[f"lyrics_line_{row_index}"].hide()

        actions = {
            "ok": self.closePressed,
            "cancel": self.closePressed,
            "left": self.closePressed,
            "right": self.closePressed,
            "up": self.scrollUp,
            "down": self.scrollDown,
        }

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions"],
            actions,
            -1,
        )

        self._refresh_timer.callback.append(self._refresh)

        self._refresh_timer.start(self.REFRESH_INTERVAL_MS, False)

        self._decodeBackgroundImage()

        self._refresh()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Background image (round 94, per direct request -- reuses
    # MainMenu's own background image asset and decode pattern
    # exactly; see mainmenu.py's own _decodeBackgroundImage()/
    # _onBackgroundImageDecoded() for the full reasoning behind the
    # widget-not-ready-yet retry, not repeated here)
    # ------------------------------------------------------------------

    def _decodeBackgroundImage(self) -> None:

        if self["background"].instance is None:

            logger.verbose("[LyricsFullscreenScreen] background widget not ready yet, retrying decode shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(self._decodeBackgroundImage)

            retry_timer.start(100, True)

            self._pending_background_retry_timer = retry_timer

            return

        image_path = os.path.join(
            SKIN_PATH,
            self._skin_variant,
            _resolveLyricsFullscreenResolutionTier(self._screen_width),
            "lyrics_fullscreen_background.png",
        )

        try:
            width, height = self._screen_width, self._screen_height

            aspect = AVSwitch().getFramebufferScale()

            self._background_picload.setPara((width, height, aspect[0], aspect[1], False, 1, "#00000000"))

            if self._background_picload.startDecode(image_path) != 0:
                raise RuntimeError("startDecode() reported failure")

        except Exception as error:

            logger.verbose(f"[LyricsFullscreenScreen] Unable to decode background image {image_path}: {error}")

    # ------------------------------------------------------------------

    def _onBackgroundImageDecoded(self, picture_info=None) -> None:

        try:
            pixmap = self._background_picload.getData()

            if pixmap is None:
                return

            self["background"].instance.setPixmap(pixmap)

            self["background"].show()

        except Exception as error:

            logger.verbose(f"[LyricsFullscreenScreen] Background decode callback failed: {error}")

    # ------------------------------------------------------------------
    # Live update
    # ------------------------------------------------------------------

    def _refresh(self) -> None:

        # Round 94, per direct request -- same title (including the
        # lyrics offset suffix, e.g. "(+3.5s)") the windowed panel's
        # own getCurrentTitle() already shows, kept live here too
        # rather than the static title passed in at construction.
        self["title"].setText(self._information_panel.getCurrentTitle())

        lyrics_window = self._information_panel.getCurrentLyricsWindowData(len(self.LYRICS_WINDOW_ROWS))

        if lyrics_window is not None:

            self["content"].hide()

            self._showLyricsWindow(lyrics_window)

        else:

            self._hideLyricsWindow()

            self["content"].show()

    # ------------------------------------------------------------------

    def _showLyricsWindow(self, lyrics_window: dict) -> None:
        """
        Same algorithm as MainScreen's own _showLyricsWindow() (round
        93) -- see that method's own docstring for the full reasoning
        (padded, fixed-position window; runtime gFont() switch so
        unsynchronized lyrics never get the bigger/bold tiers).
        Duplicated rather than shared: the two screens' widget names,
        scaling and skin are otherwise unrelated, and the algorithm
        itself is short enough that sharing it would need its own
        small abstraction for little benefit.
        """

        lines = lyrics_window["lines"]

        synchronized = lyrics_window["synchronized"]

        _normal_height, normal_size, normal_bold = self.LYRICS_WINDOW_ROWS[0]

        for row_index, (_row_height, row_font_size, row_bold) in enumerate(self.LYRICS_WINDOW_ROWS):

            widget = self[f"lyrics_line_{row_index}"]

            widget.setText(lines[row_index] if row_index < len(lines) else "")

            effective_size, effective_bold = (row_font_size, row_bold) if synchronized else (normal_size, normal_bold)

            if widget.instance is not None:

                family = "Bold" if effective_bold else self._lyrics_font_family

                widget.instance.setFont(gFont(family, max(10, int(effective_size * self._lyrics_font_scale))))

            widget.show()

    # ------------------------------------------------------------------

    def _hideLyricsWindow(self) -> None:

        for row_index in range(len(self.LYRICS_WINDOW_ROWS)):

            self[f"lyrics_line_{row_index}"].hide()

    # ------------------------------------------------------------------
    # Remote control
    # ------------------------------------------------------------------

    def scrollUp(self) -> None:

        self._information_panel.scroll(-1)

    # ------------------------------------------------------------------

    def scrollDown(self) -> None:

        self._information_panel.scroll(1)

    # ------------------------------------------------------------------
    # Exit
    # ------------------------------------------------------------------

    def closePressed(self) -> None:

        logger.verbose("[LyricsFullscreenScreen] Close pressed.")

        try:
            self._refresh_timer.stop()

        except Exception as error:

            self._log(f"Error while stopping refresh timer: {error}")

        self._log("Closed")

        self.close(None)

# ==============================================================================
# End of file
# ==============================================================================

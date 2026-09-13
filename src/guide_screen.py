# ==============================================================================
#
# MediaPlayer3
#
# File        : guide_screen.py
#
# Description :
#
#     GuideScreen
#
#     Generic, scrollable plain-text document viewer used to display
#     the context-sensitive information content GuideManager.getGuide() loads
#     and renders. GuideScreen never reads help files itself or knows
#     which screen it was opened from -- it is handed a ready title +
#     rendered text and just displays it (HELP_SCREEN_SPEC.md
#     "GuideScreen shall not: Locate help files / Read documentation
#     directly from disk").
#
# Implements :
#
#     HELP_SCREEN_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md (Build 0008 -- new Screen)
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
# 2026-07-28  Build 0008
#   - Initial version.
#
# 2026-09-09  Build 0010 (device test round 139)
#   - Renamed from HelpScreen/help_screen.py (see guide_manager.py's
#     own round 139 comment for the full reasoning -- avoiding a name
#     collision with the unrelated, pre-existing InformationPanel).
#     Default title/fallback text changed from "Help"/"No help
#     available." to "Information"/"No information available."
# ------------------------------------------------------------------------------

from __future__ import annotations

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Label import Label
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen

from .compatibility import compatibility
from .localization import _
from .logger import logger
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)


class GuideScreen(Screen, HelpableScreen):
    """
    Generic scrollable document viewer for context-sensitive information.
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.3"

    # Number of text lines shown at once -- same conservative,
    # not-dynamically-measured estimate approach as DeveloperScreen's
    # own VISIBLE_LINES (Build 0006 device test round 2). Lowered
    # from 20 to 18 (round 81, per direct request): 20 lines' worth of
    # rendered text height was landing right at the edge of the
    # content box for this font/line-height, so the last line only
    # partially fit; 18 leaves enough headroom that every line is
    # always shown in full.
    VISIBLE_LINES = 18

    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 540

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build GuideScreen's skin for an exact `width` x `height`
        window, scaling from the 700x540 design resolution above --
        same fullscreen/white-panel pattern as every other screen
        since Build 0007 (device test rounds 8 and 12).
        """

        sx = width / GuideScreen.DESIGN_WIDTH
        sy = height / GuideScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3GuideScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Information">

            <widget name="title"
                    {rect(20, 10, 660, 30)}
                    {font(18)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="content"
                    {rect(20, 50, 660, 450)}
                    {font(16)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="hint"
                    {rect(20, 505, 660, 30)}
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

    def __init__(self, session, title: str = "", content: str = ""):
        """
        `title`/`content` are always supplied by the caller's own
        GuideManager.getGuide() call -- GuideScreen never loads help
        documents itself (HELP_SCREEN_SPEC.md).
        """

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        HelpableScreen.__init__(self)

        self.session = session

        self._title = title or _("Information")

        self._lines = (content or _("No information available.")).split("\n")

        # Device test round 81 -- a trailing blank buffer line, added
        # here rather than to each help document's own Markdown source
        # (GuideManager._collapseBlankLines() strips trailing blank
        # lines before this ever sees the content, so editing the
        # source files alone would have no effect). Guarantees the
        # last real line of any help text is never the very last line
        # rendered, so it's never the one a too-tight content box
        # would partially clip.
        self._lines.append("")

        self._scroll_offset = 0

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[GuideScreen] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["title"] = Label("")
        self["content"] = Label("")
        self["hint"] = Label(_("UP/DOWN: Scroll   LEFT/RIGHT: Page   HELP/EXIT: Close"))

        actions = {
            "cancel": self.closePressed,
            "up": self.scrollUp,
            "down": self.scrollDown,
            "left": self.pageUp,
            "right": self.pageDown,
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

            actions[action_name] = self.closePressed

        # PROVISIONAL context list -- HELP's real ActionMap context is
        # unverified on real hardware (Build 0008, no device testing
        # yet). "InfobarActions" is included since several other
        # auxiliary keys (INFO's plain form) resolved through it in
        # Build 0007; "HelpActions" is a guess at a dedicated context
        # name. Expect this to need correction from real device
        # eActionMap log evidence, the same way RADIO/CH+/CH-/INFO
        # did.
        contexts = ["OkCancelActions", "DirectionActions", "InfobarActions", "HelpActions"]

        help_text_by_handler = {
            self.closePressed: _("close this information screen"),
            self.scrollUp: _("scroll up"),
            self.scrollDown: _("scroll down"),
            self.pageUp: _("previous page"),
            self.pageDown: _("next page"),
        }

        # Round 131: see mainscreen.py's own round 130 comment for the
        # full reasoning behind this try/except.
        try:

            helpable_actions = {
                action_name: (handler, help_text_by_handler.get(handler, ""))
                for action_name, handler in actions.items()
            }

            self["actions"] = HelpableActionMap(self, contexts, helpable_actions, -1)

        except Exception as error:

            logger.warning(f"[GuideScreen] HelpableActionMap unavailable, falling back to plain ActionMap: {error}")

            self["actions"] = ActionMap(contexts, actions, -1)

        self._renderVisible()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Rendering (HELP_SCREEN_SPEC.md "Navigation")
    # ------------------------------------------------------------------

    def _renderVisible(self) -> None:

        total = len(self._lines)

        visible = self._lines[self._scroll_offset:self._scroll_offset + self.VISIBLE_LINES]

        title = self._title

        if total > self.VISIBLE_LINES:

            first = self._scroll_offset + 1

            last = min(self._scroll_offset + self.VISIBLE_LINES, total)

            title = f"{title}  ({first}-{last} / {total})"

        self["title"].setText(title)

        self["content"].setText("\n".join(visible))

    # ------------------------------------------------------------------

    def scrollUp(self) -> None:

        logger.verbose("[GuideScreen] UP pressed.")

        if self._scroll_offset <= 0:
            return

        self._scroll_offset = max(0, self._scroll_offset - 1)

        self._renderVisible()

    # ------------------------------------------------------------------

    def scrollDown(self) -> None:

        logger.verbose("[GuideScreen] DOWN pressed.")

        max_offset = max(0, len(self._lines) - self.VISIBLE_LINES)

        if self._scroll_offset >= max_offset:
            return

        self._scroll_offset = min(max_offset, self._scroll_offset + 1)

        self._renderVisible()

    # ------------------------------------------------------------------

    def pageUp(self) -> None:

        logger.verbose("[GuideScreen] LEFT pressed.")

        self._scroll_offset = max(0, self._scroll_offset - self.VISIBLE_LINES)

        self._renderVisible()

    # ------------------------------------------------------------------

    def pageDown(self) -> None:

        logger.verbose("[GuideScreen] RIGHT pressed.")

        max_offset = max(0, len(self._lines) - self.VISIBLE_LINES)

        self._scroll_offset = min(max_offset, self._scroll_offset + self.VISIBLE_LINES)

        self._renderVisible()

    # ------------------------------------------------------------------
    # Exit
    # ------------------------------------------------------------------

    def closePressed(self) -> None:

        logger.verbose("[GuideScreen] Close pressed.")

        self._log("Closed")

        self.close(None)

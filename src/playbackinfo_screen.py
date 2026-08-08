# ==============================================================================
#
# MediaPlayer3
#
# File        : playbackinfo_screen.py
#
# Description :
#
#     PlaybackInfoScreen
#
#     Displays detailed, read-only information about the currently
#     selected or currently playing media. Never controls playback.
#
# Implements :
#
#     PLAYBACKINFO_SPEC.md v0.1
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
# 2026-07-19  Build 0006
#   - Expanded to General/Technical/File sections using real tag
#     metadata (metadata.py, via PlaybackController.getMetadata()) and
#     stream info (via getStreamInfo()) instead of filename-only
#     placeholders (BUILD_0006_PLAN.md "Playback Information").
#     PlaybackInfoScreen still only displays -- it never reads files
#     or queries services itself.
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
# ------------------------------------------------------------------------------

from __future__ import annotations

import os

from Components.ActionMap import ActionMap
from Components.Label import Label
from Screens.Screen import Screen

from .compatibility import compatibility
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)


class PlaybackInfoScreen(Screen):
    """
    Read-only playback/metadata information display.
    """

    SPECIFICATION_VERSION = "0.6"
    ARCHITECTURE_VERSION = "0.3"

    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 560

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build PlaybackInfoScreen's skin for an exact `width` x
        `height` window, scaling from the 700x560 design resolution
        above (Build 0007, device test round 8).
        """

        sx = width / PlaybackInfoScreen.DESIGN_WIDTH
        sy = height / PlaybackInfoScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3PlaybackInfoScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Playback Information">

            <widget name="filename"
                    {rect(20, 20, 660, 30)}
                    {font(20)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="details"
                    {rect(20, 60, 660, 460)}
                    {font(16)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="hint"
                    {rect(20, 530, 660, 25)}
                    {font(14)}
                    halign="center"
                    valign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

        </screen>
        """

    UNKNOWN = "Unknown"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, session, playback_controller):

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        self.session = session

        self._playback = playback_controller

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[PlaybackInfoScreen] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["filename"] = Label("")
        self["details"] = Label("")
        self["hint"] = Label("INFO/EXIT: Close   MENU: Main Menu")

        actions = {
            "cancel": self.exitPressed,
            "menu": self.menuPressed,
        }

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.infoPressed

        self["actions"] = ActionMap(
            ["OkCancelActions", "InfoActions", "MenuActions", "InfobarEPGActions"],
            actions,
            -1,
        )

        self._log("Playback information requested.")

        self._refresh()

        self._initialized = True

        self._log("Ready")

# End of Part 1
    # ------------------------------------------------------------------
    # Display (PLAYBACKINFO_SPEC.md sections 4 and 8)
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        """
        Refresh displayed playback information from PlaybackController.

        Build 0006 -- General/Technical/File sections
        (BUILD_0006_PLAN.md "Playback Information"), using real tag
        metadata (metadata.py) and stream info (compatibility.py via
        ServiceController) where available. Missing metadata never
        prevents display -- every field falls back to "Unknown"
        (metadata.py's own default) rather than being left blank.
        """

        filename = self._playback.getCurrentFile()

        if not filename:

            self["filename"].setText(_("No media selected"))

            self["details"].setText("")

            return

        metadata = self._playback.getMetadata() or {}

        stream_info = self._playback.getStreamInfo()

        title = metadata.get("title", self.UNKNOWN)

        if title == self.UNKNOWN:
            title = os.path.basename(filename)

        self["filename"].setText(title)

        duration = self._playback.getDuration()

        file_size = metadata.get("file_size")

        lines = [
            "General",
            f"  Artist: {metadata.get('artist', self.UNKNOWN)}",
            f"  Album: {metadata.get('album', self.UNKNOWN)}",
            f"  Title: {title}",
            f"  Track Number: {metadata.get('track_number', self.UNKNOWN)}",
            f"  Genre: {metadata.get('genre', self.UNKNOWN)}",
            f"  Year: {metadata.get('year', self.UNKNOWN)}",
            "",
            "Technical",
            f"  Codec: {stream_info.get('codec', self.UNKNOWN)}",
            f"  Bitrate: {stream_info.get('bitrate', self.UNKNOWN)}",
            f"  Sample Rate: {stream_info.get('sample_rate', self.UNKNOWN)}",
            f"  Bit Depth: {metadata.get('bit_depth', self.UNKNOWN)}",
            f"  Channels: {stream_info.get('channels', self.UNKNOWN)}",
            f"  Duration: {duration if duration is not None else self.UNKNOWN}",
            f"  File Size: {self._formatFileSize(file_size)}",
            "",
            "File",
            f"  Full Path: {filename}",
            f"  File Name: {os.path.basename(filename)}",
            f"  Metadata Source: {metadata.get('source', 'None')}",
        ]

        self["details"].setText("\n".join(lines))

    # ------------------------------------------------------------------

    def _formatFileSize(self, size_bytes) -> str:

        if not size_bytes:
            return self.UNKNOWN

        for unit in ("B", "KB", "MB", "GB"):

            if size_bytes < 1024:
                return f"{size_bytes:.0f} {unit}" if unit == "B" else f"{size_bytes:.1f} {unit}"

            size_bytes /= 1024

        return f"{size_bytes:.1f} TB"

        logger.verbose("[PlaybackInfoScreen] Metadata loaded from filename fallback.")

    # ------------------------------------------------------------------
    # Event Handlers (PLAYBACKINFO_SPEC.md section 6)
    # ------------------------------------------------------------------

    def infoPressed(self) -> None:

        logger.verbose("[PlaybackInfoScreen] INFO pressed.")

        self._closeScreen()

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[PlaybackInfoScreen] EXIT pressed.")

        self._closeScreen()

    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[PlaybackInfoScreen] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "playback_info"):

            self._refresh()

            return

        self._log("Returning to MainScreen.")

        self._closeScreen(action_id)

    # ------------------------------------------------------------------

    def _closeScreen(self, result=None) -> None:

        self._log("Closing")

        self._log("Closed")

        self.close(result)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"PlaybackInfoScreen(initialized={self._initialized})"


# ==============================================================================
#
# Build Notes
#
# PlaybackInfoScreen never controls playback and never accesses
# ServiceController, Compatibility or Enigma2 playback services
# directly -- it only reads from the shared PlaybackController
# instance passed in by MainScreen.
#
# A dedicated metadata provider (ID3 tags etc.) is reserved for a
# future build, per PLAYBACKINFO_SPEC.md section 10.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

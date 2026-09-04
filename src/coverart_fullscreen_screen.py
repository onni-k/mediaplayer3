# ==============================================================================
#
# MediaPlayer3
#
# File        : coverart_fullscreen_screen.py
#
# Description :
#
#     CoverArtFullscreenScreen
#
#     Shows the currently playing track's cover art at full screen
#     size, opened from MainScreen's Information panel (round 87, per
#     direct request). OK, EXIT and every arrow key all close it and
#     return to MainScreen (per direct request: "Paluu molemmissa
#     ok- exit- tai nuolinapeilla"). MainScreen resolves and hands
#     over the artwork's file path already -- this screen only
#     decodes and displays it (same ePicLoad pattern MainScreen's own
#     "cover" widget uses, at a bigger size), it never resolves
#     artwork itself.
#
# Implements :
#
#     Round 87 -- new Screen.
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
#   - Initial version. Decode-on-layout-ready pattern (retry via a
#     short one-shot eTimer if the widget's own `instance` isn't ready
#     yet) copied directly from MainScreen's own _decodeCoverArt() --
#     that exact race (and the eTimer-retry fix for it) was already
#     found and confirmed on real hardware there (Build 0009, device
#     test rounds 5-6), so reusing it here rather than risking the
#     same bug fresh in a new screen.
# ------------------------------------------------------------------------------

"""
CoverArtFullscreenScreen -- shows the cover art at full screen size.
"""

from __future__ import annotations

from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from enigma import ePicLoad, eTimer
from Components.AVSwitch import AVSwitch

from .compatibility import compatibility
from .localization import _
from .logger import logger
from .skin import to_opaque_skin_color


class CoverArtFullscreenScreen(Screen):
    """
    Full-screen cover art viewer.
    """

    SPECIFICATION_VERSION = "0.1"

    DESIGN_WIDTH = 1920
    DESIGN_HEIGHT = 1080

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:

        background_color = to_opaque_skin_color("#00000000")

        return f"""
        <screen name="MediaPlayer3CoverArtFullscreenScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Cover Art">

            <widget name="cover"
                    position="0,0"
                    size="{width},{height}"
                    zPosition="1"/>

        </screen>
        """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, session, artwork_path: str):

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        self.session = session

        self._artwork_path = artwork_path

        self._picload = ePicLoad()

        compatibility.connectPictureDataSignal(self._picload, self._onArtworkDecoded)

        self._pending_retry_timer = None

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[CoverArtFullscreenScreen] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["cover"] = Pixmap()

        actions = {
            "ok": self.closePressed,
            "cancel": self.closePressed,
            "up": self.closePressed,
            "down": self.closePressed,
            "left": self.closePressed,
            "right": self.closePressed,
        }

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions"],
            actions,
            -1,
        )

        self._decodeArtwork()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _decodeArtwork(self) -> None:
        """
        Same decode-on-layout-ready pattern as MainScreen's own
        _decodeCoverArt() -- see this file's own round 87 change
        history entry for why.
        """

        if self["cover"].instance is None:

            logger.verbose("[CoverArtFullscreenScreen] Cover widget not ready yet, retrying decode shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(self._decodeArtwork)

            retry_timer.start(100, True)

            self._pending_retry_timer = retry_timer

            return

        try:
            widget_size = self["cover"].instance.size()

            width, height = widget_size.width(), widget_size.height()

            aspect = AVSwitch().getFramebufferScale()

            self._picload.setPara((width, height, aspect[0], aspect[1], False, 1, "#00000000"))

            if self._picload.startDecode(self._artwork_path) != 0:
                raise RuntimeError("startDecode() reported failure")

        except Exception as error:

            logger.verbose(f"[CoverArtFullscreenScreen] Unable to decode {self._artwork_path}: {error}")

            self["cover"].hide()

    # ------------------------------------------------------------------

    def _onArtworkDecoded(self, picture_info=None) -> None:

        try:
            pixmap = self._picload.getData()

            if pixmap is None:

                self["cover"].hide()

                return

            self["cover"].instance.setPixmap(pixmap)

            self["cover"].show()

            self._log(f"Cover art loaded: {self._artwork_path}")

        except Exception as error:

            logger.verbose(f"[CoverArtFullscreenScreen] Decode callback failed: {error}")

            self["cover"].hide()

    # ------------------------------------------------------------------
    # Exit
    # ------------------------------------------------------------------

    def closePressed(self) -> None:

        logger.verbose("[CoverArtFullscreenScreen] Close pressed.")

        self._log("Closed")

        self.close(None)

# ==============================================================================
# End of file
# ==============================================================================

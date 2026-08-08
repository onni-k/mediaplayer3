# ==============================================================================
#
# MediaPlayer3
#
# File        : developer_screen.py
#
# Description :
#
#     DeveloperScreen
#
#     Diagnostic and development tools: Runtime Status, Logger, System
#     Information, Compatibility and Build Information pages. Never
#     modifies playback unless explicitly requested (Export log is the
#     only write operation, and it only writes a diagnostic file).
#
# Implements :
#
#     DEVELOPER_SCREEN_SPEC.md v0.1
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
#   - Runtime Status page extended with Playback Statistics: queue
#     position/size, remaining time, codec, sample rate, bitrate,
#     channels (BUILD_0005_PLAN.md "Playback Statistics"). Stream
#     info comes from PlaybackController.getStreamInfo() -> ...->
#     compatibility.py; DeveloperScreen still never talks to
#     ServiceController or compatibility.py directly.
#
# 2026-07-19  Build 0006
#   - Added "Metadata & Artwork" page (all metadata.FIELDS plus bit
#     depth/file size/embedded artwork info, read from
#     PlaybackController.getMetadata()/getEmbeddedArtwork()) and
#     "Localization" page (LocalizationManager.getTranslationStats()).
#   - "Compatibility" page extended with Skin/Theme info
#     (SkinManager.getCompatibilityReport()).
#
# 2026-07-19  Build 0006 (device test round 2)
#   - Added UP/DOWN manual scrolling: a real device screenshot showed
#     System Information cut off vertically with no way to see the
#     rest. Pages longer than VISIBLE_LINES now show a
#     "(first-last / total)" indicator in the page title.
#
# 2026-07-19  Build 0007
#   - Added "Storage", "Playlists" and "Internet Radio" diagnostic
#     pages (StorageManager.getDiagnostics() /
#     PlaylistManager.getDiagnostics() /
#     InternetRadioManager.getDiagnostics()).
#
# 2026-07-24  Build 0007 (device test round 5)
#   - Added INFO handling: DeveloperScreen previously had no
#     "InfoActions" context at all, showing Enigma2's "unhandled key"
#     indicator (same audit that found PlaylistScreen/SettingsScreen
#     missing it, confirmed on OpenATV).
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
from datetime import datetime

from Components.ActionMap import ActionMap
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from . import metadata as md
from .compatibility import compatibility
from .help_manager import help_manager
from .help_screen import HelpScreen
from .config import config_manager
from .internetradio_manager import internetradio_manager
from .localization import localization_manager
from .logger import logger
from .mainmenu import MainMenu
from .paths import LOG_PATH
from .playlist_manager import playlist_manager
from .project import (
    APPLICATION_ID,
    AUTHOR,
    COPYRIGHT,
    LICENSE,
    PROJECT_NAME,
)
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)
from .storage import storage_manager
from .systeminfo import systeminfo
from .version import get_build, get_version, get_version_string


class DeveloperScreen(Screen):
    """
    Developer diagnostics and tools.
    """

    SPECIFICATION_VERSION = "0.7"
    ARCHITECTURE_VERSION = "0.3"

    PAGES = (
        "runtime", "metadata", "localization", "storage", "playlist", "radio",
        "logger", "systeminfo", "compatibility", "build",
    )

    # Build 0006 (device test round 2) -- number of text lines shown
    # at once in the "details" widget; UP/DOWN scroll pages longer
    # than this. Sized for the current 640x450 skin's details area at
    # its default font size; not dynamically measured (Enigma2 has no
    # simple "how many lines fit" query), so this is a conservative
    # estimate, not an exact fit.
    VISIBLE_LINES = 14

    PAGE_TITLES = {
        "runtime": "Runtime Status",
        "metadata": "Metadata & Artwork",
        "localization": "Localization",
        "storage": "Storage",
        "playlist": "Playlists",
        "radio": "Internet Radio",
        "logger": "Logger",
        "systeminfo": "System Information",
        "compatibility": "Compatibility",
        "build": "Build Information",
    }

    DESIGN_WIDTH = 640
    DESIGN_HEIGHT = 450

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build DeveloperScreen's skin for an exact `width` x `height`
        window, scaling from the 640x450 design resolution above
        (Build 0007, device test round 8).
        """

        sx = width / DeveloperScreen.DESIGN_WIDTH
        sy = height / DeveloperScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3DeveloperScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Developer Tools">

            <widget name="page_title"
                    {rect(20, 10, 600, 30)}
                    {font(20)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="details"
                    {rect(20, 50, 600, 330)}
                    {font(16)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="hint"
                    {rect(20, 400, 600, 40)}
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

    def __init__(self, session, playback_controller=None):

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        self.session = session

        self._playback = playback_controller

        self._page_index = 0

        # Build 0006 (device test round 2) -- manual scroll state for
        # pages whose content doesn't fit in the details widget (a
        # real device screenshot showed System Information cut off
        # vertically with no way to see the rest).
        self._page_lines = []
        self._scroll_offset = 0

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[DeveloperScreen] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._log("Collecting runtime information.")

        self._log("Collecting system information.")

        self._log("Initializing developer pages.")

        self["page_title"] = Label("")
        self["details"] = Label("")
        self["hint"] = Label(
            "LEFT/RIGHT: Page   UP/DOWN: Scroll   RED: Export log   MENU: Menu   EXIT: Back"
        )

        actions = {
            "cancel": self.exitPressed,
            "left": self.previousPage,
            "right": self.nextPage,
            "up": self.scrollUp,
            "down": self.scrollDown,
            "red": self.exportLog,
            "menu": self.menuPressed,
        }

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.infoPressed

        for action_name in compatibility.getHelpKeyActionNames():
            actions[action_name] = self.helpPressed

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions", "MenuActions", "InfoActions", "InfobarEPGActions", "HelpActions"],
            actions,
            -1,
        )

        self._showPage()

        self._initialized = True

        self._log("Ready")

# End of Part 1
    # ------------------------------------------------------------------
    # Page Navigation
    # ------------------------------------------------------------------

    def previousPage(self) -> None:

        logger.verbose("[DeveloperScreen] LEFT pressed.")

        self._page_index = (self._page_index - 1) % len(self.PAGES)

        self._showPage()

    # ------------------------------------------------------------------

    def nextPage(self) -> None:

        logger.verbose("[DeveloperScreen] RIGHT pressed.")

        self._page_index = (self._page_index + 1) % len(self.PAGES)

        self._showPage()

    # ------------------------------------------------------------------

    def _showPage(self) -> None:

        page = self.PAGES[self._page_index]

        self._log(f"Opening {self.PAGE_TITLES[page]}.")

        handler = getattr(self, f"_page_{page}")

        self._page_lines = handler().split("\n")

        self._scroll_offset = 0

        self._renderVisiblePage(page)

    # ------------------------------------------------------------------

    def _renderVisiblePage(self, page=None) -> None:
        """
        Render the current scroll window of `self._page_lines` into
        the "details" widget, with a "(showing X-Y of N)" indicator in
        the page title when the page doesn't fully fit
        (VISIBLE_LINES) -- added after a real device screenshot showed
        System Information cut off vertically with no way to see the
        rest.
        """

        if page is None:
            page = self.PAGES[self._page_index]

        total = len(self._page_lines)

        visible = self._page_lines[self._scroll_offset:self._scroll_offset + self.VISIBLE_LINES]

        title = self.PAGE_TITLES[page]

        if total > self.VISIBLE_LINES:

            first = self._scroll_offset + 1

            last = min(self._scroll_offset + self.VISIBLE_LINES, total)

            title = f"{title}  ({first}-{last} / {total})"

        self["page_title"].setText(title)

        self["details"].setText("\n".join(visible))

    # ------------------------------------------------------------------

    def scrollUp(self) -> None:

        logger.verbose("[DeveloperScreen] UP pressed.")

        if self._scroll_offset <= 0:
            return

        self._scroll_offset = max(0, self._scroll_offset - 1)

        self._renderVisiblePage()

    # ------------------------------------------------------------------

    def scrollDown(self) -> None:

        logger.verbose("[DeveloperScreen] DOWN pressed.")

        max_offset = max(0, len(self._page_lines) - self.VISIBLE_LINES)

        if self._scroll_offset >= max_offset:
            return

        self._scroll_offset = min(max_offset, self._scroll_offset + 1)

        self._renderVisiblePage()

    # ------------------------------------------------------------------
    # Pages (DEVELOPER_SCREEN_SPEC.md sections 5-9)
    # ------------------------------------------------------------------

    def _page_runtime(self) -> str:

        if self._playback is not None:

            current_file = self._playback.getCurrentFile() or "None"
            state = self._playback.getState()
            elapsed = self._playback.getElapsedTime()
            duration = self._playback.getDuration()
            queue_size = self._playback.getQueueSize()
            queue_position = self._playback.getQueuePosition()
            stream_info = self._playback.getStreamInfo()

        else:

            current_file = "Unknown"
            state = "Unknown"
            elapsed = None
            duration = None
            queue_size = 0
            queue_position = 0
            stream_info = {
                "codec": "Unknown",
                "sample_rate": "Unknown",
                "bitrate": "Unknown",
                "channels": "Unknown",
            }

        if elapsed is not None and duration is not None:
            remaining = max(0, duration - elapsed)
        else:
            remaining = None

        lines = [
            f"Current media: {current_file}",
            f"Playback state: {state}",
            f"Queue position: {queue_position if queue_size else 'Unknown'}",
            f"Queue size: {queue_size}",
            f"Elapsed: {elapsed if elapsed is not None else 'Unknown'}",
            f"Remaining: {remaining if remaining is not None else 'Unknown'}",
            f"Duration: {duration if duration is not None else 'Unknown'}",
            f"Codec: {stream_info['codec']}",
            f"Sample rate: {stream_info['sample_rate']}",
            f"Bitrate: {stream_info['bitrate']}",
            f"Channels: {stream_info['channels']}",
            f"Current screen: DeveloperScreen",
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_metadata(self) -> str:
        """
        Build 0006 -- Metadata & Artwork diagnostics
        (BUILD_0006_PLAN.md "Developer Improvements": "Metadata
        diagnostics", "Artwork diagnostics").
        """

        if self._playback is None:

            return "No metadata available (no PlaybackController)."

        metadata = self._playback.getMetadata()

        if metadata is None:

            return "No metadata loaded (no media played yet)."

        lines = [f"Metadata source: {metadata.get('source', 'None')}"]

        for field in md.FIELDS:

            lines.append(f"{field}: {metadata.get(field, 'Unknown')}")

        lines.append(f"Bit depth: {metadata.get('bit_depth', 'Unknown')}")
        lines.append(f"File size: {metadata.get('file_size', 'Unknown')}")

        lines.append("")
        lines.append("Artwork:")

        embedded = self._playback.getEmbeddedArtwork()

        if embedded is not None:

            mime_type, image_bytes = embedded

            lines.append(f"  Embedded artwork: {mime_type}, {len(image_bytes)} bytes")

        else:

            lines.append("  Embedded artwork: None")

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_localization(self) -> str:
        """
        Build 0006 -- Translation diagnostics
        (BUILD_0006_PLAN.md "Developer Improvements": "Translation
        diagnostics").
        """

        stats = localization_manager.getTranslationStats()

        lines = [f"{key}: {value}" for key, value in stats.items()]

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_storage(self) -> str:
        """
        Build 0007 -- Storage diagnostics (STORAGE_MANAGER_SPEC.md).
        """

        report = storage_manager.getDiagnostics()

        lines = [f"{key}: {value}" for key, value in report.items()]

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_playlist(self) -> str:
        """
        Build 0007 -- Playlist statistics
        (PLAYLIST_MANAGER_SPEC.md "Logging" -- "Playlist statistics").
        """

        report = playlist_manager.getDiagnostics()

        lines = [f"{key}: {value}" for key, value in report.items()]

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_radio(self) -> str:
        """
        Build 0007 -- Internet Radio diagnostics
        (INTERNETRADIO_MANAGER_SPEC.md "Logging").
        """

        report = internetradio_manager.getDiagnostics()

        lines = [f"{key}: {value}" for key, value in report.items()]

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_logger(self) -> str:

        lines = [
            f"Developer Mode: {'On' if config_manager.isDeveloperMode() else 'Off'}",
            f"Developer log level: {config_manager.getDeveloperLogLevel()}",
            f"Debug logging: {'On' if config_manager.get('logging.debug_logging', False) else 'Off'}",
            f"Log directory: {LOG_PATH}",
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_systeminfo(self) -> str:

        info = systeminfo.getSummary()

        lines = []

        for section, values in info.items():

            lines.append(f"{section}:")

            if isinstance(values, dict):

                for key, value in values.items():

                    lines.append(f"    {key}: {value}")

            else:

                lines.append(f"    {values}")

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_compatibility(self) -> str:

        report = compatibility.getCompatibilityReport()

        lines = [f"{key}: {value}" for key, value in report.items()]

        lines.append("")
        lines.append("Skin & Theme:")

        skin_report = skin_manager.getCompatibilityReport()

        for key, value in skin_report.items():

            lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _page_build(self) -> str:

        lines = [
            f"Application: {PROJECT_NAME}",
            f"Application ID: {APPLICATION_ID}",
            f"Version: {get_version()}",
            f"Build: {get_build()}",
            f"Architecture: {self.ARCHITECTURE_VERSION}",
            f"Author: {AUTHOR}",
            f"{COPYRIGHT}",
            f"License: {LICENSE}",
        ]

        return "\n".join(lines)

# End of Part 2
    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def infoPressed(self) -> None:
        """
        Build 0007, device test round 5 -- DeveloperScreen previously
        had no INFO handling at all, showing Enigma2's "unhandled
        key" indicator (same audit that found PlaylistScreen/
        SettingsScreen missing it, confirmed on OpenATV). Restates
        which page is currently shown -- DeveloperScreen's page
        content is already comprehensive, so INFO has nothing more
        useful to add beyond confirming the current page.
        """

        logger.verbose("[Developer] INFO pressed.")

        page = self.PAGES[self._page_index]

        self.session.open(MessageBox, self.PAGE_TITLES.get(page, page), MessageBox.TYPE_INFO)

    # ------------------------------------------------------------------

    def helpPressed(self) -> None:
        """
        Build 0008 -- opens HelpScreen with DeveloperScreen's own
        context-sensitive help document.
        """

        logger.verbose("[Developer] HELP pressed.")

        title, content = help_manager.getHelp("developerscreen")

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------

    def exportLog(self) -> None:
        """
        Export a diagnostic snapshot to LOG_PATH
        (DEVELOPER_SCREEN_SPEC.md section 6).
        """

        logger.verbose("[DeveloperScreen] RED pressed.")

        self._log("Exporting log.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        export_path = os.path.join(LOG_PATH, f"MediaPlayer3_diagnostics_{timestamp}.txt")

        try:

            with open(export_path, "w", encoding="utf-8") as handle:

                handle.write(get_version_string() + "\n\n")

                for page in self.PAGES:

                    handle.write(f"== {self.PAGE_TITLES[page]} ==\n")

                    handle.write(getattr(self, f"_page_{page}")())

                    handle.write("\n\n")

            self._log(f"Log exported: {export_path}")

        except Exception as error:

            self._log(f"Unable to export log: {error}")

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[DeveloperScreen] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "developer"):

            self._showPage()

            return

        self._log("Returning to MainScreen.")

        self._close(action_id)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[DeveloperScreen] EXIT pressed.")

        self._log("Returning to MainScreen.")

        self._close(None)

    # ------------------------------------------------------------------

    def _close(self, result=None) -> None:
        """
        Standard lifecycle close: logs Closing/Closed and returns to
        MainScreen with `result`.
        """

        self._log("Closing")

        self._log("Closed")

        self.close(result)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"DeveloperScreen(initialized={self._initialized})"


# ==============================================================================
#
# Build Notes
#
# DeveloperScreen reads from PlaybackController, Logger/ConfigurationManager,
# SystemInfo and Compatibility only through their public interfaces. It
# never talks to ServiceController, NavigationInstance or Enigma2
# playback services directly, per DEVELOPER_SCREEN_SPEC.md section 10.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

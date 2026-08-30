# ==============================================================================
#
# MediaPlayer3
#
# File        : podcastscreen.py
#
# Description :
#
#     PodcastScreen
#
#     Podcast discovery, subscription management and episode
#     browsing/playback (PODCAST_SCREEN_SPEC.md). Three navigable
#     columns: Available Podcasts | Subscribed Podcasts | Episodes.
#
#     Structurally mirrors RadioBrowserScreen closely (same
#     LEFT/RIGHT column-focus model, ChoiceBox action menus,
#     VirtualKeyBoard search, PAGE_STEP for CHANNEL UP/DOWN) --
#     RadioBrowserScreen is explicitly the reference model
#     BUILD_0010_PLAN.md names for this screen's three-column
#     browsing. Column-header highlighting reuses MainScreen's own
#     confirmed-safe pattern from Build 0009 (two overlapping
#     background-colour rectangles per header, toggled with
#     hide()/show(), never a runtime widget recolour) -- extended
#     here with a second colour tier for inactive headers
#     (BUILD_0010_PLAN.md "Visual Refinement": "Inactive header rows
#     shall use a light blue background", "Active header row shall
#     continue to use the existing blue highlight").
#
#     PodcastScreen does not implement podcast business logic (that's
#     podcast_manager.py) and does not talk to the Podcast Index API
#     directly (that's podcast_providers/podcastindex/) --
#     PODCAST_SCREEN_SPEC.md "Purpose".
#
# Implements :
#
#     PODCAST_SCREEN_SPEC.md
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
# 2026-08-09  Build 0010 (round 3)
#   - Initial version. Structure and interaction model confirmed via
#     stub-environment testing; not yet exercised on real hardware
#     (no device test round yet for Build 0010).
# ------------------------------------------------------------------------------

"""
podcastscreen -- three-column podcast browser (Available Podcasts |
Subscribed Podcasts | Episodes), per PODCAST_SCREEN_SPEC.md.
"""

from __future__ import annotations

import os

from enigma import ePicLoad, eTimer

from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from .compatibility import compatibility
from .config import config_manager
from .ffprobe_helper import isAvailable as ffprobe_available, probe as ffprobe_probe
from .help_manager import help_manager
from .help_screen import HelpScreen
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .paths import SKIN_PATH
from .playlist_manager import playlist_manager
from .podcast_manager import podcast_manager
from .skin import to_opaque_skin_color

COLUMNS = ("available", "subscribed", "episodes")

# Device test round 56 -- background-image variant/tier system, a
# copy of MusicLibraryScreen's own (round 39/46), matching the same
# "reuse Music Library's images and colours" pattern already used for
# RadioBrowserScreen (round 54) and BrowserScreen (round 55).
PODCAST_SKIN_VARIANTS = ("light", "dark")

PODCAST_DEFAULT_SKIN_VARIANT = "light"

PODCAST_SKIN_PALETTES = {
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


def _resolvePodcastSkinVariant() -> str:

    variant = config_manager.get("appearance.skin", PODCAST_DEFAULT_SKIN_VARIANT)

    if variant not in PODCAST_SKIN_VARIANTS:
        return PODCAST_DEFAULT_SKIN_VARIANT

    return variant


def _resolvePodcastResolutionTier(screen_width: int) -> str:

    return "hd" if screen_width >= 1000 else "sd"


# CHANNEL UP/DOWN page-step, matching RadioBrowserScreen's own
# PAGE_STEP convention for long lists.
PAGE_STEP = 10

# Device test round 29 -- matches RadioBrowserScreen's own
# CODEC_LOG_DEBOUNCE_MS exactly (same reasoning: long enough that
# scrolling through episodes doesn't fire a probe per episode passed
# through, short enough to still feel responsive once the user stops).
EPISODE_CODEC_DEBOUNCE_MS = 700

# How long a codec-check failure warning stays in the "status" line
# before reverting to whatever it would normally show.
EPISODE_CODEC_WARNING_MS = 4000


def _formatDuration(seconds) -> str:
    """
    Format an episode duration (seconds, possibly None/non-numeric --
    Podcast Index doesn't guarantee this field) as "H:MM:SS" or
    "M:SS". Returns "" for anything unusable rather than raising.
    """

    try:
        total_seconds = int(seconds)

    except (TypeError, ValueError):

        return ""

    if total_seconds <= 0:
        return ""

    hours, remainder = divmod(total_seconds, 3600)

    minutes, secs = divmod(remainder, 60)

    if hours:

        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


def _formatPublished(timestamp) -> str:
    """
    Format an episode's publication date (Podcast Index gives a Unix
    timestamp) as "YYYY-MM-DD". Returns "" for anything unusable.
    """

    try:
        from datetime import datetime

        return datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d")

    except (TypeError, ValueError, OSError, OverflowError):

        return ""


class PodcastScreen(Screen):
    """
    Podcast discovery, subscriptions and episode browsing
    (PODCAST_SCREEN_SPEC.md).
    """

    SPECIFICATION_VERSION = "0.1"

    # Device test round 56 -- changed from 700x540 to 1672x941,
    # matching MusicLibraryScreen's own round 39 reasoning.
    DESIGN_WIDTH = 1672
    DESIGN_HEIGHT = 941

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Device test round 56 -- reuses MusicLibraryScreen's own
        background-image approach exactly (per direct request: same
        pattern already used for RadioBrowserScreen/BrowserScreen).
        Icons: available->headphones, subscribed->checkmark,
        episodes->microphone, cropped from the user's own Podcasts
        mockup. New "info" widget shows the currently selected
        podcast's or episode's own description (falls back to a
        "press INFO to search" hint when nothing is available), per
        direct request -- this screen never had a description display
        before.
        """

        sx = width / PodcastScreen.DESIGN_WIDTH
        sy = height / PodcastScreen.DESIGN_HEIGHT

        self._screen_width = width

        self._screen_height = height

        self._skin_variant = _resolvePodcastSkinVariant()

        palette = PODCAST_SKIN_PALETTES[self._skin_variant]

        panel_background_color = to_opaque_skin_color(palette["panel_background_color"])
        panel_text_color = palette["panel_text_color"]

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Bold;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3PodcastScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{panel_background_color}"
                title="MediaPlayer3 - Podcasts">

            <widget name="background"
                    position="0,0"
                    size="{width},{height}"
                    alphatest="blend"/>

            <widget name="status"
                    {rect(60, 19, 1550, 55)}
                    {font(34)}
                    halign="center"
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="warning"
                    {rect(60, 19, 1550, 55)}
                    {font(28)}
                    halign="center"
                    valign="center"
                    backgroundColor="#B00000"
                    foregroundColor="#FFFFFF"/>

            <widget name="available_title_normal"
                    {rect(135, 80, 383, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="available_title_active"
                    {rect(135, 80, 383, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="subscribed_title_normal"
                    {rect(652, 80, 422, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="subscribed_title_active"
                    {rect(652, 80, 422, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="episodes_title_normal"
                    {rect(1207, 80, 403, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="episodes_title_active"
                    {rect(1207, 80, 403, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="available_list"
                    {rect(40, 138, 498, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="#E0E0E0"
                    scrollbarMode="showOnDemand"/>

            <widget name="subscribed_list"
                    {rect(557, 138, 537, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="#E0E0E0"
                    scrollbarMode="showOnDemand"/>

            <widget name="episodes_list"
                    {rect(1112, 138, 518, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="#E0E0E0"
                    scrollbarMode="showOnDemand"/>

            <widget name="info"
                    {rect(60, 702, 1550, 130)}
                    {font(22)}
                    foregroundColor="{panel_text_color}"
                    backgroundColor="{panel_background_color}"/>

            <widget name="hint_text_leftright"
                    {rect(74, 874, 249, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_updown"
                    {rect(339, 874, 200, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_ok"
                    {rect(589, 874, 159, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_info"
                    {rect(798, 874, 141, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_help"
                    {rect(989, 874, 128, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_menu"
                    {rect(1167, 874, 163, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_exit"
                    {rect(1380, 874, 155, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
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

        self.session = session

        self._playback = playback_controller

        self._focus = "available"

        self._search_query = ""

        self._available_podcasts = []

        self._subscribed_podcasts = []

        self._episodes = []

        # Build 0010 -- the podcast whose episodes are currently
        # loaded into the Episodes column, and which column it came
        # from -- PODCAST_SCREEN_SPEC.md "The selected podcast remains
        # the current podcast while the user moves between columns."
        self._current_podcast_id = None

        self._current_podcast_title = ""

        # Device test round 29 -- same debounced ffprobe check
        # RadioBrowserScreen already has (CODEC_LOG_DEBOUNCE_MS there),
        # per direct request ("Sama voisi olla myos podcastien jaksoja
        # selatessa"). No dedicated info-panel widget exists here the
        # way RadioBrowserScreen has one, so this screen only logs and
        # shows a failure warning via the existing "status" line
        # (auto-reverting) -- see _checkSelectedEpisodeCodec()'s own
        # docstring for the fuller reasoning.
        self._episode_codec_timer = eTimer()

        self._episode_codec_timer.callback.append(self._checkSelectedEpisodeCodec)

        self._episode_codec_revert_timer = eTimer()

        self._episode_codec_revert_timer.callback.append(self._hideEpisodeWarning)

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Podcast] %s", message)

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
        self["warning"] = Label("")
        self["warning"].hide()

        for column_name in COLUMNS:

            self[f"{column_name}_title_normal"] = Label("")
            self[f"{column_name}_title_active"] = Label("")
            self[f"{column_name}_title_active"].hide()
            self[f"{column_name}_list"] = MenuList([])

        # Device test round 56 -- new: shows the currently selected
        # podcast's or episode's own description (falls back to a
        # "press INFO to search" hint), per direct request. Didn't
        # exist before this round.
        self["info"] = Label("")

        self["hint_text_leftright"] = Label(_("LEFT/RIGHT: Column"))
        self["hint_text_updown"] = Label(_("UP/DOWN: Move"))
        self["hint_text_ok"] = Label(_("OK: Actions"))
        self["hint_text_info"] = Label(_("INFO: Search"))
        self["hint_text_help"] = Label(_("HELP: Help"))
        self["hint_text_menu"] = Label(_("MENU: Menu"))
        self["hint_text_exit"] = Label(_("EXIT: Back"))

        self._subscribed_podcasts = podcast_manager.getSubscriptions()

        actions = {
            "ok": self.okPressed,
            "cancel": self.exitPressed,
            "left": self.focusPrevious,
            "right": self.focusNext,
            "up": self.moveUp,
            "down": self.moveDown,
            "menu": self.menuPressed,
        }

        for action_name in compatibility.getChannelUpKeyActionNames():
            actions[action_name] = self.pageUp

        for action_name in compatibility.getChannelDownKeyActionNames():
            actions[action_name] = self.pageDown

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.searchPressed

        for action_name in compatibility.getHelpKeyActionNames():
            actions[action_name] = self.helpPressed

        self["actions"] = ActionMap(
            [
                "OkCancelActions",
                "DirectionActions",
                "MenuActions",
                "InfoActions",
                "InfobarActions",
                "InfobarBouquetActions",
                "InfobarEPGActions",
                "HelpActions",
            ],
            actions,
            -1,
        )

        self._updateDisplay()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _updateDisplay(self) -> None:

        self["available_list"].setList(
            [podcast.get("title", "?") for podcast in self._available_podcasts]
        )

        self["subscribed_list"].setList(
            [podcast.get("title", "?") for podcast in self._subscribed_podcasts]
        )

        self["episodes_list"].setList(
            [self._formatEpisodeEntry(episode) for episode in self._episodes]
        )

        titles = {
            "available": _("Available Podcasts"),
            "subscribed": _("Subscribed Podcasts"),
            "episodes": _("Episodes"),
        }

        for column_name, title_text in titles.items():

            # Device test round 57 -- the "> " marker removed: the
            # background image's own colour already distinguishes the
            # active column, and the marker's extra characters were
            # causing the title to wrap onto two lines when selected
            # (confirmed directly from the user's own screenshot).

            self[f"{column_name}_title_normal"].setText(title_text)

            self[f"{column_name}_title_active"].setText(title_text)

        self._updateColumnHighlighting()

        self._updateInfoDescription()

        if self._search_query:

            self["status"].setText(_("Search: %s") % self._search_query)

        else:

            # Build 0010, device test round 7 -- user request:
            # "Ylhäällä voisi lukea mikä ikkuna on kyseessä." Idle
            # (no active search) previously left this blank; shows
            # this screen's own name now instead, reusing the exact
            # "Podcasts" string MainMenu's own entry already uses.
            self["status"].setText(_("Podcasts"))

    # ------------------------------------------------------------------

    def _updateInfoDescription(self) -> None:
        """
        Device test round 56 -- shows the currently selected podcast's
        or episode's own "description" field (already fetched by
        podcast_providers/podcastindex/podcastindex_provider.py for
        both feeds and episodes, just never displayed anywhere before
        this round) in the new "info" widget, matching whichever
        column currently has focus. Falls back to a "press INFO to
        search" hint whenever there's nothing to show -- the focused
        list is empty (the case explicitly named in the request: no
        podcasts visible yet), the selection index is out of range, or
        the selected entry's own description is blank.
        """

        source = {
            "available": self._available_podcasts,
            "subscribed": self._subscribed_podcasts,
            "episodes": self._episodes,
        }.get(self._focus, [])

        index = self[f"{self._focus}_list"].getSelectedIndex()

        description = ""

        if source and 0 <= index < len(source):

            description = (source[index].get("description") or "").strip()

        if description:

            self["info"].setText(description)

        else:

            self["info"].setText(_("Press EPG/INFO to search"))

    # ------------------------------------------------------------------

    def _formatEpisodeEntry(self, episode) -> str:

        title = episode.get("title", "?")

        duration_text = _formatDuration(episode.get("duration"))

        published_text = _formatPublished(episode.get("published"))

        details = " / ".join(part for part in (published_text, duration_text) if part)

        if details:

            return f"{title} ({details})"

        return title

    # ------------------------------------------------------------------

    def _updateColumnHighlighting(self) -> None:
        """
        Device test round 56 -- the active/inactive column-header
        colouring now lives in one of three pre-rendered background
        images (resources/skins/{variant}/{tier}/podcast_{focus}_
        active.png), swapped here instead of toggling individual bg
        widgets, matching MusicLibraryScreen's own round 39/45 and
        RadioBrowserScreen's/BrowserScreen's own rounds 54/55. Header
        TEXT stays real, translatable normal/active widget pairs,
        toggled here too.
        """

        self._decodeBackgroundImage(self._focus)

        for column_name in COLUMNS:

            is_active = column_name == self._focus

            try:
                self[f"{column_name}_title_normal"].hide() if is_active else self[f"{column_name}_title_normal"].show()

                self[f"{column_name}_title_active"].show() if is_active else self[f"{column_name}_title_active"].hide()

            except Exception as error:

                logger.verbose(f"[Podcast] Unable to set column highlight visibility: {error}")

    # ------------------------------------------------------------------
    # Background image (device test round 56 -- mirrors
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

            logger.verbose("[Podcast] background widget not ready yet, retrying decode shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(lambda: self._decodeBackgroundImage(focus_state))

            retry_timer.start(100, True)

            self._pending_background_retry_timer = retry_timer

            return

        image_path = os.path.join(
            SKIN_PATH,
            self._skin_variant,
            _resolvePodcastResolutionTier(self._screen_width),
            f"podcast_{focus_state}_active.png",
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

            logger.verbose(f"[Podcast] Unable to decode background image {image_path}: {error}")

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

            logger.verbose(f"[Podcast] Unable to apply decoded background image: {error}")

        finally:

            self._background_decode_in_progress = False

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def focusPrevious(self) -> None:

        logger.verbose("[Podcast] LEFT pressed.")

        self._focus = COLUMNS[(COLUMNS.index(self._focus) - 1) % len(COLUMNS)]

        self._updateDisplay()

    # ------------------------------------------------------------------

    def focusNext(self) -> None:

        logger.verbose("[Podcast] RIGHT pressed.")

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

        for _step in range(PAGE_STEP):

            self[f"{self._focus}_list"].up()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageDown(self) -> None:

        for _step in range(PAGE_STEP):

            self[f"{self._focus}_list"].down()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def _onSelectionChanged(self) -> None:
        """
        PODCAST_SCREEN_SPEC.md "Available Podcasts"/"Subscribed
        Podcasts": "Selecting a podcast updates the Episodes column
        with the available episodes for that podcast." Only applies
        while browsing Available/Subscribed -- moving the selection
        within Episodes itself doesn't reload anything, but does
        restart the debounced codec check below (device test round
        29).
        """

        if self._focus == "episodes":

            self._hideEpisodeWarning()

            if config_manager.get("logging.log_station_codecs", True):

                self._episode_codec_timer.start(EPISODE_CODEC_DEBOUNCE_MS, True)

            # Device test round 57 -- fixes a real reported bug: moving
            # within an already-loaded Episodes list never refreshed
            # the info panel's own description, since only
            # _updateDisplay() called _updateInfoDescription() and
            # this method returned before reaching it. The first
            # episode's description showed correctly (set by the
            # _updateDisplay() call that ran when the episode list was
            # first loaded), but scrolling further never updated it.
            self._updateInfoDescription()

            return

        if self._focus not in ("available", "subscribed"):
            return

        podcast = self._selectedPodcast()

        if podcast is None:
            return

        self._loadEpisodes(podcast)

        # Device test round 57 -- same fix as above, for the Available/
        # Subscribed columns: show the newly selected podcast's own
        # description immediately rather than waiting for
        # _loadEpisodes()'s own eventual _updateDisplay() call (episode
        # fetching is asynchronous and may take a moment).
        self._updateInfoDescription()

    # ------------------------------------------------------------------

    def _selectedPodcast(self):

        source = self._available_podcasts if self._focus == "available" else self._subscribed_podcasts

        index = self[f"{self._focus}_list"].getSelectedIndex()

        if not (0 <= index < len(source)):
            return None

        return source[index]

    # ------------------------------------------------------------------

    def _hideEpisodeWarning(self) -> None:

        self["warning"].hide()

        self["status"].show()

    # ------------------------------------------------------------------

    def _checkSelectedEpisodeCodec(self) -> None:
        """
        Device test round 29 -- user request: "Sama voisi olla myos
        podcastien jaksoja selatessa," extending RadioBrowserScreen's
        own debounced ffprobe codec check (round 27/29) to podcast
        episodes. Gated by the same cfg.logging.log_station_codecs
        toggle (on by default) -- reused rather than adding a second,
        separate setting for what's conceptually the same feature.

        Unlike RadioBrowserScreen, this screen has no dedicated info-
        panel widget to update with a measured codec/bitrate line, so
        this only logs (still builds the same real-world data over
        time) and, on a failed/timed-out probe specifically, shows a
        brief warning via the existing "status" line -- the closest
        equivalent this screen's actual layout has to RadioBrowser-
        Screen's own info panel -- auto-reverting after
        EPISODE_CODEC_WARNING_MS via _episode_codec_revert_timer.
        """

        if not ffprobe_available():
            return

        index = self["episodes_list"].getSelectedIndex()

        if not self._episodes or not (0 <= index < len(self._episodes)):
            return

        episode = self._episodes[index]

        url = episode.get("playback_url")

        if not url:
            return

        result = ffprobe_probe(url)

        title = episode.get("title", "?")

        if result:

            logger.info(f"[Podcast] Episode codec (ffprobe): {title} -> {result}")

            return

        logger.info(f"[Podcast] Episode codec (ffprobe): {title} -> probe failed or timed out")

        if self._focus == "episodes" and self["episodes_list"].getSelectedIndex() == index:

            self["warning"].setText(_("Warning: this episode may not work."))

            self["warning"].show()

            self["status"].hide()

            self._episode_codec_revert_timer.start(EPISODE_CODEC_WARNING_MS, True)

    # ------------------------------------------------------------------

    def _loadEpisodes(self, podcast, force_refresh: bool = False) -> None:

        podcast_id = podcast.get("podcast_id")

        if not podcast_id:
            return

        self._current_podcast_id = podcast_id

        # Build 0010, device test round 23 -- kept alongside
        # _current_podcast_id so _addEpisodeToPlaylist() can store the
        # show's own name (playlist_manager.addTrack()'s artist=), not
        # just the episode's own title -- see that method's own
        # docstring.
        self._current_podcast_title = podcast.get("title", "")

        self._episodes = podcast_manager.getEpisodes(podcast_id, force_refresh=force_refresh)

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Search (PODCAST_SCREEN_SPEC.md "Search")
    # ------------------------------------------------------------------

    def searchPressed(self) -> None:

        logger.verbose("[Podcast] INFO pressed.")

        self.session.openWithCallback(
            self._searchQueryEntered,
            VirtualKeyBoard,
            title=_("Search podcasts"),
            text=self._search_query,
        )

    # ------------------------------------------------------------------

    def _searchQueryEntered(self, text) -> None:

        if text is None:
            return

        if not text.strip():
            return

        self._search_query = text

        self["status"].setText(_("Searching..."))

        results = podcast_manager.searchPodcasts(text)

        self._available_podcasts = results

        self._focus = "available"

        self._updateDisplay()

        if not results:

            self.session.open(
                MessageBox,
                _("No podcasts found for \"%s\".") % text,
                MessageBox.TYPE_INFO,
                timeout=4,
            )

    # ------------------------------------------------------------------
    # Actions (PODCAST_SCREEN_SPEC.md "Podcast Actions")
    # ------------------------------------------------------------------

    def okPressed(self) -> None:

        logger.verbose("[Podcast] OK pressed.")

        if self._focus == "available":

            self._availablePodcastMenu()

        elif self._focus == "subscribed":

            self._subscribedPodcastMenu()

        elif self._focus == "episodes":

            self._episodeMenu()

    # ------------------------------------------------------------------

    def _availablePodcastMenu(self) -> None:

        podcast = self._selectedPodcast()

        if podcast is None:
            return

        podcast_id = podcast.get("podcast_id")

        choices = []

        if podcast_manager.isSubscribed(podcast_id):

            choices.append((_("Already subscribed"), "__noop__"))

        else:

            choices.append((_("Subscribe"), "subscribe"))

        choices.append((_("Open podcast"), "open"))
        choices.append((_("Cancel"), "cancel"))

        self.session.openWithCallback(
            lambda choice: self._availableMenuChosen(choice, podcast),
            ChoiceBox,
            title=podcast.get("title", "?"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _availableMenuChosen(self, choice, podcast) -> None:

        if choice is None or choice[1] in ("cancel", "__noop__"):
            return

        if choice[1] == "subscribe":

            if podcast_manager.subscribe(podcast):

                self._subscribed_podcasts = podcast_manager.getSubscriptions()

                self._updateDisplay()

            else:

                self.session.open(MessageBox, _("Unable to subscribe."), MessageBox.TYPE_ERROR)

        elif choice[1] == "open":

            self._loadEpisodes(podcast)

            self._focus = "episodes"

            self._updateDisplay()

    # ------------------------------------------------------------------

    def _subscribedPodcastMenu(self) -> None:

        podcast = self._selectedPodcast()

        if podcast is None:
            return

        choices = [
            (_("Open podcast"), "open"),
            (_("Refresh"), "refresh"),
            (_("Unsubscribe"), "unsubscribe"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._subscribedMenuChosen(choice, podcast),
            ChoiceBox,
            title=podcast.get("title", "?"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _subscribedMenuChosen(self, choice, podcast) -> None:

        if choice is None or choice[1] == "cancel":
            return

        podcast_id = podcast.get("podcast_id")

        if choice[1] == "open":

            self._loadEpisodes(podcast)

            self._focus = "episodes"

            self._updateDisplay()

        elif choice[1] == "refresh":

            self["status"].setText(_("Refreshing..."))

            if not podcast_manager.refreshPodcast(podcast_id):

                self.session.open(
                    MessageBox,
                    _("Refresh failed -- keeping previous information."),
                    MessageBox.TYPE_INFO,
                    timeout=4,
                )

            self._subscribed_podcasts = podcast_manager.getSubscriptions()

            if self._current_podcast_id == podcast_id:

                self._episodes = podcast_manager.getEpisodes(podcast_id)

            self._updateDisplay()

        elif choice[1] == "unsubscribe":

            podcast_manager.unsubscribe(podcast_id)

            self._subscribed_podcasts = podcast_manager.getSubscriptions()

            self._updateDisplay()

    # ------------------------------------------------------------------

    def _episodeMenu(self) -> None:

        index = self["episodes_list"].getSelectedIndex()

        if not (0 <= index < len(self._episodes)):
            return

        episode = self._episodes[index]

        choices = [
            (_("Play"), "play"),
            (_("Add to playlist"), "add_to_playlist"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._episodeMenuChosen(choice, episode),
            ChoiceBox,
            title=episode.get("title", "?"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _episodeMenuChosen(self, choice, episode) -> None:

        if choice is None or choice[1] == "cancel":
            return

        if choice[1] == "play":

            self._playEpisode(episode)

        elif choice[1] == "add_to_playlist":

            self._choosePlaylistForEpisode(episode)

    # ------------------------------------------------------------------
    # Playback (PODCAST_SCREEN_SPEC.md "Playback Integration")
    # ------------------------------------------------------------------

    def _playEpisode(self, episode) -> None:
        """
        Episodes are finite, seekable audio files (unlike a live
        Internet Radio stream), so this uses the same playQueue()
        local-file-style playback path as BrowserScreen/PlaylistScreen
        rather than playStream() -- see PLAYBACK_CONTROLLER_SPEC.md's
        own confirmation that Enigma2's GStreamer/MP3 service factory
        already resolves http(s):// URIs the same way it resolves
        local paths, so no podcast-specific playback path is needed
        here either.
        """

        if self._playback is None:
            return

        playback_url = episode.get("playback_url")

        if not playback_url:

            self.session.open(MessageBox, _("This episode has no playable audio."), MessageBox.TYPE_ERROR)

            return

        self._log(f"Playback requested: {episode.get('title', '?')}")

        if self._playback.playQueue([playback_url], start_index=0):

            self.close("played")

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------
    # Playlist integration (PODCAST_SCREEN_SPEC.md "Playlist
    # Integration")
    # ------------------------------------------------------------------

    def _choosePlaylistForEpisode(self, episode) -> None:

        names = playlist_manager.getPlaylistNames()

        choices = [(name, name) for name in names]

        choices.append((_("Create New"), "__new__"))
        choices.append((_("Cancel"), "__cancel__"))

        self.session.openWithCallback(
            lambda choice: self._playlistChosenForEpisode(choice, episode),
            ChoiceBox,
            title=_("Select playlist"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _playlistChosenForEpisode(self, choice, episode) -> None:

        if choice is None or choice[1] == "__cancel__":
            return

        if choice[1] == "__new__":

            self.session.openWithCallback(
                lambda name: self._createPlaylistForEpisode(name, episode),
                VirtualKeyBoard,
                title=_("New playlist name"),
                text="",
            )

            return

        self._addEpisodeToPlaylist(choice[1], episode)

    # ------------------------------------------------------------------

    def _createPlaylistForEpisode(self, name, episode) -> None:

        if not name:
            return

        self._addEpisodeToPlaylist(name, episode)

    # ------------------------------------------------------------------

    def _addEpisodeToPlaylist(self, playlist_name, episode) -> None:

        playback_url = episode.get("playback_url")

        if not playback_url:

            self.session.open(MessageBox, _("This episode has no playable audio."), MessageBox.TYPE_ERROR)

            return

        # Build 0010, device test round 1: per user request ("Siina
        # voisi tulla perana (podcast), kuten radion suosikkilistoilla"),
        # mirrors PlaylistScreen's own "(Radio)" suffix convention for
        # its combined playlist/radio-list display. Also fixes a real
        # bug found in the same round: without an explicit title,
        # addTrack() derived one from the URL via os.path.basename(),
        # which for a URL with query-string parameters (confirmed from
        # a real device log -- Bauer's own podcast CDN does this)
        # included the entire query string verbatim in the stored
        # title. The episode's own real title is already known here,
        # so there's no reason to derive a worse one from the URL.
        episode_title = episode.get("title", "?")

        display_title = f"{episode_title} ({_('Podcast')})"

        if playlist_manager.addTrack(playlist_name, playback_url, title=display_title, artist=self._current_podcast_title):

            self.session.open(
                MessageBox,
                _("Added to playlist: %s") % playlist_name,
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        else:

            self.session.open(MessageBox, _("Unable to add to playlist."), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def helpPressed(self) -> None:

        logger.verbose("[Podcast] HELP pressed.")

        title, content = help_manager.getHelp("podcastscreen")

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[Podcast] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "podcast"):
            return

        self.close(action_id)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[Podcast] EXIT pressed.")

        self._log("Closing")

        self.close(None)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"PodcastScreen(initialized={self._initialized})"


# ==============================================================================
# End of file
# ==============================================================================

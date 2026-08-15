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

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from .compatibility import compatibility
from .help_manager import help_manager
from .help_screen import HelpScreen
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .playlist_manager import playlist_manager
from .podcast_manager import podcast_manager
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)

COLUMNS = ("available", "subscribed", "episodes")

# CHANNEL UP/DOWN page-step, matching RadioBrowserScreen's own
# PAGE_STEP convention for long lists.
PAGE_STEP = 10


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

    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 540

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Three equal-width columns (Available | Subscribed | Episodes),
        each with a highlighted title and a scrollable list below,
        scaled from the 700x540 design resolution -- same canvas size
        RadioBrowserScreen uses, for a consistent look between the two
        three-column browsers.
        """

        sx = width / PodcastScreen.DESIGN_WIDTH
        sy = height / PodcastScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR
        active_color = to_opaque_skin_color(skin_manager.getColor("selection_background", "#0056B3"))

        # Build 0010 -- BUILD_0010_PLAN.md "Visual Refinement":
        # inactive column headers get a light blue background (not
        # the neutral panel_background_color Build 0009's MainScreen
        # panels used for "inactive") while the active header keeps
        # the existing blue highlight. No theme key existed for this
        # yet, so a sensible standalone default is used directly here
        # rather than inventing a new getColor() key on the spot --
        # can be promoted to a real theme colour once THEME_SPEC.md's
        # Light/Dark themes are implemented.
        inactive_color = to_opaque_skin_color(skin_manager.getColor("inactive_highlight", "#ADD8E6"))

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        column_width = 220

        def column_x(index):
            return 20 + index * (column_width + 10)

        columns_xml = ""

        titles = (_("Available Podcasts"), _("Subscribed Podcasts"), _("Episodes"))

        for index, (column_name, title_text) in enumerate(zip(COLUMNS, titles)):

            x = column_x(index)

            columns_xml += f"""
            <widget name="{column_name}_title_bg_normal"
                    {rect(x, 45, column_width, 25)}
                    backgroundColor="{inactive_color}"/>

            <widget name="{column_name}_title_bg_active"
                    {rect(x, 45, column_width, 25)}
                    backgroundColor="{active_color}"/>

            <widget name="{column_name}_title"
                    {rect(x, 45, column_width, 25)}
                    {font(16)}
                    halign="left"
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="{column_name}_list"
                    {rect(x, 75, column_width, 340)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>
            """

        return f"""
        <screen name="MediaPlayer3PodcastScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Podcasts">

            <widget name="status"
                    {rect(20, 10, 660, 25)}
                    {font(16)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            {columns_xml}

            <widget name="hint"
                    {rect(20, 425, 660, 90)}
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

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Podcast] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["status"] = Label("")

        for column_name in COLUMNS:

            self[f"{column_name}_title_bg_normal"] = Label("")
            self[f"{column_name}_title_bg_active"] = Label("")
            self[f"{column_name}_title"] = Label("")
            self[f"{column_name}_list"] = MenuList([])

        self["hint"] = Label(
            _(
                "LEFT/RIGHT: Column   UP/DOWN: Move   OK: Actions   "
                "INFO: Search   HELP: Help   MENU: Menu   EXIT: Back"
            )
        )

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

            marker = "> " if column_name == self._focus else ""

            self[f"{column_name}_title"].setText(f"{marker}{title_text}")

        self._updateColumnHighlighting()

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
        Build 0010 -- see this file's own _buildSkin() docstring for
        why this uses hide()/show() on a pair of pre-positioned
        background rectangles per column, exactly mirroring
        MainScreen's own confirmed-safe Build 0009 pattern, rather
        than a runtime widget recolour.
        """

        for column_name in COLUMNS:

            is_active = column_name == self._focus

            try:
                self[f"{column_name}_title_bg_normal"].hide() if is_active else self[f"{column_name}_title_bg_normal"].show()

                self[f"{column_name}_title_bg_active"].show() if is_active else self[f"{column_name}_title_bg_active"].hide()

            except Exception as error:

                logger.verbose(f"[Podcast] Unable to set column highlight visibility: {error}")

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
        within Episodes itself doesn't reload anything.
        """

        if self._focus not in ("available", "subscribed"):
            return

        podcast = self._selectedPodcast()

        if podcast is None:
            return

        self._loadEpisodes(podcast)

    # ------------------------------------------------------------------

    def _selectedPodcast(self):

        source = self._available_podcasts if self._focus == "available" else self._subscribed_podcasts

        index = self[f"{self._focus}_list"].getSelectedIndex()

        if not (0 <= index < len(source)):
            return None

        return source[index]

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

# ==============================================================================
#
# MediaPlayer3
#
# File        : musiclibraryscreen.py
#
# Description :
#
#     MusicLibraryScreen
#
#     Metadata-based browsing of the local music collection: three
#     panels (Artists/Albums/Tracks), navigation modeled directly on
#     RadioBrowserScreen (Build 0007) -- LEFT/RIGHT switches the
#     active panel, UP/DOWN moves within it, OK plays. Never reads
#     media files or performs playback itself -- always asks
#     LibraryManager for a PlaybackQueue and hands it to the shared
#     PlaybackController, exactly like BrowserScreen/PlaylistScreen/
#     RadioBrowserScreen already do.
#
# Implements :
#
#     MUSICLIBRARY_SCREEN_SPEC.md v0.1
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
# ------------------------------------------------------------------------------

from __future__ import annotations

from enigma import eTimer

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from .compatibility import compatibility
from .help_manager import help_manager
from .help_screen import HelpScreen
from .library_manager import library_manager
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)

PANELS = ("artists", "albums", "tracks")

# CHANNEL UP/DOWN jump this many entries at once -- same convenience
# feature RadioBrowserScreen added after real device testing (long
# lists are slow to scroll one entry at a time). PROVISIONAL for this
# screen specifically: CH+/CH- is itself unconfirmed to even reach
# RadioBrowserScreen on real hardware (Build 0007, device test rounds
# 4-9) -- left in as harmless best-effort, same reasoning as there.
PAGE_STEP = 10


class MusicLibraryScreen(Screen):
    """
    Metadata-based music browsing, search and playback queue
    generation (Build 0008).
    """

    SPECIFICATION_VERSION = "0.1"

    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 540

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build MusicLibraryScreen's skin for an exact `width` x
        `height` window, scaling from the 700x540 design resolution
        above -- same fullscreen/white-panel pattern as every other
        screen since Build 0007 (device test rounds 8 and 12).
        """

        sx = width / MusicLibraryScreen.DESIGN_WIDTH
        sy = height / MusicLibraryScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR
        active_color = to_opaque_skin_color(skin_manager.getColor("selection_background", "#0056B3"))
        inactive_color = to_opaque_skin_color(skin_manager.getColor("inactive_highlight", "#ADD8E6"))

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        # Build 0010, device test round 6 -- BUILD_0010_PLAN.md "Visual
        # Refinement": same two-tier column-header highlighting
        # PodcastScreen/BrowserScreen already use (active: existing
        # blue; inactive: light blue), extended here per user request
        # ("Musiikkikirjasto ... osikkorivin väri ei vaihdu samalla
        # tavalla kuin tiedostoselaimessa") so all three-column
        # browsers look consistent, not just the two built after this
        # highlighting existed.
        panel_rects = {
            "artists": (20, 45, 220, 25),
            "albums": (250, 45, 220, 25),
            "tracks": (480, 45, 200, 25),
        }

        highlight_xml = ""

        for panel_name, (x, y, w, h) in panel_rects.items():

            highlight_xml += f"""
            <widget name="{panel_name}_title_bg_normal"
                    {rect(x, y, w, h)}
                    backgroundColor="{inactive_color}"/>

            <widget name="{panel_name}_title_bg_active"
                    {rect(x, y, w, h)}
                    backgroundColor="{active_color}"/>
            """

        return f"""
        <screen name="MediaPlayer3MusicLibraryScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Music Library">

            <widget name="status"
                    {rect(20, 10, 660, 25)}
                    {font(16)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            {highlight_xml}

            <widget name="artists_title"
                    {rect(20, 45, 220, 25)}
                    {font(18)}
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="albums_title"
                    {rect(250, 45, 220, 25)}
                    {font(18)}
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="tracks_title"
                    {rect(480, 45, 200, 25)}
                    {font(18)}
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="artists"
                    {rect(20, 75, 220, 280)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="albums"
                    {rect(250, 75, 220, 280)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="tracks"
                    {rect(480, 75, 200, 280)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="info"
                    {rect(20, 365, 660, 120)}
                    {font(16)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="hint"
                    {rect(20, 495, 660, 40)}
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

        self._focus = "artists"

        self._artists = []
        self._albums = []
        self._tracks = []

        self._search_query = ""

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[MusicLibrary] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["status"] = Label("")

        # Build 0010, device test round 7: bg widgets MUST be added to
        # self before the title widgets -- Enigma2's paint order
        # follows Python insertion order (self[name] = ...), not the
        # skin XML declaration order. Getting this backwards (title
        # added first) makes the opaque bg rectangles paint over the
        # title text, hiding it completely -- exactly what device
        # testing showed here. PodcastScreen/BrowserScreen already do
        # this correctly (bg_normal, bg_active, title, in that order,
        # per column) -- matched that order here too.
        for panel_name in PANELS:

            self[f"{panel_name}_title_bg_normal"] = Label("")
            self[f"{panel_name}_title_bg_active"] = Label("")

        self["artists_title"] = Label(_("Artists"))
        self["albums_title"] = Label(_("Albums"))
        self["tracks_title"] = Label(_("Tracks"))

        self["artists"] = MenuList([])
        self["albums"] = MenuList([])
        self["tracks"] = MenuList([])
        self["info"] = Label("")
        self["hint"] = Label(
            _("LEFT/RIGHT: Panel   UP/DOWN: Move   OK: Play   INFO: Search   MENU: Menu   EXIT: Back")
        )

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
            actions[action_name] = self.searchByName

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

        # Build 0007, device test round 8 -- a blocking scan/search
        # called synchronously here could let the screen finish
        # opening before anything has actually been indexed, leaving
        # the user looking at an empty screen with no explanation.
        # Same deferred-timer "please wait" pattern
        # RadioBrowserScreen's search already uses.
        self["status"].setText(_("Loading library, please wait..."))

        self._initial_load_timer = eTimer()

        self._initial_load_timer.callback.append(self._performInitialLoad)

        self._initial_load_timer.start(10, True)

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _performInitialLoad(self) -> None:

        if not library_manager.isScanned():

            library_manager.scan()

        self._refreshArtists()

        self._updateFocusIndicator()

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def _refreshArtists(self) -> None:

        self._artists = library_manager.getArtists()

        self["artists"].setList(self._artists)

        self._refreshAlbums()

    # ------------------------------------------------------------------

    def _refreshAlbums(self) -> None:

        artist = self._selectedArtist()

        self._albums = library_manager.getAlbums(artist=artist)

        self["albums"].setList(self._albums)

        self._refreshTracks()

    # ------------------------------------------------------------------

    def _refreshTracks(self) -> None:

        artist = self._selectedArtist()

        album = self._selectedAlbum()

        self._tracks = library_manager.getTracks(artist=artist, album=album)

        self["tracks"].setList([track["title"] for track in self._tracks])

        self._updateInfoPanel()

    # ------------------------------------------------------------------

    def _selectedArtist(self):

        index = self["artists"].getSelectedIndex()

        if self._artists and 0 <= index < len(self._artists):
            return self._artists[index]

        return None

    # ------------------------------------------------------------------

    def _selectedAlbum(self):

        index = self["albums"].getSelectedIndex()

        if self._albums and 0 <= index < len(self._albums):
            return self._albums[index]

        return None

    # ------------------------------------------------------------------

    def _selectedTrack(self):

        index = self["tracks"].getSelectedIndex()

        if self._tracks and 0 <= index < len(self._tracks):
            return self._tracks[index]

        return None

    # ------------------------------------------------------------------

    def _updateInfoPanel(self) -> None:

        if not library_manager.getTrackCount():

            self["info"].setText(
                _("No music library available.\n\nUse Library Update from the menu\nafter adding music files.")
            )

            return

        track = self._selectedTrack()

        if track is not None:

            self["info"].setText(
                f"{track['title']}\n"
                f"{_('Artist')}: {track['artist']}   {_('Album')}: {track['album']}\n"
                f"{_('Genre')}: {track['genre']}   {_('Year')}: {track['year']}"
            )

            return

        album = self._selectedAlbum()

        if album is not None:

            track_count = len(library_manager.getTracks(artist=self._selectedArtist(), album=album))

            self["info"].setText(f"{album}\n{track_count} {_('track(s)')}")

            return

        artist = self._selectedArtist()

        if artist is not None:

            album_count = len(library_manager.getAlbums(artist=artist))

            self["info"].setText(f"{artist}\n{album_count} {_('album(s)')}")

            return

        self["info"].setText("")

    # ------------------------------------------------------------------
    # Panel navigation (mirrors RADIOBROWSER_SCREEN_SPEC.md
    # "Navigation")
    # ------------------------------------------------------------------

    def focusPrevious(self) -> None:

        logger.verbose("[MusicLibrary] LEFT pressed.")

        index = (PANELS.index(self._focus) - 1) % len(PANELS)

        self._focus = PANELS[index]

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def focusNext(self) -> None:

        logger.verbose("[MusicLibrary] RIGHT pressed.")

        index = (PANELS.index(self._focus) + 1) % len(PANELS)

        self._focus = PANELS[index]

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def _updateFocusIndicator(self) -> None:
        """
        Build 0010, device test round 7 -- user request: "Ylhäällä
        voisi lukea mikä ikkuna on kyseessä." Previously showed the
        active panel's own name here (Artists/Albums/Tracks), now
        redundant with the column-header highlighting itself (Round
        6/9) -- shows this screen's own name instead, reusing the
        exact "Music Library" string MainMenu's own entry already
        uses for consistency.
        """

        self["status"].setText(_("Music Library"))

        self._updateColumnHighlighting()

    # ------------------------------------------------------------------

    def _updateColumnHighlighting(self) -> None:
        """
        Build 0010, device test round 6 -- see this file's own
        _buildSkin() comment. Identical hide()/show() mechanism to
        PodcastScreen/BrowserScreen's own _updateColumnHighlighting();
        see either's docstring for why hide()/show() on pre-positioned
        rectangles is used instead of a runtime widget recolour.
        """

        for panel_name in PANELS:

            is_active = panel_name == self._focus

            try:
                self[f"{panel_name}_title_bg_normal"].hide() if is_active else self[f"{panel_name}_title_bg_normal"].show()

                self[f"{panel_name}_title_bg_active"].show() if is_active else self[f"{panel_name}_title_bg_active"].hide()

            except Exception as error:

                logger.verbose(f"[MusicLibrary] Unable to set column highlight visibility: {error}")

    # ------------------------------------------------------------------

    def moveUp(self) -> None:

        logger.verbose("[MusicLibrary] UP pressed.")

        self[self._focus].up()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def moveDown(self) -> None:

        logger.verbose("[MusicLibrary] DOWN pressed.")

        self[self._focus].down()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageUp(self) -> None:

        logger.verbose("[MusicLibrary] CH+ pressed.")

        for _step in range(PAGE_STEP):
            self[self._focus].up()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageDown(self) -> None:

        logger.verbose("[MusicLibrary] CH- pressed.")

        for _step in range(PAGE_STEP):
            self[self._focus].down()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def _onSelectionChanged(self) -> None:

        if self._focus == "artists":

            self._refreshAlbums()

        elif self._focus == "albums":

            self._refreshTracks()

        else:

            self._updateInfoPanel()

    # ------------------------------------------------------------------
    # Playback (MUSICLIBRARY_SCREEN_SPEC.md "Playback")
    # ------------------------------------------------------------------

    def okPressed(self) -> None:

        logger.verbose("[MusicLibrary] OK pressed.")

        if not library_manager.getTrackCount():
            return

        if self._focus == "tracks":

            track = self._selectedTrack()

            if track is None:
                return

            queue = library_manager.createQueue(tracks=self._tracks)

            start_index = self._tracks.index(track)

        elif self._focus == "albums":

            album = self._selectedAlbum()

            if album is None:
                return

            queue = library_manager.createQueue(artist=self._selectedArtist(), album=album)

            start_index = 0

        else:

            artist = self._selectedArtist()

            if artist is None:
                return

            queue = library_manager.createQueue(artist=artist)

            start_index = 0

        if not queue:
            return

        if self._playback is not None and self._playback.playQueue(queue, start_index):

            self._close("played")

    # ------------------------------------------------------------------
    # Search (MUSICLIBRARY_SCREEN_SPEC.md "Search")
    # ------------------------------------------------------------------

    def searchByName(self) -> None:

        logger.verbose("[MusicLibrary] INFO pressed.")

        self.session.openWithCallback(
            self._searchNameEntered,
            VirtualKeyBoard,
            title=_("Search the music library"),
            text=self._search_query,
        )

    # ------------------------------------------------------------------

    def _searchNameEntered(self, text) -> None:

        if text is None:
            return

        self._search_query = text

        results = library_manager.search(text)

        self._tracks = results

        self["tracks"].setList([track["title"] for track in results])

        self._focus = "tracks"

        self["status"].setText(_("Search: {0} ({1} results)").format(text, len(results)))

        self["info"].setText("")

        self._updateInfoPanel()

    # ------------------------------------------------------------------
    # Menu (Library functions)
    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[MusicLibrary] MENU pressed.")

        choices = [
            (_("Update Library"), "update"),
            (_("Main Menu"), "mainmenu"),
        ]

        self.session.openWithCallback(self._menuChoiceMade, ChoiceBox, title=_("Music Library"), list=choices)

    # ------------------------------------------------------------------

    def _menuChoiceMade(self, choice) -> None:

        if choice is None:
            return

        action = choice[1]

        if action == "update":

            self["status"].setText(_("Loading library, please wait..."))

            self._initial_load_timer = eTimer()

            self._initial_load_timer.callback.append(self._performRescan)

            self._initial_load_timer.start(10, True)

        elif action == "mainmenu":

            self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _performRescan(self) -> None:

        count = library_manager.scan()

        self._refreshArtists()

        self._updateFocusIndicator()

        self._log(f"Library rescanned: {count} track(s).")

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id is None:
            return

        self._close(("open_menu", action_id))

    # ------------------------------------------------------------------
    # Help (Build 0008)
    # ------------------------------------------------------------------

    def helpPressed(self) -> None:
        """
        Build 0008 -- opens HelpScreen with MusicLibraryScreen's own
        context-sensitive help document.
        """

        logger.verbose("[MusicLibrary] HELP pressed.")

        title, content = help_manager.getHelp("musiclibraryscreen")

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------
    # Exit
    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[MusicLibrary] EXIT pressed.")

        self._close(None)

    # ------------------------------------------------------------------

    def _close(self, result=None) -> None:

        self._log("Closing")

        self._log("Closed")

        self.close(result)

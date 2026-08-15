# ==============================================================================
#
# MediaPlayer3
#
# File        : playlistscreen.py
#
# Description :
#
#     PlaylistScreen
#
#     Dual-panel playlist management: left panel lists local
#     PlaylistManager playlists AND InternetRadioManager favorite
#     lists together (local first, then radio); right panel lists the
#     selected entry's tracks or stations. All modifications are
#     delegated to PlaylistManager/InternetRadioManager -- PlaylistScreen
#     only displays and dispatches user choices.
#
# Implements :
#
#     PLAYLISTSCREEN_SPEC.md v0.2
#
# Architecture :
#
#     ARCHITECTURE.md (Build 0007)
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
# 2026-07-19  Build 0007
#   - Initial version (local playlists only).
#
# 2026-07-24  Build 0007 (device test round 3)
#   - Combined local playlists and Internet Radio favorite lists in
#     the left panel (local first, then radio -- "Vasemmassa listassa
#     ensin paikalliset soittolistat ja sitten internetradiolistat"),
#     requested after real device testing. Each entry tracked as
#     ("local", name)/("radio", name); context menus, playback and
#     information dialogs all branch on entry type. Radio-list "Play"
#     plays the first station in that favorite list; radio entries
#     have a leaner menu (no Export/Move Up/Move Down, which don't
#     apply to stations).
#
# 2026-07-24  Build 0007 (device test round 5)
#   - Added INFO handling (infoPressed()): PlaylistScreen previously
#     had no "InfoActions" context or "info"/"showEventInfo" binding
#     at all, showing Enigma2's "unhandled key" indicator on OpenATV.
#     Shows Information for whichever panel/entry currently has focus.
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
from .internetradio_manager import internetradio_manager
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .playlist_manager import playlist_manager
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)

# Build 0010, device test round 6 -- named for _updateColumnHighlighting()'s
# loop, matching RadioBrowserScreen/MusicLibraryScreen/PodcastScreen's own
# PANELS/COLUMNS convention (this screen previously used the "playlists"/
# "tracks" string literals directly everywhere else, which is unaffected).
PANELS = ("playlists", "tracks")


class PlaylistScreen(Screen):
    """
    Dual-panel playlist management (Build 0007).
    """

    SPECIFICATION_VERSION = "0.1"

    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 500

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build PlaylistScreen's skin for an exact `width` x `height`
        window, scaling from the 700x500 design resolution above
        (Build 0007, device test round 8).
        """

        sx = width / PlaylistScreen.DESIGN_WIDTH
        sy = height / PlaylistScreen.DESIGN_HEIGHT

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
        # Refinement", same fix and reasoning as MusicLibraryScreen/
        # RadioBrowserScreen's own _buildSkin() comments.
        panel_rects = {
            "playlists": (20, 45, 320, 25),
            "tracks": (360, 45, 320, 25),
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
        <screen name="MediaPlayer3PlaylistScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Playlists">

            <widget name="status"
                    {rect(20, 10, 660, 25)}
                    {font(16)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            {highlight_xml}

            <widget name="playlists_title"
                    {rect(20, 45, 320, 25)}
                    {font(18)}
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="tracks_title"
                    {rect(360, 45, 320, 25)}
                    {font(18)}
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="playlists"
                    {rect(20, 75, 320, 360)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="tracks"
                    {rect(360, 75, 320, 360)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="hint"
                    {rect(20, 450, 660, 40)}
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

        self._focus = "playlists"

        # Combined local playlists + radio favorite lists (Build 0007,
        # device test round 3), each entry ("local", name) or
        # ("radio", name) -- see _reloadPlaylists().
        self._entries = []
        self._current_entry_type = None

        self._current_playlist = None
        self._current_tracks = []

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Playlist] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self["status"] = Label("")

        # Build 0010, device test round 7 -- see MusicLibraryScreen's
        # own _initialize() comment for why bg widgets must be added
        # before the title widgets here.
        for panel_name in PANELS:

            self[f"{panel_name}_title_bg_normal"] = Label("")
            self[f"{panel_name}_title_bg_active"] = Label("")

        self["playlists_title"] = Label(_("Playlists"))
        self["tracks_title"] = Label(_("Tracks"))
        self["playlists"] = MenuList([])
        self["tracks"] = MenuList([])
        self["hint"] = Label(
            _("LEFT/RIGHT: Panel   UP/DOWN: Move   OK: Options   MENU: Menu   EXIT: Back")
        )

        actions = {
            "ok": self.okPressed,
            "cancel": self.exitPressed,
            "left": self.focusLeft,
            "right": self.focusRight,
            "up": self.moveUp,
            "down": self.moveDown,
            "menu": self.menuPressed,
        }

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.infoPressed

        for action_name in compatibility.getHelpKeyActionNames():
            actions[action_name] = self.helpPressed

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "MenuActions", "InfoActions", "InfobarEPGActions", "HelpActions"],
            actions,
            -1,
        )

        self._reloadPlaylists()

        self._updateFocusIndicator()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Panel / list management
    # ------------------------------------------------------------------

    def _reloadPlaylists(self) -> None:
        """
        Build the combined left-panel list: local PlaylistManager
        playlists first, then InternetRadioManager favorite lists
        (Build 0007, device test round 3 -- "Vasemmassa listassa
        ensin paikalliset soittolistat ja sitten internetradiolistat").
        Each entry is ("local", name) or ("radio", name); radio
        entries are shown with a "(Radio)" suffix to disambiguate from
        a local playlist that happens to share the same name.
        """

        local_names = playlist_manager.getPlaylistNames()

        radio_names = internetradio_manager.getFavoriteListNames()

        self._entries = [("local", name) for name in local_names] + [("radio", name) for name in radio_names]

        display = local_names + [f"{name} ({_('Radio')})" for name in radio_names]

        self["playlists"].setList(display)

        if self._entries:

            self._selectEntry(0)

        else:

            self._current_playlist = None

            self._current_entry_type = None

            self._current_tracks = []

            self["tracks"].setList([])

    # ------------------------------------------------------------------

    def _selectEntry(self, index: int) -> None:

        if not (0 <= index < len(self._entries)):
            return

        self._current_entry_type, self._current_playlist = self._entries[index]

        self._reloadTracks()

    # ------------------------------------------------------------------

    def _reloadTracks(self) -> None:

        if not self._current_playlist:

            self["tracks"].setList([])

            return

        if self._current_entry_type == "radio":

            self._current_tracks = internetradio_manager.getFavorites(self._current_playlist)

            display = [entry.get("name", "Unknown") for entry in self._current_tracks]

        else:

            self._current_tracks = playlist_manager.loadPlaylist(self._current_playlist)

            display = [
                track.get("title") or track.get("file_name", "Unknown")
                for track in self._current_tracks
            ]

        self["tracks"].setList(display)

        logger.verbose(
            f"[Playlist] Track list updated\n\n"
            f"List: {self._current_playlist} ({self._current_entry_type})\n\n"
            f"Entries: {len(display)}\n"
        )

    # ------------------------------------------------------------------

    def _updateFocusIndicator(self) -> None:
        """
        Build 0010, device test round 7 -- see MusicLibraryScreen's
        identical fix/reasoning.
        """

        self["status"].setText(_("Playlists"))

        self._updateColumnHighlighting()

    # ------------------------------------------------------------------

    def _updateColumnHighlighting(self) -> None:
        """
        Build 0010, device test round 6 -- see this file's own
        _buildSkin() comment / MusicLibraryScreen/RadioBrowserScreen's
        identical fix.
        """

        for panel_name in PANELS:

            is_active = panel_name == self._focus

            try:
                self[f"{panel_name}_title_bg_normal"].hide() if is_active else self[f"{panel_name}_title_bg_normal"].show()

                self[f"{panel_name}_title_bg_active"].show() if is_active else self[f"{panel_name}_title_bg_active"].hide()

            except Exception as error:

                logger.verbose(f"[Playlist] Unable to set column highlight visibility: {error}")

    # ------------------------------------------------------------------
    # Navigation (PLAYLISTSCREEN_SPEC.md "Navigation")
    # ------------------------------------------------------------------

    def focusLeft(self) -> None:

        logger.verbose("[Playlist] LEFT pressed.")

        self._focus = "playlists"

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def focusRight(self) -> None:

        logger.verbose("[Playlist] RIGHT pressed.")

        self._focus = "tracks"

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def moveUp(self) -> None:

        logger.verbose("[Playlist] UP pressed.")

        if self._focus == "playlists":

            self["playlists"].up()

            self._onPlaylistSelectionChanged()

        else:

            self["tracks"].up()

    # ------------------------------------------------------------------

    def moveDown(self) -> None:

        logger.verbose("[Playlist] DOWN pressed.")

        if self._focus == "playlists":

            self["playlists"].down()

            self._onPlaylistSelectionChanged()

        else:

            self["tracks"].down()

    # ------------------------------------------------------------------

    def _onPlaylistSelectionChanged(self) -> None:
        """
        Selecting a playlist/list automatically loads its contents;
        playback is never started automatically
        (PLAYLISTSCREEN_SPEC.md "Playlist Selection").
        """

        self._selectEntry(self["playlists"].getSelectedIndex())

# End of Part 1
    # ------------------------------------------------------------------
    # Context Menus (PLAYLISTSCREEN_SPEC.md "Playlist Context Menu" /
    # "Track Context Menu")
    # ------------------------------------------------------------------

    def okPressed(self) -> None:

        logger.verbose("[Playlist] OK pressed.")

        if self._focus == "playlists":

            self._openPlaylistMenu()

        else:

            self._openTrackMenu()

    # ------------------------------------------------------------------

    def infoPressed(self) -> None:
        """
        Build 0007, device test round 5 -- PlaylistScreen previously
        had no INFO handling at all, showing Enigma2's "unhandled
        key" indicator (confirmed on OpenATV). Shows Information for
        whichever panel/entry currently has focus -- the same
        Information a track/playlist's own context menu already
        offers, just reachable directly.
        """

        logger.verbose("[Playlist] INFO pressed.")

        if self._focus == "playlists":

            if self._current_playlist:

                self._showPlaylistInformation()

            return

        if not self._current_tracks:
            return

        index = self["tracks"].getSelectedIndex()

        if 0 <= index < len(self._current_tracks):

            self._trackMenuChosen(("Information", "information"), index, self._current_tracks[index])

    # ------------------------------------------------------------------

    def helpPressed(self) -> None:
        """
        Build 0008 -- opens HelpScreen with PlaylistScreen's own
        context-sensitive help document.
        """

        logger.verbose("[Playlist] HELP pressed.")

        title, content = help_manager.getHelp("playlistscreen")

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------

    def _openPlaylistMenu(self) -> None:

        if not self._current_playlist:

            self._openCreationMenu()

            return

        if self._current_entry_type == "radio":

            choices = [
                (_("Play"), "play"),
                (_("Rename"), "rename"),
                (_("Delete"), "delete"),
                (_("Information"), "information"),
                (_("Create New"), "create"),
                (_("Cancel"), "cancel"),
            ]

        else:

            choices = [
                (_("Play"), "play"),
                (_("Rename"), "rename"),
                (_("Delete"), "delete"),
                (_("Export"), "export"),
                (_("Information"), "information"),
                (_("Create New"), "create"),
                (_("Cancel"), "cancel"),
            ]

        self.session.openWithCallback(
            self._playlistMenuChosen,
            ChoiceBox,
            title=self._current_playlist,
            list=choices,
        )

    # ------------------------------------------------------------------

    def _playlistMenuChosen(self, choice) -> None:

        if choice is None:
            return

        action = choice[1]

        if action == "play":

            self._playCurrentPlaylist()

        elif action == "rename":

            self._promptText(_("New playlist name"), self._current_playlist, self._renamePlaylist)

        elif action == "delete":

            self._confirmDeletePlaylist()

        elif action == "export":

            path = playlist_manager.exportPlaylist(self._current_playlist)

            if path:

                self.session.open(MessageBox, f"{_('Exported')}: {path}", MessageBox.TYPE_INFO)

        elif action == "information":

            self._showPlaylistInformation()

        elif action == "create":

            self._openCreationMenu()

    # ------------------------------------------------------------------

    def _openTrackMenu(self) -> None:

        if not self._current_tracks:
            return

        index = self["tracks"].getSelectedIndex()

        if not (0 <= index < len(self._current_tracks)):
            return

        entry = self._current_tracks[index]

        if self._current_entry_type == "radio":

            choices = [
                (_("Play"), "play"),
                (_("Remove from Playlist"), "remove"),
                (_("Information"), "information"),
                (_("Cancel"), "cancel"),
            ]

            title = entry.get("name", "Unknown")

        else:

            choices = [
                (_("Play"), "play"),
                (_("Remove from Playlist"), "remove"),
                (_("Move Up"), "move_up"),
                (_("Move Down"), "move_down"),
                (_("Information"), "information"),
                (_("Cancel"), "cancel"),
            ]

            title = entry.get("title", entry.get("file_name", "Unknown"))

        self.session.openWithCallback(
            lambda choice: self._trackMenuChosen(choice, index, entry),
            ChoiceBox,
            title=title,
            list=choices,
        )

    # ------------------------------------------------------------------

    def _trackMenuChosen(self, choice, index, entry) -> None:

        if choice is None:
            return

        action = choice[1]

        is_radio = self._current_entry_type == "radio"

        if action == "play":

            self._playFromTrack(index)

        elif action == "remove":

            if is_radio:

                internetradio_manager.removeFavorite(entry.get("stationuuid"), self._current_playlist)

            else:

                playlist_manager.removeTrack(self._current_playlist, index)

            self._reloadTracks()

        elif action == "move_up" and not is_radio:

            playlist_manager.moveTrack(self._current_playlist, index, -1)

            self._reloadTracks()

        elif action == "move_down" and not is_radio:

            playlist_manager.moveTrack(self._current_playlist, index, 1)

            self._reloadTracks()

        elif action == "information":

            if is_radio:

                lines = [
                    entry.get("name", "Unknown"),
                    "",
                    f"{_('Codec')}: {entry.get('codec', 'Unknown')}",
                    f"{_('Country')}: {entry.get('country', 'Unknown')}",
                    f"{_('Tags')}: {entry.get('tags', 'Unknown')}",
                ]

            else:

                lines = [
                    entry.get("title", "Unknown"),
                    "",
                    f"Artist: {entry.get('artist', 'Unknown')}",
                    f"Path: {entry.get('path', 'Unknown')}",
                ]

            self.session.open(MessageBox, "\n".join(lines), MessageBox.TYPE_INFO)

# End of Part 2
    # ------------------------------------------------------------------
    # Playback (delegates to PlaybackController via MainScreen's shared
    # instance -- PlaylistScreen never talks to ServiceController)
    # ------------------------------------------------------------------

    def _playCurrentPlaylist(self) -> None:

        self._playFromTrack(0)

    # ------------------------------------------------------------------

    def _playFromTrack(self, start_index: int) -> None:

        if self._playback is None or not self._current_playlist:
            return

        if self._current_entry_type == "radio":

            self._playRadioListEntry(start_index)

            return

        queue = playlist_manager.generatePlaybackQueue(self._current_playlist)

        if not queue:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        start_index = min(start_index, len(queue) - 1)

        self._log(f"Play Playlist: {self._current_playlist} (starting at {start_index})")

        if self._playback.playQueue(queue, start_index):

            self.close(("played", self._current_playlist))

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------

    def _playRadioListEntry(self, index: int) -> None:
        """
        Play the station at `index` in the current radio favorite
        list (Build 0007, device test round 3). Mirrors
        RadioBrowserScreen._playStation() -- PlaylistScreen prepares
        and plays the stream itself rather than depending on
        MainScreen, matching how it already plays local queues
        directly.
        """

        stations = internetradio_manager.getFavorites(self._current_playlist)

        if not stations or not (0 <= index < len(stations)):

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        station = stations[index]

        result = internetradio_manager.prepareStream(station)

        if result is None or not self._playback.playStream(result["url"], result["station"]):

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        self._log(f"Play Radio List: {self._current_playlist} -> {station.get('name', '?')}")

        self.close(("played", None))

    # ------------------------------------------------------------------
    # Playlist Creation (PLAYLISTSCREEN_SPEC.md "Playlist Creation")
    # ------------------------------------------------------------------

    def _openCreationMenu(self) -> None:

        choices = [
            (_("Empty Playlist"), "empty"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            self._creationMenuChosen,
            ChoiceBox,
            title=_("Create playlist"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _creationMenuChosen(self, choice) -> None:

        if choice is None or choice[1] != "empty":
            return

        self._promptText(_("New playlist name"), "", self._createPlaylist)

    # ------------------------------------------------------------------

    def _createPlaylist(self, name) -> None:
        """
        "Create New" always creates a LOCAL playlist -- radio favorite
        lists have their own creation flow in RadioBrowserScreen
        (Add to Favorites -> Create New), which also lets a station be
        added to the new list in the same step.
        """

        if not name:
            return

        if playlist_manager.createPlaylist(name):

            self._reloadPlaylists()

            self._selectEntryByTypeAndName("local", name)

        else:

            self.session.open(MessageBox, _("Playlist already exists"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------

    def _renamePlaylist(self, new_name) -> None:

        if not new_name or new_name == self._current_playlist:
            return

        if self._current_entry_type == "radio":

            ok = internetradio_manager.renameFavoriteList(self._current_playlist, new_name)

        else:

            ok = playlist_manager.renamePlaylist(self._current_playlist, new_name)

        if ok:

            entry_type = self._current_entry_type

            self._reloadPlaylists()

            self._selectEntryByTypeAndName(entry_type, new_name)

    # ------------------------------------------------------------------

    def _confirmDeletePlaylist(self) -> None:

        self.session.openWithCallback(
            self._deleteConfirmed,
            MessageBox,
            f"{_('Delete')} \"{self._current_playlist}\"?",
            MessageBox.TYPE_YESNO,
        )

    # ------------------------------------------------------------------

    def _deleteConfirmed(self, confirmed) -> None:

        if not confirmed or not self._current_playlist:
            return

        if self._current_entry_type == "radio":

            internetradio_manager.deleteFavoriteList(self._current_playlist)

        else:

            playlist_manager.deletePlaylist(self._current_playlist)

        self._reloadPlaylists()

    # ------------------------------------------------------------------

    def _showPlaylistInformation(self) -> None:

        type_label = _("Internet Radio") if self._current_entry_type == "radio" else _("Playlists")

        lines = [
            self._current_playlist,
            "",
            f"{_('Type')}: {type_label}",
            f"{_('Tracks') if self._current_entry_type != 'radio' else _('Stations')}: {len(self._current_tracks)}",
        ]

        self.session.open(MessageBox, "\n".join(lines), MessageBox.TYPE_INFO)

    # ------------------------------------------------------------------

    def _selectEntryByTypeAndName(self, entry_type, name) -> None:

        if (entry_type, name) in self._entries:

            self._selectEntry(self._entries.index((entry_type, name)))

    # ------------------------------------------------------------------

    def _promptText(self, title, initial_text, callback) -> None:

        self.session.openWithCallback(
            lambda text: callback(text) if text else None,
            VirtualKeyBoard,
            title=title,
            text=initial_text,
        )

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[Playlist] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "playlists"):
            return

        self.close(action_id)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[Playlist] EXIT pressed.")

        self._log("Closing")

        self._log("Closed")

        self.close(None)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"PlaylistScreen(initialized={self._initialized})"


# ==============================================================================
# End of file
# ==============================================================================

# ==============================================================================
#
# MediaPlayer3
#
# File        : browserscreen.py
#
# Description :
#
#     BrowserScreen
#
#     Local file browsing and playlist building. BrowserScreen is a
#     *temporary* screen: it is opened from MainScreen when the user
#     wants to browse local storage, and it returns to MainScreen
#     either after playback has started or on EXIT/MENU.
#
#     Build 0010 -- three-column browsing model (BUILD_0010_PLAN.md
#     "Local File Browser" / "File Browser Actions"), structurally
#     following PodcastScreen's own three-column pattern (same
#     LEFT/RIGHT column-focus model, ChoiceBox action menus, two-tier
#     column header highlighting):
#
#         Directories | Files | Playlist
#
#     The left column browses the directory tree (subdirectories of
#     the current root, plus ".." to go up). The middle column
#     previews the supported audio files inside whichever directory is
#     currently *selected* in the left column (auto-updates on
#     selection change, exactly like PodcastScreen's Episodes column
#     already does for the podcast selected in Available/Subscribed --
#     BUILD_0010_PLAN.md: "The middle column contains files in the
#     selected directory."). The right column shows the current
#     working playlist, which OK's per-column action menus add to.
#
#     BUILD_0010_PLAN.md's own "File Browser Actions" section lists
#     OK's per-column action menu contents but -- confirmed with the
#     user directly, since LEFT/RIGHT is already committed to column
#     switching and LEFT/RIGHT/OK is otherwise fully accounted for --
#     does not say how a directory is actually *entered* (descended).
#     Fixed by adding one extra item, "Open directory", to the
#     Directories column's OK menu alongside the plan's own "Add
#     entire directory to playlist" -- deliberately a small, explicit
#     deviation from the plan's literal wording rather than a silent
#     one. Two further small, equally-flagged additions for the same
#     "this literally cannot function without it" reason:
#
#       - PLAY (existing hardware key, used throughout this project)
#         still starts playback directly -- from Directories (queue =
#         entire previewed directory, like Build 0007's "Play Folder"),
#         Files (queue = previewed directory, starting at the selected
#         file) or Playlist (the current playlist, starting at the
#         selected track). BUILD_0010_PLAN.md's OK-menu lists never
#         include a "Play" item themselves (this screen becomes
#         primarily a playlist-building tool, per the plan's own
#         framing), so without this, nothing in the new design could
#         ever actually start playback -- and the plan is explicit
#         that "the existing playback and playlist handling shall
#         remain unchanged".
#       - INFO opens a "Select Playlist" picker (existing playlist,
#         or create new), settable at any time, not just implicitly on
#         first Add. Without this there would be no way to switch the
#         Playlist column to a different existing playlist once one
#         had been chosen.
#
#     BrowserScreen receives MainScreen's shared PlaybackController
#     instance and forwards playback requests to it -- it never talks
#     to ServiceController, Compatibility or Enigma2 playback services
#     directly (BROWSERSCREEN_SPEC.md section 8).
#
# Implements :
#
#     BROWSERSCREEN_SPEC.md v0.7 (three-column redesign pending a
#     matching spec revision -- see docs/Claude_notes_build0010.txt,
#     Round 6)
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
# 2026-07-04  Build 0001
#   - Initial version (as browser.py, application's primary screen).
#
# 2026-07-10  Build 0003 Revision 1
#   - Layered architecture: playback delegated to PlaybackController.
#
# 2026-07-12  Build 0004
#   - Renamed from browser.py to browserscreen.py.
#   - No longer the primary application window -- MainScreen is.
#   - No longer creates its own PlaybackController; receives the shared
#     instance from MainScreen so playback state survives navigation.
#
# 2026-07-19  Build 0007
#   - Added an INFO context menu for folder/file/playlist-file actions.
#
# 2026-07-28  Build 0008
#   - Added HELP key handling.
#
# 2026-08-09  Build 0010 (round 6)
#   - Full redesign: single-column file list + INFO context menu
#     replaced with the three-column Directories | Files | Playlist
#     model described above. Old single-column implementation is kept
#     in source control history (not reproduced here) rather than
#     inline, per this project's own convention of not carrying dead
#     code forward across a full-screen rewrite.
# ------------------------------------------------------------------------------

"""
browserscreen -- three-column local file browser (Directories | Files |
Playlist), per BUILD_0010_PLAN.md "Local File Browser" / "File Browser
Actions".
"""

from __future__ import annotations

import os
from typing import List, Optional

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from .compatibility import compatibility
from .config import config_manager
from .constants import PLAYLIST_FILE_EXTENSIONS, SUPPORTED_AUDIO_EXTENSIONS
from .help_manager import help_manager
from .help_screen import HelpScreen
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

COLUMNS = ("directories", "files", "playlist")

# CHANNEL UP/DOWN page-step, matching RadioBrowserScreen/PodcastScreen's
# own PAGE_STEP convention for long lists.
PAGE_STEP = 10


def _defaultPlayPlaylistName() -> str:
    """
    Build 0010, device test round 6 -- user request: "Ylikirjoitus-
    riskin voi välttää luomalla suosikin Tiedostot, jota muokataan
    oletuksena." Directories/Files columns' "Play" action (Round 8)
    originally named the created/overwritten playlist after the
    folder or file itself -- risking a silent overwrite of an
    existing, unrelated, hand-curated playlist that happened to share
    that name. Fixed: always use this one fixed, reserved playlist
    name instead (the existing "Files"/"Tiedostot" translation,
    reused rather than inventing a new string) -- only this single
    dedicated playlist is ever touched by quick-play, never anything
    the user named themselves. A function (not a module-level
    constant) since _() needs localization_manager already
    initialized, which may not be true yet at import time.
    """

    return _("Files")


class BrowserScreen(Screen):
    """
    Local file browsing and playlist building
    (BUILD_0010_PLAN.md "Local File Browser").

    BrowserScreen is temporary: it is always opened from MainScreen and
    always returns to it.
    """

    SPECIFICATION_VERSION = "0.7"
    ARCHITECTURE_VERSION = "0.3"

    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 540

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Three equal-width columns (Directories | Files | Playlist),
        each with a highlighted title and a scrollable list below --
        same layout approach and design canvas as PodcastScreen's own
        _buildSkin(), for a consistent look between the project's
        three-column browsers.
        """

        sx = width / BrowserScreen.DESIGN_WIDTH
        sy = height / BrowserScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR
        active_color = to_opaque_skin_color(skin_manager.getColor("selection_background", "#0056B3"))
        inactive_color = to_opaque_skin_color(skin_manager.getColor("inactive_highlight", "#ADD8E6"))

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        column_width = 220

        def column_x(index):
            return 20 + index * (column_width + 10)

        columns_xml = ""

        titles = (_("Directories"), _("Files"), _("Playlist"))

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
        <screen name="MediaPlayer3BrowserScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Browser">

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

    def __init__(self, session, playback_controller):
        """
        `playback_controller` is MainScreen's shared PlaybackController
        instance -- BrowserScreen never creates its own
        (BROWSERSCREEN_SPEC.md section 8).
        """

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        self.session = session

        self._playback = playback_controller

        self._focus = "directories"

        # Build 0010 -- identified during the Build 0009 exception
        # audit: an unavailable configured startup directory must
        # never crash this screen outright (a disconnected USB drive
        # or unmounted network share is a normal, expected situation,
        # not a bug). Falls back to "/" (always exists on any
        # Linux-based system).
        startup_directory = config_manager.getStartupDirectory()

        if not os.path.isdir(startup_directory):

            logger.warning(f"[BrowserScreen] Startup directory unavailable, falling back to '/': {startup_directory}")

            startup_directory = "/"

        self._current_root = startup_directory

        self._directory_entries: List[str] = []  # display names, ".." first if present

        self._current_playlist_name: Optional[str] = None

        self._playlist_tracks: List[dict] = []

        self._files_in_preview: List[str] = []

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[BrowserScreen] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
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
                "PLAY: Play   INFO: Select Playlist   HELP: Help   "
                "MENU: Menu   EXIT: Back"
            )
        )

        self._reloadDirectoryColumn()

        actions = {
            "ok": self.okPressed,
            "cancel": self.exitPressed,
            "play": self.playPressed,
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
            actions[action_name] = self.selectPlaylistPressed

        for action_name in compatibility.getHelpKeyActionNames():
            actions[action_name] = self.helpPressed

        for action_name in compatibility.getPvrKeyActionNames():
            actions[action_name] = self.exitPressed

        self["actions"] = ActionMap(
            [
                "OkCancelActions",
                "DirectionActions",
                "MediaPlayerActions",
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
    # Directory Handling
    # ------------------------------------------------------------------

    def _reloadDirectoryColumn(self) -> None:
        """
        Populate the Directories column with the subdirectories of
        self._current_root, ".." first if not at the filesystem root.
        """

        entries = [".."] if self._current_root not in ("/", "") else []

        try:
            for entry in sorted(os.listdir(self._current_root), key=str.lower):

                if entry.startswith("."):
                    continue

                if os.path.isdir(os.path.join(self._current_root, entry)):

                    entries.append(entry)

        except OSError as error:

            self._log(f"Unable to scan directory: {self._current_root} ({error})")

        self._directory_entries = entries

    # ------------------------------------------------------------------

    def _selectedDirectoryPath(self) -> Optional[str]:
        """
        Full path corresponding to the currently selected entry in the
        Directories column, or None if nothing usable is selected.
        ".." resolves to the parent of the current root.
        """

        index = self["directories_list"].getSelectedIndex()

        if not (0 <= index < len(self._directory_entries)):
            return None

        entry = self._directory_entries[index]

        if entry == "..":

            return os.path.dirname(self._current_root.rstrip("/")) or "/"

        return os.path.join(self._current_root, entry)

    # ------------------------------------------------------------------

    def _openSelectedDirectory(self) -> None:
        """
        Descend into (or go up out of) the selected Directories entry
        -- the "Open directory" action added to the OK menu (see this
        file's own header comment for why).
        """

        target = self._selectedDirectoryPath()

        if target is None or not os.path.isdir(target):

            self.session.open(MessageBox, _("Directory not available."), MessageBox.TYPE_ERROR)

            return

        self._current_root = target

        self._reloadDirectoryColumn()

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _updateDisplay(self) -> None:

        self["directories_list"].setList(self._directory_entries)

        preview_directory = self._previewDirectory()

        files = playlist_manager.listDirectoryAudioFiles(preview_directory) if preview_directory else []

        self._files_in_preview = files

        self["files_list"].setList([os.path.basename(path) for path in files])

        self["playlist_list"].setList(
            [self._formatTrackEntry(track) for track in self._playlist_tracks]
        )

        titles = {
            "directories": _("Directories"),
            "files": _("Files"),
            "playlist": (
                _("Playlist: %s") % self._current_playlist_name
                if self._current_playlist_name
                else _("Playlist")
            ),
        }

        for column_name, title_text in titles.items():

            marker = "> " if column_name == self._focus else ""

            self[f"{column_name}_title"].setText(f"{marker}{title_text}")

        self._updateColumnHighlighting()

        self["status"].setText(self._current_root)

    # ------------------------------------------------------------------

    def _formatTrackEntry(self, track: dict) -> str:

        artist = track.get("artist", "Unknown")
        title = track.get("title", track.get("file_name", "Unknown"))

        if artist and artist != "Unknown":

            return f"{artist} - {title}"

        return title

    # ------------------------------------------------------------------

    def _previewDirectory(self) -> Optional[str]:
        """
        The directory whose files the Files column currently previews
        -- BUILD_0010_PLAN.md "The middle column contains files in the
        selected directory": tracks the Directories column's current
        *selection*, live, the same way PodcastScreen's Episodes
        column already tracks the selected podcast, without requiring
        "Open directory" first.
        """

        index = self["directories_list"].getSelectedIndex()

        if not (0 <= index < len(self._directory_entries)):

            return self._current_root

        entry = self._directory_entries[index]

        if entry == "..":

            return os.path.dirname(self._current_root.rstrip("/")) or "/"

        return os.path.join(self._current_root, entry)

    # ------------------------------------------------------------------

    def _updateColumnHighlighting(self) -> None:
        """
        Two-tier column header highlighting -- see PodcastScreen's own
        _updateColumnHighlighting() docstring for why hide()/show() on
        pre-positioned rectangles is used instead of a runtime widget
        recolour.
        """

        for column_name in COLUMNS:

            is_active = column_name == self._focus

            try:
                self[f"{column_name}_title_bg_normal"].hide() if is_active else self[f"{column_name}_title_bg_normal"].show()

                self[f"{column_name}_title_bg_active"].show() if is_active else self[f"{column_name}_title_bg_active"].hide()

            except Exception as error:

                logger.verbose(f"[BrowserScreen] Unable to set column highlight visibility: {error}")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def focusPrevious(self) -> None:

        logger.verbose("[BrowserScreen] LEFT pressed.")

        self._focus = COLUMNS[(COLUMNS.index(self._focus) - 1) % len(COLUMNS)]

        self._updateDisplay()

    # ------------------------------------------------------------------

    def focusNext(self) -> None:

        logger.verbose("[BrowserScreen] RIGHT pressed.")

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
        Moving within Directories live-updates the Files preview
        (BUILD_0010_PLAN.md, see _previewDirectory()). Moving within
        Files or Playlist doesn't reload anything else.
        """

        if self._focus != "directories":
            return

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Playback (PLAY key -- see this file's own header comment)
    # ------------------------------------------------------------------

    def playPressed(self) -> None:

        logger.verbose("[BrowserScreen] PLAY pressed.")

        if self._focus == "directories":

            self._playSelectedDirectory()

        elif self._focus == "files":

            self._playSelectedFile()

        elif self._focus == "playlist":

            self._playCurrentPlaylist()

    # ------------------------------------------------------------------

    def _playSelectedDirectory(self) -> None:
        """
        Recursively play every supported audio file under the
        previewed directory (Build 0007's "Play Folder", carried
        forward unchanged in behaviour).
        """

        directory = self._previewDirectory()

        if not directory or not os.path.isdir(directory):

            self.session.open(MessageBox, _("Directory not available."), MessageBox.TYPE_ERROR)

            return

        collected = []

        try:
            for root, _directories, files in os.walk(directory):

                for entry in sorted(files, key=str.lower):

                    if entry.startswith("."):
                        continue

                    if entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):

                        collected.append(os.path.join(root, entry))

        except OSError as error:

            self._log(f"Unable to scan directory for playback: {directory} ({error})")

        if not collected:

            self.session.open(MessageBox, _("No playable files found."), MessageBox.TYPE_ERROR)

            return

        self._log(f"Play directory: {directory} ({len(collected)} track(s))")

        if self._playback.playQueue(collected, 0):

            self.close("played")

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------

    def _playSelectedFile(self) -> None:

        index = self["files_list"].getSelectedIndex()

        if not (0 <= index < len(self._files_in_preview)):

            return

        queue = self._files_in_preview

        self._log(f"Play file: {queue[index]}")

        if self._playback.playQueue(queue, index):

            self.close("played")

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------

    def _playCurrentPlaylist(self) -> None:

        if not self._current_playlist_name:

            self.session.open(MessageBox, _("No playlist selected."), MessageBox.TYPE_INFO, timeout=3)

            return

        index = self["playlist_list"].getSelectedIndex()

        if index < 0:
            index = 0

        queue = playlist_manager.generatePlaybackQueue(self._current_playlist_name)

        if not queue:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        start_index = index if index < len(queue) else 0

        self._log(f"Play playlist: {self._current_playlist_name} ({len(queue)} track(s))")

        if self._playback.playQueue(queue, start_index):

            self.close(("played", self._current_playlist_name))

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------
    # Actions (OK -- BUILD_0010_PLAN.md "File Browser Actions")
    # ------------------------------------------------------------------

    def okPressed(self) -> None:

        logger.verbose("[BrowserScreen] OK pressed.")

        if self._focus == "directories":

            self._directoryMenu()

        elif self._focus == "files":

            self._fileMenu()

        elif self._focus == "playlist":

            self._playlistItemMenu()

    # ------------------------------------------------------------------

    def _directoryMenu(self) -> None:

        target = self._selectedDirectoryPath()

        if target is None:
            return

        index = self["directories_list"].getSelectedIndex()

        label = self._directory_entries[index] if 0 <= index < len(self._directory_entries) else "?"

        choices = [(_("Open directory"), "open")]

        # ".." only makes sense to open, not to bulk-add/play -- "play/
        # add the entire parent directory" isn't a meaningful action
        # here and would recurse back into this browser's own current
        # directory a second time.
        if label != "..":

            choices.append((_("Play"), "play"))

            choices.append((_("Add entire directory to playlist"), "add"))

        choices.append((_("Cancel"), "cancel"))

        self.session.openWithCallback(
            lambda choice: self._directoryMenuChosen(choice, target),
            ChoiceBox,
            title=label,
            list=choices,
        )

    # ------------------------------------------------------------------

    def _directoryMenuChosen(self, choice, target: str) -> None:

        if choice is None or choice[1] == "cancel":
            return

        if choice[1] == "open":

            self._openSelectedDirectory()

        elif choice[1] == "play":

            self._playDirectoryAsPlaylist(target)

        elif choice[1] == "add":

            self._requireCurrentPlaylist(lambda name: self._addDirectoryToPlaylist(name, target))

    # ------------------------------------------------------------------

    def _playDirectoryAsPlaylist(self, directory: str) -> None:
        """
        Build 0010, device test round 5 -- Directories column's "Play"
        action: "Jos valitsee kansion kohdalla soita, niin se voisi
        luoda suoraan soittolistan koko kansiosta ja alkaa
        soittamaan." Round 6: uses the fixed default playlist name
        (_defaultPlayPlaylistName(), "Files"/"Tiedostot") rather than
        the folder's own name, after a real overwrite-risk concern --
        see that function's own docstring, and
        playlist_manager.createPlaylistFromFolder()'s, for the
        overwrite-by-design reasoning this still relies on.
        """

        playlist_name = _defaultPlayPlaylistName()

        count = playlist_manager.createPlaylistFromFolder(playlist_name, directory)

        if count <= 0:

            self.session.open(MessageBox, self._describeAddFailure(), MessageBox.TYPE_ERROR)

            return

        self._startPlaylistPlayback(playlist_name)

    # ------------------------------------------------------------------

    def _describeAddFailure(self) -> str:
        """
        Build 0010, device test round 20 (OpenPLI, disk-full test box):
        a folder/file add or "Play" action returning 0/False can mean
        either "genuinely nothing to add" or "found files, but saving
        the playlist itself failed" (disk full, permissions, ...) --
        these need different messages, or a real write failure looks
        identical to an empty folder and the actual, fixable problem
        (device out of storage) never reaches the user. Checks
        playlist_manager's own getLastSaveError() (set on any
        savePlaylist() failure, which every "add"/"Play" action here
        eventually goes through) to tell them apart.
        """

        error = playlist_manager.getLastSaveError()

        if error:

            return _("Save failed: %s") % error

        return _("No playable files found.")

    # ------------------------------------------------------------------

    def _addDirectoryToPlaylist(self, playlist_name: str, directory: str) -> None:

        count = playlist_manager.addFolder(playlist_name, directory)

        self._afterAdd(playlist_name, count)

    # ------------------------------------------------------------------

    def _fileMenu(self) -> None:

        index = self["files_list"].getSelectedIndex()

        if not (0 <= index < len(self._files_in_preview)):
            return

        filepath = self._files_in_preview[index]

        choices = [
            (_("Play"), "play"),
            (_("Add this file"), "add_one"),
            (_("Add this file and remaining files in directory"), "add_remaining"),
            (_("Add all files from directory"), "add_all"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._fileMenuChosen(choice, filepath),
            ChoiceBox,
            title=os.path.basename(filepath),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _fileMenuChosen(self, choice, filepath: str) -> None:

        if choice is None or choice[1] == "cancel":
            return

        directory = os.path.dirname(filepath)

        if choice[1] == "play":

            self._playFileAsPlaylist(filepath)

        elif choice[1] == "add_one":

            self._requireCurrentPlaylist(
                lambda name: self._afterAdd(name, 1 if playlist_manager.addTrack(name, filepath) else 0)
            )

        elif choice[1] == "add_remaining":

            self._requireCurrentPlaylist(
                lambda name: self._afterAdd(
                    name, playlist_manager.addFilesInDirectory(name, directory, from_filename=filepath)
                )
            )

        elif choice[1] == "add_all":

            self._requireCurrentPlaylist(
                lambda name: self._afterAdd(name, playlist_manager.addFilesInDirectory(name, directory))
            )

    # ------------------------------------------------------------------

    def _afterAdd(self, playlist_name: str, count: int) -> None:

        self._log(f"Added {count} track(s) to playlist: {playlist_name}")

        if count <= 0:

            box_type = MessageBox.TYPE_ERROR if playlist_manager.getLastSaveError() else MessageBox.TYPE_INFO

            self.session.open(MessageBox, self._describeAddFailure(), box_type, timeout=3)

        elif count == 1:

            self.session.open(
                MessageBox,
                _("Added to playlist: %s") % playlist_name,
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        else:

            self.session.open(
                MessageBox,
                _("Added %d tracks to playlist: %s") % (count, playlist_name),
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        if self._current_playlist_name == playlist_name:

            self._playlist_tracks = playlist_manager.loadPlaylist(playlist_name)

            self._updateDisplay()

    # ------------------------------------------------------------------

    def _playFileAsPlaylist(self, filepath: str) -> None:
        """
        Build 0010, device test round 5 -- Files column's "Play"
        action: "Tiedoston kohdalla voisi luoda soittolistan vain
        siitä tiedostosta ja alkaa soittamaan." Round 6: uses the
        fixed default playlist name (_defaultPlayPlaylistName(),
        "Files"/"Tiedostot") rather than the file's own basename --
        see that function's own docstring for why (same overwrite-risk
        concern as the Directories column's "Play").
        """

        playlist_name = _defaultPlayPlaylistName()

        if not playlist_manager.createPlaylistFromFile(playlist_name, filepath):

            self.session.open(MessageBox, self._describeAddFailure(), MessageBox.TYPE_ERROR)

            return

        self._startPlaylistPlayback(playlist_name)

    # ------------------------------------------------------------------

    def _startPlaylistPlayback(self, playlist_name: str) -> None:
        """
        Shared by both new "Play" actions (Directories/Files columns):
        loads `playlist_name` fresh and starts playback from the
        beginning, closing with ("played", playlist_name) -- same
        convention as the Playlist column's own PLAY/OK handling, so
        MainScreen's "Back" (BUILD_0010_PLAN.md "MainScreen OK Menu")
        returns here to BrowserScreen, and LEFT/RIGHT favorites-view
        playlist cycling picks it up too.
        """

        queue = playlist_manager.generatePlaybackQueue(playlist_name)

        if not queue or not self._playback.playQueue(queue, 0):

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        self._log(f"Play: {playlist_name} ({len(queue)} track(s))")

        self.close(("played", playlist_name))

    # ------------------------------------------------------------------

    def _playlistItemMenu(self) -> None:

        if not self._current_playlist_name:

            self.selectPlaylistPressed()

            return

        index = self["playlist_list"].getSelectedIndex()

        if not (0 <= index < len(self._playlist_tracks)):
            return

        choices = [
            (_("Play"), "play"),
            (_("Remove"), "remove"),
            (_("Move up"), "up"),
            (_("Move down"), "down"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._playlistItemMenuChosen(choice, index),
            ChoiceBox,
            title=self._formatTrackEntry(self._playlist_tracks[index]),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _playlistItemMenuChosen(self, choice, index: int) -> None:

        if choice is None or choice[1] == "cancel":
            return

        name = self._current_playlist_name

        if choice[1] == "play":

            # Build 0010, device test round 5: "Soittolistanäkymässä
            # soita voisi alkaa suoraan soittamaan listalla olevat
            # kappaleet valitusta kappaleesta eteenpäin." Same queue-
            # from-selected-index logic PLAY already used
            # (_playCurrentPlaylist()) -- just reachable from OK too
            # now, with the selection already known from this menu.
            self._playCurrentPlaylist()

            return

        elif choice[1] == "remove":

            playlist_manager.removeTrack(name, index)

        elif choice[1] == "up":

            playlist_manager.moveTrack(name, index, -1)

        elif choice[1] == "down":

            playlist_manager.moveTrack(name, index, 1)

        self._playlist_tracks = playlist_manager.loadPlaylist(name)

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Current playlist selection (INFO -- see this file's own header
    # comment for why this exists)
    # ------------------------------------------------------------------

    def selectPlaylistPressed(self) -> None:

        logger.verbose("[BrowserScreen] INFO pressed.")

        self._requireCurrentPlaylist(self._setCurrentPlaylist, force_prompt=True)

    # ------------------------------------------------------------------

    def _requireCurrentPlaylist(self, callback, force_prompt: bool = False) -> None:
        """
        Ensure a current playlist is set before running `callback(name)`.
        If one is already set and force_prompt is False, calls back
        immediately; otherwise opens the picker first.
        """

        if self._current_playlist_name and not force_prompt:

            callback(self._current_playlist_name)

            return

        names = playlist_manager.getPlaylistNames()

        choices = [(name, name) for name in names]

        choices.append((_("Create new playlist..."), "__new__"))
        choices.append((_("Cancel"), "__cancel__"))

        self.session.openWithCallback(
            lambda choice: self._playlistPickerChosen(choice, callback),
            ChoiceBox,
            title=_("Select playlist"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _playlistPickerChosen(self, choice, callback) -> None:

        if choice is None or choice[1] == "__cancel__":
            return

        if choice[1] == "__new__":

            self.session.openWithCallback(
                lambda text: self._newPlaylistNameEntered(text, callback),
                VirtualKeyBoard,
                title=_("New playlist name"),
                text="",
            )

            return

        self._setCurrentPlaylist(choice[1])

        callback(choice[1])

    # ------------------------------------------------------------------

    def _newPlaylistNameEntered(self, text, callback) -> None:

        if not text:
            return

        playlist_manager.createPlaylist(text)

        self._setCurrentPlaylist(text)

        callback(text)

    # ------------------------------------------------------------------

    def _setCurrentPlaylist(self, name: str) -> None:

        self._current_playlist_name = name

        self._playlist_tracks = playlist_manager.loadPlaylist(name)

        self._updateDisplay()

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def helpPressed(self) -> None:

        logger.verbose("[BrowserScreen] HELP pressed.")

        title, content = help_manager.getHelp("browserscreen")

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[BrowserScreen] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "browser"):
            return

        self._log("Returning to MainScreen.")

        self.close(action_id)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[BrowserScreen] EXIT/PVR pressed.")

        self._log("Closing")

        self.close(None)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"BrowserScreen(initialized={self._initialized})"


# ==============================================================================
#
# Build Notes
#
# BrowserScreen responsibilities:
#
#   - Directory browsing (Directories column)
#   - File preview and selection (Files column)
#   - Playlist building (Playlist column, via OK's per-column menus)
#   - Forwarding playback requests to the shared PlaybackController
#   - Returning to MainScreen
#
# BrowserScreen is intentionally NOT responsible for:
#
#   - Playback implementation
#   - Playback status display (MainScreen's StatusBar handles that)
#   - Enigma2 service handling
#   - Platform compatibility
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

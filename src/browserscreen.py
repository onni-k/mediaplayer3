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
#     Directory browsing and media file selection. BrowserScreen is a
#     *temporary* screen: it is opened from MainScreen when the user
#     wants to browse available media, and it returns to MainScreen
#     either after a successful file selection or on PVR/EXIT.
#
#     BrowserScreen receives MainScreen's shared PlaybackController
#     instance and forwards playback requests to it -- it never talks
#     to ServiceController, Compatibility or Enigma2 playback services
#     directly (BROWSERSCREEN_SPEC.md section 8).
#
# Implements :
#
#     BROWSERSCREEN_SPEC.md v0.1
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
#   - PVR now returns to MainScreen without changing playback, instead
#     of stopping it (BROWSERSCREEN_SPEC.md section 6).
#   - EXIT now always returns to MainScreen (directory-up navigation is
#     handled by selecting the ".." entry via OK, as FileList already
#     provides -- BROWSERSCREEN_SPEC.md section 6 lists only OK for
#     directory navigation).
#   - MENU now opens the shared MainMenu instead of doing nothing.
#
# 2026-07-13  Build 0004
#   - PVR key now bound via both "showMovies" and "showInfobar" action
#     names, matching the fix in mainscreen.py.
#   - Directory entries are now always listed with a trailing slash on
#     `directory` (see paths.ensure_trailing_slash()), fixing a real
#     device bug where a subdirectory (e.g. "flac") was misclassified
#     as a file when reached via the configured startup directory.
#   - Added verbose-only (Developer Mode VERBOSE) directory/selection
#     logging matching docs/log_example1.txt: "Enter directory",
#     "Found", "Selected" and "Starting playback".
#
# 2026-07-14  Build 0005
#   - playSelected() now builds a Playback Queue from every supported
#     media file in the current directory (PLAYBACK_QUEUE_SPEC.md) and
#     hands it to PlaybackController.playQueue() instead of calling
#     play() with a single filename. BrowserScreen never touches the
#     queue again after handing it over -- PlaybackController owns
#     navigation within it from that point on.
#
# 2026-07-14  Build 0005 (device test fix)
#   - _buildQueueFromCurrentDirectory() now matches the selected file
#     by basename instead of full-path equality. A real device test
#     showed FileList.getFilename()'s path never matched this
#     os.path.join()-built queue exactly, so the "not found" fallback
#     fired on every single selection and only the first track in the
#     directory ever actually played, regardless of what the user
#     picked (see docs/Claude_notes_build0005.txt).
#
# 2026-07-19  Build 0007
#   - Added a context menu (INFO key, not OK -- OK's existing descend/
#     play behaviour is real-device verified and must not change):
#     folders get Play Folder/Add Folder to Playlist/Create Playlist,
#     audio files get Play/Add to Playlist/Information, playlist
#     files (.m3u/.m3u8) get Play Playlist/Import Playlist/
#     Information (PLAYLIST_MANAGER_SPEC.md "Browser Integration").
#     Uses standard Enigma2 ChoiceBox/VirtualKeyBoard screens -- no
#     custom menu UI needed.
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
from typing import Optional

from Components.ActionMap import ActionMap
from Components.Label import Label
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from .compatibility import compatibility
from .help_manager import help_manager
from .help_screen import HelpScreen
from .config import config_manager
from .constants import PLAYLIST_FILE_EXTENSIONS, SUPPORTED_AUDIO_EXTENSIONS
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
from .statusbar import StatusBar


class BrowserScreen(Screen):
    """
    Directory browsing and media file selection.

    BrowserScreen is temporary: it is always opened from MainScreen and
    always returns to it.
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.3"

    # Design canvas that the skin below is authored for; _buildSkin()
    # scales every position/size from this to the actual desktop
    # resolution (Build 0007, device test round 8 -- fullscreen for
    # every screen, following the pattern MainScreen established in
    # Build 0005).
    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 500

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build BrowserScreen's skin for an exact `width` x `height`
        window, scaling every coordinate from the 700x500 design
        resolution above -- same approach as
        MainScreen._buildSkin() (Build 0005), extended to every
        screen in Build 0007 device test round 8 so the box's own
        background never shows through around a small centered
        window, and so the theme's background colour (e.g. the new
        Gray theme, #A0A0A0) fills the whole display consistently.
        """

        sx = width / BrowserScreen.DESIGN_WIDTH
        sy = height / BrowserScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Regular;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3BrowserScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Browser">

            <widget name="status"
                    {rect(20, 10, 660, 30)}
                    {font(18)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="filelist"
                    {rect(20, 50, 660, 380)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="path"
                    {rect(20, 440, 660, 20)}
                    {font(14)}
                    halign="center"
                    valign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="hint"
                    {rect(20, 470, 660, 25)}
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

        # self.skin must be set *before* Screen.__init__() runs --
        # see BrowserScreen._buildSkin()'s docstring.
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

        logger.info("[BrowserScreen] %s", message)

    # ------------------------------------------------------------------

    def _logVerboseBlock(self, header: str, *content_lines: str) -> None:
        """
        Write a multi-line, verbose-only log block matching the format
        in docs/log_example1.txt:

            [BrowserScreen] Enter directory:
            /media/hdd/music

        Only written when Developer Mode is VERBOSE (logger.verbose());
        silent otherwise, so normal use never sees these.
        """

        text = "[BrowserScreen] " + header + "\n" + "\n".join(content_lines) + "\n"

        logger.verbose(text)

    # ------------------------------------------------------------------

    def _logDirectoryEntered(self, directory: str) -> None:
        """
        Log the "Enter directory" / "Found" verbose block for
        `directory` (docs/log_example1.txt).
        """

        self._logVerboseBlock("Enter directory:", directory)

        directory_count, file_count = self._countDirectoryContents(directory)

        self._logVerboseBlock(
            "Found:",
            f"{directory_count} directories",
            f"{file_count} files",
        )

    # ------------------------------------------------------------------

    def _countDirectoryContents(self, directory: str):
        """
        Return (directory_count, file_count) for `directory`.

        Counted independently of Components.FileList.FileList's own
        internal listing (used only for this verbose diagnostic log),
        so a listing quirk in FileList can never affect these counts.
        Best-effort: returns (0, 0) on any filesystem error (e.g.
        permission denied) rather than raising.
        """

        directory_count = 0
        file_count = 0

        try:

            for entry in os.listdir(directory):

                if os.path.isdir(os.path.join(directory, entry)):

                    directory_count += 1

                else:

                    file_count += 1

        except OSError as error:

            logger.verbose(f"[BrowserScreen] Unable to count directory contents: {error}")

        return directory_count, file_count

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        startup_directory = config_manager.getStartupDirectory()

        self["status"] = Label(_("Select a file to play"))
        self["path"] = Label("")
        self["hint"] = Label(
            "OK: Select   INFO: Options   PLAY: Play   PVR: Back   MENU: Menu   EXIT: Back"
        )

        self._statusbar = StatusBar(self["status"])

        self["filelist"] = compatibility.createFileList(startup_directory)

        self._logDirectoryEntered(startup_directory)

        # Note: hidden-file filtering is not applied yet -- see
        # compatibility.createFileList() for why the extra FileList
        # keyword arguments this would need cannot be assumed
        # supported on every image. "general.hidden_files" is
        # therefore stored but not yet enforced; wiring it up is
        # reserved for a future build.
        #
        # (Read without assigning to a variable -- Build 0006 imports
        # `_` as the localization translate() alias, and a local `_ =
        # ...` assignment anywhere in this method would shadow it for
        # the method's entire body, breaking _("Select a file to
        # play") above.)
        config_manager.get("general.hidden_files", False)

        actions = {
            "ok": self.okPressed,
            "cancel": self.exitPressed,
            "play": self.playSelected,
            "menu": self.menuPressed,
        }

        for action_name in compatibility.getPvrKeyActionNames():
            actions[action_name] = self.pvrPressed

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.openContextMenu

        for action_name in compatibility.getHelpKeyActionNames():
            actions[action_name] = self.helpPressed

        self["actions"] = ActionMap(
            [
                "OkCancelActions",
                "ColorActions",
                "MediaPlayerActions",
                "InfobarActions",
                "MenuActions",
                "InfoActions",
                "InfobarEPGActions",
                "HelpActions",
            ],
            actions,
            -1,
        )

        self._updateStatus()

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Directory Handling
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """
        Refresh current directory.
        """

        self["filelist"].refresh()

        self._updateStatus()

    # ------------------------------------------------------------------

    def openDirectory(self) -> None:
        """
        Enter the currently selected directory.
        """

        if self["filelist"].canDescent():

            self["filelist"].descent()

            self._log("Directory opened.")

            self._updateStatus()

            current_directory = self["filelist"].getCurrentDirectory()

            if current_directory:

                self._logDirectoryEntered(current_directory)

    # ------------------------------------------------------------------

    def getSelectedFilename(self):
        """
        Return the currently selected filename.

        Components.FileList.FileList.getSelection() returns a raw
        tuple (path, isDir, ...), not an object -- there is no
        .getPath() method on it. FileList already provides a safe
        helper for this: getFilename() returns the path string, or
        None when nothing is selected.
        """

        return self["filelist"].getFilename()

    # ------------------------------------------------------------------

    def _close(self, result=None) -> None:
        """
        Standard lifecycle close: logs Closing/Closed and returns to
        MainScreen with `result`.
        """

        self._log("Closing")

        self._log("Closed")

        self.close(result)

# End of Part 1
    # ------------------------------------------------------------------
    # Playback Commands (BROWSERSCREEN_SPEC.md section 8)
    # ------------------------------------------------------------------

    def playSelected(self) -> None:
        """
        Build a Playback Queue from the current directory and request
        playback of the selected file within it, returning to
        MainScreen on success (BROWSERSCREEN_SPEC.md section 5,
        PLAYBACK_QUEUE_SPEC.md "Queue Creation").
        """

        filename = self.getSelectedFilename()

        if not filename:

            self._log("No file selected.")

            return

        self._log("Media file selected.")

        queue, start_index = self._buildQueueFromCurrentDirectory(filename)

        if not queue:

            # Selected item isn't a supported media file (or the
            # directory scan failed) -- fall back to playing just the
            # selected file directly, so a single oddly-named file
            # still plays instead of silently doing nothing.
            queue, start_index = [filename], 0

        self._log(f"Playback requested: {filename}")

        self._logVerboseBlock("Selected:", os.path.basename(filename))

        logger.verbose("[BrowserScreen] Starting playback")

        if self._playback.playQueue(queue, start_index):

            self._log("Returning to MainScreen.")

            self._close("played")

        else:

            self._statusbar.showError("Playback failed")

    # ------------------------------------------------------------------

    def _buildQueueFromCurrentDirectory(self, selected_filename: str):
        """
        Build an ordered Playback Queue of supported media files from
        the current directory, and find `selected_filename`'s index
        within it.

        Directories, hidden files (dotfiles) and unsupported
        extensions are excluded (PLAYBACK_QUEUE_SPEC.md "Queue
        Contents"). Ordering matches BrowserScreen's own alphabetical
        listing.

        Returns:
            (queue, start_index) -- queue is a list of full paths;
            start_index is 0 if `selected_filename` could not be
            found in it. queue is [] if the directory could not be
            scanned or contains no supported media files.
        """

        try:
            current_directory = self["filelist"].getCurrentDirectory()

        except Exception as error:

            self._log(f"Unable to determine current directory: {error}")

            return [], 0

        if not current_directory:
            return [], 0

        try:
            entries = os.listdir(current_directory)

        except OSError as error:

            self._log(f"Unable to scan directory for queue: {error}")

            return [], 0

        supported = []

        for entry in sorted(entries, key=str.lower):

            if entry.startswith("."):
                continue

            full_path = os.path.join(current_directory, entry)

            if os.path.isdir(full_path):
                continue

            if not entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):
                continue

            supported.append(full_path)

        #
        # Match by basename, not full-path equality. Confirmed on a
        # real device: FileList.getFilename()'s path never matched
        # this os.path.join()-built list exactly (see
        # docs/Claude_notes_build0005.txt) even though the file
        # unquestionably exists in this directory -- exact-path
        # comparison silently fell back to index 0 on every single
        # selection, so only the first track in the directory ever
        # played regardless of what the user picked. Basenames are
        # unaffected by whatever path representation FileList uses
        # internally (trailing slashes, separator handling, etc.).
        #
        selected_basename = os.path.basename(selected_filename)

        start_index = 0

        for index, path in enumerate(supported):

            if os.path.basename(path) == selected_basename:

                start_index = index

                break

        else:

            self._log("Selected file not found in supported queue; starting at position 1.")

        return supported, start_index

    # ------------------------------------------------------------------
    # Event Handlers (BROWSERSCREEN_SPEC.md section 6)
    # ------------------------------------------------------------------

    def okPressed(self) -> None:
        """
        Enter directories, or select and play a file.
        """

        logger.verbose("[BrowserScreen] OK pressed.")

        if self["filelist"].canDescent():

            self.openDirectory()

            return

        self.playSelected()

    # ------------------------------------------------------------------
    # Context Menu (Build 0007 -- PLAYLIST_MANAGER_SPEC.md "Browser
    # Integration")
    # ------------------------------------------------------------------
    #
    # Deliberately bound to INFO, not OK: OK's existing descend-into-
    # folder / play-file behaviour is real-device verified across
    # several Build 0005/0006 test rounds and must not change. INFO
    # was unbound in BrowserScreen before this, and reads naturally as
    # "more options about the selected item" -- avoids a colour button
    # per user request, where INFO already fits the purpose.

    def helpPressed(self) -> None:
        """
        Build 0008 -- opens HelpScreen with BrowserScreen's own
        context-sensitive help document.
        """

        logger.verbose("[BrowserScreen] HELP pressed.")

        title, content = help_manager.getHelp("browserscreen")

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------

    def openContextMenu(self) -> None:

        logger.verbose("[BrowserScreen] INFO pressed.")

        filename = self.getSelectedFilename()

        if self["filelist"].canDescent():

            directory = filename or self["filelist"].getCurrentDirectory()

            self._openFolderMenu(directory)

            return

        if not filename:
            return

        if filename.lower().endswith(PLAYLIST_FILE_EXTENSIONS):

            self._openPlaylistFileMenu(filename)

        else:

            self._openAudioFileMenu(filename)

    # ------------------------------------------------------------------

    def _openFolderMenu(self, directory: str) -> None:

        choices = [
            (_("Play Folder"), "play_folder"),
            (_("Add Folder to Playlist"), "add_folder"),
            (_("Create Playlist"), "create_playlist"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._folderMenuChosen(choice, directory),
            ChoiceBox,
            title=_("Folder options"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _folderMenuChosen(self, choice, directory: str) -> None:

        if choice is None:
            return

        action = choice[1]

        if action == "play_folder":

            self._playFolderQueue(directory)

        elif action == "add_folder":

            self._openPlaylistPicker(lambda name: self._addFolderToPlaylist(name, directory))

        elif action == "create_playlist":

            self._promptNewPlaylistName(lambda name: self._log(f"Playlist created: {name}") if playlist_manager.createPlaylist(name) else None)

    # ------------------------------------------------------------------

    def _openAudioFileMenu(self, filepath: str) -> None:

        choices = [
            (_("Play"), "play"),
            (_("Add to Playlist"), "add_to_playlist"),
            (_("Information"), "information"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._audioFileMenuChosen(choice, filepath),
            ChoiceBox,
            title=os.path.basename(filepath),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _audioFileMenuChosen(self, choice, filepath: str) -> None:

        if choice is None:
            return

        action = choice[1]

        if action == "play":

            self.playSelected()

        elif action == "add_to_playlist":

            self._openPlaylistPicker(lambda name: self._addTrackToPlaylist(name, filepath))

        elif action == "information":

            self._showFileInformation(filepath)

    # ------------------------------------------------------------------

    def _openPlaylistFileMenu(self, filepath: str) -> None:

        choices = [
            (_("Play Playlist"), "play_playlist"),
            (_("Import Playlist"), "import_playlist"),
            (_("Information"), "information"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._playlistFileMenuChosen(choice, filepath),
            ChoiceBox,
            title=os.path.basename(filepath),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _playlistFileMenuChosen(self, choice, filepath: str) -> None:

        if choice is None:
            return

        action = choice[1]

        playlist_name = os.path.splitext(os.path.basename(filepath))[0]

        if action == "play_playlist":

            self._playImportedPlaylistFile(filepath, playlist_name)

        elif action == "import_playlist":

            imported_name = playlist_manager.importPlaylist(filepath)

            if imported_name:

                self._statusbar.showState(self._playback.getState(), None)

                self._log(f"Playlist imported: {imported_name}")

        elif action == "information":

            self._showPlaylistFileInformation(filepath)

# End of Part 1
    # ------------------------------------------------------------------
    # Context Menu Actions
    # ------------------------------------------------------------------

    def _playFolderQueue(self, directory: str) -> None:
        """
        Recursively collect every supported audio file under
        `directory` and play it as a queue -- the same queue shape
        BrowserScreen already builds when playing a single selected
        file (PLAYBACK_QUEUE_SPEC.md), just seeded from "Play Folder"
        instead of a single OK press.
        """

        collected = []

        try:
            for root, _directories, files in os.walk(directory):

                for entry in sorted(files, key=str.lower):

                    if entry.startswith("."):
                        continue

                    if entry.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):

                        collected.append(os.path.join(root, entry))

        except OSError as error:

            self._log(f"Unable to scan folder for playback: {directory} ({error})")

        if not collected:

            self._statusbar.showError(_("Playback failed"))

            return

        self._log(f"Play Folder: {directory} ({len(collected)} track(s))")

        if self._playback.playQueue(collected, 0):

            self._close("played")

        else:

            self._statusbar.showError(_("Playback failed"))

    # ------------------------------------------------------------------

    def _addFolderToPlaylist(self, playlist_name: Optional[str], directory: str) -> None:

        if not playlist_name:
            return

        count = playlist_manager.addFolder(playlist_name, directory)

        self._log(f"Added {count} track(s) from folder to playlist: {playlist_name}")

    # ------------------------------------------------------------------

    def _addTrackToPlaylist(self, playlist_name: Optional[str], filepath: str) -> None:

        if not playlist_name:
            return

        playlist_manager.addTrack(playlist_name, filepath)

    # ------------------------------------------------------------------

    def _playImportedPlaylistFile(self, filepath: str, playlist_name: str) -> None:

        tracks = playlist_manager.readPlaylistFile(filepath)

        queue = [track["path"] for track in playlist_manager.validatePlaylist(tracks)]

        if not queue:

            self._statusbar.showError(_("Playback failed"))

            return

        self._log(f"Play Playlist: {filepath} ({len(queue)} track(s))")

        if self._playback.playQueue(queue, 0):

            self._close("played")

        else:

            self._statusbar.showError(_("Playback failed"))

    # ------------------------------------------------------------------

    def _showFileInformation(self, filepath: str) -> None:

        try:
            size_bytes = os.path.getsize(filepath)

        except OSError:
            size_bytes = None

        lines = [
            os.path.basename(filepath),
            "",
            f"{_('Path')}: {filepath}",
            f"Size: {size_bytes} bytes" if size_bytes is not None else "Size: Unknown",
        ]

        self.session.open(MessageBox, "\n".join(lines), MessageBox.TYPE_INFO)

    # ------------------------------------------------------------------

    def _showPlaylistFileInformation(self, filepath: str) -> None:

        tracks = playlist_manager.readPlaylistFile(filepath)

        lines = [
            os.path.basename(filepath),
            "",
            f"Tracks: {len(tracks)}",
        ]

        self.session.open(MessageBox, "\n".join(lines), MessageBox.TYPE_INFO)

    # ------------------------------------------------------------------
    # Playlist Picker (shared by folder/audio-file "Add to Playlist")
    # ------------------------------------------------------------------

    def _openPlaylistPicker(self, callback) -> None:

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

            self._promptNewPlaylistName(callback)

            return

        callback(choice[1])

    # ------------------------------------------------------------------

    def _promptNewPlaylistName(self, callback) -> None:

        try:
            from Screens.VirtualKeyBoard import VirtualKeyBoard

        except ImportError as error:

            self._log(f"Text input unavailable: {error}")

            return

        self.session.openWithCallback(
            lambda text: callback(text) if text else None,
            VirtualKeyBoard,
            title=_("New playlist name"),
            text="",
        )

    # ------------------------------------------------------------------

    def pvrPressed(self) -> None:
        """
        Return to MainScreen without changing playback
        (BROWSERSCREEN_SPEC.md section 6).
        """

        logger.verbose("[BrowserScreen] PVR pressed.")

        self._log("Returning to MainScreen.")

        self._close(None)

    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[BrowserScreen] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit"):
            return

        if action_id == "browser":
            # Already in BrowserScreen; nothing to do.
            return

        # Every other destination (playback_info, settings, developer,
        # about) is reached through MainScreen, per
        # BROWSERSCREEN_SPEC.md section 7: "BrowserScreen shall never
        # open SettingsScreen directly." Close back to MainScreen and
        # let it handle the navigation.
        self._log("Returning to MainScreen.")

        self._close(action_id)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:
        """
        Return to MainScreen (BROWSERSCREEN_SPEC.md section 6).
        """

        logger.verbose("[BrowserScreen] EXIT pressed.")

        self._log("Returning to MainScreen.")

        self._close(None)

# End of Part 2
    # ------------------------------------------------------------------
    # Status Updates
    # ------------------------------------------------------------------

    def _updateStatus(self) -> None:
        """
        Update browser status information.
        """

        try:

            current_directory = self["filelist"].getCurrentDirectory()

            if current_directory:

                self["path"].setText(current_directory)

                logger.verbose(f"[BrowserScreen] Current directory: {current_directory}")

        except Exception as error:

            self._log(f"Unable to update status: {error}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"BrowserScreen(initialized={self._initialized})"


# ==============================================================================
#
# Build Notes
#
# Build 0004 converts BrowserScreen into a temporary Screen, opened
# only by explicit user request from MainScreen. BrowserScreen
# responsibilities:
#
#   - Directory browsing
#   - File selection
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

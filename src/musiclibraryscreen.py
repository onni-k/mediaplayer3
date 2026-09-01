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

import os

from enigma import ePicLoad, eTimer

from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from .compatibility import compatibility
from .config import config_manager
from .help_manager import help_manager
from .help_screen import HelpScreen
from .library_manager import library_manager
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .paths import RESOURCE_PATH, SKIN_PATH
from .skin import to_opaque_skin_color

# Device test round 32 -- icon set provided directly by the user
# (skin_test5.png), cropped to individual 40x40 PNGs (white
# background, matching PANEL_BACKGROUND_COLOR exactly, so no alpha
# transparency is needed when composited onto a panel).
# Device test round 39 -- pre-rendered background images (one per
# active-column state), confirmed working via ePicLoad in rounds
# 36-38's own dedicated experiment.
# Device test round 46 -- reorganized under resources/skins/{variant}/
# {tier}/, matching cfg.appearance.skin's own "light"/"dark" choices
# and SkinManager's existing SKIN_PATH convention (resources/skins/
# default/skin.json already followed this layout; light/dark now have
# their own skin.json alongside their hd/sd image folders). "tier" is
# a resolution class, not an exact size -- HD covers 1280x720 and
# larger (1920x1080, 4K devices all get the same HD source, upscaled
# a little further by ePicLoad rather than needing a distinct asset
# per exact resolution); SD is for genuinely low-resolution
# (720x576-class) devices, so they aren't stuck downscaling a much
# larger HD source for no benefit. Filenames within each folder still
# match self._focus's own three values exactly
# (musiclibrary_{focus}_active.png).
SKIN_VARIANTS = ("light", "dark")

DEFAULT_SKIN_VARIANT = "light"

# Device test round 46 -- per-variant colours for every widget this
# screen draws itself (the background images only carry the header/
# hint icon+colour chrome -- everything else, from panel backgrounds
# to body text to the info card's blue labels, still needs an actual
# matching colour here). Dark values sampled directly from the user's
# own dark mockup (skin_test9.png) rather than guessed -- see the
# background-image generation notes in this round's own changelog
# entry for the exact sampled RGB values.
SKIN_PALETTES = {
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
        # Device test round 47 -- re-sourced from the user's own
        # Internet Radio dark mockup (MediaPlayer3_radio_skin_test2.png)
        # after the first dark palette (round 46, sampled from
        # skin_test9.png) came back "a bit too dark" overall. The key
        # difference: that first palette's header_inactive_bg (#17171D)
        # was only ~3-5 units away from its own panel_bg (#14181C) --
        # nearly indistinguishable, which is likely why headers didn't
        # stand out and the whole screen read as flat. This palette's
        # header_inactive_bg is a distinctly lighter, blue-tinted slate
        # (~30 units lighter than panel_bg), giving real hierarchy
        # instead of everything blending into near-black. Every value
        # below is a real sampled colour (mode over a small clean
        # patch, avoiding anti-aliased text edges), not estimated.
        #
        # Device test round 48 -- panel_background_color lightened
        # further (#151820 -> #1C202B) per direct request; selected_
        # row_fg switched from white to a gold/amber sampled from the
        # same radio mockup's own selected-item text (peak pixel
        # (199,172,78) in the "Arrow Classic Rock" row, avoiding
        # anti-aliased edges the same way the rest of this palette
        # was sampled).
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


def _resolveSkinVariant() -> str:

    variant = config_manager.get("appearance.skin", DEFAULT_SKIN_VARIANT)

    if variant not in SKIN_VARIANTS:
        # "default" (the pre-round-46 placeholder value, still the
        # cfg-wide default) and any future/unrecognised value both
        # fall back here -- matches SkinManager.loadSkin()'s own
        # "unknown skin -> fall back, never raise" convention.
        return DEFAULT_SKIN_VARIANT

    return variant


def _resolveResolutionTier(screen_width: int) -> str:

    return "hd" if screen_width >= 1000 else "sd"


PANELS = ("artists", "albums", "tracks")

# CHANNEL UP/DOWN jump this many entries at once -- same convenience
# feature RadioBrowserScreen added after real device testing (long
# lists are slow to scroll one entry at a time). PROVISIONAL for this
# screen specifically: CH+/CH- is itself unconfirmed to even reach
# RadioBrowserScreen on real hardware (Build 0007, device test rounds
# 4-9) -- left in as harmless best-effort, same reasoning as there.
PAGE_STEP = 15


class MusicLibraryScreen(Screen):
    """
    Metadata-based music browsing, search and playback queue
    generation (Build 0008).
    """

    SPECIFICATION_VERSION = "0.1"

    DESIGN_WIDTH = 1672
    DESIGN_HEIGHT = 941

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Device test round 39 -- full rewrite using pre-rendered
        background images (resources/backgrounds/musiclibrary_*.png,
        supplied directly by the user) instead of composing the
        column headers, hint row, and highlighting from individual
        widgets. Confirmed viable in rounds 36-38's own dedicated
        experiment: a static Pixmap's pixmap= attribute does NOT
        scale a mismatched source image at all, but ePicLoad (already
        proven for cover art since Build 0005) scales correctly,
        filling its target box exactly when the source image's own
        aspect ratio matches the box's -- see _decodeBackgroundImage()
        below, which reuses that exact mechanism.

        Design canvas deliberately set to the background images' own
        native pixel size (1672x941, matching their own ~16:9 aspect
        ratio) rather than an arbitrary smaller design resolution, so
        every rect() coordinate in this method can be read directly
        off the source images' own measured pixel boundaries with no
        extra conversion arithmetic -- confirmed by measuring every
        boundary used below directly from the actual image files
        (colour-transition scans), not estimated by eye.

        Column header bars, their icons, their active/inactive
        colouring, and the entire hint row are now part of the
        background image itself, not real widgets -- removed
        entirely: title_bg_normal/active, the per-column icon
        widgets, title_normal/active label pairs, and all six
        hint_icon_*/hint_text_* pairs from round 33. Only the
        genuinely dynamic content stays as real widgets: the three
        MenuLists, the "Musiikkikirjasto" title (not present in the
        reference images, kept as a separate overlay in their own
        empty top margin), and the info card's text fields.
        """

        sx = width / MusicLibraryScreen.DESIGN_WIDTH
        sy = height / MusicLibraryScreen.DESIGN_HEIGHT

        # Device test round 40 -- a device screenshot showed the
        # background image decoded far larger than the actual screen,
        # overflowing off the right/bottom edges. _buildSkin() is
        # called with the exact real device width/height Enigma2 itself
        # is about to render at -- storing them here and using them
        # directly for ePicLoad's setPara() (_decodeBackgroundImage())
        # sidesteps whatever self["background"].instance.size() was
        # actually returning at decode time, rather than trying to
        # explain that discrepancy without a live device to inspect.
        self._screen_width = width

        self._screen_height = height

        # Device test round 46 -- resolved once here (not per-widget)
        # and stored on self so _decodeBackgroundImage() picks the
        # matching image set without re-reading the config setting
        # mid-session; a variant change only takes effect on next
        # screen open, matching how cfg.appearance.theme's own changes
        # already work for every other screen (SettingsScreen's own
        # apply step, not a live in-place re-skin).
        self._skin_variant = _resolveSkinVariant()

        palette = SKIN_PALETTES[self._skin_variant]

        panel_background_color = to_opaque_skin_color(palette["panel_background_color"])
        panel_text_color = palette["panel_text_color"]

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Bold;{max(10, int(size * sx))}"'

        return f"""
        <screen name="MusicLibraryScreen" position="0,0" size="{width},{height}" backgroundColor="{panel_background_color}" flags="wfNoBorder">

            <widget name="background"
                    {rect(0, 0, 1672, 941)}
                    alphatest="blend"/>

            <!-- Device test round 45: user request: header/hint
                 text moved out of the background images entirely and
                 back into real widgets, so switching the app's
                 language actually re-translates them (baked-in image
                 text can't). The background images now only carry
                 the icon+colour chrome; every position/colour below
                 is taken directly from the same pixel measurements
                 used to build those images, so text lines up with
                 its own icon exactly. Column headers keep the round
                 34 normal/active pair pattern (dark text on the
                 light-blue inactive header has poor contrast against
                 the more saturated active blue header, and vice
                 versa): toggled the same way in
                 _updateColumnHighlighting() the old widget-only
                 version already did. -->

            <widget name="artists_title_normal"
                    {rect(135, 80, 383, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="artists_title_active"
                    {rect(135, 80, 383, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="albums_title_normal"
                    {rect(652, 80, 422, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="albums_title_active"
                    {rect(652, 80, 422, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="tracks_title_normal"
                    {rect(1207, 80, 403, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="tracks_title_active"
                    {rect(1207, 80, 403, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="hint_text_leftright"
                    {rect(82, 874, 313, 63)}
                    {font(24)}
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_updown"
                    {rect(447, 874, 254, 63)}
                    {font(24)}
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_ok"
                    {rect(753, 874, 141, 63)}
                    {font(24)}
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_info"
                    {rect(946, 874, 167, 63)}
                    {font(24)}
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_menu"
                    {rect(1165, 874, 210, 63)}
                    {font(24)}
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_exit"
                    {rect(1427, 874, 193, 63)}
                    {font(24)}
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="status"
                    {rect(60, 19, 1550, 55)}
                    {font(34)}
                    halign="center"
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="artists"
                    {rect(40, 138, 498, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="#E0E0E0"
                    scrollbarMode="showOnDemand"/>

            <widget name="albums"
                    {rect(557, 138, 537, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="#E0E0E0"
                    scrollbarMode="showOnDemand"/>

            <widget name="tracks"
                    {rect(1112, 138, 518, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="#E0E0E0"
                    scrollbarMode="showOnDemand"/>

            <widget name="info_title"
                    {rect(60, 702, 1550, 42)}
                    {font(28)}
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="info_artist_label"
                    {rect(60, 752, 160, 36)}
                    {font(20)}
                    valign="center"
                    foregroundColor="{palette['info_label_fg']}"
                    transparent="1"/>

            <widget name="info_artist_value"
                    {rect(230, 752, 540, 36)}
                    {font(20)}
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="info_album_label"
                    {rect(820, 752, 160, 36)}
                    {font(20)}
                    valign="center"
                    foregroundColor="{palette['info_label_fg']}"
                    transparent="1"/>

            <widget name="info_album_value"
                    {rect(990, 752, 600, 36)}
                    {font(20)}
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="info_genre_label"
                    {rect(60, 796, 160, 36)}
                    {font(20)}
                    valign="center"
                    foregroundColor="{palette['info_label_fg']}"
                    transparent="1"/>

            <widget name="info_genre_value"
                    {rect(230, 796, 540, 36)}
                    {font(20)}
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="info_year_label"
                    {rect(820, 796, 160, 36)}
                    {font(20)}
                    valign="center"
                    foregroundColor="{palette['info_label_fg']}"
                    transparent="1"/>

            <widget name="info_year_value"
                    {rect(990, 796, 600, 36)}
                    {font(20)}
                    valign="center"
                    foregroundColor="{panel_text_color}"
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

        # Device test round 39 -- background image (one of three,
        # swapped per _focus -- see _decodeBackgroundImage()) replaces
        # the column header bg/icon/title widgets and the whole hint
        # row entirely; must be added to self before every widget that
        # should paint on top of it, same paint-order rule as before
        # (Round 7's own lesson), just with a single background layer
        # now instead of per-column bg pairs.
        self["background"] = Pixmap()

        self._background_picload = ePicLoad()

        compatibility.connectPictureDataSignal(self._background_picload, self._onBackgroundImageDecoded)

        # Cache of already-decoded background pixmaps, keyed by focus
        # state -- avoids re-running ePicLoad's own (real, if brief)
        # async decode every time the user just moves LEFT/RIGHT
        # between panels they've already visited this session.
        self._background_pixmap_cache = {}

        # Device test round 62 -- guards against starting a second
        # concurrent decode while one is already running.
        self._background_decode_in_progress = False

        # Device test round 45 -- header text moved back to real,
        # translatable widgets; see _buildSkin()'s own comment. Same
        # bg-before-title-before-active insertion-order convention
        # this project has used since Round 7 (bg/icon already live
        # only in the background image now, but the normal/active
        # text pair still needs the same ordering relative to each
        # other).
        self["artists_title_normal"] = Label(_("Artists"))
        self["artists_title_active"] = Label(_("Artists"))
        self["artists_title_active"].hide()
        self["albums_title_normal"] = Label(_("Albums"))
        self["albums_title_active"] = Label(_("Albums"))
        self["albums_title_active"].hide()
        self["tracks_title_normal"] = Label(_("Tracks"))
        self["tracks_title_active"] = Label(_("Tracks"))
        self["tracks_title_active"].hide()

        self["hint_text_leftright"] = Label(_("LEFT/RIGHT: Panel"))
        self["hint_text_updown"] = Label(_("UP/DOWN: Move"))
        self["hint_text_ok"] = Label(_("OK: Play"))
        self["hint_text_info"] = Label(_("INFO: Search"))
        self["hint_text_menu"] = Label(_("MENU: Menu"))
        self["hint_text_exit"] = Label(_("EXIT: Back"))

        self["status"] = Label(_("Music Library"))

        self["artists"] = MenuList([])
        self["albums"] = MenuList([])
        self["tracks"] = MenuList([])

        # Device test round 32 -- structured detail card (title +
        # blue-labelled Artist/Album/Genre/Year rows) replacing the
        # old single "info" Label -- see _buildSkin()'s own comment.
        # Device test round 39: "info_bg" removed -- the background
        # image's own info-card box already provides this now.
        self["info_title"] = Label("")
        self["info_artist_label"] = Label("")
        self["info_artist_value"] = Label("")
        self["info_album_label"] = Label("")
        self["info_album_value"] = Label("")
        self["info_genre_label"] = Label("")
        self["info_genre_value"] = Label("")
        self["info_year_label"] = Label("")
        self["info_year_value"] = Label("")

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

    def _setInfoFields(self, title: str, artist: str = "", album: str = "", genre: str = "", year: str = "") -> None:
        """
        Device test round 32 -- shared by every _updateInfoPanel()
        branch below. Leaving a field blank ("") simply shows an empty
        label/value pair, which reads fine visually (matches how the
        old single-Label version handled a partial info line).
        """

        self["info_title"].setText(title)

        self["info_artist_label"].setText(f"{_('Artist')}:" if artist else "")
        self["info_artist_value"].setText(artist)

        self["info_album_label"].setText(f"{_('Album')}:" if album else "")
        self["info_album_value"].setText(album)

        self["info_genre_label"].setText(f"{_('Genre')}:" if genre else "")
        self["info_genre_value"].setText(genre)

        self["info_year_label"].setText(f"{_('Year')}:" if year else "")
        self["info_year_value"].setText(year)

    # ------------------------------------------------------------------

    def _updateInfoPanel(self) -> None:

        if not library_manager.getTrackCount():

            self._setInfoFields(
                _("No music library available.\n\nUse Library Update from the menu\nafter adding music files.")
            )

            return

        track = self._selectedTrack()

        if track is not None:

            self._setInfoFields(
                track["title"],
                artist=track["artist"],
                album=track["album"],
                genre=track["genre"],
                year=str(track["year"]),
            )

            return

        album = self._selectedAlbum()

        if album is not None:

            track_count = len(library_manager.getTracks(artist=self._selectedArtist(), album=album))

            self._setInfoFields(album, album=f"{track_count} {_('track(s)')}")

            return

        artist = self._selectedArtist()

        if artist is not None:

            album_count = len(library_manager.getAlbums(artist=artist))

            self._setInfoFields(artist, artist=f"{album_count} {_('album(s)')}")

            return

        self._setInfoFields("")

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
        Device test round 39 -- the active/inactive column-header
        BACKGROUND colouring lives in one of three pre-rendered
        background images (resources/backgrounds/
        musiclibrary_{focus}_active.png), swapped here instead of
        toggling individual bg widgets. See _decodeBackgroundImage()'s
        own docstring for the actual ePicLoad mechanics and caching.

        Device test round 45 -- the header TEXT itself moved back out
        of those images into real widgets (translatable), so still
        needs the normal/active hide()/show() toggle here, the same
        mechanism this project has used since Round 34.
        """

        self._decodeBackgroundImage(self._focus)

        for panel_name in PANELS:

            is_active = panel_name == self._focus

            try:
                self[f"{panel_name}_title_normal"].hide() if is_active else self[f"{panel_name}_title_normal"].show()

                self[f"{panel_name}_title_active"].show() if is_active else self[f"{panel_name}_title_active"].hide()

            except Exception as error:

                logger.verbose(f"[MusicLibrary] Unable to set column title visibility: {error}")

    # ------------------------------------------------------------------
    # Background image (device test round 39 -- see _buildSkin()'s own
    # docstring and rounds 36-38's dedicated experiment confirming
    # ePicLoad, not a static Pixmap, is the correct mechanism here)
    # ------------------------------------------------------------------

    def _decodeBackgroundImage(self, focus_state: str) -> None:
        """
        Starts an async decode of the background image matching
        `focus_state` ("artists"/"albums"/"tracks") from this screen's
        own resolved skin variant/resolution tier (self._skin_variant,
        set once in _buildSkin(); tier resolved fresh here from
        self._screen_width since it's a cheap, pure function of a
        value that's also fixed for the screen's lifetime), or applies
        it instantly from cache if this exact state has already been
        decoded once this session -- LEFT/RIGHT between panels the
        user has already visited doesn't need to re-run ePicLoad's own
        decode every time. Mirrors mainscreen.py's own
        _decodeCoverArt() pattern (same widget-not-ready retry via a
        one-shot eTimer, same setPara() tuple shape/scale_mode), the
        one already confirmed working on real hardware in this
        project, rather than anything new/unverified.
        """

        if focus_state in self._background_pixmap_cache:

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

            logger.verbose("[MusicLibrary] background widget not ready yet, retrying shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(lambda: self._decodeBackgroundImage(focus_state))

            retry_timer.start(100, True)

            self._pending_background_retry_timer = retry_timer

            return

        image_path = os.path.join(
            SKIN_PATH,
            self._skin_variant,
            _resolveResolutionTier(self._screen_width),
            f"musiclibrary_{focus_state}_active.png",
        )

        # Remember which state this in-flight decode is for -- ePicLoad
        # only has one PictureData callback, so if the user changes
        # focus again before this decode finishes, the callback needs
        # to know which state to cache the result under.
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

            logger.verbose(f"[MusicLibrary] Unable to decode background image {image_path}: {error}")

    # ------------------------------------------------------------------

    def _onBackgroundImageDecoded(self, picture_info=None) -> None:

        # Device test round 62 -- cleared in a finally below so every
        # branch (including early returns) reliably clears it once
        # the decode has genuinely finished.
        try:
            pixmap = self._background_picload.getData()

            if pixmap is None:
                return

            focus_state = getattr(self, "_pending_background_focus_state", self._focus)

            self._background_pixmap_cache[focus_state] = pixmap

            # The user may have moved focus again while this decode
            # was still in flight -- only actually apply the result if
            # it's still the state currently wanted.
            if focus_state != self._focus:
                return

            self["background"].instance.setPixmap(pixmap)

            self["background"].show()

        except Exception as error:

            logger.verbose(f"[MusicLibrary] Unable to apply decoded background image: {error}")

        finally:

            self._background_decode_in_progress = False

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

        steps = min(PAGE_STEP, self[self._focus].getSelectedIndex())

        for _step in range(steps):
            self[self._focus].up()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageDown(self) -> None:

        logger.verbose("[MusicLibrary] CH- pressed.")

        entries = self[self._focus].list or []

        steps = min(PAGE_STEP, max(0, len(entries) - 1 - self[self._focus].getSelectedIndex()))

        for _step in range(steps):
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

# ==============================================================================
#
# MediaPlayer3
#
# File        : mainscreen.py
#
# Description :
#
#     MainScreen
#
#     Primary application window of MediaPlayer3, replacing the Build
#     0003 Browser as the startup screen. MainScreen presents playback
#     status and information and provides access to every other
#     Screen. It never browses directories itself -- that is
#     BrowserScreen's job.
#
#     MainScreen owns the single, shared PlaybackController instance
#     for the lifetime of the application and passes it to every
#     Screen it opens, so playback state survives navigation between
#     screens (MainScreen <-> BrowserScreen <-> ...).
#
# Implements :
#
#     MAINSCREEN_SPEC.md v0.1
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
# 2026-07-13  Build 0004
#   - PVR key now also opens BrowserScreen: bound both "showMovies" and
#     "showInfobar" action names to pvrPressed(), since this keymap's
#     actual PVR-key action name was not "showInfobar" as originally
#     assumed and the PVR key had no effect on device.
#
# 2026-07-14  Build 0005
#   - Added a graphical progress bar, elapsed/remaining time labels and
#     a queue-position label, refreshed once per second by an eTimer
#     while playback is active (MAINSCREEN_SPEC.md "Progress Bar" /
#     "Screen Refresh"). eTimer is a base Enigma2 binding identical on
#     every image, so it is used directly here rather than through
#     compatibility.py -- unlike the position/duration values it
#     drives, which do go through PlaybackController ->
#     ServiceController -> compatibility.py.
#   - Added Previous/Next Track remote key handling, forwarded to
#     PlaybackController.
#   - All four new "User Interface" settings (show progress bar /
#     elapsed time / remaining time / playback state) are applied on
#     open and re-applied every time a child Screen closes, so a
#     change made in SettingsScreen takes effect immediately.
#
# 2026-07-14  Build 0005 (device test fix)
#   - Next/Previous Track keys had no effect on device: a real test
#     showed the physical track-skip buttons produced no ActionMap
#     match at all with only "next"/"previous" bound. Now bound via
#     compatibility.getNextTrackKeyActionNames() /
#     getPreviousTrackKeyActionNames(), which add "nextBouquet"/
#     "prevBouquet" (Enigma2 core keymap.xml's actual action names for
#     KEY_NEXT/KEY_PREVIOUS in "InfobarActions") as further candidates
#     -- same pattern as the earlier PVR key fix.
#
# 2026-07-16  Build 0005 (device test round 2)
#   - Added seeking: FASTFORWARD/REWIND (long step) and LEFT/RIGHT
#     (short step) now seek within the current track via
#     PlaybackController.seekForward()/seekBackward(). Previously
#     unbound entirely, which made Enigma2 show its native "unhandled
#     key" indicator for these keys.
#   - Added a cover art Pixmap widget: shows cover.jpg/cover.png/
#     folder.jpg/folder.png from the current track's directory when
#     present. Plain Components.Pixmap/Tools.LoadPixmap usage,
#     unrelated to the GStreamer playback backend.
#   - Total track duration is now shown before the "Track N / M" text
#     (queueposition label), per user feedback.
#
# 2026-07-17  Build 0005 (device test round 3)
#   - Cover art rewritten to use ePicLoad instead of raw LoadPixmap:
#     photos from a real device test showed the unscaled image only
#     displaying its zoomed top-left corner. ePicLoad decodes and
#     scales asynchronously to fit the widget (see
#     _onCoverArtDecoded()). setPara()'s exact scale_mode semantics
#     are not yet confirmed on this device -- see
#     docs/Claude_notes_build0005.txt.
#   - Cover art is now a full-window background (skin `cover` widget,
#     0,0 700x460, zPosition -1, behind all text) instead of a small
#     side thumbnail, so it visually replaces whatever background was
#     showing through MainScreen's window. That background is the
#     box's own generic audio-playback picture, drawn outside
#     MediaPlayer3's window in the video/background layer -- not
#     something ServiceApp (a playback *backend*, unrelated to
#     graphics) or any Python Screen code can reach directly; painting
#     our own opaque cover art across the window is what overrides it.
#
# 2026-07-17  Build 0005 (device test round 4)
#   - Text widgets (version/media/meta/status/elapsed/remaining/
#     queueposition/hint) now use transparent="1" in the skin. A real
#     device screenshot showed the cover art background hidden behind
#     each text row's own opaque Label background -- Enigma2 Label
#     widgets paint an opaque backdrop by default, so the cover art
#     was only visible in the gaps between text rows.
#   - Added backgroundColor="#000000" on the <screen> itself, so any
#     area not covered by an opaque widget (letterboxed cover edges,
#     etc.) is solid black instead of letting the box's native
#     background bleed through -- matches the user's report that the
#     default background showed through "everywhere".
#   - Added compatibility.connectPictureDataSignal(): checked
#     github.com/oe-mirrors/yampmusicplayer and github.com/mx3L/
#     mediaplayer2 per user request; found a documented real-world bug
#     report showing ePicLoad.PictureData needs ".get()" on some
#     Enigma2 bindings and not on others. Connecting the signal now
#     tries both forms defensively (see
#     docs/Claude_notes_build0005.txt for what could and couldn't be
#     retrieved from those repos).
#
# 2026-07-17  Build 0005 (device test round 5)
#   - MainScreen is now a genuinely full-screen window (position 0,0,
#     size = getDesktop(0).size()) instead of a small centered box.
#     A real device photo showed the box's own background still
#     visible around MainScreen's window edges -- normal Enigma2
#     behaviour for any non-fullscreen window, not fixable from
#     inside a smaller window. The whole skin (_buildSkin()) now
#     scales proportionally from the original 700x460 design to
#     whatever exact resolution is detected at runtime.
#   - Cover art decoding now requests the *real* "cover" widget size
#     (self["cover"].instance.size()) instead of a hardcoded 700x460,
#     and uses AVSwitch().getFramebufferScale() for setPara()'s aspect
#     ratio parameters instead of a hardcoded (1, 1) -- this exact
#     setPara() tuple shape and scale_mode=1 come from a
#     confirmed-working reference implementation (YampMusicPlayer's
#     YampCoverArtPixmap / OpenPli MediaPlayer's MediaPixmap, both
#     checked per user request) rather than a guess.
#
# 2026-07-17  Build 0005 (device test round 6)
#   - Fullscreen window confirmed fixed (default background no longer
#     visible at all). Cover art layout redesigned per user feedback
#     and modelled directly on YampMusicPlayer's own FHD skin
#     (plugin/skins/fhd/Yamp.xml, checked per user request): "cover"
#     is now a modest 160x160 corner square (design coordinates,
#     proportional to YAMP's own 230x230-on-1920x1080 coverArt
#     widget) instead of a full-window background, positioned so no
#     text widget overlaps it. Text moved into its own column to the
#     right of the cover; progress bar thinned from 20px to 14px tall
#     (design coordinates) to match YAMP's slim 12px-on-1080 bar.
#
# 2026-07-19  Build 0006
#   - Theme colors/font family now come from SkinManager instead of
#     being hardcoded (SKIN_MANAGER_SPEC.md / THEME_SPEC.md).
#   - Artist/Album ("meta") and Title ("media") now prefer real tag
#     metadata (PlaybackController.getMetadata()) over the "Unknown"
#     placeholders, falling back to them when no metadata is
#     available. Artwork resolution now also checks embedded artwork
#     first (see _updateCoverArt()).
#
# 2026-07-19  Build 0006 (device test round 1)
#   - Progress bar's unfilled portion had no explicit backgroundColor
#     and let the fullscreen artwork show through -- given an opaque
#     backgroundColor from the theme's "accent" color.
#   - EXIT now stops playback first (if active) and only closes on a
#     second press with nothing playing, matching common media player
#     convention.
#   - Title priority fixed: MainScreen's own "media" label was always
#     showing the filename even when a real tag Title existed
#     (PlaybackInfoScreen already used the tag correctly) -- added
#     _formatTitle() so MainScreen follows the same priority rule.
#
# 2026-07-19  Build 0006 (device test round 2)
#   - play() now clears cached position/duration for the previous
#     track immediately, instead of leaving them until the next
#     tick() call -- confirmed on a real device: switching tracks
#     briefly showed the OLD track's elapsed/duration/progress
#     (e.g. "01:35 / 02:49" moments after starting a fresh track that
#     was actually at 10s).
#   - Every text field is now tall enough for two lines, not one (see
#     _buildSkin()) -- a real device screenshot showed long filenames/
#     status text clipped after one line with no way to see the rest.
#
# 2026-07-19  Build 0006 (device test round 3)
#   - Now stops whatever's playing (typically live TV) immediately on
#     open, via PlaybackController.stopPreviousServiceNow(), instead
#     of waiting until the first track is played -- requested after a
#     real device test.
#   - FASTFORWARD/REWIND's seek step is now read from
#     playback.seek_step_seconds (Settings) instead of the fixed
#     SEEK_STEP_LONG constant; default changed 30s -> 60s per that
#     request.
#
# 2026-07-19  Build 0006 (device test round 4)
#   - Seek step default reconsidered back to 30s (was briefly 60s in
#     round 3); SEEK_STEP_LONG fallback constant kept in sync.
#
# 2026-07-19  Build 0007
#   - Now stops whatever's playing (typically live TV) immediately on
#     open via stopPreviousServiceNow() (carried over from Build 0006
#     device test round 3, unchanged).
#   - Added Internet Radio station navigation: while playing a stream
#     (PlaybackController.isPlayingStream()), LEFT/RIGHT switch
#     between the favorites list and the history list, UP/DOWN step
#     to the previous/next station -- local file seeking is completely
#     unaffected, since a playback session is always either a stream
#     or a local file. Added playRadioStation()/_switchRadioList()/
#     _radioStationStep()/_playRadioListEntry().
#
# 2026-07-24  Build 0007 (device test round 2)
#   - INFO now toggles between two views ("seek", the existing
#     default, and "favorites") instead of opening PlaybackInfoScreen
#     directly -- PlaybackInfoScreen remains reachable from Main Menu.
#     Favorites view: the top label shows the current folder/playlist
#     name (local) or favorites/history list name (radio) instead of
#     the app version string; the remaining-time position shows
#     "N/M" (queue/list position) instead of a duration. Requested
#     after real device testing.
#   - Added RADIO key (compatibility.getRadioKeyActionNames(),
#     candidates not yet confirmed against a real device) to toggle
#     between the last-played local file and the last-played Internet
#     Radio station.
#
# 2026-07-24  Build 0007 (device test round 3)
#   - Radio favicon used as cover art for streams when available
#     (InternetRadioManager.downloadFavicon()), before falling back to
#     default artwork.
#   - Radio list cycling (LEFT/RIGHT) now cycles through every
#     favorite list the user has created, plus history -- was
#     previously a hard-coded favorites/history binary toggle. Also
#     fixed _refreshRadioList() passing no list name to getFavorites()
#     (always resolved to "General" regardless of _radio_list_name).
#   - Local file playlist cycling added: LEFT/RIGHT cycle through
#     every stored PlaylistManager playlist and UP/DOWN step tracks
#     within it, mirroring radio's list/station navigation, while in
#     favorites view. Top label shows the active playlist name;
#     cleared when playback starts from BrowserScreen (folder-based,
#     not playlist-based).
#   - radioPressed() refined: pressing RADIO while already playing a
#     stream now opens BrowserScreen (previously silently resumed the
#     last local file) -- "Kun radiotilassa painaa radio-nappia, niin
#     voisi aueta browser." Removed the now-unread
#     _last_local_file tracking this replaced.
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
#   - OK on an empty MainScreen (nothing playing) now asks which
#     source to open (Internet Radio/Local Music/Playlists) instead of
#     always going straight to BrowserScreen.
#   - Choosing Internet Radio switches to favorites view and resumes
#     the last history station, falling back to the "General"
#     favorite list's first station, falling back to opening
#     RadioBrowserScreen to search.
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
#   - Round 11's fix still didn't stop the video/background bleeding
#     through. The user found, empirically, that a WHITE background
#     reliably avoids the issue where gray/near-black backgrounds
#     don't. Added a new "header_background" widget spanning the top
#     text area (version/cover/media/meta/status, down to just above
#     the progress bar) with an opaque white background -- previously
#     this whole area had no widget-level background at all, relying
#     entirely on the screen's own (gray) background. elapsed/
#     remaining/queueposition/hint each got their own explicit white
#     background too. The screen's own edges keep the theme's
#     background colour.
#
# 2026-07-28  Build 0007 (device test round 13)
#   - Fixed a real skin error confirmed by device logs across OpenATV,
#     OpenViX and OpenBH: round 12's new "header_background" widget
#     was added to the generated skin XML but never registered as a
#     Python-side component (self["header_background"] = ...) --
#     Enigma2 requires both; the skin XML alone doesn't create a
#     widget. Every device log showed "Component with name
#     'header_background' was not found in skin of screen" for this
#     exact reason. This didn't visibly break the screen (Enigma2
#     skips the one widget it can't construct and continues), but is
#     a real defect, not just a harmless warning. Added the missing
#     self["header_background"] = Label("") registration.
#
# 2026-07-28  Build 0008
#   - Added HELP key handling: opens HelpScreen with this screen's own
#     context-sensitive help document via HelpManager.getHelp(). HELP
#     key action names are PROVISIONAL/unverified on real hardware --
#     see compatibility.py's HELP_KEY_ACTIONS.
#   - Added the lower-right information panel (BUILD_0008_PLAN.md
#     "MainScreen Information Views"): TEXT cycles Lyrics -> Metadata
#     -> Codec Information -> Lyrics... Lyrics come from the new
#     LyricsManager (synchronized .lrc lines tracked against elapsed
#     time when available). TEXT key action names are also
#     PROVISIONAL/unverified.
#   - Added the lower-left Previous/Next queue preview
#     (BUILD_0008_PLAN.md "Previous / Next Preview"): shows the
#     adjacent PlaybackQueue item for local files (new
#     PlaybackController.getAdjacentFiles()) or the adjacent station
#     in the current radio list for Internet Radio.
#   - Added openMusicLibraryScreen() and wired "music_library" into
#     both the Main Menu callback and the startup chooser (OK with
#     nothing playing).
#
# 2026-08-01  Build 0008 (device test round 6)
#   - _seek() now silently ignores the dedicated seek keys while an
#     Internet Radio stream is playing, instead of showing "Seek
#     failed" -- a device log showed this reaching PlaybackController
#     while streaming, which isn't a failure from the user's point of
#     view, just a key that doesn't apply (LEFT/RIGHT already treats
#     streaming differently for the same reason).
#
# 2026-08-01  Build 0008 (device test round 7)
#   - "remaining" always shows actual time remaining now. Build 0007's
#     favorites-view special case (showing the track's position within
#     the current list here instead, e.g. "7/14") was removed per user
#     feedback: the queueposition widget below already shows this,
#     making it here redundant.
#
# 2026-08-01  Build 0008 (device test round 8)
#   - Fixed a real bug confirmed by a device log: on this remote,
#     KEY_INFO's "Break" (release) event fired infoPressed() a second
#     time, ~230ms after "Make" (press) already had, flipping
#     _view_mode right back before the user could see the other view
#     settle -- "vaihtuu kappaleen nimi näkyviin sen aikaa kun painaa
#     epg-nappia" (changes to show the track name for as long as the
#     button is held, then reverts on release) described this exactly.
#     Added a general _isDebounced() guard rather than trying to
#     detect and special-case specific remote control models -- the
#     same technique applies to any other toggle-style handler that
#     turns out to need it later, on this or any other remote.
#
# 2026-08-01  Build 0008 (device test round 9)
#   - _seek() no longer calls PlaybackController.tick() after a
#     successful seek. A device log showed this re-querying GStreamer
#     immediately after seekTo(), catching it still mid-flush from
#     that same seek and transiently returning position 0 -- silently
#     accepted (the sanity check only rejected readings too HIGH, not
#     too low) and overwriting the correct position
#     seekForward()/seekBackward() had just set. Visible as a SECOND
#     seek right after a first one computing its target from "current:
#     0s" instead of the real position. PlaybackController already
#     knows the correct position after a successful seek without
#     asking GStreamer again immediately.
#   - _formatLyricsPanel() now shows a scrolling window of lines
#     (LyricsManager.getScrollWindow()) instead of a single line or
#     the raw, unmoving lyrics block -- see lyrics_manager.py's own
#     change history for the full reasoning and the real report this
#     fixes.
#
# 2026-08-03  Build 0009 (device test round 1)
#   - Fixed a real, confirmed startup crash: two of the new "MainScreen
#     2.0" skin's XML comments used a double hyphen ("--") as prose
#     punctuation -- the same dash style used throughout this
#     project's own Python comments/docstrings, but XML forbids "--"
#     ANYWHERE inside a <!-- --> comment except at the closing "-->"
#     itself. A device log showed this raised
#     xml.etree.ElementTree.ParseError ("not well-formed (invalid
#     token)") the moment MainScreen tried to open, crashing the
#     whole plugin before anything else could run. Fixed both
#     comments (replaced "--" with ","/":" instead); verified by
#     actually parsing the generated skin string with
#     xml.etree.ElementTree (the same parser Enigma2's own skin.py
#     uses), not just checking Python's own syntax -- a Python
#     f-string with malformed XML inside it compiles and runs fine
#     from Python's point of view, so py_compile alone could never
#     have caught this. Also parsed every other Screen's own
#     _buildSkin() output the same way as a precaution; all nine of
#     the others were already valid.
# ------------------------------------------------------------------------------

from __future__ import annotations

import os
import time

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from Components.AVSwitch import AVSwitch
from enigma import ePicLoad, eTimer, getDesktop

from .browserscreen import BrowserScreen
from .compatibility import compatibility
from . import finland_radio_epg_registry
from .help_manager import help_manager
from .information_panel import InformationPanel
from .epg_manager import epg_manager
from .help_screen import HelpScreen
from .config import config_manager
from .developer_screen import DeveloperScreen
from .internetradio_manager import internetradio_manager
from .playlist_manager import playlist_manager
from .localization import _
from .logger import logger
from .mainmenu import MainMenu
from .musiclibraryscreen import MusicLibraryScreen
from .paths import CACHE_PATH, RESOURCE_PATH
from .playback_controller import PlaybackController
from .playbackinfo_screen import PlaybackInfoScreen
from .playlistscreen import PlaylistScreen
from .radiobrowserscreen import RadioBrowserScreen
from .settingsscreen import SettingsScreen
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)
from .statusbar import StatusBar
from .systeminfo import systeminfo
from .version import get_version_string

DEFAULT_ARTWORK_PATH = os.path.join(RESOURCE_PATH, "icons", "default_artwork.png")

# Build 0009, device test round 2 -- _updateCoverArt(None) now means
# "definitely no media, show default artwork" (see that method's own
# docstring), so _cover_file's initial value can no longer be None
# too, or the very first such call would short-circuit on "filename
# == self._cover_file" (None == None) and never run at all -- exactly
# the bug the user reported ("nyt on aloituksessa tyhja").
_COVER_ART_NOT_YET_CHECKED = object()


class MainScreen(Screen):
    """
    MediaPlayer3 primary application window.
    """

    SPECIFICATION_VERSION = "0.5"
    ARCHITECTURE_VERSION = "0.3"

    # Seek step sizes in seconds. LEFT/RIGHT use the fixed short step;
    # FASTFORWARD/REWIND (and their candidate action names) use the
    # long step, which is configurable (playback.seek_step_seconds,
    # Build 0006 device test round 3) -- SEEK_STEP_LONG below is only
    # the fallback default if that config value is ever unavailable.
    SEEK_STEP_SHORT = 10
    SEEK_STEP_LONG = 30

    # Cover art candidate filenames, checked case-insensitively in the
    # current track's directory (requested after a real device test;
    # see docs/Claude_notes_build0005.txt). This is plain Enigma2
    # Pixmap/image loading -- unrelated to the GStreamer playback
    # backend, so it works regardless of which backend plays the audio.
    COVER_ART_FILENAMES = ("cover.jpg", "cover.png", "folder.jpg", "folder.png")

    # Design resolution the skin coordinates below are authored for;
    # _buildSkin() scales every coordinate and font size to whatever
    # the real desktop resolution turns out to be at runtime.
    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 520

    @staticmethod
    def _buildSkin(width: int, height: int) -> str:
        """
        Build MainScreen's skin for an exact `width` x `height`
        window, scaling every coordinate and font size from the
        700x520 design resolution above.

        MainScreen is sized to the full desktop (position 0,0,
        size = getDesktop(0).size()) rather than a fixed small window,
        so the box's own background never shows through around the
        window edges (confirmed fixed on a real device -- see
        docs/Claude_notes_build0005.txt).

        Build 0009 -- MAINSCREEN_SPEC.md's "MainScreen 2.0": three
        primary areas instead of Build 0008's fixed header + Lyrics/
        Metadata/Codec cycle:

            Album Art | Artist - Album / Song   (top, compact)
            Playlist  | Information              (middle, most of
                                                    the screen -- the
                                                    Information Panel
                                                    now gets
                                                    "significantly
                                                    more vertical
                                                    space",
                                                    MAINSCREEN_SPEC.md)
            Progress Bar                         (bottom)

        Only one of the three panels (Player/Playlist/Information) is
        active at a time (selected via EPG/INFO, replacing Build
        0008's TEXT-based info-view cycling entirely --
        MAINSCREEN_SPEC.md "Remote Control": "The TEXT button is no
        longer used"). The active panel's own title widget
        (player_title/playlist_title/info_title) is drawn in the
        skin's "highlight" colour; the other two stay in the normal
        panel text colour -- MainScreen's Python side is responsible
        for actually swapping `foregroundColor` per refresh, this
        skin only establishes the three distinct title widgets that
        makes that possible.

        The old fixed "MediaPlayer3 x.y.z" banner and the keyboard-
        shortcut hint footer are both dropped in this layout -- the
        version now lives in the screen's own `title` attribute
        instead of a full-width on-screen banner, and HELP now opens
        real, context-sensitive documentation per active panel
        instead of a permanently-visible hint line
        (MAINSCREEN_SPEC.md "Help Integration"), freeing up the
        vertical space the Information Panel needed.

        Build 0006 -- colors and font family come from SkinManager's
        current theme/skin instead of being hardcoded, so switching
        theme in Settings changes MainScreen's appearance without a
        restart (MainScreen re-applies its skin on every open).
        """

        sx = width / MainScreen.DESIGN_WIDTH
        sy = height / MainScreen.DESIGN_HEIGHT

        background_color = to_opaque_skin_color(skin_manager.getColor("background", "#0A0A0A"))
        panel_background_color = to_opaque_skin_color(PANEL_BACKGROUND_COLOR)
        panel_text_color = PANEL_TEXT_COLOR
        selection_background_color = to_opaque_skin_color(skin_manager.getColor("selection_background", "#0056B3"))
        progress_color = skin_manager.getColor("progress", "#E6E6E6")
        progress_track_color = to_opaque_skin_color(skin_manager.getColor("accent", "#4C4449"))
        font_family = skin_manager.getFont("Regular")

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="{font_family};{max(10, int(size * sx))}"'

        return f"""
        <screen name="MediaPlayer3MainScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="{get_version_string()}">

            <!-- Top area: Album Art | Artist - Album / Song -->

            <widget name="cover"
                    {rect(20, 10, 160, 160)}
                    alphatest="blend"/>

            <widget name="player_title_bg_normal"
                    {rect(200, 10, 480, 22)}
                    backgroundColor="{panel_background_color}"/>

            <widget name="player_title_bg_active"
                    {rect(200, 10, 480, 22)}
                    backgroundColor="{selection_background_color}"/>

            <widget name="player_title"
                    {rect(200, 10, 480, 22)}
                    {font(14)}
                    halign="left"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="meta"
                    {rect(200, 36, 480, 40)}
                    {font(18)}
                    halign="left"
                    foregroundColor="{panel_text_color}"
                    backgroundColor="{panel_background_color}"/>

            <widget name="media"
                    {rect(200, 78, 480, 84)}
                    {font(22)}
                    halign="left"
                    foregroundColor="{panel_text_color}"
                    backgroundColor="{panel_background_color}"/>

            <!-- Slim status line (StatusBar messages: "Seek failed",
                 loading confirmations, etc.): not part of
                 MAINSCREEN_SPEC.md's own ASCII layout diagram, which
                 only captures the three main panels, but dropping
                 transient status feedback entirely would be a real
                 regression from Build 0008, so it's kept as a slim
                 row in the gap between the top and middle areas. -->

            <widget name="status"
                    {rect(200, 162, 480, 18)}
                    {font(12)}
                    halign="left"
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    backgroundColor="{panel_background_color}"/>

            <!-- Middle area: Playlist | Information, the bulk of
                 the screen, per MAINSCREEN_SPEC.md's "significantly
                 more vertical space for the Information Panel" -->

            <widget name="playlist_title_bg_normal"
                    {rect(20, 185, 160, 24)}
                    backgroundColor="{panel_background_color}"/>

            <widget name="playlist_title_bg_active"
                    {rect(20, 185, 160, 24)}
                    backgroundColor="{selection_background_color}"/>

            <widget name="playlist_title"
                    {rect(20, 185, 160, 24)}
                    {font(15)}
                    halign="left"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="playlist_list"
                    {rect(20, 213, 160, 252)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="info_title_bg_normal"
                    {rect(200, 185, 480, 24)}
                    backgroundColor="{panel_background_color}"/>

            <widget name="info_title_bg_active"
                    {rect(200, 185, 480, 24)}
                    backgroundColor="{selection_background_color}"/>

            <widget name="info_title"
                    {rect(200, 185, 480, 24)}
                    {font(15)}
                    halign="left"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="info_content"
                    {rect(200, 213, 480, 252)}
                    {font(15)}
                    halign="left"
                    foregroundColor="{panel_text_color}"
                    backgroundColor="{panel_background_color}"/>

            <!-- Bottom area: Progress Bar -->

            <widget name="elapsed"
                    {rect(20, 475, 100, 20)}
                    {font(16)}
                    halign="left"
                    valign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="progressbar"
                    {rect(130, 478, 440, 14)}
                    borderWidth="1"
                    backgroundColor="{progress_track_color}"
                    foregroundColor="{progress_color}"/>

            <widget name="remaining"
                    {rect(580, 475, 100, 20)}
                    {font(16)}
                    halign="right"
                    valign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            <widget name="queueposition"
                    {rect(20, 498, 660, 18)}
                    {font(13)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

        </screen>
    """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, session):

        # self.skin must be set *before* Screen.__init__() runs, since
        # that is what actually applies the skin -- an instance
        # attribute here overrides the (unused, but still present as a
        # documented fallback) class-level default.
        try:
            desktop_size = getDesktop(0).size()

            self.skin = self._buildSkin(desktop_size.width(), desktop_size.height())

        except Exception as error:

            logger.warning("[MainScreen] Unable to determine desktop size, using design resolution: %s", error)

            self.skin = self._buildSkin(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        Screen.__init__(self, session)

        self.session = session

        self._initialized = False

        self._log("Created")

        #
        # MainScreen owns the single PlaybackController instance for the
        # whole application lifetime (ARCHITECTURE.md section 4).
        #
        self._playback = PlaybackController()

        # Build 0006 (device test round 3) -- stop whatever's playing
        # (typically live TV) immediately, rather than waiting until
        # the user actually picks a track. A real device test showed
        # TV audio continuing in the background until playback of the
        # first file actually started.
        try:
            self._playback.stopPreviousServiceNow()

        except Exception as error:

            logger.warning("[MainScreen] Unable to stop previous service at startup: %s", error)

        # Avoids re-resolving artwork on every 1-second refresh tick --
        # only re-resolved when the current file changes. Keyed by
        # file (not directory) since Build 0006 embedded artwork can
        # differ track to track within the same directory.
        self._cover_file = _COVER_ART_NOT_YET_CHECKED

        # Internet Radio station navigation state (Build 0007 --
        # BUILD_0007_PLAN.md "MainScreen Navigation"). Populated by
        # playRadioStation(); LEFT/RIGHT switch _radio_list_name
        # between "favorites"/"history", UP/DOWN step _radio_index
        # within whichever list is currently active.
        self._radio_list_name = self._resolveInitialRadioListName()
        self._radio_list = []
        self._radio_index = -1

        # Build 0009, MAINSCREEN_SPEC.md "Active Panels" -- replaces
        # Build 0008's TEXT-driven _info_view cycle entirely ("The
        # TEXT button is no longer used"). One of "player"/"playlist"/
        # "information"; EPG/INFO cycles through them
        # (activePanelPressed()). Directional-key behaviour actually
        # changing per active panel (MAINSCREEN_SPEC.md's Player/
        # Playlist/Information Panel key tables) is a separate,
        # follow-up piece of work -- this build establishes the panel
        # state and its visual highlighting (skin's
        # player_title/playlist_title/info_title) first.
        self._active_panel = "player"

        # Build 0009, MAINSCREEN_SPEC.md "Playlist Panel" -- which
        # absolute PlaybackQueue/radio-list index each entry currently
        # shown in playlist_list corresponds to, and whether those
        # indices are radio-list or PlaybackQueue indices. Populated
        # by _updatePlaylistPanel(); read by okPressed() to jump to
        # the selected entry.
        self._playlist_panel_indices: list = []
        self._playlist_panel_is_radio = False

        # Build 0009 -- owns the Information Panel's page list,
        # selection and scroll position (INFORMATION_PANEL_SPEC.md).
        # Replaces Build 0008's fixed lyrics/metadata/codec cycle
        # (_info_view, _formatLyricsPanel/_formatMetadataPanel/
        # _formatCodecPanel, all removed) with a dynamically-built
        # page list that also covers Internet Radio (Radio EPG/Now
        # Playing/Station), which the old fixed cycle never did.
        self._information_panel = InformationPanel()

        # Build 0008, device test round 8 -- last-fired time per action
        # name, used by _isDebounced() to guard toggle-style handlers
        # against remotes/keymaps that bind an action to both the
        # press AND release hardware events for the same key (confirmed
        # by a device log: KEY_INFO's "Break" event fired
        # infoPressed() a second time, ~230ms after "Make" already had,
        # flipping _view_mode right back before the user could see it
        # settle). A general, remote-agnostic fix rather than trying to
        # detect and special-case specific remote control models --
        # the same technique applies to any other toggle-style handler
        # that turns out to need it later, on this or any other remote.
        self._last_action_time = {}

        # RADIO switches to Internet Radio -- resumes the last-played
        # station if there is one (Build 0007, device test round 3;
        # refined from round 2, which also tracked a "last local file"
        # to resume -- since round 3 changed radio-mode RADIO to open
        # BrowserScreen instead, that tracking is no longer read
        # anywhere and was removed). _last_radio_station is set
        # explicitly wherever a station is actually played
        # (playRadioStation()/_playRadioListEntry()), since MainScreen
        # needs the real station dict, not just a URL, to resume it.
        self._last_radio_station = None

        # Currently selected local playlist for LEFT/RIGHT cycling in
        # favorites view (Build 0007, device test round 3) --
        # mirrors _radio_list_name's role for radio, but for
        # PlaylistManager's stored playlists. None means "not
        # currently playing from a stored playlist" (e.g. a
        # BrowserScreen folder queue) -- the top label falls back to
        # the folder name in that case (_updateTopLabel()).
        self._current_local_playlist_name = None

        # ePicLoad decodes and scales cover art asynchronously to fit
        # the "cover" widget exactly (fixes a real device bug where an
        # unscaled cover.jpg only showed its top-left corner, zoomed
        # in -- see docs/Claude_notes_build0005.txt). ePicLoad itself
        # is a base Enigma2 binding, identical across images, like
        # eTimer -- used directly, not through compatibility.py.
        # Connecting its PictureData signal IS version-dependent
        # (differs across bindings -- see
        # compatibility.connectPictureDataSignal()), so that one step
        # goes through compatibility.py.
        self._picload = ePicLoad()
        compatibility.connectPictureDataSignal(self._picload, self._onCoverArtDecoded)

        # Periodic refresh timer (MAINSCREEN_SPEC.md "Screen Refresh",
        # typical interval 1 second). eTimer is a base Enigma2 binding,
        # identical across images -- used directly, not through
        # compatibility.py.
        self._refresh_timer = eTimer()
        self._refresh_timer.callback.append(self._onRefreshTimer)

        # Build 0009, device test round 6 -- holds the one-shot retry
        # timer _decodeCoverArt() creates when self["cover"].instance
        # isn't ready yet (see that method's own docstring). Stored on
        # self so the timer object itself isn't garbage-collected
        # before it fires, same reason _refresh_timer is kept here
        # too rather than as a local variable.
        self._pending_cover_retry_timer = None

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[MainScreen] %s", message)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _initialize(self) -> None:
        """
        Initialize MainScreen (MAINSCREEN_SPEC.md section 3, Lifecycle).
        """

        self._log("Initializing")

        systeminfo.logSystemInformation()

        self["cover"] = Pixmap()
        self["player_title_bg_normal"] = Label("")
        self["player_title_bg_active"] = Label("")
        self["player_title"] = Label(_("Player"))
        self["meta"] = Label("")
        self["media"] = Label(_("No media selected"))
        self["status"] = Label(_("Ready"))
        self["playlist_title_bg_normal"] = Label("")
        self["playlist_title_bg_active"] = Label("")
        self["playlist_title"] = Label(_("Playlist"))
        self["playlist_list"] = MenuList([])
        self["info_title_bg_normal"] = Label("")
        self["info_title_bg_active"] = Label("")
        self["info_title"] = Label(_("Information"))
        self["info_content"] = Label("")
        self["elapsed"] = Label("--:--")
        self["progressbar"] = ProgressBar()
        self["remaining"] = Label("--:--")
        self["queueposition"] = Label("")

        self._statusbar = StatusBar(self["status"])

        actions = {
            "ok": self.okPressed,
            "cancel": self.exitPressed,
            "play": self.playPressed,
            "pause": self.pausePressed,
            "stop": self.stopPressed,
            "menu": self.menuPressed,
        }

        for action_name in compatibility.getPvrKeyActionNames():
            actions[action_name] = self.pvrPressed

        for action_name in compatibility.getNextTrackKeyActionNames():
            actions[action_name] = self.nextTrackPressed

        for action_name in compatibility.getPreviousTrackKeyActionNames():
            actions[action_name] = self.previousTrackPressed

        # Build 0009, MAINSCREEN_SPEC.md "Player Panel": "CH+ / CH- ->
        # Previous / Next track". Best-effort, same as everywhere else
        # this project has tried CH+/CH- (RadioBrowserScreen/
        # MusicLibraryScreen, Build 0007) -- Build 0007's own device
        # testing left it an open question whether CH+/CH- reaches a
        # custom Screen's ActionMap at all on real hardware (it may be
        # intercepted at the InfoBarGenerics level before ever getting
        # here), so this may turn out to be a no-op in practice. Not
        # confirmed either way for MainScreen specifically yet.
        for action_name in compatibility.getChannelUpKeyActionNames():
            actions[action_name] = self.nextTrackPressed

        for action_name in compatibility.getChannelDownKeyActionNames():
            actions[action_name] = self.previousTrackPressed

        for action_name in compatibility.getSeekForwardKeyActionNames():
            actions[action_name] = self.seekForwardPressed

        for action_name in compatibility.getSeekBackwardKeyActionNames():
            actions[action_name] = self.seekBackwardPressed

        for action_name in compatibility.getRadioKeyActionNames():
            actions[action_name] = self.radioPressed

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.activePanelPressed

        for action_name in compatibility.getHelpKeyActionNames():
            actions[action_name] = self.helpPressed

        # LEFT/RIGHT double as a smaller seek step, per user feedback
        # after a real device test (docs/Claude_notes_build0005.txt).
        actions["left"] = self.seekBackwardShortPressed
        actions["right"] = self.seekForwardShortPressed

        # UP/DOWN: Internet Radio station navigation only (Build 0007
        # -- a no-op for local file playback, see upPressed()/
        # downPressed()).
        actions["up"] = self.upPressed
        actions["down"] = self.downPressed

        self["actions"] = ActionMap(
            [
                "OkCancelActions",
                "ColorActions",
                "MediaPlayerActions",
                "InfobarActions",
                "InfobarSeekActions",
                "DirectionActions",
                "MenuActions",
                "InfoActions",
                "InfobarEPGActions",
                "HelpActions",
                "TeletextActions",
            ],
            actions,
            -1,
        )

        self._applyUiSettings()

        self._updateDisplay()

        self._refresh_timer.start(1000, False)

        self._initialized = True

        self._log("Ready")

        self.onShown.append(self._onShown)

    # ------------------------------------------------------------------

    def _onShown(self) -> None:

        self._updateDisplay()

    # ------------------------------------------------------------------

    def _onRefreshTimer(self) -> None:
        """
        Periodic refresh (MAINSCREEN_SPEC.md "Screen Refresh", typical
        interval 1 second). Advances PlaybackController's cached
        position/duration (and, via that, Automatic Next Track) and
        redraws the display. A no-op cost when nothing is playing --
        PlaybackController.tick() itself already skips work in that
        case.
        """

        self._playback.tick()

        self._updateDisplay()

# End of Part 1
    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _applyUiSettings(self) -> None:
        """
        Show/hide presentation widgets per the "User Interface"
        settings category (SETTINGSSCREEN_SPEC.md section 6). Called
        on open and again every time a child Screen closes, so a
        change made in SettingsScreen takes effect immediately without
        restarting MediaPlayer3.
        """

        self._show_progress_bar = bool(config_manager.get("ui.show_progress_bar", True))
        self._show_elapsed_time = bool(config_manager.get("ui.show_elapsed_time", True))
        self._show_remaining_time = bool(config_manager.get("ui.show_remaining_time", True))
        self._show_playback_state = bool(config_manager.get("ui.show_playback_state", True))

        self._setWidgetVisible(self["progressbar"], self._show_progress_bar)
        self._setWidgetVisible(self["elapsed"], self._show_elapsed_time)
        self._setWidgetVisible(self["remaining"], self._show_remaining_time)
        self._setWidgetVisible(self["status"], self._show_playback_state)

    # ------------------------------------------------------------------

    def _setWidgetVisible(self, widget, visible: bool) -> None:

        try:
            if visible:
                widget.show()
            else:
                widget.hide()

        except Exception as error:

            logger.verbose(f"[MainScreen] Unable to set widget visibility: {error}")

    # ------------------------------------------------------------------

    def _updateDisplay(self) -> None:
        """
        Refresh MainScreen's display from PlaybackController's current
        state (MAINSCREEN_SPEC.md section 4).
        """

        logger.verbose("[MainScreen] UI refresh.")

        if not self._playback.hasMedia():

            self["media"].setText(_("No media selected"))

            self["meta"].setText("")

            self._statusbar.showReady()

            self["elapsed"].setText("--:--")
            self["remaining"].setText("--:--")
            self["progressbar"].setValue(0)
            self["queueposition"].setText("")
            self["playlist_list"].setList([])
            self["info_content"].setText("")

            self._updatePanelHighlighting()

            self._updateCoverArt(None)

            return

        filename = self._playback.getCurrentFile()

        # Build 0006 -- real tag Title takes priority over the
        # filename, per PLAYBACKINFO_SPEC.md's Metadata Priority rules
        # (and per user feedback after a real device test: the
        # filename was always shown even when a Title tag existed).
        self["media"].setText(self._formatTitle(filename))

        self["meta"].setText(self._formatArtistAlbum())

        self._statusbar.showState(self._playback.getState(), filename)

        self._updateCoverArt(filename)

        elapsed = self._playback.getElapsedTime()
        duration = self._playback.getDuration()

        self["elapsed"].setText(self._formatTime(elapsed))

        # Build 0008, device test round 7 -- "remaining" always shows
        # actual time remaining now. Build 0007's favorites-view
        # special case (showing the track's position within the
        # current list here instead, e.g. "7/14") was removed per
        # user feedback: the queueposition widget below already shows
        # this, making it here redundant ("Alhaalla lukee oikein
        # kokonaisaika ja kappalemäärä, joten jäljellä olevan ajan
        # kohdalla ei tarvitsisi lukea kappalemäärää").
        if duration is not None and elapsed is not None:

            self["remaining"].setText(self._formatTime(max(0, duration - elapsed)))

        else:

            self["remaining"].setText("--:--")

        progress = self._playback.getProgress()

        self["progressbar"].setValue(int(progress * 100) if progress is not None else 0)

        self["queueposition"].setText(self._formatQueuePosition(duration))

        self._updatePlaylistPanel()

        self._updateInformationPanel(filename, elapsed, duration)

        self._updatePanelHighlighting()

        logger.verbose(
            "[MainScreen] Progress bar update\n\nElapsed: %s\n\nRemaining: %s\n\nProgress: %s\n",
            self._formatTime(elapsed),
            self._formatTime(duration - elapsed) if duration is not None and elapsed is not None else "--:--",
            f"{int(progress * 100)}%" if progress is not None else "Unknown",
        )

    # ------------------------------------------------------------------

    def _updatePlaylistPanel(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md "Playlist Panel" -- replaces
        Build 0008's static queue_preview text (just "Previous"/"Next"
        names) with a real MenuList showing Previous/Current/Next, the
        current item highlighted.

        Also records, in self._playlist_panel_indices, which absolute
        PlaybackQueue index (local) or radio-list index (streaming)
        each displayed entry corresponds to -- okPressed() needs this
        to jump to the right place when the Playlist Panel is active
        and the user selects something other than the current item.
        """

        self._playlist_panel_is_radio = self._playback.isPlayingStream()

        if self._playlist_panel_is_radio:

            entries = []

            self._playlist_panel_indices = []

            current_position_in_list = None

            if self._radio_list and 0 <= self._radio_index < len(self._radio_list):

                if self._radio_index > 0:

                    entries.append(self._radio_list[self._radio_index - 1].get("name", "--"))

                    self._playlist_panel_indices.append(self._radio_index - 1)

                current_position_in_list = len(entries)

                entries.append(self._radio_list[self._radio_index].get("name", "--"))

                self._playlist_panel_indices.append(self._radio_index)

                if self._radio_index + 1 < len(self._radio_list):

                    entries.append(self._radio_list[self._radio_index + 1].get("name", "--"))

                    self._playlist_panel_indices.append(self._radio_index + 1)

            self["playlist_list"].setList(entries)

            if current_position_in_list is not None:

                self._moveListToIndex(self["playlist_list"], current_position_in_list)

            return

        previous_file, next_file = self._playback.getAdjacentFiles()

        current_file = self._playback.getCurrentFile()

        current_queue_index = self._playback.getQueuePosition() - 1

        entries = []

        self._playlist_panel_indices = []

        current_position_in_list = None

        if previous_file:

            entries.append(self._basenameWithoutExtension(previous_file))

            self._playlist_panel_indices.append(current_queue_index - 1)

        if current_file:

            current_position_in_list = len(entries)

            entries.append(self._basenameWithoutExtension(current_file))

            self._playlist_panel_indices.append(current_queue_index)

        if next_file:

            entries.append(self._basenameWithoutExtension(next_file))

            self._playlist_panel_indices.append(current_queue_index + 1)

        self["playlist_list"].setList(entries)

        if current_position_in_list is not None:

            self._moveListToIndex(self["playlist_list"], current_position_in_list)

    # ------------------------------------------------------------------

    def _moveListToIndex(self, widget, target_index: int) -> None:
        """
        Moves `widget`'s selection to `target_index` using only
        up()/down() -- the most basic list-navigation primitives,
        universally supported by every Enigma2 MenuList/List
        implementation across every supported image, unlike
        moveToIndex() (not available in at least one tested
        environment). Fine performance-wise here since
        playlist_list never holds more than 3 entries
        (Previous/Current/Next).
        """

        current = widget.getSelectedIndex()

        if current is None:
            return

        while current < target_index:

            widget.down()

            current += 1

        while current > target_index:

            widget.up()

            current -= 1

    # ------------------------------------------------------------------

    def _playSelectedPlaylistEntry(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md "Playlist Panel" -- OK while
        the Playlist Panel is active: "The selected entry immediately
        becomes the new PlaybackQueue position. Playback continues
        normally through the remaining playlist." Uses
        self._playlist_panel_indices (populated by
        _updatePlaylistPanel()) to map the MenuList's current
        selection back to an absolute queue/radio-list index.
        """

        selected_position = self["playlist_list"].getSelectedIndex()

        if selected_position is None or not (0 <= selected_position < len(self._playlist_panel_indices)):
            return

        target_index = self._playlist_panel_indices[selected_position]

        if self._playlist_panel_is_radio:

            if not (0 <= target_index < len(self._radio_list)):
                return

            # Build 0009, device test round 3: a real device log and
            # screenshot showed selecting an entry here correctly
            # showed "Omat" briefly, then flipped to "Playlist:
            # favorites" (empty, stuck) -- traced to this call
            # omitting list_name, which made playRadioStation() fall
            # back to reading cfg.radio.navigation_mode's raw value
            # ("favorites"/"history", a MODE selector) and treating it
            # as if it were an actual favorite list's NAME. There is
            # no favorite list literally named "favorites", so that
            # always produced an empty list. Passing list_name
            # explicitly keeps the actual active list (e.g. "Omat").
            self.playRadioStation(self._radio_list[target_index], list_name=self._radio_list_name)

            return

        if self._playback.jumpToQueueIndex(target_index):

            self._updateDisplay()

        else:

            self._statusbar.showError(_("Unable to play selected track"))

    # ------------------------------------------------------------------

    def _switchActivePlaylist(self, direction: int) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md "Playlist Panel" -- LEFT/RIGHT
        while the Playlist Panel is active switches the active
        playlist/radio list, reusing the exact same underlying
        mechanism the Player Panel's own LEFT/RIGHT used for this in
        Build 0008 (_switchRadioList()/_cycleLocalPlaylist()) -- only
        the panel that owns triggering it has changed.
        """

        if self._playback.isPlayingStream():

            self._switchRadioList(direction)

        else:

            self._cycleLocalPlaylist(direction)

    # ------------------------------------------------------------------

    def _basenameWithoutExtension(self, filepath: str) -> str:

        return os.path.splitext(os.path.basename(filepath))[0]

    # ------------------------------------------------------------------

    def _updateInformationPanel(self, filename, elapsed, duration) -> None:
        """
        Build 0009, INFORMATION_PANEL_SPEC.md -- replaces Build 0008's
        fixed Lyrics/Metadata/Codec cycle (_info_view, TEXT-driven)
        with InformationPanel's dynamically-built page list, which
        also covers Internet Radio (Radio EPG/Now Playing/Station)
        that the old fixed cycle never did.
        """

        station = self._radio_list[self._radio_index] if (
            self._playback.isPlayingStream() and self._radio_list and 0 <= self._radio_index < len(self._radio_list)
        ) else None

        self._information_panel.refresh(self._playback, filename, elapsed, duration, station=station)

        self["info_content"].setText(self._information_panel.getCurrentContent())

    # ------------------------------------------------------------------

    def activePanelPressed(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md "Remote Control" -- EPG/INFO
        cycles the active panel: Player -> Playlist -> Information ->
        Player. Replaces Build 0008's INFO (view-mode toggle) and TEXT
        (info-view cycle) entirely; both are gone.

        Build 0009, device test round 9: while streaming Internet
        Radio, the Playlist Panel is skipped entirely in this cycle
        (Player -> Information -> Player) per user request ("Laitetaan
        Player tilassa sivunuolilla suosikkilistan vaihto ja
        poistetaan kokonaan siirtyminen playlist tilaan
        radiokanavilla. Playlist nakyma voi silti paivittya kuten
        tahankin asti.") -- LEFT/RIGHT in the Player Panel now covers
        what the Playlist Panel offered for radio anyway (switching
        favorite lists, see seekForwardShortPressed()), and seeking
        never applied to a live stream regardless. playlist_list/
        playlist_title keep updating in the background exactly as
        before (_updatePlaylistPanel() doesn't check which panel is
        active) -- only reachability via this cycle changes.

        Reuses _isDebounced() (Build 0008, device test round 8): a
        device log showed INFO firing on both the Make and Break
        hardware events on at least one remote -- the same guard
        applies here since EPG/INFO is the same physical key.
        """

        logger.verbose("[MainScreen] EPG/INFO pressed.")

        if self._isDebounced("active_panel"):

            logger.verbose("[MainScreen] EPG/INFO debounced (fired twice for the same physical press).")

            return

        order = ("player", "information") if self._playback.isPlayingStream() else ("player", "playlist", "information")

        if self._active_panel not in order:

            # Was on "playlist" when radio playback started -- no
            # longer reachable in the streaming cycle, land on Player.
            self._active_panel = "player"

        else:

            self._active_panel = order[(order.index(self._active_panel) + 1) % len(order)]

        self._log(f"Active panel: {self._active_panel}")

        self._updateDisplay()

    # ------------------------------------------------------------------

    def _updatePanelHighlighting(self) -> None:
        """
        Marks whichever of player_title/playlist_title/info_title
        matches self._active_panel (MAINSCREEN_SPEC.md "Active
        Panels": "The active panel title is highlighted using the
        active selection colour provided by the current Enigma2
        skin").

        Build 0009, device test round 2: added a background-colour
        highlight per user request ("Otsikkorivilla voisi olla
        sininen tausta, kun on valittuna"), using ONLY hide()/show()
        rather than a runtime foreground/background-colour change --
        Enigma2's exact API for recolouring an already-constructed
        widget varies across images/versions and couldn't be verified
        against real hardware from this environment. Each title has a
        pair of identically-positioned background rectangles
        (<title>_bg_normal/<title>_bg_active, see _buildSkin()) with
        the title's own text on top (transparent background); only
        one of the pair is ever shown at a time. hide()/show() are
        long-confirmed safe in this codebase (cover art, and every
        other widget-visibility toggle so far). The text marker
        ("> ") from the previous round is kept alongside the colour --
        costs nothing and still helps wherever the highlight colour
        alone isn't distinct enough (e.g. a custom skin).

        playlist_title also absorbs Build 0007's old "show the current
        playlist/folder/history name" behaviour (previously shown in
        the now-removed top-of-screen version banner, toggled by
        _view_mode -- see _getPlaylistLabel()) -- the Playlist Panel is
        the natural home for that now that it's always visible rather
        than only in a toggled "favorites view".
        """

        for panel_name, bg_normal_name, bg_active_name in (
            ("player", "player_title_bg_normal", "player_title_bg_active"),
            ("playlist", "playlist_title_bg_normal", "playlist_title_bg_active"),
            ("information", "info_title_bg_normal", "info_title_bg_active"),
        ):

            is_active = panel_name == self._active_panel

            try:
                self[bg_normal_name].hide() if is_active else self[bg_normal_name].show()

                self[bg_active_name].show() if is_active else self[bg_active_name].hide()

            except Exception as error:

                logger.verbose(f"[MainScreen] Unable to set panel highlight visibility: {error}")

        player_marker = "> " if self._active_panel == "player" else ""

        self["player_title"].setText(f"{player_marker}{_('Player')}")

        playlist_marker = "> " if self._active_panel == "playlist" else ""

        self["playlist_title"].setText(f"{playlist_marker}{self._getPlaylistLabel()}")

        info_marker = "> " if self._active_panel == "information" else ""

        self["info_title"].setText(f"{info_marker}{self._information_panel.getCurrentTitle()}")

    # ------------------------------------------------------------------

    def _getPlaylistLabel(self) -> str:
        """
        Returns "Playlist" on its own, or "Playlist: <name>" when a
        specific playlist/folder/radio list is active -- folded in
        from Build 0007's _updateTopLabel() (see this file's own
        change history), which used to show this in a now-removed
        top-of-screen banner instead.
        """

        if not self._playback.hasMedia():
            return _("Playlist")

        if self._playback.isPlayingStream():

            list_label = _("History") if self._radio_list_name == "history" else self._radio_list_name

            return f"{_('Playlist')}: {list_label}" if list_label else _("Playlist")

        if self._current_local_playlist_name:

            return f"{_('Playlist')}: {self._current_local_playlist_name}"

        filename = self._playback.getCurrentFile()

        folder_name = os.path.basename(os.path.dirname(filename)) if filename else ""

        return f"{_('Playlist')}: {folder_name}" if folder_name else _("Playlist")

    # ------------------------------------------------------------------

    def _formatPositionCount(self) -> str:
        """
        Return "N/M" (1-based position / total count) within the
        current queue or radio list, for the favorites view's
        remaining-time position (Build 0007).
        """

        if self._playback.isPlayingStream():

            if not self._radio_list:

                return "--/--"

            return f"{self._radio_index + 1}/{len(self._radio_list)}"

        size = self._playback.getQueueSize()

        if size <= 0:

            return "--/--"

        return f"{self._playback.getQueuePosition()}/{size}"

    # ------------------------------------------------------------------

    def _formatTitle(self, filename) -> str:
        """
        Return the track's Title, preferring real tag metadata over
        the filename (Build 0006, per user feedback after a real
        device test) -- matches PLAYBACKINFO_SPEC.md's Metadata
        Priority rules.
        """

        if not filename:
            return "Unknown"

        metadata = self._playback.getMetadata()

        if metadata is not None:

            title = metadata.get("title", "Unknown")

            if title and title != "Unknown":
                return title

        return os.path.basename(filename)

    # ------------------------------------------------------------------

    def _formatArtistAlbum(self) -> str:
        """
        Return "Artist \u2013 Album" using real tag metadata when
        available (Build 0006), falling back to the "Unknown Artist"/
        "Unknown Album" placeholders MainScreen used before metadata
        support existed.

        Build 0009, device test round 9: while streaming Internet
        Radio, local file metadata obviously never applies (always
        "Unknown Artist \u2013 Unknown Album" for every station), so
        this now shows the current station's Now Playing info
        instead, per user request ("Radiolla ylhaalla lukee nyt
        Unknown - Unknown. Siina voisi nakya now playing -tieto").
        Falls back to the station's own name when now-playing data
        isn't available for that station (not every station has a
        registered provider or sends ICY tags), rather than an empty
        or placeholder-looking line.

        Build 0009, device test round 10: Yle stations only have a
        schedule provider registered (Teksti-TV has no track-level
        now-playing data, just programme titles -- see
        finland_radio_epg_registry.py), so getNowPlaying() falls
        through to generic ICY stream tags for them, which Yle's
        streams evidently don't send either -- the meta line fell all
        the way to the bare station name even though the Information
        Panel's Radio EPG page clearly had the current programme's
        title available. Added that as a middle fallback: current
        programme title (from schedule data) when Now Playing itself
        isn't available, before finally falling back to just the
        station name when neither is.
        """

        if self._playback.isPlayingStream():

            station = (
                self._radio_list[self._radio_index]
                if self._radio_list and 0 <= self._radio_index < len(self._radio_list)
                else None
            )

            if station is not None:

                try:
                    now_playing = epg_manager.getNowPlaying(station)

                except Exception as error:

                    logger.verbose(f"[MainScreen] Now-playing lookup failed for meta line: {error}")

                    now_playing = {"available": False}

                if now_playing.get("available"):

                    return epg_manager.formatNowPlaying(now_playing)

                try:
                    programme = epg_manager.getCurrentProgramme(station)

                except Exception as error:

                    logger.verbose(f"[MainScreen] Current-programme lookup failed for meta line: {error}")

                    programme = None

                if programme and programme.get("title"):

                    return programme["title"]

                return station.get("name", "")

            return ""

        metadata = self._playback.getMetadata()

        if metadata is None:

            return f"{_('Unknown Artist')} \u2013 {_('Unknown Album')}"

        artist = metadata.get("artist", "Unknown")

        album = metadata.get("album", "Unknown")

        return f"{artist} \u2013 {album}"

    # ------------------------------------------------------------------

    def _formatQueuePosition(self, duration=None) -> str:
        """
        Return "MM:SS   Track N / M" for the current Playback Queue
        (total duration shown before the track text, per user
        feedback after a real device test), or just "MM:SS" / "" when
        there is no queue (single-file playback outside a queue).
        """

        duration_text = self._formatTime(duration) if duration is not None else None

        size = self._playback.getQueueSize()

        if size <= 0:
            return duration_text or ""

        track_text = f"Track {self._playback.getQueuePosition()} / {size}"

        if duration_text is None:
            return track_text

        return f"{duration_text}   {track_text}"

    # ------------------------------------------------------------------

    def _updateCoverArt(self, filename) -> None:
        """
        Show artwork for `filename` in the small "cover" widget,
        following BUILD_0006_PLAN.md's "Artwork loading priority":

            1. Embedded artwork (from PlaybackController's cached
               metadata -- ID3 APIC / FLAC PICTURE block)
            2. cover.jpg / cover.png / folder.jpg / folder.png in the
               file's directory
            3. Default MediaPlayer3 artwork (always bundled, so
               something is always shown once media is playing)

        Cached per *file* rather than per directory (Build 0006 --
        embedded artwork can differ track to track within the same
        directory, unlike a shared cover.jpg); only re-resolves
        artwork when the file actually changed since the last call.

        Requested after real device tests (Build 0005): the box's own
        generic audio-playback background showed through MainScreen's
        window (fixed by making MainScreen fullscreen), and the
        initial cover art implementation only showed a zoomed,
        unscaled top-left crop of the image (fixed by scaling via
        ePicLoad). The cover widget is a modest corner square,
        positioned so no text widget overlaps it -- the same layout
        approach YampMusicPlayer's and OpenPli MediaPlayer's own
        coverArt widgets use (both checked per user request; see
        docs/Claude_notes_build0005.txt). Scaling/decoding uses
        ePicLoad, which runs asynchronously -- the actual widget
        update happens in _onCoverArtDecoded() once decoding
        completes.
        """

        if filename == self._cover_file:
            return

        self._cover_file = filename

        if not filename:

            # Build 0009, device test round 2 -- previously hid the
            # cover widget entirely here, leaving it blank at startup
            # before anything has played yet: "Favicon kohdalla voi
            # aina olla jokin kuva, nyt on aloituksessa tyhjä." Falls
            # through to the same default-artwork logic used below
            # when a file is playing but has no other artwork, instead
            # of returning early.
            if os.path.exists(DEFAULT_ARTWORK_PATH):

                logger.verbose("[MainScreen] Artwork source: default artwork (no media)\n")

                self._decodeCoverArt(DEFAULT_ARTWORK_PATH)

            else:

                self["cover"].hide()

            return

        artwork_path = None
        source = None

        if self._playback.isPlayingStream():

            artwork_path = self._resolveStationFavicon()

            source = "station favicon"

        else:

            artwork_path = self._resolveEmbeddedArtworkFile()

            source = "embedded artwork"

            if artwork_path is None:

                artwork_path = self._findFolderCoverArt(os.path.dirname(filename))

                source = "folder artwork"

        if artwork_path is None:

            artwork_path = DEFAULT_ARTWORK_PATH if os.path.exists(DEFAULT_ARTWORK_PATH) else None

            source = "default artwork"

        if artwork_path is None:

            self._log("Artwork unavailable: no embedded, folder or default artwork found.")

            self["cover"].hide()

            return

        logger.verbose(f"[MainScreen] Artwork source: {source}\n\nPath: {artwork_path}\n")

        self._decodeCoverArt(artwork_path)

    # ------------------------------------------------------------------

    def _resolveStationFavicon(self):
        """
        Return the current radio station's favicon (downloaded/cached
        by InternetRadioManager -- MainScreen never makes HTTP
        requests itself), or None if there is no favicon URL or the
        download failed (Build 0007, device test round 3).
        """

        if not self._last_radio_station:
            return None

        favicon_url = self._last_radio_station.get("favicon")

        if not favicon_url:
            return None

        return internetradio_manager.downloadFavicon(favicon_url)

    # ------------------------------------------------------------------

    def _resolveEmbeddedArtworkFile(self):
        """
        Write the current track's embedded artwork (if any) to
        CACHE_PATH and return its path, or None if there is none.
        ePicLoad needs a filesystem path, not raw bytes.
        """

        artwork = self._playback.getEmbeddedArtwork()

        if artwork is None:
            return None

        mime_type, image_bytes = artwork

        if not image_bytes:
            return None

        extension = ".png" if "png" in (mime_type or "") else ".jpg"

        cache_file = os.path.join(CACHE_PATH, f"embedded_cover{extension}")

        try:
            os.makedirs(CACHE_PATH, exist_ok=True)

            with open(cache_file, "wb") as handle:

                handle.write(image_bytes)

            return cache_file

        except OSError as error:

            logger.verbose(f"[MainScreen] Unable to cache embedded artwork: {error}")

            return None

    # ------------------------------------------------------------------

    def _findFolderCoverArt(self, directory):
        """
        Return the path to cover.jpg/cover.png/folder.jpg/folder.png
        in `directory`, or None if none exist.
        """

        if not directory:
            return None

        try:
            entries = {entry.lower(): entry for entry in os.listdir(directory)}

            for candidate in self.COVER_ART_FILENAMES:

                if candidate in entries:

                    return os.path.join(directory, entries[candidate])

        except OSError as error:

            logger.verbose(f"[MainScreen] Unable to scan for cover art: {error}")

        return None

    # ------------------------------------------------------------------

    def _decodeCoverArt(self, artwork_path: str) -> None:
        """
        Build 0009, device test round 5: a device log showed the very
        first call here (during __init__, before anything has played
        yet -- the "show default artwork at startup" fix) failing with
        "'NoneType' object has no attribute 'size'", while every later
        call for the same file succeeded. Traced to a race:
        self["cover"].instance is None until Enigma2 has actually
        applied the skin to this screen, which hasn't happened yet
        the moment __init__ itself calls this.

        Build 0009, device test round 6: the first attempt at fixing
        this (deferring via self.onLayoutFinish.append(a lambda)) is
        the prime suspect for a full plugin startup crash a device log
        showed immediately after -- "TypeError: exec() arg 1 must be a
        string, bytes or code object" inside Enigma2's own
        Screen.createGUIScreen(), triggered by dialog.applySkin()
        during session.open(MainScreen), i.e. exactly where a screen's
        onLayoutFinish entries get processed. Nothing else changed
        that round touches screen/skin lifecycle at all -- every other
        change was pure information_panel.py logic. Not proven beyond
        doubt without Enigma2's own source at that exact line, but
        strong enough circumstantial evidence to stop using
        onLayoutFinish for this rather than risk a repeat. Replaced
        with a short one-shot eTimer retry instead -- the same
        eTimer-based deferral mechanism this class already uses safely
        for _refresh_timer, so this reuses a pattern already confirmed
        working on real hardware rather than reaching for a second
        unverified API in a row.
        """

        if self["cover"].instance is None:

            logger.verbose(f"[MainScreen] Cover widget not ready yet, retrying decode of {artwork_path} shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(lambda: self._decodeCoverArt(artwork_path))

            retry_timer.start(100, True)

            self._pending_cover_retry_timer = retry_timer

            return

        try:
            widget_size = self["cover"].instance.size()

            width, height = widget_size.width(), widget_size.height()

            aspect = AVSwitch().getFramebufferScale()

            # setPara(width, height, aspect_x, aspect_y, useCache,
            # scale_mode, background_color). This exact tuple shape
            # and scale_mode=1 (aspect-ratio-corrected scaling) come
            # from a confirmed-working reference implementation
            # (YampMusicPlayer / OpenPli MediaPlayer's own coverArt
            # Pixmap, checked per user request -- see
            # docs/Claude_notes_build0005.txt) rather than a guess.
            self._picload.setPara((width, height, aspect[0], aspect[1], False, 1, "#00000000"))

            if self._picload.startDecode(artwork_path) != 0:
                raise RuntimeError("startDecode() reported failure")

        except Exception as error:

            logger.verbose(f"[MainScreen] Unable to decode cover art {artwork_path}: {error}")

            self["cover"].hide()

    # ------------------------------------------------------------------

    def _onCoverArtDecoded(self, picture_info=None) -> None:
        """
        ePicLoad callback: fires once decoding (started in
        _decodeCoverArt()) completes.
        """

        try:
            pixmap = self._picload.getData()

            if pixmap is None:

                self["cover"].hide()

                return

            self["cover"].instance.setPixmap(pixmap)

            self["cover"].show()

            self._log(f"Cover art loaded: {self._cover_file}")

        except Exception as error:

            logger.verbose(f"[MainScreen] Cover art decode callback failed: {error}")

            self["cover"].hide()

    # ------------------------------------------------------------------

    def _formatTime(self, seconds) -> str:
        """
        Format `seconds` as "MM:SS", or "H:MM:SS" past one hour.
        Returns "--:--" for None (unknown).
        """

        if seconds is None:
            return "--:--"

        try:
            total_seconds = max(0, int(seconds))

        except (TypeError, ValueError):
            return "--:--"

        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"

        return f"{minutes:02d}:{secs:02d}"

    # ------------------------------------------------------------------
    # Remote Control Handlers (MAINSCREEN_SPEC.md section 6)
    # ------------------------------------------------------------------

    def okPressed(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md -- dispatches by active panel:
        Playlist Panel plays the selected entry, Information Panel
        does nothing ("OK: No action"), Player Panel keeps Build
        0007/0008's existing behaviour (startup chooser / resume /
        replay) plus the new "OK: Play/Pause" -- toggling pause when
        something is actually playing, which the old behaviour never
        did on its own (a dedicated PAUSE key handled that instead).
        """

        logger.verbose("[MainScreen] OK pressed.")

        if self._active_panel == "playlist":

            self._playSelectedPlaylistEntry()

            return

        if self._active_panel == "information":

            return

        if not self._playback.hasMedia():

            self._openStartupChooser()

            return

        if self._playback.isPaused():

            self._resume()

            return

        if self._playback.isStopped():

            self._replayCurrent()

            return

        # Build 0009, device test round 12: pausePressed() itself now
        # handles Internet Radio specially (stops cleanly rather than
        # attempting a pause that doesn't actually work for a live
        # stream) -- see its own docstring for the full reasoning.
        self.pausePressed()

    # ------------------------------------------------------------------

    def _openStartupChooser(self) -> None:
        """
        Build 0007, device test round 8 -- OK on an empty MainScreen
        (nothing playing yet) asks which source to open, instead of
        always going straight to BrowserScreen: "Kun ohjelma
        käynnistyy, niin jos painaa ok, voisi tulla kysely
        avataaanko internetradio, paikallinen musiikki vai
        soittolistat."
        """

        choices = [
            (_("Internet Radio"), "radio"),
            (_("Local Music"), "local"),
            (_("Music Library"), "music_library"),
            (_("Playlists"), "playlists"),
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            self._startupChoiceMade,
            ChoiceBox,
            title=_("What would you like to open?"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _startupChoiceMade(self, choice) -> None:

        if choice is None or choice[1] == "cancel":
            return

        action = choice[1]

        if action == "radio":

            self._startRadioMode()

        elif action == "local":

            self.openBrowser()

        elif action == "music_library":

            self.openMusicLibraryScreen()

        elif action == "playlists":

            self.openPlaylistScreen()

    # ------------------------------------------------------------------

    def _startRadioMode(self) -> None:
        """
        "Jos valitsee radio, niin mainscreen voisi mennä suosikkitilaan
        ja alkaa soittamaan historian viimeisintä kanavaa. Jos
        historiassa ei ole kanavaa, niin sitten general-listalta ja jos
        ei sielläkään ole kanavaa, niin sitten avaa internetradion
        kanavien haun."

        Tries, in order: the most recent history entry, the first
        station in the "General" favorite list, and finally
        RadioBrowserScreen itself (to search) if neither has anything.
        """

        history = internetradio_manager.getHistory()

        if history:

            self._radio_list_name = "history"

            self._radio_list = history

            self._radio_index = 0

            self._playRadioListEntry(history[0])

            return

        general = internetradio_manager.getFavorites("General")

        if general:

            self.playRadioStation(general[0], list_name="General")

            return

        self.openRadioBrowserScreen()

    # ------------------------------------------------------------------

    def playPressed(self) -> None:

        logger.verbose("[MainScreen] PLAY pressed.")

        if self._playback.isPaused():

            self._resume()

            return

        if self._playback.hasMedia() and self._playback.isStopped():

            self._replayCurrent()

            return

        if not self._playback.hasMedia():

            self.openBrowser()

    # ------------------------------------------------------------------

    def pausePressed(self) -> None:
        """
        Build 0009, device test round 12: a real device log showed
        KEY_OK pressed while a station was confirmed actively playing
        (Now Playing correctly showing the current song), followed
        immediately by the underlying stream stopping -- togglePause()
        has no stream-specific handling, and a live stream apparently
        can't be cleanly paused/resumed the way a local file can
        through this backend (GStreamer or ExtEplayer3): the pause
        attempt stops it outright, MediaPlayer3's own state then
        incorrectly shows "paused", and a later resume attempt hits a
        service that's already dead -- nothing comes back, with no
        clear way out. While streaming, this now stops the stream
        cleanly instead (the same confirmed-working path the
        dedicated STOP key already uses) rather than attempting a
        pause that doesn't actually work -- okPressed()'s own
        isStopped() branch then restarts the same station fresh on
        the next OK press (see _replayCurrent()).
        """

        logger.verbose("[MainScreen] PAUSE pressed.")

        if self._playback.isPlayingStream():

            self.stopPressed()

            return

        if self._playback.togglePause():

            self._updateDisplay()

        else:

            self._statusbar.showError(_("Pause failed"))

    # ------------------------------------------------------------------

    def stopPressed(self) -> None:

        logger.verbose("[MainScreen] STOP pressed.")

        self._log("Playback stopped.")

        if self._playback.stop():

            self._updateDisplay()

        else:

            self._statusbar.showError(_("Stop failed"))

    # ------------------------------------------------------------------

    def nextTrackPressed(self) -> None:

        logger.verbose("[MainScreen] NEXT pressed.")

        if self._playback.nextTrack():

            self._updateDisplay()

        else:

            self._statusbar.showError(_("No next track"))

    # ------------------------------------------------------------------

    def previousTrackPressed(self) -> None:

        logger.verbose("[MainScreen] PREVIOUS pressed.")

        if self._playback.previousTrack():

            self._updateDisplay()

        else:

            self._statusbar.showError(_("Already at first track"))

    # ------------------------------------------------------------------

    def seekForwardPressed(self) -> None:
        """
        Build 0009, device test round 2: a device log showed this
        firing regardless of the active panel -- only
        seekForwardShortPressed()/seekBackwardShortPressed() (LEFT/
        RIGHT) had been made panel-aware, the dedicated FF/RW keys
        were missed entirely. Confirmed from a real log: switching to
        the Playlist Panel and pressing RIGHT correctly switched
        playlists, but a follow-up press of the dedicated seek-forward
        key still seeked 30s regardless. MAINSCREEN_SPEC.md only lists
        seeking under the Player Panel, so this now matches
        seekForwardShortPressed()'s own guard.
        """

        logger.verbose("[MainScreen] SEEK FORWARD pressed.")

        if self._active_panel != "player":
            return

        self._seek(self._getSeekStep())

    # ------------------------------------------------------------------

    def seekBackwardPressed(self) -> None:
        """
        Build 0009, device test round 2 -- see seekForwardPressed()'s
        docstring; same fix, opposite direction.
        """

        logger.verbose("[MainScreen] SEEK BACKWARD pressed.")

        if self._active_panel != "player":
            return

        self._seek(-self._getSeekStep())

    # ------------------------------------------------------------------

    def _getSeekStep(self) -> int:
        """
        Return the configured long seek step in seconds
        (playback.seek_step_seconds, Build 0006 device test round 3),
        falling back to SEEK_STEP_LONG if the config value is missing
        or invalid.
        """

        try:
            return int(config_manager.get("playback.seek_step_seconds", self.SEEK_STEP_LONG))

        except (TypeError, ValueError):
            return self.SEEK_STEP_LONG

    # ------------------------------------------------------------------

    def seekForwardShortPressed(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md -- dispatches by active panel:
        Playlist Panel switches the active playlist/radio list,
        Information Panel switches to the next information page,
        Player Panel seeks forward (Build 0007/0008 behaviour,
        unchanged) for local files.

        Build 0009, device test round 9: while streaming Internet
        Radio, Player Panel now switches the active favorite list
        instead of attempting a seek -- seeking a live stream was
        always a no-op anyway (PlaybackController rejects it, no
        seekable timeline), so per user request ("Koska radiokanavia
        ei voi kelata... Laitetaan Player tilassa sivunuolilla
        suosikkilistan vaihto") this repurposes the key productively
        for radio specifically, without changing anything for local
        file playback.
        """

        logger.verbose("[MainScreen] RIGHT pressed.")

        if self._active_panel == "playlist":

            self._switchActivePlaylist(1)

            return

        if self._active_panel == "information":

            self._information_panel.switchPage(1)

            self._updateDisplay()

            return

        if self._playback.isPlayingStream():

            self._switchActivePlaylist(1)

            return

        self._seek(self.SEEK_STEP_SHORT)

    # ------------------------------------------------------------------

    def seekBackwardShortPressed(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md -- see
        seekForwardShortPressed()'s docstring; same dispatch, opposite
        direction.
        """

        logger.verbose("[MainScreen] LEFT pressed.")

        if self._active_panel == "playlist":

            self._switchActivePlaylist(-1)

            return

        if self._active_panel == "information":

            self._information_panel.switchPage(-1)

            self._updateDisplay()

            return

        if self._playback.isPlayingStream():

            self._switchActivePlaylist(-1)

            return

        self._seek(-self.SEEK_STEP_SHORT)

    # ------------------------------------------------------------------

    def upPressed(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md -- dispatches by active panel:
        Playlist Panel moves the selection, Information Panel scrolls
        the current page, Player Panel steps to the previous track (or
        radio station, while streaming -- Build 0007's own
        interpretation of "track" for radio, kept since the new spec
        doesn't say otherwise).
        """

        logger.verbose("[MainScreen] UP pressed.")

        if self._active_panel == "playlist":

            self["playlist_list"].up()

            return

        if self._active_panel == "information":

            self._information_panel.scroll(-1)

            self._updateDisplay()

            return

        if self._playback.isPlayingStream():

            self._radioStationStep(-1)

        else:

            self.previousTrackPressed()

    # ------------------------------------------------------------------

    def downPressed(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md -- see upPressed()'s docstring;
        same dispatch, opposite direction.
        """

        logger.verbose("[MainScreen] DOWN pressed.")

        if self._active_panel == "playlist":

            self["playlist_list"].down()

            return

        if self._active_panel == "information":

            self._information_panel.scroll(1)

            self._updateDisplay()

            return

        if self._playback.isPlayingStream():

            self._radioStationStep(1)

        else:

            self.nextTrackPressed()

    # ------------------------------------------------------------------

    def _seek(self, offset_seconds: int) -> None:
        """
        Build 0008, device test round 6: a device log showed the
        dedicated seek keys reaching here while an Internet Radio
        stream was playing, which PlaybackController now rejects
        (streams have no seekable timeline) -- silently ignored here
        too, rather than showing "Seek failed", since this isn't a
        failure from the user's point of view, just a key that
        doesn't apply while streaming (LEFT/RIGHT already treats
        streaming differently for the same reason).
        """

        if not self._playback.hasMedia():
            return

        if self._playback.isPlayingStream():
            return

        success = (
            self._playback.seekForward(offset_seconds)
            if offset_seconds >= 0
            else self._playback.seekBackward(-offset_seconds)
        )

        if success:

            # Build 0008, device test round 9: this used to also call
            # self._playback.tick() here, which re-queries GStreamer
            # immediately after the seek -- a device log showed this
            # catching GStreamer still mid-flush from the seek just
            # requested, transiently reporting position 0. The
            # existing sanity check only rejects readings that are
            # implausibly HIGH (the original bug pattern from rounds
            # 1-6), so a too-LOW reading like this got accepted and
            # silently overwrote the correct position
            # seekForward()/seekBackward() had just set via
            # _rebaselineAfterSeek() -- visible as the NEXT seek then
            # computing its target from "current: 0s" instead of the
            # real position. Removing the extra tick() call fixes this
            # at the source: PlaybackController already knows the
            # correct position after a successful seek without
            # needing to ask GStreamer again immediately.
            self._updateDisplay()

        else:

            self._statusbar.showError(_("Seek failed"))

    # ------------------------------------------------------------------

    def pvrPressed(self) -> None:

        logger.verbose("[MainScreen] PVR pressed.")

        self.openBrowser()

    # ------------------------------------------------------------------

    def menuPressed(self) -> None:

        logger.verbose("[MainScreen] MENU pressed.")

        self.openMainMenu()

    # ------------------------------------------------------------------

    def _isDebounced(self, action_name: str, min_interval: float = 0.4) -> bool:
        """
        Returns True if `action_name` fired again too soon after its
        own previous call to be a genuinely new, separate press --
        guards toggle-style handlers against a keymap binding an
        action to both the Make (press) and Break (release) hardware
        events for the same key, which would otherwise fire twice per
        physical press (see this file's Build 0008, device test
        round 8 change history for the confirming device log). 0.4s
        is comfortably longer than the ~0.2-0.3s Make-to-Break gap a
        real device log showed, but far shorter than any two
        deliberate, separate presses a person would make.
        """

        now = time.time()

        last = self._last_action_time.get(action_name, 0.0)

        self._last_action_time[action_name] = now

        return (now - last) < min_interval

    # ------------------------------------------------------------------

    # ------------------------------------------------------------------

    def helpPressed(self) -> None:
        """
        Build 0009, MAINSCREEN_SPEC.md "Help Integration" -- opens
        whichever help document matches the currently active panel
        (player.md/playlist.md/information.md), replacing Build
        0008's single, fixed mainscreen.md.
        """

        logger.verbose("[MainScreen] HELP pressed.")

        title, content = help_manager.getHelp(self._active_panel)

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------

    def radioPressed(self) -> None:
        """
        Build 0007, device test round 3 -- refined from round 2's
        local/radio toggle: "Kun radiotilassa painaa radio-nappia,
        niin voisi aueta browser." (While in radio mode, pressing
        RADIO could open Browser.)

        Not playing a stream: switches TO radio -- resumes the last-
        played station if there is one, otherwise opens
        RadioBrowserScreen to pick one.

        Already playing a stream: opens BrowserScreen, instead of
        silently resuming the last local file as round 2 did --
        RADIO now reads as a forward-cycling shortcut (local/nothing
        -> radio -> browse local -> ...) rather than a strict toggle.
        """

        logger.verbose("[MainScreen] RADIO pressed.")

        if self._playback.isPlayingStream():

            self.openBrowser()

            return

        if self._last_radio_station:

            self.playRadioStation(self._last_radio_station, list_name=self._radio_list_name)

        else:

            self.openRadioBrowserScreen()

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[MainScreen] EXIT pressed.")

        if self._playback.isPlaying() or self._playback.isPaused():

            self._log("EXIT: stopping playback (press again to close).")

            self.stopPressed()

            return

        self.closePlayer()

# End of Part 2
    # ------------------------------------------------------------------
    # Internet Radio (Build 0007 -- BUILD_0007_PLAN.md "MainScreen
    # Navigation")
    # ------------------------------------------------------------------

    def playRadioStation(self, station, list_name=None) -> bool:
        """
        Prepare and play `station` (a RadioBrowser station dict),
        opened from RadioBrowserScreen or Main Menu's Internet Radio
        entry. Refreshes the active navigation list (favorites or
        history, per Settings) and positions _radio_index on the
        station just played, so UP/DOWN work immediately afterwards.
        """

        result = internetradio_manager.prepareStream(station)

        if result is None:

            self._statusbar.showError(_("Playback failed"))

            return False

        if not self._playback.playStream(result["url"], result["station"]):

            self._statusbar.showError(_("Playback failed"))

            return False

        self._last_radio_station = result["station"]

        # Build 0009, device test round 2 -- the missing piece between
        # "Yle/Bauer EPG providers exist and are confirmed working"
        # and "a station actually shows EPG data": matches this
        # station against known Yle/Bauer stations by name and
        # registers the right provider for its real stationuuid, if
        # any matches. See finland_radio_epg_registry.py's own header
        # for why name matching (not stationuuid) and how reliable
        # it's expected to be.
        finland_radio_epg_registry.registerProvidersForStation(result["station"])

        # Build 0009, device test round 9 -- the Playlist Panel is no
        # longer reachable via EPG/INFO while streaming (see
        # activePanelPressed()'s own docstring); if the user was on it
        # for local music and then switched straight to radio, land on
        # Player immediately rather than leaving them on a panel
        # they can no longer navigate back to until it cycles there
        # again on its own.
        if self._active_panel == "playlist":

            self._active_panel = "player"

        # Build 0009, device test round 3: a real device log and
        # screenshot showed a station correctly playing from "Omat",
        # then the panel flipping to "Playlist: favorites" (empty,
        # stuck, couldn't switch away). Traced to this line: when
        # list_name wasn't given, it read cfg.radio.navigation_mode's
        # raw value ("favorites"/"history", a MODE selector) and used
        # it AS IF it were an actual favorite list's name -- no
        # favorite list is literally named "favorites", so that always
        # produced an empty list. _resolveInitialRadioListName()
        # already existed and already did this correctly (mode ->
        # real list name); this just needed to reuse it instead of
        # re-deriving it naively.
        self._radio_list_name = list_name or self._resolveInitialRadioListName()

        self._refreshRadioList(is_explicit_switch=False)

        stationuuid = station.get("stationuuid")

        self._radio_index = next(
            (i for i, entry in enumerate(self._radio_list) if entry.get("stationuuid") == stationuuid),
            0,
        )

        self._updateDisplay()

        return True

    # ------------------------------------------------------------------

    def _resolveInitialRadioListName(self) -> str:
        """
        Resolve radio.navigation_mode's "favorites"/"history" setting
        to an actual starting list name for _radio_list_name -- which,
        since device test round 3, cycles through every real favorite
        list (not just a favorites/history binary), so it needs a real
        list name, not the literal mode string.
        """

        if config_manager.get("radio.navigation_mode", "favorites") == "history":

            return "history"

        names = internetradio_manager.getFavoriteListNames()

        return names[0] if names else "history"

    # ------------------------------------------------------------------

    def _refreshRadioList(self, is_explicit_switch: bool = True) -> None:
        """
        Build 0009, device test round 8: playRadioStation() calls this
        every time ANY station starts playing, regardless of which
        list that station came from -- including while the user is
        actively browsing the History list itself in the Playlist
        Panel, where playing an entry from it (which also adds a new
        history entry -- see addHistoryEntry()) would otherwise
        immediately reshuffle the very list they're looking at right
        under their selection. Per user request ("Radion History
        listaa voisi muuttaa siten etta sita ei paiviteta silloin kun
        sita kaytetaan"), skips reloading "history" specifically when
        `is_explicit_switch` is False (playRadioStation()'s own
        incidental refresh) and the user is currently viewing it in
        the Playlist Panel with something already loaded. An explicit
        switch into History (_switchRadioList(), is_explicit_switch
        defaulting to True) always refreshes, so first viewing it
        still shows current data.
        """

        if (
            not is_explicit_switch
            and self._radio_list_name == "history"
            and self._active_panel == "playlist"
            and self._radio_list
        ):

            logger.verbose("[MainScreen] Skipping History refresh -- currently being browsed in the Playlist Panel.")

            return

        if self._radio_list_name == "history":

            self._radio_list = internetradio_manager.getHistory()

        else:

            self._radio_list = internetradio_manager.getFavorites(self._radio_list_name)

    # ------------------------------------------------------------------

    def _switchRadioList(self, direction: int = 1) -> None:
        """
        Cycle to the next/previous list in [all favorite lists...,
        "history"] (Build 0007, device test round 3 -- previously a
        binary favorites/history toggle; the user pointed out they had
        created several of their own favorite lists that this never
        reached).
        """

        lists = internetradio_manager.getFavoriteListNames() + ["history"]

        if not lists:
            return

        if self._radio_list_name in lists:

            index = (lists.index(self._radio_list_name) + direction) % len(lists)

        else:

            index = 0

        self._radio_list_name = lists[index]

        self._refreshRadioList()

        self._radio_index = 0 if self._radio_list else -1

        self._log(f"Radio navigation list switched: {self._radio_list_name}")

        if self._radio_list and 0 <= self._radio_index < len(self._radio_list):

            self._playRadioListEntry(self._radio_list[self._radio_index])

        else:

            self._statusbar.showError(_("No next track"))

    # ------------------------------------------------------------------

    def _radioStationStep(self, direction: int) -> None:

        if not self._radio_list:

            self._refreshRadioList()

        if not self._radio_list:

            self._statusbar.showError(_("No next track"))

            return

        self._radio_index = (self._radio_index + direction) % len(self._radio_list)

        self._playRadioListEntry(self._radio_list[self._radio_index])

    # ------------------------------------------------------------------

    def _playRadioListEntry(self, entry) -> None:
        """
        Play a station taken from the favorites or history list --
        history entries are stored as a lighter dict (name/stream_url/
        stationuuid) than full RadioBrowser station dicts, so this
        adapts either shape into what playStream()/prepareStream()
        expect.
        """

        if "url" in entry or "url_resolved" in entry:

            station = entry

        else:

            station = {
                "stationuuid": entry.get("stationuuid"),
                "name": entry.get("name", "Internet Radio"),
                "url": entry.get("stream_url", ""),
                "url_resolved": entry.get("stream_url", ""),
            }

        result = internetradio_manager.prepareStream(station)

        if result is None or not self._playback.playStream(result["url"], result["station"]):

            self._statusbar.showError(_("Playback failed"))

            return

        self._last_radio_station = result["station"]

        # Build 0009, device test round 3 -- this pathway (UP/DOWN
        # station stepping while the Player panel is active,
        # _radioStationStep()) never registered EPG providers at all,
        # unlike playRadioStation(); only stations reached via
        # RadioBrowserScreen/PlaylistScreen picked up EPG data. Fixed
        # to match.
        finland_radio_epg_registry.registerProvidersForStation(result["station"])

        self._updateDisplay()

    # ------------------------------------------------------------------

    def _cycleLocalPlaylist(self, direction: int) -> None:
        """
        Cycle to the next/previous stored playlist (Build 0007, device
        test round 3 -- "Sama voisi toimi myös paikallisilla
        tiedostoilla, kun mainscreenissä on valittuna soittolista
        näkymä info-napilla": the same playlist-switching LEFT/RIGHT
        already does for radio favorite lists, extended to local
        PlaylistManager playlists in the favorites view). Immediately
        starts playing the newly-selected playlist's first track,
        mirroring how radio's list switch immediately plays the first
        station in the new list.
        """

        names = playlist_manager.getPlaylistNames()

        if not names:

            self._statusbar.showError(_("No next track"))

            return

        if self._current_local_playlist_name in names:

            index = (names.index(self._current_local_playlist_name) + direction) % len(names)

        else:

            index = 0

        new_name = names[index]

        queue = playlist_manager.generatePlaybackQueue(new_name)

        if not queue:

            self._statusbar.showError(_("Playback failed"))

            return

        self._log(f"Local playlist switched: {new_name}")

        if self._playback.playQueue(queue, 0):

            self._current_local_playlist_name = new_name

            self._updateDisplay()

        else:

            self._statusbar.showError(_("Playback failed"))

    # ------------------------------------------------------------------
    # Navigation (MAINSCREEN_SPEC.md section 7)
    # ------------------------------------------------------------------

    def openBrowser(self) -> None:

        self._log("Opening BrowserScreen.")

        self.session.openWithCallback(
            self._browserClosed,
            BrowserScreen,
            self._playback,
        )

    # ------------------------------------------------------------------

    def openPlaylistScreen(self) -> None:

        self._log("Opening PlaylistScreen.")

        self.session.openWithCallback(
            self._mediaScreenClosed,
            PlaylistScreen,
            self._playback,
        )

    # ------------------------------------------------------------------

    def openMusicLibraryScreen(self) -> None:

        self._log("Opening MusicLibraryScreen.")

        self.session.openWithCallback(
            self._mediaScreenClosed,
            MusicLibraryScreen,
            self._playback,
        )

    # ------------------------------------------------------------------

    def openRadioBrowserScreen(self) -> None:

        self._log("Opening RadioBrowserScreen.")

        self.session.openWithCallback(
            self._mediaScreenClosed,
            RadioBrowserScreen,
            self._playback,
        )

    # ------------------------------------------------------------------

    def _mediaScreenClosed(self, result=None) -> None:
        """
        Shared close callback for PlaylistScreen/RadioBrowserScreen
        (Build 0007) -- both close(None) on EXIT and close("played")
        once they've started playback, exactly the same convention
        BrowserScreen already uses (see _browserClosed()).

        PlaylistScreen additionally passes back
        ("played", playlist_name) rather than a bare "played" (device
        test round 3), so LEFT/RIGHT playlist cycling in favorites
        view knows which stored playlist is now active.
        """

        self._log("PlaylistScreen/RadioBrowserScreen closed.")

        if isinstance(result, tuple) and len(result) == 2 and result[0] == "played":

            self._current_local_playlist_name = result[1]

        self._applyUiSettings()

        self._updateDisplay()

    # ------------------------------------------------------------------

    def _browserClosed(self, *args) -> None:

        self._log("BrowserScreen closed.")

        # BrowserScreen playback is always folder-based, never from a
        # stored playlist (Build 0007, device test round 3) -- clear
        # any stale playlist name so _updateTopLabel() falls back to
        # showing the folder name instead.
        self._current_local_playlist_name = None

        self._applyUiSettings()

        self._updateDisplay()

    # ------------------------------------------------------------------

    def openMainMenu(self) -> None:

        self._log("Opening Main Menu.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id is None:

            self._updateDisplay()

            return

        if action_id == "browser":

            self.openBrowser()

        elif action_id == "playlists":

            self.openPlaylistScreen()

        elif action_id == "music_library":

            self.openMusicLibraryScreen()

        elif action_id == "radio":

            self.openRadioBrowserScreen()

        elif action_id == "playback_info":

            self.openPlaybackInfo()

        elif action_id == "settings":

            self.openSettings()

        elif action_id == "developer":

            self.openDeveloperScreen()

        elif action_id == "about":

            self._showAbout()

        elif action_id == "exit":

            self._updateDisplay()

    # ------------------------------------------------------------------

    def openPlaybackInfo(self) -> None:

        self._log("Opening PlaybackInfoScreen.")

        self.session.openWithCallback(
            self._childScreenClosed,
            PlaybackInfoScreen,
            self._playback,
        )

    # ------------------------------------------------------------------

    def openSettings(self) -> None:

        self._log("Opening SettingsScreen.")

        self.session.openWithCallback(self._childScreenClosed, SettingsScreen)

    # ------------------------------------------------------------------

    def openDeveloperScreen(self) -> None:

        self._log("Opening DeveloperScreen.")

        self.session.openWithCallback(
            self._childScreenClosed,
            DeveloperScreen,
            self._playback,
        )

    # ------------------------------------------------------------------

    def _childScreenClosed(self, action_id=None) -> None:
        """
        Called when BrowserScreen, SettingsScreen, PlaybackInfoScreen or
        DeveloperScreen closes.

        Each of those Screens closes with `None` on a normal EXIT, or
        with a Main Menu action_id when the user pressed MENU inside
        them and picked a *different* destination there (they never
        open that destination themselves -- see e.g.
        settingsscreen.py._mainMenuCallback()).
        """

        self._log("Returning to MainScreen.")

        if action_id:

            self._mainMenuCallback(action_id)

            return

        self._applyUiSettings()

        self._updateDisplay()

    # ------------------------------------------------------------------

    def _showAbout(self) -> None:

        self.session.open(
            MessageBox,
            get_version_string(),
            MessageBox.TYPE_INFO,
        )

# End of Part 3
    # ------------------------------------------------------------------
    # Playback Helpers
    # ------------------------------------------------------------------

    def _resume(self) -> None:

        if self._playback.resume():

            self._updateDisplay()

        else:

            self._statusbar.showError(_("Resume failed"))

    # ------------------------------------------------------------------

    def _replayCurrent(self) -> None:
        """
        Build 0009, device test round 12: now also handles Internet
        Radio -- previously always called self._playback.play(filename),
        the local-file method, which for a stream URL would create a
        service reference directly and skip playRadioStation()'s own
        logic entirely (re-resolving the URL fresh via
        prepareStream(), which matters since the old URL may no
        longer be valid after a stop, EPG provider registration,
        history/favicon enrichment). Needed once okPressed() started
        stopping (rather than pausing) radio streams -- see its own
        docstring for why.
        """

        if self._playback.isPlayingStream() or self._last_radio_station is not None:

            if self._last_radio_station is None:
                return

            if self.playRadioStation(self._last_radio_station, list_name=self._radio_list_name):

                self._updateDisplay()

            else:

                self._statusbar.showError(_("Playback failed"))

            return

        filename = self._playback.getCurrentFile()

        if not filename:
            return

        if self._playback.play(filename):

            self._updateDisplay()

        else:

            self._statusbar.showError(_("Playback failed"))

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closePlayer(self) -> None:
        """
        Close MediaPlayer3 and return to TV (MAINSCREEN_SPEC.md
        section 6, EXIT).
        """

        self._log("Closing")

        try:
            self._refresh_timer.stop()

        except Exception as error:

            self._log(f"Error while stopping refresh timer: {error}")

        try:
            self._playback.stop()

        except Exception as error:

            self._log(f"Error while stopping playback: {error}")

        try:
            self._playback.cleanup()

        except Exception as error:

            self._log(f"Playback cleanup failed: {error}")

        self._log("Closed")

        self.close()

    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """
        Explicit cleanup, called during shutdown when required.
        """

        self.closePlayer()

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"MainScreen(initialized={self._initialized})"


# ==============================================================================
#
# Build Notes
#
# Build 0004 introduces MainScreen as the application's primary window,
# replacing Build 0003's Browser. MainScreen responsibilities:
#
#   - Playback user interface and status display
#   - Remote control handling
#   - Opening BrowserScreen, Main Menu, PlaybackInfoScreen,
#     SettingsScreen and DeveloperScreen
#
# MainScreen is intentionally NOT responsible for:
#
#   - Directory browsing (BrowserScreen)
#   - Playback implementation (PlaybackController / ServiceController)
#   - Platform compatibility (Compatibility)
#
# MainScreen owns the single PlaybackController instance for the whole
# application and hands it to every Screen that needs to read or
# request playback, so state remains consistent across navigation.
#
# Build 0005 adds a graphical progress bar, elapsed/remaining time,
# queue position display and Previous/Next Track handling, driven by a
# 1-second eTimer that calls PlaybackController.tick() -- see
# PLAYBACK_QUEUE_SPEC.md and PLAYBACK_CONTROLLER_SPEC.md.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

# ==============================================================================
#
# MediaPlayer3
#
# File        : radiobrowserscreen.py
#
# Description :
#
#     RadioBrowserScreen
#
#     Dedicated Internet Radio browsing UI: three panels (Stations,
#     Language, Region) plus an information panel for the currently
#     selected station. Communicates exclusively with
#     InternetRadioManager -- never with the RadioBrowser API
#     directly.
#
# Implements :
#
#     RADIOBROWSER_SCREEN_SPEC.md v0.1
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
#   - Initial version.
#
# 2026-07-24  Build 0007 (device test round 2)
#   - Added CH+/CH-  page-jump (compatibility.getChannelUpKeyActionNames()/
#     getChannelDownKeyActionNames(), candidates not yet confirmed
#     against a real device) for the focused panel -- requested after
#     real device testing showed long lists slow to scroll one entry
#     at a time.
#   - Added _promoteAppLanguage(): moves the app's own configured UI
#     language to position 2 in the Language panel (right after
#     "Any"), so it doesn't require scrolling through potentially
#     hundreds of entries to find. Requested after real device
#     testing.
#
# 2026-07-24  Build 0007 (device test round 4)
#   - CH+/CH-'s real action names CONFIRMED via a full raw
#     eActionMap/InfoBarGenerics log as "BOUQUET+"/"BOUQUET-"
#     (compatibility.py updated); added "InfobarBouquetActions" to
#     this screen's ActionMap contexts defensively, since the log
#     didn't show which context group resolves them.
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

from enigma import ePicLoad, eTimer

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from .compatibility import compatibility
from .config import config_manager
from .ffprobe_helper import isAvailable as ffprobe_available, probe as ffprobe_probe
from .guide_manager import guide_manager
from .guide_screen import GuideScreen
from .internetradio_manager import APP_LANGUAGE_TO_RADIOBROWSER_NAME, internetradio_manager
from .paths import BUTTON_ICON_PATH
from .skin import resolve_skin_asset_path, to_opaque_skin_color
from .localization import _, getCurrentLanguage
from .logger import logger

# Build 0010, device test round 16 -- user request: "Internetradion
# kohdalla riittää, että vaihtaa järjestyksen keskimmäiseen kieli ja
# oikean puoleiseen alue, koska kieli valitaan useammin." Order here
# drives both the visual left-to-right column layout (_buildSkin())
# and the LEFT/RIGHT focus cycle (focusPrevious()/focusNext()) --
# both must agree, so this tuple is the single source of truth for
# column order; only the widget names ("region"/"language") stayed
# put, the position/order changed around them.
PANELS = ("stations", "language", "region")

# CHANNEL UP/DOWN jump this many entries at once in the focused panel
# (requested after real device testing: long lists of stations/
# countries/languages are slow to scroll one entry at a time).
PAGE_STEP = 15

# Round 215, per direct request: a real device report (first on
# 1.2.000, confirmed again on 1.2.003) that holding CH-/CH+ pages the
# originally-focused panel correctly ONCE, then starts paging a
# different panel instead -- less noticeable with a small channel
# count, worse with a large one. Two device logs already confirmed
# the logged self._focus value stays correct for every single CH-/
# CH+ event during a hold, so pageUp()/pageDown() now pin themselves
# to whichever panel was focused when a page-jump burst *started*
# (self._page_jump_start_focus below), for the duration of that
# burst, released this many milliseconds after the last repeat event
# -- comfortably longer than the 150-300ms gap between individual
# CH-/CH+ key-repeat events seen across those same two device logs,
# so a genuine hold never releases the lock early, but short enough
# that releasing the physical key still feels immediate.
PAGE_JUMP_RELEASE_MS = 400

# Round 218, per direct request after a fresh device log proved round
# 217's setFocus()-based fix had NO effect at all (identical symptom:
# "stations" silently drifted by a large amount -- 1605 this time --
# during a held CH-/CH+, while the locked panel only moved by the one
# step its own single resolved "Make" event caused). Whatever actually
# routes a held CH-/CH+ key's repeat events to "stations" instead of
# our own Python code, giving Enigma2 the real native GUI focus did
# not change it. Rather than guess at a third theory of the exact
# native mechanism, this polls "stations" own position frequently
# enough to catch each individual drift step shortly after it happens
# (observed repeat gaps were 107-300ms; polling well under that),
# reverses it on "stations", and replays the same movement on whatever
# panel is actually locked -- regardless of *why* "stations" moved.
DRIFT_CORRECTION_INTERVAL_MS = 80

# Round 220, found via round 219's own per-tick logging: the drift-
# correction timer WAS running correctly (ticking every 80ms exactly
# as designed) -- but during the only window it ever got to run in
# (the first PAGE_JUMP_RELEASE_MS=400ms after the initial press),
# "stations" never moved at all, every single tick. The release timer
# (armed only once, at that same initial press, and never re-armed
# because no drift had happened yet to re-arm it) then fired right at
# that 400ms mark and shut the whole mechanism down -- for the entire
# rest of an ~11-14 second hold -- before the real native drift (which
# clearly did eventually happen, per the next logged CH+ event) ever
# even started. Enigma2's own key-repeat typically has an initial
# "repeat doesn't start immediately" delay before the steady repeat
# cadence kicks in, and 400ms is apparently too short to survive it.
# Fixes this by giving the *first* drift tick a much more generous
# grace period to show up in, before falling back to the original,
# tight, already-proven-correct cadence (PAGE_JUMP_RELEASE_MS) once
# real drift has actually started happening.
DRIFT_WATCHDOG_INITIAL_MS = 1500

# Round 222, per direct device report: CH+ held on Region/Language
# silently does nothing whenever Stations already has its own FIRST
# entry selected, and the mirror case for CH- when Stations already
# has its own LAST entry selected -- worst with exactly one found
# station, where that single entry is simultaneously both. The whole
# drift-correction mechanism (round 218 onward) only ever notices a
# held key is still active by seeing Stations' own position actually
# change; when Stations is already pinned at the boundary the held
# direction's native drift would push it toward, that native
# mechanism keeps trying on every repeat but has nowhere left to move
# it, so its own position never changes at all -- indistinguishable
# from the key having already been released. See
# _armStationsDriftWatch()'s own comment for the fix.

# Device test round 27 -- how long the Stations-column selection must
# sit still before _logSelectedStationCodec() actually runs. Long
# enough that scrolling through a list doesn't fire a probe per
# station passed through; short enough to still feel responsive once
# the user does stop somewhere.
CODEC_LOG_DEBOUNCE_MS = 700

# Round 199, per direct report + a real device log showing exactly
# this: browsing the Region/Language column used to fire a full
# _runSearchWithStatus() (round 198's own streaming local-database
# search, still a real, measurable amount of work against a 59000+-
# line stations.jsonl -- see search()'s own comment) synchronously on
# EVERY single selection change, with no debounce at all -- unlike
# the Stations column's own CODEC_LOG_DEBOUNCE_MS above. Pressing
# UP/DOWN repeatedly to browse the list therefore fired one search per
# keypress, each one blocking the UI for however long that scan took,
# stacking up into exactly the "selaaminen on hidasta" (browsing is
# slow) symptom reported. Same restart-based debounce pattern as
# CODEC_LOG_DEBOUNCE_MS: only search once the selection has actually
# settled for this long, so scrolling quickly through Region/Language
# fires at most one search, for whichever entry the user stopped on --
# not one per entry passed through. 1000ms per direct request ("n. 1
# s viive").
REGION_LANGUAGE_SEARCH_DEBOUNCE_MS = 1000

# Device test round 29 -- user request: "Kun tulee takaisin toiminolla
# soittimesta radiobrowseriin, niin siina voisi sailya edellinen haku-
# tai kieliasetus, niin on helppo selata ja kokeilla useita
# samanlaisia kanavia." A fresh RadioBrowserScreen instance is created
# every time it's opened (including via MainScreen's OK-menu "Back"),
# so its own instance state can't remember anything between visits on
# its own -- these three module-level variables persist for as long
# as the process keeps running (reset on a full restart, which is
# fine: this is about the Back round-trip within one session, not
# surviving a reboot). Read in __init__()/_reloadFilters(), written
# wherever the user actually changes one of these three things.
_last_search_name = ""
_last_region_name = None
_last_language_name = None

# Device test round 54 -- background-image variant/tier system,
# mirroring MusicLibraryScreen's own SKIN_PALETTES/_resolveSkinVariant()/
# _resolveResolutionTier() exactly (same hex values for light, since
# this screen reuses MusicLibraryScreen's own colours per direct
# request). A separate copy rather than importing MusicLibraryScreen's
# own dict, since the two screens don't otherwise depend on each
# other and duplicating a small, stable palette is simpler than
# introducing a cross-module dependency for it.
RADIO_SKIN_VARIANTS = ("light", "dark", "test_skin", "vintage_radio")

RADIO_DEFAULT_SKIN_VARIANT = "light"

RADIO_SKIN_PALETTES = {
    "light": {
        "panel_background_color": "#F9F9F9",
        "list_background_color": "#EAEAEA",
        "panel_text_color": "#1A1A1A",
        "header_inactive_fg": "#1E2334",
        "header_active_fg": "#036DFA",
        "hint_fg": "#036DFA",
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
        "selected_row_bg": "#2B2F39",
        "selected_row_fg": "#C7AC4E",
    },
}

# Round 112, per direct request (a real device crash: KeyError
# 'test_skin' -- round 110 added "test_skin" to this screen's own
# SKIN_VARIANTS whitelist, letting it become the active variant,
# but never added a matching entry HERE, in the separate dict that
# actually supplies its colour palette) -- test_skin starts out
# visually identical to Dark (matches its own bundled template,
# which starts as an exact copy of Dark's PNGs too), and stays in
# sync with any future change to Dark's own palette automatically,
# since this is a reference to the same dict, not a copy of it.

# Round 149, per direct request ("test_skinin muiden ikkunoiden
# väriteema mainscreenin mukaiseksi"): see browserscreen.py's own
# round 149 comment for the full reasoning. No info_label_fg key here
# -- this screen's own Light/Dark palettes never defined one either.
RADIO_SKIN_PALETTES["test_skin"] = {
    "panel_background_color": "#1C1610",
    "list_background_color": "#161108",
    "panel_text_color": "#E8A24C",
    "header_inactive_fg": "#C08A45",
    "header_active_fg": "#FFC978",
    "hint_fg": "#FFC978",
    "selected_row_bg": "#C08A45",
    "selected_row_fg": "#1A1206",
}

# Round 155, per direct request: independent copy, see mainscreen.py's
# own round 155 comment for the full reasoning.
RADIO_SKIN_PALETTES["vintage_radio"] = {
    "panel_background_color": "#1C1610",
    "list_background_color": "#161108",
    "panel_text_color": "#E8A24C",
    "header_inactive_fg": "#C08A45",
    "header_active_fg": "#FFC978",
    "hint_fg": "#FFC978",
    "selected_row_bg": "#C08A45",
    "selected_row_fg": "#1A1206",
}


def _resolveRadioSkinVariant() -> str:

    variant = config_manager.get("appearance.skin", RADIO_DEFAULT_SKIN_VARIANT)

    if variant not in RADIO_SKIN_VARIANTS:
        return RADIO_DEFAULT_SKIN_VARIANT

    return variant


def _resolveRadioResolutionTier(screen_width: int) -> str:

    return "hd" if screen_width >= 1000 else "sd"


class RadioBrowserScreen(Screen, HelpableScreen):
    """
    Internet Radio station browsing, search and favorites (Build 0007).
    """

    SPECIFICATION_VERSION = "0.1"

    # Device test round 54 -- changed from 700x540 to 1672x941,
    # matching MusicLibraryScreen's own round 39 reasoning: every
    # widget position in _buildSkin() below is taken directly from
    # the same pixel measurements used to build the (reused, icon-
    # swapped) background images.
    DESIGN_WIDTH = 1672
    DESIGN_HEIGHT = 941

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Device test round 54 -- rewritten to reuse MusicLibraryScreen's
        own background-image approach exactly (per direct request:
        "otetaan musiikkikirjaston kuvat ja vaihdetaan vain
        kuvakkeet"): same card layout, same header/hint styling, same
        colours, same DESIGN_WIDTH/HEIGHT (1672x941, matching the
        background images' own native size). Only the icons differ
        (wifi/globe/flag instead of person/disc/musicnote, cropped
        from the user's own Internet Radio dark mockup), and the
        bottom info area is a single text block plus the existing red
        "warning" row (RadioBrowserScreen's own info format doesn't
        split into MusicLibraryScreen's label/value pairs). The hint
        row has 7 items here, not 6 (CH+/CH-: page jumping is unique
        to this screen) -- spacing recomputed from scratch for 7
        items rather than reusing MusicLibraryScreen's own 6-item
        layout, which wouldn't have fit an extra item at the same
        sizes.
        """

        sx = width / RadioBrowserScreen.DESIGN_WIDTH
        sy = height / RadioBrowserScreen.DESIGN_HEIGHT

        self._screen_width = width

        self._screen_height = height

        self._skin_variant = _resolveRadioSkinVariant()

        palette = RADIO_SKIN_PALETTES[self._skin_variant]

        panel_background_color = to_opaque_skin_color(palette["panel_background_color"])
        panel_text_color = palette["panel_text_color"]

        # Round 151, per direct request: see browserscreen.py's own
        # round 151 comment for the full reasoning -- same fix, same
        # scope (test_skin only).
        if self._skin_variant in ("test_skin", "vintage_radio"):

            scrollbar_bg = "#3A2E1A"

            info_background_attr = 'transparent="1"'

        else:

            scrollbar_bg = "#E0E0E0"

            info_background_attr = f'backgroundColor="{panel_background_color}"'

        def rect(x, y, w, h):
            return f'position="{int(x * sx)},{int(y * sy)}" size="{int(w * sx)},{int(h * sy)}"'

        def font(size):
            return f'font="Bold;{max(10, int(size * sx))}"'

        # Round 192, per direct request: see browserscreen.py's own
        # round 192 comment for the full reasoning -- same two-row
        # system_skin hint bar, adapted to this screen's own genuinely-
        # bound colour keys (only GREEN/YELLOW -- RED/BLUE aren't
        # bound here, confirmed by grepping this screen's own actions
        # dict, so no red/blue buttonTemplatePanel() call is made).
        # Round 204, per direct request ("Seuraavaksi voidaan
        # muuttaa system skin sellaisenaan ligt skiniin ja tehda
        # siita myos tumma versio dark-skiniin" -- adopt system_
        # skin's own two-row hint bar as Light's new default
        # layout, and build an equivalent for Dark too): light and
        # dark now route into this same branch. Their own
        # resources/skins/{light,dark}/{hd,sd}/*.png background
        # files were regenerated this round to match -- the exact
        # same geometric transformation already used to build
        # system_skin's own images from Light's (round 193),
        # verified against system_skin's own shipped files and
        # applied losslessly (a byte-identical flat run in each
        # content panel's own background was trimmed, not any
        # visible content). system_skin itself is intentionally
        # left in this condition too, not yet removed: the user
        # asked for it to be removed only once both Light's and
        # Dark's new two-row layouts are confirmed working on a
        # real device.
        # Round 229, per direct request ("Korvataan Vintagen
        # taustakuvat light skinin taustakuvilla ... ja lisätään
        # toinen alareunan ohjerivi käyttöön, kuten light skinissä"):
        # Vintage Radio now takes this same two-row hint bar branch
        # as Light/Dark -- its own resources/skins/vintage_radio/
        # background images were replaced this round with the Dark
        # skin's (the two-row-layout derivation of Light's, already
        # recoloured to the exact colours Vintage's own images had).
        if self._skin_variant in ("light", "dark", "vintage_radio"):

            hint_color = palette["hint_fg"]

            # Round 208, per direct request ("Nayta ylempi ohjerivi
            # (Oletuksena: Kylla)" -- let the user hide the upper
            # text row above the colour-button row): mirrors
            # mainscreen.py's own round 208 addition exactly -- see
            # its comment there for the full reasoning. The colour-
            # button row itself is untouched either way.
            show_hint_text = config_manager.get("ui.show_hint_text_row", True)

            def buttonTemplatePanel(color_name, x, y, width=280):

                icon_size = 30
                text_offset = 38
                return (
                    f'<panel position="{int(x * sx)},{int(y * sy)}" '
                    f'size="{int(width * sx)},{int(40 * sy)}">'
                    f'<panel position="0,0" '
                    f'size="{int(icon_size * sx)},{int(icon_size * sy)}">'
                    f'<panel name="__ButtonGraphic{color_name.capitalize()}__"/>'
                    f"</panel>"
                    f'<widget source="key_{color_name}" render="Label" '
                    f'position="{int(text_offset * sx)},0" '
                    f'size="{int((width - text_offset) * sx)},{int(40 * sy)}" '
                    f'font="Bold;{max(10, int(19 * sx))}" '
                    f'valign="center" halign="left" '
                    f'foregroundColor="{hint_color}" transparent="1"/>'
                    f"</panel>"
                )

            def bundledIcon(name, x_px, y):

                path = os.path.join(BUTTON_ICON_PATH, f"key_{name}.png")
                return (
                    f'<widget name="hint_icon_{name}" '
                    f'position="{int(x_px)},{int(y * sy)}" '
                    f'size="35,25" '
                    f'pixmap="{path}" alphatest="blend" transparent="1"/>'
                )

            column_x = [96, 437, 779, 1120]
            x_ok, x_menu, x_info, x_help = column_x

            icon_w, icon_h = 35, 25
            icon_gap = 6
            cluster_width = icon_w * 5 + icon_gap * 4
            right_margin = 40
            x_icon_ok = max(0, width - right_margin - cluster_width)
            x_icon_menu = x_icon_ok + icon_w + icon_gap
            x_icon_info = x_icon_menu + icon_w + icon_gap
            x_icon_help = x_icon_info + icon_w + icon_gap
            x_icon_exit = x_icon_help + icon_w + icon_gap

            x_exit = (x_icon_ok / sx) if sx else x_icon_ok

            hint_text_row_xml = f"""
            <widget name="hint_text_ok"
                    {rect(x_ok, 846, 210, 35)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{hint_color}"
                    transparent="1"/>

            <widget name="hint_text_menu"
                    {rect(x_menu, 846, 300, 35)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{hint_color}"
                    transparent="1"/>

            <widget name="hint_text_info"
                    {rect(x_info, 846, 300, 35)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{hint_color}"
                    transparent="1"/>

            <widget name="hint_text_help"
                    {rect(x_help, 846, 210, 35)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{hint_color}"
                    transparent="1"/>

            <widget name="hint_text_exit"
                    {rect(x_exit, 846, 190, 35)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{hint_color}"
                    transparent="1"/>
            """ if show_hint_text else ""

            hint_bar_xml = f"""
            {hint_text_row_xml}

            {buttonTemplatePanel("green", x_menu, 881)}

            {buttonTemplatePanel("yellow", x_info, 881)}

            {bundledIcon("ok", x_icon_ok, 881)}

            {bundledIcon("menu", x_icon_menu, 881)}

            {bundledIcon("info", x_icon_info, 881)}

            {bundledIcon("help", x_icon_help, 881)}

            {bundledIcon("exit", x_icon_exit, 881)}
            """

        else:

            hint_bar_xml = f"""
            <widget name="hint_text_leftright"
                    {rect(74, 874, 249, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_updown"
                    {rect(373, 874, 200, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_chpage"
                    {rect(623, 874, 159, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_ok"
                    {rect(832, 874, 141, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_info"
                    {rect(1023, 874, 128, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_menu"
                    {rect(1201, 874, 163, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>

            <widget name="hint_text_exit"
                    {rect(1414, 874, 155, 63)}
                    font="Bold;{max(10, int(20 * sx))}"
                    valign="center"
                    foregroundColor="{palette['hint_fg']}"
                    transparent="1"/>
            """

        return f"""
        <screen name="MediaPlayer3RadioBrowserScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{panel_background_color}"
                title="MediaPlayer3 - Internet Radio">

            <!-- Round 96: same zPosition fix as MainMenu/
                 LyricsFullscreenScreen's own round 95/96 fix for a
                 title flashing then hiding behind this background
                 once its own async decode completes; explicit,
                 permanent z-order pin, immune to decode timing. -->
            <widget name="background"
                    position="0,0"
                    size="{width},{height}"
                    zPosition="-1"
                    alphatest="blend"/>

            <widget name="status"
                    {rect(60, 19, 1550, 55)}
                    {font(34)}
                    halign="center"
                    valign="center"
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="stations_title_normal"
                    {rect(135, 80, 383, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="stations_title_active"
                    {rect(135, 80, 383, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="language_title_normal"
                    {rect(652, 80, 422, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="language_title_active"
                    {rect(652, 80, 422, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="region_title_normal"
                    {rect(1207, 80, 403, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_inactive_fg']}"
                    transparent="1"/>

            <widget name="region_title_active"
                    {rect(1207, 80, 403, 57)}
                    {font(34)}
                    valign="center"
                    foregroundColor="{palette['header_active_fg']}"
                    transparent="1"/>

            <widget name="stations"
                    {rect(40, 138, 498, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="{scrollbar_bg}"
                    scrollbarMode="showOnDemand"/>

            <widget name="language"
                    {rect(557, 138, 537, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="{scrollbar_bg}"
                    scrollbarMode="showOnDemand"/>

            <widget name="region"
                    {rect(1112, 138, 518, 518)}
                    backgroundColor="{palette['list_background_color']}"
                    foregroundColor="{panel_text_color}"
                    backgroundColorSelected="{palette['selected_row_bg']}"
                    foregroundColorSelected="{palette['selected_row_fg']}"
                    scrollbarBackgroundColor="{scrollbar_bg}"
                    scrollbarMode="showOnDemand"/>

            <widget name="info"
                    {rect(60, 702, 1550, 90)}
                    {font(22)}
                    foregroundColor="{panel_text_color}"
                    {info_background_attr}/>

            <widget name="warning"
                    {rect(60, 800, 1550, 36)}
                    {font(20)}
                    halign="center"
                    valign="center"
                    backgroundColor="#B00000"
                    foregroundColor="#FFFFFF"/>

            {hint_bar_xml}

        </screen>
        """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, session, playback_controller=None):

        width, height = compatibility.getDesktopSize(self.DESIGN_WIDTH, self.DESIGN_HEIGHT)

        self.skin = self._buildSkin(width, height)

        Screen.__init__(self, session)

        HelpableScreen.__init__(self)

        self.session = session

        self._playback = playback_controller

        self._focus = "stations"

        # Round 215, per direct request: see pageUp()/pageDown()'s own
        # comment for the full reasoning -- pins a CH+/CH- page-jump
        # burst to whichever panel it started on, so a long hold can't
        # drift onto a different panel partway through.
        self._page_jump_start_focus = None

        self._page_jump_release_timer = eTimer()

        self._page_jump_release_timer.callback.append(self._clearPageJumpFocus)

        # Round 218: see DRIFT_CORRECTION_INTERVAL_MS's own comment.
        self._stations_drift_timer = eTimer()

        self._stations_drift_timer.callback.append(self._correctStationsDrift)

        self._stations_drift_baseline = None

        # Round 222: see _armStationsDriftWatch()'s own comment.
        self._stations_nudge_direction = 0

        self._search_name = _last_search_name
        self._stations = []

        self._countries = []
        self._languages = []

        self._initialized = False

        self._log("Created")

        self._initialize()

        # Round 217: self._focus defaults to "stations" above, but
        # nothing had ever told Enigma2's real native GUI focus to
        # actually start there -- see focusPrevious()'s own comment
        # for the full finding. setFocus() needs the widgets' real GUI
        # instances, which only exist once the screen has actually
        # been shown (plugin.py's own history has a crash from an
        # "unverified onLayoutFinish API" -- onShown is the
        # already-proven-safe deferred hook, matching MainScreen's and
        # SettingsScreen's own onShown.append() precedent), so this is
        # deferred the same way rather than called directly here.
        self.onShown.append(self._onShown)

    # ------------------------------------------------------------------

    def _onShown(self) -> None:
        """
        Round 217: see __init__'s own comment -- sets Enigma2's real
        native GUI focus to match self._focus's own startup default
        ("stations") the first time this screen is actually shown.
        """

        self._setRealFocus(self._focus)

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[RadioBrowser] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        # Device test round 54 -- must be created before everything
        # else (Round 7's own paint-order rule: Python self[name]=...
        # insertion order determines paint order).
        self["background"] = Pixmap()

        self._background_picload = ePicLoad()

        compatibility.connectPictureDataSignal(self._background_picload, self._onBackgroundImageDecoded)

        self._background_pixmap_cache = {}

        # Device test round 62 -- guards against starting a second
        # concurrent decode while one is already running.
        self._background_decode_in_progress = False

        self["status"] = Label(_("Internet Radio"))

        self["stations_title_normal"] = Label(_("Stations"))
        self["stations_title_active"] = Label(_("Stations"))
        self["stations_title_active"].hide()

        self["language_title_normal"] = Label(_("Language"))
        self["language_title_active"] = Label(_("Language"))
        self["language_title_active"].hide()

        self["region_title_normal"] = Label(_("Region"))
        self["region_title_active"] = Label(_("Region"))
        self["region_title_active"].hide()

        self["stations"] = MenuList([])
        self["region"] = MenuList([])
        self["language"] = MenuList([])
        self["info"] = Label("")
        self["warning"] = Label("")
        self["warning"].hide()

        # Device test round 54 -- 7 icon+text pairs replacing the old
        # single "hint" Label, matching MusicLibraryScreen's own round
        # 33/45 pattern (icons baked into the background image, text
        # as real translatable widgets). One extra item versus
        # MusicLibraryScreen's own 6 (CH+/CH-: page jumping is unique
        # to this screen) -- spacing recomputed from scratch for 7
        # items, see _buildSkin()'s own docstring.
        self["hint_text_leftright"] = Label(_("LEFT/RIGHT: Panel"))
        self["hint_text_updown"] = Label(_("UP/DOWN: Move"))
        self["hint_text_chpage"] = Label(_("CH+/CH-: Page"))
        self["hint_text_ok"] = Label(_("OK: Options"))
        self["hint_text_info"] = Label(_("INFO: Information"))
        # Round 190: "MENU: Settings" -- menuPressed() now opens
        # SettingsScreen directly, Main Menu is gone.
        self["hint_text_menu"] = Label(_("MENU: Settings"))
        self["hint_text_exit"] = Label(_("EXIT: Back"))

        # Round 192, per direct request: see browserscreen.py's own
        # round 192 comment -- these feed system_skin's own new
        # colour-button row (_buildSkin()'s new system_skin branch).
        # RED/BLUE have no matching key_<color> source here since
        # neither is genuinely bound on this screen (confirmed by
        # grepping this file's own actions dict) -- only GREEN/
        # YELLOW's colour panels are built in that branch.
        self["key_green"] = StaticText(_("Add to Favorites"))
        self["key_yellow"] = StaticText(_("Search"))

        # Round 192: see browserscreen.py's own round 192 comment --
        # mainscreen.py's own round 167 precedent (a skin.SkinError
        # crash) requires a matching self["hint_icon_<name>"]
        # component for each of system_skin's own new bundledIcon()
        # widgets.
        self["hint_icon_ok"] = Pixmap()
        self["hint_icon_menu"] = Pixmap()
        self["hint_icon_info"] = Pixmap()
        self["hint_icon_help"] = Pixmap()
        self["hint_icon_exit"] = Pixmap()

        actions = {
            "ok": self.okPressed,
            "cancel": self.exitPressed,
            "left": self.focusPrevious,
            "right": self.focusNext,
            "up": self.moveUp,
            "down": self.moveDown,
            "menu": self.menuPressed,
            # Round 132, per direct request: EPG/INFO used to open
            # search directly; moved to YELLOW so EPG/INFO can
            # consistently open this screen's own help content
            # instead, matching every other screen.
            "yellow": self.searchByName,
            # Round 146, per direct request (colour-button audit):
            # GREEN is a direct shortcut to the station menu's own
            # existing "Add to Favorites" choice.
            "green": self.greenPressed,
        }

        for action_name in compatibility.getChannelUpKeyActionNames():
            actions[action_name] = self.pageUp

        for action_name in compatibility.getChannelDownKeyActionNames():
            actions[action_name] = self.pageDown

        for action_name in compatibility.getInfoKeyActionNames():
            actions[action_name] = self.infoPressed

        for action_name in compatibility.getHelpKeyActionNames():

            # Round 156, per direct request/device log: "displayHelpLong"
            # is excluded the same way as "displayHelp" -- a real device
            # log showed both registered on the same HelpActions context
            # for the same physical HELP key on some images, so leaving
            # it bound here let it win that key over the native handler.
            # See mainscreen.py's own round 156 comment for the full story.
            if action_name in ("displayHelp", "displayHelpLong"):

                continue

            actions[action_name] = self.infoPressed

        contexts = [
            "OkCancelActions",
            "ColorActions",
            "DirectionActions",
            "MediaPlayerActions",
            "MenuActions",
            "InfoActions",
            "InfobarActions",
            "InfobarBouquetActions",
            "InfobarEPGActions",
            "HelpActions",
        ]

        help_text_by_handler = {
            self.okPressed: _("open the actions menu"),
            self.exitPressed: _("go back"),
            self.focusPrevious: _("move to the previous column"),
            self.focusNext: _("move to the next column"),
            self.moveUp: _("move up"),
            self.moveDown: _("move down"),
            self.menuPressed: _("open settings"),
            self.pageUp: _("page up"),
            self.pageDown: _("page down"),
            self.searchByName: _("search by name"),
            self.greenPressed: _("add the selected station to favorites"),
            self.infoPressed: _("show information about this screen"),
        }

        try:

            helpable_actions = {
                action_name: (handler, help_text_by_handler.get(handler, ""))
                for action_name, handler in actions.items()
            }

            self["actions"] = HelpableActionMap(self, contexts, helpable_actions, -1)

        except Exception as error:

            logger.warning(f"[RadioBrowserScreen] HelpableActionMap unavailable, falling back to plain ActionMap: {error}")

            self["actions"] = ActionMap(contexts, actions, -1)

        # Default Region/Language follow Settings
        # (RADIOBROWSER_SCREEN_SPEC.md "Default Region and Language
        # values should follow receiver settings whenever possible." --
        # MediaPlayer3 has no reliable way to detect the receiver's
        # actual region/language on its own, so this follows the
        # user's own Settings default instead; see
        # docs/Claude_notes_build0007.txt).
        self._default_country = config_manager.get("radio.default_country", "")
        self._default_language = config_manager.get("radio.default_language", "")

        # Build 0007, device test round 8 -- "Nyt on joskus auennut
        # ikkuna ennen kuin on kanavat saatu haettua": _reloadFilters()
        # and _search() both make blocking network calls, so calling
        # them synchronously here meant the screen could finish
        # opening (with an empty list) well before Enigma2 actually
        # painted anything, leaving the user looking at a blank
        # screen with no indication anything was happening. Show an
        # immediate "please wait" message and defer the actual work
        # to the next event-loop iteration (a 10ms singleshot timer)
        # so the message is guaranteed to render first.
        self["status"].setText(_("Searching for stations, please wait..."))

        self._updateColumnHighlighting()

        self._initial_load_timer = eTimer()

        self._initial_load_timer.callback.append(self._performInitialLoad)

        # Device test round 27 -- debounced station codec logging
        # (cfg.logging.log_station_codecs). Restarted on every
        # Stations-column selection change (_onSelectionChanged());
        # only fires once the selection has actually settled for
        # CODEC_LOG_DEBOUNCE_MS, so scrolling past many stations
        # quickly triggers at most one ffprobe call, for whichever one
        # the user actually stopped on -- not one per station passed
        # through.
        self._codec_log_timer = eTimer()

        self._codec_log_timer.callback.append(self._logSelectedStationCodec)

        # Round 199 -- see REGION_LANGUAGE_SEARCH_DEBOUNCE_MS's own
        # comment above. Same restart-on-every-selection-change pattern
        # as _codec_log_timer just above.
        self._region_language_search_timer = eTimer()

        self._region_language_search_timer.callback.append(self._runSearchWithStatus)

        self._initial_load_timer.start(10, True)

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _performInitialLoad(self) -> None:
        """
        Build 0010, BUILD_0010_PLAN.md "RadioBrowser Database" /
        RADIOBROWSER_SPEC.md "Empty Database": "If no local stations
        are available... The user may be offered the option to
        download the RadioBrowser station database again." -- an
        empty local database asks before doing a first (potentially
        slow) bulk download, rather than silently blocking the screen
        on it. A non-empty database that's simply due for its
        periodic refresh (shouldAutoUpdateDatabase()) is different:
        RADIOBROWSER_SPEC.md "An automatic update shall not interrupt
        active playback" -- shows results immediately from whatever's
        already stored, then updates quietly in the background
        afterwards without touching the list currently on screen (the
        refreshed data simply takes effect next search).
        """

        if internetradio_manager.getStationDatabaseInfo()["count"] == 0:

            self._offerDatabaseDownload()

            return

        self._reloadFilters()

        self._runSearchWithStatus()

        if internetradio_manager.shouldAutoUpdateDatabase():

            self._scheduleBackgroundDatabaseUpdate()

    # ------------------------------------------------------------------

    def _offerDatabaseDownload(self) -> None:

        self.session.openWithCallback(
            self._databaseDownloadChoiceMade,
            MessageBox,
            _("No stations available yet. Download the station database now?"),
            MessageBox.TYPE_YESNO,
        )

    # ------------------------------------------------------------------

    def _databaseDownloadChoiceMade(self, confirmed) -> None:

        if not confirmed:

            self._reloadFilters()

            self._runSearchWithStatus()

            return

        self["status"].setText(_("Downloading station database, please wait..."))

        self._db_update_timer = eTimer()

        self._db_update_timer.callback.append(self._performInitialDatabaseUpdate)

        self._db_update_timer.start(10, True)

    # ------------------------------------------------------------------

    def _performInitialDatabaseUpdate(self) -> None:

        if not internetradio_manager.updateStationDatabase():

            self["status"].setText(_("Update failed. No station data available."))

        self._reloadFilters()

        self._runSearchWithStatus()

    # ------------------------------------------------------------------

    def _scheduleBackgroundDatabaseUpdate(self) -> None:

        self._background_db_update_timer = eTimer()

        self._background_db_update_timer.callback.append(internetradio_manager.updateStationDatabase)

        self._background_db_update_timer.start(500, True)

    # ------------------------------------------------------------------
    # Filters / search
    # ------------------------------------------------------------------

    def _reloadFilters(self) -> None:

        self._countries = internetradio_manager.getCountries()

        self._languages = internetradio_manager.getLanguages()

        self._promoteAppLanguage()

        self._promoteConfiguredDefault(self._languages, self._default_language)

        self._promoteConfiguredDefault(self._countries, self._default_country)

        self["region"].setList([_("Any")] + [entry.get("name", "?") for entry in self._countries])

        self["language"].setList([_("Any")] + [entry.get("name", "?") for entry in self._languages])

        if _last_region_name:

            self._selectListEntry("region", _last_region_name)

        elif self._default_country:

            self._selectListEntry("region", self._default_country)

        if _last_language_name:

            self._selectListEntry("language", _last_language_name)

        elif self._default_language:

            self._selectListEntry("language", self._default_language)

    # ------------------------------------------------------------------

    # RadioBrowser identifies languages by full English name ("finnish",
    # "english", ...), not by MediaPlayer3's own "fi"/"en" language
    # codes -- this maps the ones localization.py's own AVAILABLE_LANGUAGES
    # currently ships.
    # Round 104 -- moved to internetradio_manager.py's own module-level
    # APP_LANGUAGE_TO_RADIOBROWSER_NAME (shared with that module's own
    # supplemental-download pass); kept as an alias here so this
    # class's own two existing call sites below didn't need touching.
    _APP_LANGUAGE_TO_RADIOBROWSER_NAME = APP_LANGUAGE_TO_RADIOBROWSER_NAME

    def _promoteAppLanguage(self) -> None:
        """
        Move the app's own configured UI language (Settings ->
        Language, general.language) to position 2 in the Language
        panel -- right after "Any" -- since with potentially hundreds
        of languages in the full RadioBrowser list, the one the user
        is most likely to want shouldn't require scrolling to find
        (requested after real device testing).

        A no-op if the app's language has no known RadioBrowser name
        mapping, or if that name isn't present in the results RadioBrowser
        actually returned.
        """

        app_language_name = self._APP_LANGUAGE_TO_RADIOBROWSER_NAME.get(getCurrentLanguage())

        if not app_language_name:
            return

        match = next(
            (entry for entry in self._languages if entry.get("name", "").lower() == app_language_name),
            None,
        )

        if match is None:
            return

        self._languages.remove(match)

        self._languages.insert(0, match)

    # ------------------------------------------------------------------

    def _promoteConfiguredDefault(self, entries, default_value) -> None:
        """
        Round 100, per direct request: generic version of
        _promoteAppLanguage()'s own "move to position 2, right after
        Any" logic, for whatever the user has explicitly set as their
        own Radio default language/country via OK on a language/
        region entry (see okPressed()/_setAsRadioDefault()) -- not
        tied to one specific language-name mapping table the way
        _promoteAppLanguage() is, since radio.default_language/
        radio.default_country already store the RadioBrowser-native
        name directly (the exact same "name" field these entries
        already carry), needing no translation lookup at all. Called
        after _promoteAppLanguage() in _reloadFilters() so an
        explicit user choice here wins the position-2 spot over the
        automatic app-language promotion if the two ever differ.
        """

        if not default_value:
            return

        match = next((entry for entry in entries if entry.get("name", "") == default_value), None)

        if match is None:
            return

        entries.remove(match)

        entries.insert(0, match)

    # ------------------------------------------------------------------

    def _selectListEntry(self, widget_name, value) -> None:

        entries = self[widget_name].list or []

        try:
            index = entries.index(value)

        except ValueError:
            return

        while self[widget_name].getSelectedIndex() != index:

            self[widget_name].down()

    # ------------------------------------------------------------------

    def _selectedRegion(self):

        index = self["region"].getSelectedIndex()

        return self._countries[index - 1]["name"] if index > 0 else None

    # ------------------------------------------------------------------

    def _selectedLanguage(self):

        index = self["language"].getSelectedIndex()

        return self._languages[index - 1]["name"] if index > 0 else None

    # ------------------------------------------------------------------

    def _search(self) -> None:

        search_language = self._selectedLanguage()

        # Device test round 68 -- see config.py's own comments for
        # radio.search_limit/radio.unlimited_for_own_language for the
        # full reasoning; this is the one place both settings actually
        # take effect.
        limit = config_manager.get("radio.search_limit", 100)

        if search_language and config_manager.get("radio.unlimited_for_own_language", False):

            app_language_code = getCurrentLanguage()

            app_language_name = self._APP_LANGUAGE_TO_RADIOBROWSER_NAME.get(app_language_code)

            if app_language_name and search_language.lower() == app_language_name.lower():

                limit = 0

        self._stations = internetradio_manager.search(
            name=self._search_name or None,
            country=self._selectedRegion(),
            language=search_language,
            limit=limit,
        )

        self["stations"].setList([entry.get("name", "?") for entry in self._stations])

        self._updateInfoPanel()

    # ------------------------------------------------------------------

    def _runSearchWithStatus(self) -> None:
        """
        Show a "please wait" message immediately, then defer the
        actual (blocking) search to the next event-loop iteration so
        the message is guaranteed to render first, and finally show a
        "found N stations" message for a moment before reverting to
        the normal focus indicator (Build 0007, device test round 8 --
        used for every search, not just the initial load, since a
        filter or name-search change makes the same kind of blocking
        network call).
        """

        self["status"].setText(_("Searching for stations, please wait..."))

        self._search_timer = eTimer()

        self._search_timer.callback.append(self._performDeferredSearch)

        self._search_timer.start(10, True)

    # ------------------------------------------------------------------

    def _performDeferredSearch(self) -> None:

        self._search()

        # Round 214, per direct request: a search with every filter
        # left on "Any" and no name text is the one case
        # internetradio_manager.search() may itself cap below what was
        # actually asked for (UNFILTERED_SEARCH_RESULT_CAP, round
        # 213) -- shown here as "Found X/Y stations" (Y = the local
        # database's own total station count, already tracked via
        # getStationDatabaseInfo() and refreshed whenever the database
        # itself is updated) so it's clear the smaller number is a
        # deliberate cap, not "that's all there is". Any filtered
        # search keeps the plain "Found N stations" message -- the
        # database's own overall total isn't a meaningful comparison
        # once a filter has already narrowed the result set to begin
        # with.
        found = len(self._stations)

        no_filter_at_all = not (self._search_name or self._selectedRegion() or self._selectedLanguage())

        total = internetradio_manager.getStationDatabaseInfo().get("count", 0)

        if no_filter_at_all and total and found < total:

            self["status"].setText(_("Found {0}/{1} stations").format(found, total))

        else:

            self["status"].setText(_("Found {0} stations").format(found))

        self._result_message_timer = eTimer()

        self._result_message_timer.callback.append(self._updateFocusIndicator)

        self._result_message_timer.start(1500, True)

# End of Part 1
    # ------------------------------------------------------------------
    # Panel navigation (RADIOBROWSER_SCREEN_SPEC.md "Navigation")
    # ------------------------------------------------------------------

    def focusPrevious(self) -> None:

        old_focus = self._focus

        self._focus = PANELS[(PANELS.index(self._focus) - 1) % len(PANELS)]

        # Round 216, diagnostic (per direct request): logs the actual
        # before/after transition, not just "LEFT pressed" -- this is
        # the ONLY code path that can reassign self._focus at all
        # (confirmed by reading every other method in this file), so
        # if a device log ever shows self._focus becoming "stations"
        # without one of these two lines immediately before it, the
        # real cause is proven to be something other than self._focus
        # itself, e.g. the "stations" widget's own selection moving
        # independently of which panel self._focus says is active.
        logger.verbose("[RadioBrowser] LEFT pressed. focus %s -> %s", old_focus, self._focus)

        # Round 217 (root cause found via the 1.2.005 diagnostic log):
        # self._focus is only ever this screen's OWN bookkeeping of
        # which panel is "logically" active -- it never actually moved
        # Enigma2's real native GUI keyboard focus away from
        # "stations" (the first widget created in _initialize()),
        # because nothing in this file ever called setFocus()/
        # canFocus()/selectionEnabled() (confirmed by grep returning no
        # matches at all). A held CH-/CH+ key only resolves its very
        # first ("Make") event through the ActionMap into our own
        # pageUp()/pageDown(); every subsequent auto-repeat event never
        # reaches the ActionMap/our code at all and instead falls
        # through directly to whatever widget holds real native focus
        # -- always "stations", regardless of what self._focus said.
        # That's exactly the symptom reported: the first CH- page-jump
        # lands on the right (logically focused) panel, then every
        # further repeat silently scrolls "stations" instead. Giving
        # Enigma2 the real focus transfer here (and in focusNext(),
        # and once at startup to match the "stations" default) should
        # make repeat events land on whichever panel is actually
        # active.
        self._setRealFocus(self._focus)

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def focusNext(self) -> None:

        old_focus = self._focus

        self._focus = PANELS[(PANELS.index(self._focus) + 1) % len(PANELS)]

        # Round 216: see focusPrevious()'s own comment.
        logger.verbose("[RadioBrowser] RIGHT pressed. focus %s -> %s", old_focus, self._focus)

        # Round 217: see focusPrevious()'s own comment.
        self._setRealFocus(self._focus)

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def _setRealFocus(self, panel_name: str) -> None:
        """
        Round 217: transfers Enigma2's actual native GUI keyboard focus
        to the named panel's widget, so that key-repeat events this
        screen's own ActionMap never sees (see focusPrevious()'s own
        comment for the full device-log evidence) land on the correct
        widget instead of always on "stations". Wrapped in try/except
        and never raises -- if a particular skin/widget combination
        doesn't support it for some reason, the worst case is exactly
        today's existing (already-reported) behaviour, not a crash.
        """

        try:
            self.setFocus(self[panel_name])

        except Exception as error:

            logger.verbose(f"[RadioBrowser] _setRealFocus({panel_name}) failed: {error}")

    # ------------------------------------------------------------------

    def moveUp(self) -> None:

        logger.verbose("[RadioBrowser] UP pressed. focus=%s", self._focus)

        self._logPanelIndices("UP before")

        self[self._focus].up()

        self._logPanelIndices("UP after")

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def moveDown(self) -> None:

        logger.verbose("[RadioBrowser] DOWN pressed. focus=%s", self._focus)

        self._logPanelIndices("DOWN before")

        self[self._focus].down()

        self._logPanelIndices("DOWN after")

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageUp(self) -> None:
        """
        CH+ -- jump PAGE_STEP entries up in the focused panel
        (requested after real device testing). Clamped so it stops at
        the top of the list instead of wrapping around when fewer
        than PAGE_STEP entries remain (round 80, per direct request).

        Round 215: see PAGE_JUMP_RELEASE_MS's own comment -- the first
        CH+/CH- event of a burst locks the page-jump to whatever panel
        is focused at that moment (self._page_jump_start_focus);
        every repeat event within the same burst keeps acting on that
        same panel even if self._focus itself were to change
        underneath it, instead of re-reading self._focus fresh each
        time. The lock releases PAGE_JUMP_RELEASE_MS after the last
        repeat event, so a genuinely new press (after releasing the
        key) picks up whatever panel LEFT/RIGHT has since moved to.

        Round 218: if this is a fresh lock (not already active from a
        near-simultaneous previous call) and the locked panel isn't
        "stations" itself, also arms the drift-correction timer -- see
        _correctStationsDrift()'s own comment for why.
        """

        fresh_lock = self._page_jump_start_focus is None

        if fresh_lock:

            self._page_jump_start_focus = self._focus

        panel = self._page_jump_start_focus

        logger.verbose("[RadioBrowser] CH+ pressed. focus=%s", panel)

        self._logPanelIndices("CH+ before")

        steps = min(PAGE_STEP, self[panel].getSelectedIndex())

        for _step in range(steps):

            self[panel].up()

        self._logPanelIndices("CH+ after up()")

        if fresh_lock and panel != "stations":

            # Round 222: see _armStationsDriftWatch()'s own comment.
            self._armStationsDriftWatch("up")

            self._armStationsDriftTimer()

            # Round 220: the drift timer's own first tick needs a much
            # longer grace period than a plain repeat gap -- see
            # DRIFT_WATCHDOG_INITIAL_MS's own comment.
            self._page_jump_release_timer.start(DRIFT_WATCHDOG_INITIAL_MS, True)

        else:

            self._page_jump_release_timer.start(PAGE_JUMP_RELEASE_MS, True)

        self._onSelectionChanged()

        self._logPanelIndices("CH+ after _onSelectionChanged()")

    # ------------------------------------------------------------------

    def pageDown(self) -> None:
        """
        CH- -- see pageUp()'s own comment (round 80 for PAGE_STEP,
        round 215 for the same-panel lock across a key-repeat burst,
        round 218 for the drift-correction timer).
        """

        fresh_lock = self._page_jump_start_focus is None

        if fresh_lock:

            self._page_jump_start_focus = self._focus

        panel = self._page_jump_start_focus

        logger.verbose("[RadioBrowser] CH- pressed. focus=%s", panel)

        self._logPanelIndices("CH- before")

        entries = self[panel].list or []

        steps = min(PAGE_STEP, max(0, len(entries) - 1 - self[panel].getSelectedIndex()))

        for _step in range(steps):

            self[panel].down()

        if fresh_lock and panel != "stations":

            # Round 222: see _armStationsDriftWatch()'s own comment.
            self._armStationsDriftWatch("down")

            self._armStationsDriftTimer()

        self._logPanelIndices("CH- after down()")

        if fresh_lock and panel != "stations":

            # Round 220: see pageUp()'s own comment / DRIFT_WATCHDOG_INITIAL_MS.
            self._page_jump_release_timer.start(DRIFT_WATCHDOG_INITIAL_MS, True)

        else:

            self._page_jump_release_timer.start(PAGE_JUMP_RELEASE_MS, True)

        self._onSelectionChanged()

        self._logPanelIndices("CH- after _onSelectionChanged()")

    # ------------------------------------------------------------------

    def _logPanelIndices(self, label: str) -> None:
        """
        Round 216, diagnostic only (per direct request after three
        device logs in a row showed self._focus/the locked panel
        logging correctly on every single CH+/CH- event, yet the
        Stations column was still reported moving instead of Region/
        Language): logs every panel's own current getSelectedIndex()
        in one line, so a device log can show directly whether a
        panel OTHER than the one pageUp()/pageDown() just acted on
        also moved -- something logging just the chosen panel's name
        can never catch. Called at several points around each page-
        jump (before/after the up()/down() loop, and again after
        _onSelectionChanged()) so the exact moment any unexpected
        change happens narrows down to one of those three windows.
        Never raises -- a widget that isn't ready yet just logs
        nothing rather than breaking the key handling it's attached
        to.
        """

        try:
            indices = {name: self[name].getSelectedIndex() for name in PANELS}

        except Exception as error:

            logger.verbose(f"[RadioBrowser] {label}: unable to read panel indices ({error}).")

            return

        logger.verbose(
            f"[RadioBrowser] {label}: stations={indices['stations']} "
            f"language={indices['language']} region={indices['region']}"
        )

    # ------------------------------------------------------------------

    def _clearPageJumpFocus(self) -> None:
        """
        Round 215: releases the CH+/CH- same-panel lock
        PAGE_JUMP_RELEASE_MS after the last repeat event of a burst --
        see PAGE_JUMP_RELEASE_MS's own comment for why that particular
        duration. Letting self._page_jump_start_focus go back to None
        is enough; the next CH+/CH- event (if any) re-reads whatever
        self._focus is at that point, same as a fresh, un-held press
        always has.

        Round 218: also stops the drift-correction timer, if it was
        running -- see _correctStationsDrift()'s own comment. Safe to
        call .stop() even if it was never started.

        Round 222: also undoes any still-pending one-step nudge from
        _armStationsDriftWatch() -- see its own comment. This runs
        whether or not any real drift ever happened in between, since
        every drift correction always puts Stations back at the
        nudged baseline, never at its true original position.
        """

        self._page_jump_start_focus = None

        self._stations_drift_timer.stop()

        self._stations_drift_baseline = None

        if self._stations_nudge_direction:

            # Round 223: self._stations_nudge_direction now holds a
            # signed STEP COUNT (see _armStationsDriftWatch()'s own
            # comment), not just a +1/-1 direction, so reversing it
            # takes that many steps, not just one.
            steps = abs(self._stations_nudge_direction)

            if self._stations_nudge_direction < 0:

                for _step in range(steps):

                    self["stations"].down()

            else:

                for _step in range(steps):

                    self["stations"].up()

            self._stations_nudge_direction = 0

            self._onSelectionChanged()

    # ------------------------------------------------------------------

    def _armStationsDriftWatch(self, direction: str) -> None:
        """
        Round 222, per direct device report: CH+ held on Region/
        Language silently does nothing whenever Stations already has
        its own FIRST entry selected, and the mirror case for CH- when
        Stations already has its own LAST entry selected -- worst with
        exactly one found station, where that single entry is
        simultaneously both (reported as the clearest way to reproduce
        it). The whole drift-correction mechanism (round 218 onward)
        only ever notices a held key is still active by seeing
        Stations' own position actually change; when Stations is
        already pinned at the boundary the held direction would push
        it toward, the native drift mechanism keeps trying on every
        repeat but has nowhere left to move it, so its own position
        never changes at all -- indistinguishable from the key having
        already been released, so the lock on Region/Language's own
        panel (and the drift correction) was clearing out early
        exactly like it did before round 220's fix, just for a
        different underlying reason.

        If Stations already sits on that boundary when the lock
        engages, nudges it OFF that boundary first, in the opposite
        direction from the held key, so the very next native repeat
        (if the key really is still held) has somewhere to go and
        becomes visible to the drift-correction timer like any other
        case. _clearPageJumpFocus() undoes the nudge once the hold
        actually ends, restoring Stations to its true original
        position -- this is the one-time cost of the fix, a block of
        steps applied once and then reversed once, rather than a
        change that lingers.

        Round 223, per direct device report: the initial version of
        this nudged by exactly ONE step, which worked (CH+ on Region/
        Language started moving again) but only ever one row at a
        time, while CH- (never needing a nudge, since Stations always
        had plenty of room already) kept moving a full PAGE_STEP at a
        time as intended. Per that same device log, a single unclaimed
        repeat event apparently moves Stations by a full native "page"
        in one go, not by one row -- round 218's own correction only
        ever sees however much of that native page-jump actually fit
        before Stations hit its own boundary again. A one-step nudge
        left only one row of room, clamping every native page-jump
        down to a one-row move; nudging by a full PAGE_STEP's worth of
        room instead (clamped to however much the list actually has,
        same as pageUp()/pageDown()'s own clamping) gives a real
        native page-jump room to land in full, matching CH-'s own
        already-correct behaviour.

        Has no effect (and nothing to undo later) when Stations has
        more than one entry but isn't already sitting on the relevant
        boundary -- the normal, most common case. With exactly one
        found station, the single entry is both boundaries at once,
        so there is no direction to nudge it in at all; that specific
        edge case remains a known limitation.
        """

        entries = self["stations"].list or []

        nudge = 0

        if entries:

            current = self["stations"].getSelectedIndex()

            if direction == "down" and current >= len(entries) - 1:

                steps = min(PAGE_STEP, current)

                for _step in range(steps):

                    self["stations"].up()

                # Only record the nudge if it actually moved something
                # -- with exactly one entry, up() is itself clamped at
                # the same single index, so there is nowhere to nudge
                # to and nothing will need undoing later either.
                actual_steps = current - self["stations"].getSelectedIndex()

                if actual_steps:

                    nudge = -actual_steps

            elif direction == "up" and current <= 0:

                steps = min(PAGE_STEP, max(0, len(entries) - 1 - current))

                for _step in range(steps):

                    self["stations"].down()

                actual_steps = self["stations"].getSelectedIndex() - current

                if actual_steps:

                    nudge = actual_steps

        self._stations_nudge_direction = nudge

        self._stations_drift_baseline = self["stations"].getSelectedIndex()

    # ------------------------------------------------------------------

    def _armStationsDriftTimer(self) -> None:
        """
        Round 219, diagnostic addition: isolates the
        self._stations_drift_timer.start() call behind its own
        explicit success/failure log line, since the previous device
        log showed the whole drift-correction mechanism having zero
        effect with no error anywhere -- this rules out (or confirms)
        the .start() call itself silently failing.
        """

        try:
            self._stations_drift_timer.start(DRIFT_CORRECTION_INTERVAL_MS, False)

            logger.verbose(
                f"[RadioBrowser] Drift timer armed (interval={DRIFT_CORRECTION_INTERVAL_MS}ms, "
                f"baseline={self._stations_drift_baseline})."
            )

        except Exception as error:

            logger.verbose(f"[RadioBrowser] Drift timer failed to arm: {error}")

    # ------------------------------------------------------------------

    def _correctStationsDrift(self) -> None:
        """
        Round 218 (per direct request after a fresh device log proved
        round 217's setFocus() fix had no effect): a held CH-/CH+ key
        only ever gets ONE event through to this project's own Python
        code (see pageUp()'s/pageDown()'s own comment and round 217's
        full finding) -- every repeat event after that lands somewhere
        that still ends up moving the "stations" MenuList's own
        selection directly, regardless of which panel is actually
        locked/focused, by some mechanism giving Enigma2 real GUI
        focus did not change. Rather than keep guessing at what that
        mechanism actually is, this runs on a short repeating timer
        (armed only while the locked panel isn't "stations" itself,
        so there's nothing to correct) and treats the symptom
        directly: any change in "stations"' own position since the
        last tick is undone there and replayed on the actually-locked
        panel instead, in the same direction and by the same amount.
        Each real correction also re-arms the release timer (round
        215's own PAGE_JUMP_RELEASE_MS, previously only ever armed
        once per hold since pageUp()/pageDown() itself is only ever
        called once per hold) -- a real drift tick IS the proof that
        the key is still actually held, which pageUp()/pageDown()
        being called again never was.

        Round 219, diagnostic addition (per direct request after a
        device log showed ZERO effect from this timer at all -- not
        even one "drifted" log line across an ~11s hold that still
        ended up moving Stations by over a thousand -- despite
        MainScreen's own 1000ms refresh timer firing normally
        throughout that exact same window, which rules out the whole
        reactor/event loop being blocked): wrapped the entire body in
        try/except (previously had none at all -- if this ever raised
        on its very first tick, Enigma2's own callback dispatcher
        could have silently discarded that exception, which would
        perfectly explain total silence despite correct-looking code)
        and now logs unconditionally on every single tick, not just
        when a correction actually happens, so the next device log
        can show directly whether this method is ever even being
        invoked at all, and if so, what it's actually reading.
        """

        try:

            self._correctStationsDriftImpl()

        except Exception as error:

            logger.verbose(f"[RadioBrowser] _correctStationsDrift tick raised: {error}")

    # ------------------------------------------------------------------

    def _correctStationsDriftImpl(self) -> None:

        panel = self._page_jump_start_focus

        logger.verbose(
            f"[RadioBrowser] drift tick: panel={panel} "
            f"stations={self['stations'].getSelectedIndex()} "
            f"baseline={self._stations_drift_baseline}"
        )

        if panel is None or panel == "stations":

            self._stations_drift_timer.stop()

            self._stations_drift_baseline = None

            return

        if self._stations_drift_baseline is None:

            self._stations_drift_baseline = self["stations"].getSelectedIndex()

            return

        current = self["stations"].getSelectedIndex()

        delta = current - self._stations_drift_baseline

        if delta == 0:

            return

        logger.verbose(
            f"[RadioBrowser] Stations drifted by {delta} while locked to "
            f"{panel} -- redirecting."
        )

        if delta > 0:

            for _step in range(delta):

                self["stations"].up()

        else:

            for _step in range(-delta):

                self["stations"].down()

        entries = self[panel].list or []

        if delta > 0:

            steps = min(delta, max(0, len(entries) - 1 - self[panel].getSelectedIndex()))

            for _step in range(steps):

                self[panel].down()

        else:

            steps = min(-delta, self[panel].getSelectedIndex())

            for _step in range(steps):

                self[panel].up()

        self._stations_drift_baseline = self["stations"].getSelectedIndex()

        self._page_jump_release_timer.start(PAGE_JUMP_RELEASE_MS, True)

        self._onSelectionChanged()

        self._logPanelIndices("drift-corrected")

    # ------------------------------------------------------------------

    def _onSelectionChanged(self) -> None:

        if self._focus == "stations":

            self._updateInfoPanel()

            # Device test round 27 -- restart, not just start: an
            # eTimer already running when start() is called again
            # keeps counting from the new call, which is exactly the
            # debounce behaviour wanted here (see CODEC_LOG_DEBOUNCE_MS's
            # own comment).
            if config_manager.get("logging.log_station_codecs", False):

                self._codec_log_timer.start(CODEC_LOG_DEBOUNCE_MS, True)

        else:

            # Region/Language selection changes trigger an automatic
            # re-search (RADIOBROWSER_SCREEN_SPEC.md "Search results
            # update automatically whenever a filter changes.").
            global _last_region_name, _last_language_name

            _last_region_name = self._selectedRegion()

            _last_language_name = self._selectedLanguage()

            # Round 199 -- restart, not just start: an eTimer already
            # running when start() is called again keeps counting from
            # the new call, the same debounce behaviour
            # CODEC_LOG_DEBOUNCE_MS already relies on above. Only
            # actually searches once the Region/Language selection has
            # settled on one entry for REGION_LANGUAGE_SEARCH_DEBOUNCE_MS
            # -- browsing quickly through the column no longer fires a
            # search (each one a real, measurable scan of the local
            # station database) per keypress.
            self._region_language_search_timer.start(REGION_LANGUAGE_SEARCH_DEBOUNCE_MS, True)

    # ------------------------------------------------------------------

    def _logSelectedStationCodec(self) -> None:
        """
        Device test round 27 -- user request: a log entry for the
        real (ffprobe-measured) codec of whatever station the
        Stations-column selection has settled on, building up
        real-world data across many stations/sessions -- named
        examples of specific stations worth checking this way were
        Radio Nova and Radio SuomiRock. Gated by cfg.logging.
        log_station_codecs (on by default since device test round 29
        -- see that config entry's own comment) and
        _onSelectionChanged()'s own debounce (CODEC_LOG_DEBOUNCE_MS).

        Device test round 29: now also updates the info panel itself,
        not just the log -- "Radioselaimen alaosassa voisi nakya
        ensin radiobrowserin tarjoama kanavatieto, kuten nyt ja sitten
        kun ffprobe on saanut tiedon kerattya, niin siihen voisi
        paivittya koodekki bittinopeus yms." _updateInfoPanel() (called
        first, synchronously, from _onSelectionChanged()) already
        shows RadioBrowser's own reported info immediately; once this
        debounced probe actually completes, its real measurement
        replaces the codec/bitrate line if the selection is still on
        the same station (re-checked below).

        A failed/timed-out probe ("ffprobe testi ei mene lapi") shows
        a warning line instead, per direct request.
        """

        if not ffprobe_available():
            return

        index = self["stations"].getSelectedIndex()

        if not self._stations or not (0 <= index < len(self._stations)):
            return

        station = self._stations[index]

        url = station.get("url_resolved") or station.get("url")

        if not url:
            return

        result = ffprobe_probe(url)

        name = station.get("name", "Unknown")

        if result:

            logger.info(f"[RadioBrowser] Station codec (ffprobe): {name} -> {result}")

        else:

            logger.info(f"[RadioBrowser] Station codec (ffprobe): {name} -> probe failed or timed out")

        if self["stations"].getSelectedIndex() == index:

            self["info"].setText(self._formatStationInfo(station, probe_result=result))

            self._setWarning(_("Warning: this station may not work.") if result is None else None)

    # ------------------------------------------------------------------

    def _updateFocusIndicator(self) -> None:
        """
        Build 0010, device test round 7 -- see MusicLibraryScreen's
        identical fix/reasoning. Only overrides the panel-name display
        this method used to own -- the separate, still-important
        transient messages ("Searching...", "Found N stations") set
        elsewhere are unaffected and still take priority whenever
        they're active.
        """

        self["status"].setText(_("Internet Radio"))

        self._updateColumnHighlighting()

    # ------------------------------------------------------------------

    def _updateColumnHighlighting(self) -> None:
        """
        Device test round 54 -- the active/inactive column-header
        colouring now lives in one of three pre-rendered background
        images (resources/skins/{variant}/{tier}/radiobrowser_
        {focus}_active.png), swapped here instead of toggling
        individual bg widgets, matching MusicLibraryScreen's own round
        39/45. Header TEXT stays real, translatable normal/active
        widget pairs (round 45's own lesson), toggled here too.
        """

        self._decodeBackgroundImage(self._focus)

        for panel_name in PANELS:

            is_active = panel_name == self._focus

            try:
                self[f"{panel_name}_title_normal"].hide() if is_active else self[f"{panel_name}_title_normal"].show()

                self[f"{panel_name}_title_active"].show() if is_active else self[f"{panel_name}_title_active"].hide()

            except Exception as error:

                logger.verbose(f"[RadioBrowser] Unable to set column highlight visibility: {error}")

    # ------------------------------------------------------------------
    # Background image (device test round 54 -- mirrors
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

            logger.verbose("[RadioBrowser] background widget not ready yet, retrying decode shortly.")

            retry_timer = eTimer()

            retry_timer.callback.append(lambda: self._decodeBackgroundImage(focus_state))

            retry_timer.start(100, True)

            self._pending_background_retry_timer = retry_timer

            return

        image_path = resolve_skin_asset_path(
            self._skin_variant,
            _resolveRadioResolutionTier(self._screen_width),
            f"radiobrowser_{focus_state}_active.png",
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

            logger.verbose(f"[RadioBrowser] Unable to decode background image {image_path}: {error}")

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

            logger.verbose(f"[RadioBrowser] Unable to apply decoded background image: {error}")

        finally:

            self._background_decode_in_progress = False

    # ------------------------------------------------------------------

    def _updateInfoPanel(self) -> None:

        index = self["stations"].getSelectedIndex()

        # Device test round 30: clear any warning left over from a
        # previous station's probe result -- a fresh selection hasn't
        # been probed yet, so nothing about it is known to be wrong.
        self._setWarning(None)

        if not self._stations or not (0 <= index < len(self._stations)):

            self["info"].setText(_("No media selected"))

            return

        station = self._stations[index]

        self["info"].setText(self._formatStationInfo(station))

    # ------------------------------------------------------------------

    def _setWarning(self, text) -> None:
        """
        Device test round 30 -- shows/hides the dedicated red-
        background "warning" widget (see _buildSkin()'s own comment
        for why this needed a separate widget rather than just another
        line inside "info"). `text=None` hides it.
        """

        if text:

            self["warning"].setText(text)

            self["warning"].show()

        else:

            self["warning"].setText("")

            self["warning"].hide()

    # ------------------------------------------------------------------

    def _formatStationInfo(self, station, probe_result=None) -> str:
        """
        Shared by _updateInfoPanel() (RadioBrowser's own reported
        info, shown immediately) and _logSelectedStationCodec() (the
        same text, with the codec/bitrate line replaced by a real
        ffprobe measurement once one becomes available) -- device test
        round 29. A failed probe no longer appends a warning line here
        (device test round 30) -- see _setWarning()'s own dedicated
        widget instead.
        """

        codec = station.get("codec", "Unknown")

        bitrate = station.get("bitrate", "Unknown")

        if probe_result:

            if probe_result.get("codec"):
                codec = f"{probe_result['codec']} ({_('measured')})"

            if probe_result.get("bitrate"):
                bitrate = f"{probe_result['bitrate']} ({_('measured')})"

        lines = [
            station.get("name", "Unknown"),
            f"{_('Codec')}: {codec}   {_('Bitrate')}: {bitrate}",
            f"{_('Country')}: {station.get('country', 'Unknown')}   {_('Language')}: {station.get('language', 'Unknown')}",
            f"{_('Tags')}: {station.get('tags', 'Unknown')}",
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Search by name (INFO key)
    # ------------------------------------------------------------------

    def searchByName(self) -> None:

        logger.verbose("[RadioBrowser] INFO pressed.")

        self.session.openWithCallback(
            self._searchNameEntered,
            VirtualKeyBoard,
            title=_("Search stations by name"),
            text=self._search_name,
        )

    # ------------------------------------------------------------------

    def infoPressed(self) -> None:
        """
        Round 139 -- renamed from helpPressed(); opens GuideScreen
        with RadioBrowserScreen's own context-sensitive information
        document.
        """

        logger.verbose("[RadioBrowser] INFO pressed.")

        title, content = guide_manager.getGuide("radiobrowserscreen")

        self.session.open(GuideScreen, title, content)

    # ------------------------------------------------------------------

    def greenPressed(self) -> None:
        """
        Round 146, per direct request (colour-button audit): direct
        shortcut to the station menu's own existing "Add to Favorites"
        choice -- adds the currently selected station without needing
        to open the full menu first. A no-op outside the Stations
        column, and when nothing is actually selected there.
        """

        if self._focus != "stations":

            return

        index = self["stations"].getSelectedIndex()

        if not (0 <= index < len(self._stations)):

            return

        self._chooseFavoriteList(self._stations[index])

    # ------------------------------------------------------------------

    def _searchNameEntered(self, text) -> None:

        if text is None:
            return

        self._search_name = text

        global _last_search_name

        _last_search_name = text

        self._runSearchWithStatus()

# End of Part 2
    # ------------------------------------------------------------------
    # Station Context Menu (RADIOBROWSER_SCREEN_SPEC.md "Station
    # Context Menu")
    # ------------------------------------------------------------------

    def okPressed(self) -> None:

        logger.verbose("[RadioBrowser] OK pressed.")

        if self._focus in ("language", "region"):

            self._offerSetAsRadioDefault()

            return

        if self._focus != "stations":
            return

        index = self["stations"].getSelectedIndex()

        if not (0 <= index < len(self._stations)):
            return

        station = self._stations[index]

        choices = [
            (_("Play"), "play"),
            (_("Add to Favorites"), "add_favorite"),
            (_("Create Favorite List"), "create_list"),
            (_("Station Information"), "information"),
            (_("Update stations"), "update_database"),
            (_("Clear station list"), "clear_database"),
        ]

        # Round 201, per direct user request following a device log
        # showing "SQLite not available on this receiver": offered only
        # when this receiver's Python build actually lacks sqlite3 --
        # compatibility.hasSqlite3() is cached for the process lifetime
        # (see internetradio_manager.installSqliteSupport()'s own
        # comment), so a receiver that already has it never sees this
        # entry at all, and one that installs it here still sees it
        # until Enigma2 is restarted.
        if not compatibility.hasSqlite3():

            choices.append((_("Install SQLite support (faster search)"), "install_sqlite"))

        choices.append((_("Cancel"), "cancel"))

        self.session.openWithCallback(
            lambda choice: self._stationMenuChosen(choice, station),
            ChoiceBox,
            title=station.get("name", "?"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _offerSetAsRadioDefault(self) -> None:
        """
        Round 100, per direct request: OK on a Language/Region entry
        (previously did nothing outside the Stations column) offers
        setting the currently selected entry as Radio's own default
        language/country -- the exact same config_manager keys
        Settings' own "Radio default language"/"Radio default country"
        already expose (SETTINGSSCREEN_SPEC.md), just reachable
        directly from here too.

        Round 106, per direct request: "Any" (index 0) now offers
        CLEARING that default (setting it back to "") instead of being
        excluded entirely -- lets the user restrict a search by only
        one of language/region, leaving the other unset, without a
        detour through Settings to blank it out by hand.
        """

        widget_name = self._focus

        index = self[widget_name].getSelectedIndex()

        if index < 0:
            return

        if index == 0:

            label = _("Clear Radio default language") if widget_name == "language" else _("Clear Radio default country")

            self.session.openWithCallback(
                lambda confirmed: self._setAsRadioDefaultConfirmed(confirmed, widget_name, ""),
                MessageBox,
                _("{0}?").format(label),
                MessageBox.TYPE_YESNO,
            )

            return

        entries = self._languages if widget_name == "language" else self._countries

        entry_index = index - 1

        if not (0 <= entry_index < len(entries)):
            return

        entry_name = entries[entry_index].get("name", "")

        if not entry_name:
            return

        label = _("Set as Radio default language") if widget_name == "language" else _("Set as Radio default country")

        self.session.openWithCallback(
            lambda confirmed: self._setAsRadioDefaultConfirmed(confirmed, widget_name, entry_name),
            MessageBox,
            _("{0}: {1}?").format(label, entry_name),
            MessageBox.TYPE_YESNO,
        )

    # ------------------------------------------------------------------

    def _setAsRadioDefaultConfirmed(self, confirmed, widget_name, entry_name) -> None:

        if not confirmed:
            return

        if widget_name == "language":

            config_manager.set("radio.default_language", entry_name)

            self._default_language = entry_name

        else:

            config_manager.set("radio.default_country", entry_name)

            self._default_country = entry_name

        # Round 196, per direct report (radio default country/language
        # not surviving an Enigma2 restart): config_manager.set() above
        # only ever updates the in-memory value -- unlike
        # browserscreen.py's own _setConfigDirectory() (used for
        # startup_directory/scan_directory), nothing here previously
        # called config_manager.save() afterwards, so this value was
        # only ever actually written to disk if the user happened to
        # separately visit SettingsScreen and press MENU/EXIT there
        # (the only other place that calls it) before the next
        # restart. Saving immediately here, matching
        # _setConfigDirectory()'s own already-established pattern,
        # removes that dependency on an unrelated screen's own exit
        # path -- on top of, and independent from, the ConfigBrowsePath
        # setValue() fix in config.py that was needed regardless, since
        # a save() call was never enough by itself to persist a value
        # whose own default had already been silently moved to match it.
        config_manager.save()

        self._log(f"Radio default {widget_name} set to: {entry_name}")

        # Re-promotes the just-configured default to position 2 (right
        # after "Any") and re-selects it, the same as _promoteAppLanguage()
        # already does for the app's own UI language.
        self._reloadFilters()

    # ------------------------------------------------------------------

    def _stationMenuChosen(self, choice, station) -> None:

        if choice is None:
            return

        action = choice[1]

        if action == "play":

            self._playStation(station)

        elif action == "add_favorite":

            self._chooseFavoriteList(station)

        elif action == "create_list":

            self.session.openWithCallback(
                lambda name: self._createFavoriteList(name, station),
                VirtualKeyBoard,
                title=_("New favorite list name"),
                text="",
            )

        elif action == "information":

            lines = [
                station.get("name", "Unknown"),
                f"{_('Codec')}: {station.get('codec', 'Unknown')}",
                f"{_('Bitrate')}: {station.get('bitrate', 'Unknown')}",
                f"{_('Country')}: {station.get('country', 'Unknown')}",
                f"{_('Language')}: {station.get('language', 'Unknown')}",
                f"{_('Tags')}: {station.get('tags', 'Unknown')}",
                f"{_('Homepage')}: {station.get('homepage', 'Unknown')}",
            ]

            self.session.open(MessageBox, "\n".join(lines), MessageBox.TYPE_INFO)

        elif action == "update_database":

            self._updateStationDatabase()

        elif action == "clear_database":

            self.session.openWithCallback(
                self._clearStationDatabaseConfirmed,
                MessageBox,
                _("Clear the local station database?"),
                MessageBox.TYPE_YESNO,
            )

        elif action == "install_sqlite":

            self._offerInstallSqlite()

    # ------------------------------------------------------------------

    def _offerInstallSqlite(self) -> None:
        """
        Round 201. Companion to the ipk's own opkg dependency
        (mediaplayer3.bb/ipkbuild/control/control, both now declaring
        python3-sqlite3) for anyone already running a build from
        before that was added -- see internetradio_manager.
        installSqliteSupport()'s own comment for the full rationale.
        """

        self.session.openWithCallback(
            self._installSqliteChoiceMade,
            MessageBox,
            _("Install SQLite support now? This downloads a small package "
              "(python3-sqlite3) using opkg and requires an internet "
              "connection. A full receiver restart (not just closing this "
              "plugin) is needed afterwards for it to take effect."),
            MessageBox.TYPE_YESNO,
        )

    # ------------------------------------------------------------------

    def _installSqliteChoiceMade(self, confirmed) -> None:

        if not confirmed:
            return

        self["status"].setText(_("Installing SQLite support, please wait..."))

        self._sqlite_install_timer = eTimer()

        self._sqlite_install_timer.callback.append(self._performSqliteInstall)

        self._sqlite_install_timer.start(10, True)

    # ------------------------------------------------------------------

    def _performSqliteInstall(self) -> None:

        success, message = internetradio_manager.installSqliteSupport()

        if success:

            self.session.open(
                MessageBox,
                _("SQLite support installed. Restart your receiver (not just "
                  "this plugin) for faster station search to take effect."),
                MessageBox.TYPE_INFO,
            )

        else:

            self.session.open(
                MessageBox,
                _("Installing SQLite support failed:\n%s") % message,
                MessageBox.TYPE_WARNING,
            )

        self["status"].setText("")

        self._reloadFilters()

        self._runSearchWithStatus()

    # ------------------------------------------------------------------

    def _updateStationDatabase(self) -> None:
        """
        Build 0010, device test round 9 -- user request: moved here
        from SettingsScreen's RED action (device test round 8) to
        avoid a colour button, per RADIOBROWSER_SCREEN_SPEC.md's own
        "Color buttons shall not be required." Same deferred
        please-wait pattern as _runSearchWithStatus() -- a real,
        potentially slow network operation.
        """

        self["status"].setText(_("Updating station database, please wait..."))

        self._manual_db_update_timer = eTimer()

        self._manual_db_update_timer.callback.append(self._performManualDatabaseUpdate)

        self._manual_db_update_timer.start(10, True)

    # ------------------------------------------------------------------

    def _performManualDatabaseUpdate(self) -> None:

        ok = internetradio_manager.updateStationDatabase()

        info = internetradio_manager.getStationDatabaseInfo()

        if ok:

            self.session.open(
                MessageBox,
                _("Station database updated: %d station(s).") % info["count"],
                MessageBox.TYPE_INFO,
                timeout=3,
            )

        elif info["count"] > 0:

            self.session.open(
                MessageBox,
                _("Update failed -- keeping existing database (%d station(s)).") % info["count"],
                MessageBox.TYPE_WARNING,
                timeout=4,
            )

        else:

            self.session.open(MessageBox, _("Update failed. No station data available."), MessageBox.TYPE_WARNING, timeout=4)

        self._reloadFilters()

        self._runSearchWithStatus()

    # ------------------------------------------------------------------

    def _clearStationDatabaseConfirmed(self, confirmed) -> None:

        if not confirmed:
            return

        internetradio_manager.clearStationDatabase()

        self.session.open(MessageBox, _("Station list cleared."), MessageBox.TYPE_INFO, timeout=3)

        self._reloadFilters()

        self._runSearchWithStatus()

    # ------------------------------------------------------------------

    def _chooseFavoriteList(self, station) -> None:

        names = internetradio_manager.getFavoriteListNames()

        choices = [(name, name) for name in names]

        choices.append((_("Create New"), "__new__"))
        choices.append((_("Cancel"), "__cancel__"))

        self.session.openWithCallback(
            lambda choice: self._favoriteListChosen(choice, station),
            ChoiceBox,
            title=_("Select favorite list"),
            list=choices,
        )

    # ------------------------------------------------------------------

    def _favoriteListChosen(self, choice, station) -> None:

        if choice is None or choice[1] == "__cancel__":
            return

        if choice[1] == "__new__":

            self.session.openWithCallback(
                lambda name: self._createFavoriteList(name, station),
                VirtualKeyBoard,
                title=_("New favorite list name"),
                text="",
            )

            return

        internetradio_manager.addFavorite(station, list_name=choice[1])

    # ------------------------------------------------------------------

    def _createFavoriteList(self, name, station=None) -> None:

        if not name:
            return

        internetradio_manager.createFavoriteList(name)

        if station is not None:

            internetradio_manager.addFavorite(station, list_name=name)

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _playStation(self, station) -> None:

        if self._playback is None:
            return

        result = internetradio_manager.prepareStream(station)

        if result is None:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

            return

        self._log(f"Playback requested: {station.get('name', '?')}")

        if self._playback.playStream(result["url"], result["station"]):

            self.close("played")

        else:

            self.session.open(MessageBox, _("Playback failed"), MessageBox.TYPE_ERROR)

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def menuPressed(self) -> None:
        """
        Round 190, per direct request (Main Menu removed entirely --
        see mainscreen.py's own round 190 comment on menuPressed()):
        opens SettingsScreen directly instead of Main Menu, then
        simply returns here on close. Imported locally, not at module
        level, because settingsscreen.py itself already imports
        RadioBrowserScreen (for its own unrelated feature) -- a
        module-level import here would be a circular import.
        """

        logger.verbose("[RadioBrowser] MENU pressed.")

        from .settingsscreen import SettingsScreen

        self.session.open(SettingsScreen)

    # ------------------------------------------------------------------

    def exitPressed(self) -> None:

        logger.verbose("[RadioBrowser] EXIT pressed.")

        self._log("Closing")

        self._log("Closed")

        self.close(None)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"RadioBrowserScreen(initialized={self._initialized})"


# ==============================================================================
# End of file
# ==============================================================================

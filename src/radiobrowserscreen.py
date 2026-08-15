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

from enigma import eTimer

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
from .config import config_manager
from .internetradio_manager import internetradio_manager
from .skin import (
    PANEL_BACKGROUND_COLOR,
    PANEL_TEXT_COLOR,
    skin_manager,
    to_opaque_skin_color,
)
from .localization import _
from .logger import logger
from .mainmenu import MainMenu

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
PAGE_STEP = 10


class RadioBrowserScreen(Screen):
    """
    Internet Radio station browsing, search and favorites (Build 0007).
    """

    SPECIFICATION_VERSION = "0.1"

    DESIGN_WIDTH = 700
    DESIGN_HEIGHT = 540

    # ------------------------------------------------------------------

    def _buildSkin(self, width: int, height: int) -> str:
        """
        Build RadioBrowserScreen's skin for an exact `width` x
        `height` window, scaling from the 700x540 design resolution
        above (Build 0007, device test round 8).
        """

        sx = width / RadioBrowserScreen.DESIGN_WIDTH
        sy = height / RadioBrowserScreen.DESIGN_HEIGHT

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
        # Refinement", same fix and reasoning as MusicLibraryScreen's
        # own _buildSkin() comment.
        panel_rects = {
            "stations": (20, 45, 300, 25),
            "language": (330, 45, 170, 25),
            "region": (510, 45, 170, 25),
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
        <screen name="MediaPlayer3RadioBrowserScreen"
                position="0,0"
                size="{width},{height}"
                backgroundColor="{background_color}"
                title="MediaPlayer3 - Internet Radio">

            <widget name="status"
                    {rect(20, 10, 660, 25)}
                    {font(16)}
                    halign="center"
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"/>

            {highlight_xml}

            <widget name="stations_title"
                    {rect(20, 45, 300, 25)}
                    {font(18)}
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="language_title"
                    {rect(330, 45, 170, 25)}
                    {font(18)}
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="region_title"
                    {rect(510, 45, 170, 25)}
                    {font(18)}
                    foregroundColor="{panel_text_color}"
                    transparent="1"/>

            <widget name="stations"
                    {rect(20, 75, 300, 280)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="language"
                    {rect(330, 75, 170, 280)}
                    backgroundColor="{panel_background_color}"
                    foregroundColor="{panel_text_color}"
                    scrollbarMode="showOnDemand"/>

            <widget name="region"
                    {rect(510, 75, 170, 280)}
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

        self._focus = "stations"

        self._search_name = ""
        self._stations = []

        self._countries = []
        self._languages = []

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[RadioBrowser] %s", message)

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

        self["stations_title"] = Label(_("Stations"))
        self["region_title"] = Label(_("Region"))
        self["language_title"] = Label(_("Language"))
        self["stations"] = MenuList([])
        self["region"] = MenuList([])
        self["language"] = MenuList([])
        self["info"] = Label("")
        self["hint"] = Label(
            _("LEFT/RIGHT: Panel   UP/DOWN: Move   CH+/CH-: Page   OK: Options   INFO: Search   MENU: Menu   EXIT: Back")
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

        self["region"].setList([_("Any")] + [entry.get("name", "?") for entry in self._countries])

        self["language"].setList([_("Any")] + [entry.get("name", "?") for entry in self._languages])

        if self._default_country:

            self._selectListEntry("region", self._default_country)

        if self._default_language:

            self._selectListEntry("language", self._default_language)

    # ------------------------------------------------------------------

    # RadioBrowser identifies languages by full English name ("finnish",
    # "english", ...), not by MediaPlayer3's own "fi"/"en" language
    # codes -- this maps the ones LocalizationManager currently ships.
    # Add an entry here whenever a new UI language is added.
    _APP_LANGUAGE_TO_RADIOBROWSER_NAME = {
        "fi": "finnish",
        "en": "english",
    }

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

        app_language_name = self._APP_LANGUAGE_TO_RADIOBROWSER_NAME.get(
            config_manager.get("general.language", "fi")
        )

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

        self._stations = internetradio_manager.search(
            name=self._search_name or None,
            country=self._selectedRegion(),
            language=self._selectedLanguage(),
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

        self["status"].setText(_("Found {0} stations").format(len(self._stations)))

        self._result_message_timer = eTimer()

        self._result_message_timer.callback.append(self._updateFocusIndicator)

        self._result_message_timer.start(1500, True)

# End of Part 1
    # ------------------------------------------------------------------
    # Panel navigation (RADIOBROWSER_SCREEN_SPEC.md "Navigation")
    # ------------------------------------------------------------------

    def focusPrevious(self) -> None:

        logger.verbose("[RadioBrowser] LEFT pressed.")

        self._focus = PANELS[(PANELS.index(self._focus) - 1) % len(PANELS)]

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def focusNext(self) -> None:

        logger.verbose("[RadioBrowser] RIGHT pressed.")

        self._focus = PANELS[(PANELS.index(self._focus) + 1) % len(PANELS)]

        self._updateFocusIndicator()

    # ------------------------------------------------------------------

    def moveUp(self) -> None:

        logger.verbose("[RadioBrowser] UP pressed.")

        self[self._focus].up()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def moveDown(self) -> None:

        logger.verbose("[RadioBrowser] DOWN pressed.")

        self[self._focus].down()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageUp(self) -> None:
        """
        CH+ -- jump PAGE_STEP entries up in the focused panel
        (requested after real device testing).
        """

        logger.verbose("[RadioBrowser] CH+ pressed.")

        for _step in range(PAGE_STEP):

            self[self._focus].up()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def pageDown(self) -> None:

        logger.verbose("[RadioBrowser] CH- pressed.")

        for _step in range(PAGE_STEP):

            self[self._focus].down()

        self._onSelectionChanged()

    # ------------------------------------------------------------------

    def _onSelectionChanged(self) -> None:

        if self._focus == "stations":

            self._updateInfoPanel()

        else:

            # Region/Language selection changes trigger an automatic
            # re-search (RADIOBROWSER_SCREEN_SPEC.md "Search results
            # update automatically whenever a filter changes.").
            self._runSearchWithStatus()

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
        Build 0010, device test round 6 -- see this file's own
        _buildSkin() comment / MusicLibraryScreen's identical fix.
        """

        for panel_name in PANELS:

            is_active = panel_name == self._focus

            try:
                self[f"{panel_name}_title_bg_normal"].hide() if is_active else self[f"{panel_name}_title_bg_normal"].show()

                self[f"{panel_name}_title_bg_active"].show() if is_active else self[f"{panel_name}_title_bg_active"].hide()

            except Exception as error:

                logger.verbose(f"[RadioBrowser] Unable to set column highlight visibility: {error}")

    # ------------------------------------------------------------------

    def _updateInfoPanel(self) -> None:

        index = self["stations"].getSelectedIndex()

        if not self._stations or not (0 <= index < len(self._stations)):

            self["info"].setText(_("No media selected"))

            return

        station = self._stations[index]

        lines = [
            station.get("name", "Unknown"),
            f"{_('Codec')}: {station.get('codec', 'Unknown')}   {_('Bitrate')}: {station.get('bitrate', 'Unknown')}",
            f"{_('Country')}: {station.get('country', 'Unknown')}   {_('Language')}: {station.get('language', 'Unknown')}",
            f"{_('Tags')}: {station.get('tags', 'Unknown')}",
        ]

        self["info"].setText("\n".join(lines))

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

    def helpPressed(self) -> None:
        """
        Build 0008 -- opens HelpScreen with RadioBrowserScreen's own
        context-sensitive help document.
        """

        logger.verbose("[RadioBrowser] HELP pressed.")

        title, content = help_manager.getHelp("radiobrowserscreen")

        self.session.open(HelpScreen, title, content)

    # ------------------------------------------------------------------

    def _searchNameEntered(self, text) -> None:

        if text is None:
            return

        self._search_name = text

        self._runSearchWithStatus()

# End of Part 2
    # ------------------------------------------------------------------
    # Station Context Menu (RADIOBROWSER_SCREEN_SPEC.md "Station
    # Context Menu")
    # ------------------------------------------------------------------

    def okPressed(self) -> None:

        logger.verbose("[RadioBrowser] OK pressed.")

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
            (_("Cancel"), "cancel"),
        ]

        self.session.openWithCallback(
            lambda choice: self._stationMenuChosen(choice, station),
            ChoiceBox,
            title=station.get("name", "?"),
            list=choices,
        )

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

        logger.verbose("[RadioBrowser] MENU pressed.")

        self.session.openWithCallback(self._mainMenuCallback, MainMenu)

    # ------------------------------------------------------------------

    def _mainMenuCallback(self, action_id=None) -> None:

        if action_id in (None, "exit", "radio"):
            return

        self.close(action_id)

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

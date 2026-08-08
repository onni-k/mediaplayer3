# RADIOBROWSER_SCREEN_SPEC.md

MediaPlayer3

Build 0007

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# Purpose

RadioBrowserScreen provides a dedicated user interface for Internet
Radio browsing.

RadioBrowserScreen allows users to search, filter, browse and organize
Internet Radio stations.

RadioBrowserScreen communicates exclusively with
InternetRadioManager.

RadioBrowserScreen never communicates directly with the RadioBrowser
API.

---

# Responsibilities

RadioBrowserScreen shall provide:

- Station browsing
- Station search
- Region filtering
- Language filtering
- Favorite list management
- Station playback
- Context menus
- Station information

Playback remains the responsibility of PlaybackController.

---

# Screen Layout

RadioBrowserScreen consists of three primary panels.

Left panel:

Stations

Center panel:

Region

Right panel:

Language

Example:

Stations

↓

Yle Radio Suomi

Yle Puhe

Radio Rock

Radio Nova

...

Region

↓

Finland

Sweden

Norway

...

Language

↓

Finnish

Swedish

English

...

An information panel displays detailed information for the currently
selected station.

---

# Navigation

RadioBrowserScreen follows the standard MediaPlayer3 navigation model.

LEFT

Move to previous panel.

RIGHT

Move to next panel.

UP

Move selection upward.

DOWN

Move selection downward.

CH+ / CH- (Build 0007, device test round 2)

Jump PAGE_STEP (10) entries up/down in the focused panel -- requested
after real device testing showed long lists (especially languages and
countries) slow to scroll one entry at a time. Candidate action names
(compatibility.getChannelUpKeyActionNames()/
getChannelDownKeyActionNames()) not yet confirmed against a real
device.

Device test round 3: a device log showed zero matching key events for
any of the round-2 candidates (while every other key's own log line
did appear), and the user reported CH+/CH- only affecting "channels" --
likely the keypress falling through to Enigma2's own native channel-
zap handling instead, since nothing in RadioBrowserScreen's ActionMap
claimed it. Added "nextBouquet"/"prevBouquet" as further candidates,
since those are the confirmed real action names for this device's
Next/Previous Track keys. Still not confirmed for CH+/CH- specifically --
would need a fuller log with raw eActionMap/InfoBarGenerics resolution
lines to be certain.

Device test round 4: that fuller log was provided, and CONFIRMS the
real action names are "BOUQUET+"/"BOUQUET-" (from
"KeyID='KEY_CHANNELUP' Binding='('BOUQUET+',)'." /
"KeyID='KEY_CHANNELDOWN' Binding='('BOUQUET-',)'.") -- none of the
round 2/3 guesses, including "nextBouquet"/"prevBouquet", were
correct. Confirmed names moved to the front of the candidate lists.
Added "InfobarBouquetActions" to this screen's ActionMap contexts
defensively, since the log didn't show which context group actually
resolves them to an action.

Device test round 5: the user reported CH+/CH- still only affecting
the stations panel regardless of focus, even with the confirmed
names in place. A device log settled this definitively: with
RadioBrowserScreen confirmed open and correctly handling every other
key ("[RadioBrowser] RIGHT/DOWN/UP/LEFT pressed." all appeared
exactly when pressed), CH+/CH- presses in between NEVER produced a
matching "[RadioBrowser] CH+/CH- pressed." log line -- only
InfoBarGenerics' own native binding line appeared, every single time,
with no exception. This is strong evidence that Enigma2 treats
CHANNELUP/CHANNELDOWN as privileged, InfoBarGenerics-level keys that
bypass an ordinary Screen's ActionMap entirely, regardless of action
name -- the same class of limitation as the global RADIO-key plugin
launch decision (see MAINSCREEN_SPEC.md / docs/Claude_notes_build0007.txt).
No further guessing at action/context names is expected to fix this;
UP/DOWN (confirmed working every round) remains the reliable way to
navigate a long panel. The CH+/CH- bindings are left in place as
harmless best-effort, in case some other image/skin combination does
route them through an ordinary ActionMap.

OK

Open context menu.

MENU

Open RadioBrowser options.

EXIT

Return to previous screen.

Color buttons shall not be required.

---

# Search

Search supports:

- Station name
- Region
- Language
- Tags

Search results update automatically whenever a filter changes.

Asynchronous search with status messages (Build 0007, device test
round 8)

"Nyt on joskus auennut ikkuna ennen kuin on kanavat saatu haettua" --
the initial search (and every subsequent one: a filter change or a
name search) makes a blocking network call. Calling it synchronously
meant the screen could finish opening, with an empty list, well
before Enigma2 actually painted anything -- the user saw a blank
screen with no indication anything was happening.

Every search now goes through _runSearchWithStatus(): the status
label immediately shows "Searching for stations, please wait...",
the actual (blocking) search is deferred to the next event-loop
iteration via a 10ms singleshot eTimer so that message is guaranteed
to render first, and once results arrive the status label shows
"Found N stations" for 1.5 seconds before reverting to the normal
panel-focus indicator.

Default language position (Build 0007, device test round 2)

The app's own configured UI language (Settings -> Language) is moved
to position 2 in the Language panel, right after "Any" -- with
potentially hundreds of languages in the full RadioBrowser list,
requiring the most likely one to be found by scrolling was reported
as impractical during real device testing. A no-op if the app's
language has no known RadioBrowser name mapping (currently "fi" ->
"finnish", "en" -> "english") or that name isn't in RadioBrowser's own
results.

Default Region and Language values should follow receiver settings
whenever possible.

---

# Station Selection

Selecting a station updates the information panel.

Playback is not started automatically.

The selected station becomes the active station.

---
# Station Context Menu

Available operations:

Play

Add to Favorites

Create Favorite List

Station Information

Cancel

All station operations are delegated to InternetRadioManager.

---

# Favorite Lists

RadioBrowserScreen supports multiple favorite lists.

Examples:

General

Finnish

Rock

Jazz

Classical

Christmas

Users may:

- Create favorite lists
- Rename favorite lists
- Delete favorite lists
- Select active favorite list

Favorite management is performed by InternetRadioManager.

---

# Information Panel

The information panel displays details for the selected station.

Typical information:

- Station name
- Country
- Language
- Tags
- Codec
- Bitrate
- Homepage
- Votes
- Last successful check

The information panel updates automatically whenever the selected
station changes.

---

# MainScreen Integration

After playback has started, RadioBrowserScreen is no longer required.

MainScreen provides radio navigation.

LEFT / RIGHT

Switch favorite list or history list.

UP / DOWN

Previous station

Next station

Playback continues while navigating between stations.

The navigation mode is configurable from Settings.

---

# Logging

RadioBrowserScreen shall provide user interface logging.

Typical events:

INFO

Station selected

Favorite list selected

Context menu opened

Search started

Search completed

WARNING

No stations found

ERROR

Search request failed

Verbose logging additionally records:

- Navigation events
- Active filters
- Panel changes
- Menu selections

Station management is logged by InternetRadioManager.

---

# Dependencies

RadioBrowserScreen depends on:

- InternetRadioManager
- PlaybackController
- Logger
- SkinManager
- LocalizationManager

RadioBrowserScreen shall never communicate directly with the
RadioBrowser API.

All Internet Radio operations are delegated to
InternetRadioManager.

---

# Future Extensions

The following features are outside the scope of Build 0007.

Possible future additions:

- Station logo display
- Station logo cache
- Advanced search filters
- Recently added stations
- Popular stations
- User defined stations
- Podcast browser
- Sleep timer integration

The current screen layout shall allow future expansion without major
navigation changes.

---

# Summary

RadioBrowserScreen provides a dedicated Internet Radio browsing
interface.

Responsibilities include:

- Station browsing
- Search and filtering
- Favorite list management
- Station playback
- Station information

All Internet Radio management is delegated to
InternetRadioManager.

Playback remains the responsibility of PlaybackController.

RadioBrowserScreen follows the common MediaPlayer3 navigation model
used by BrowserScreen, PlaylistScreen and MainScreen.

---

End of RADIOBROWSER_SCREEN_SPEC.md

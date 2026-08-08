# MediaPlayer3

# Changelog

All notable changes to this project will be documented in this file.

The format is based on the principles of "Keep a Changelog",
adapted for the MediaPlayer3 project.

---

# Version Format

Version

Major.Minor.Patch

Example

0.4.0-dev

Each development version is associated with an internal Build number.

Example

Version

0.4.0-dev

Build

0004

---

# Change Categories

Added

New functionality.

Changed

Changes to existing behaviour.

Fixed

Bug fixes.

Removed

Removed functionality.

Deprecated

Features scheduled for removal.

Known Issues

Known limitations.

---

# Build 0004

Version

0.4.0-dev

Status

Implemented (pending device testing on OpenViX 6.8 / OpenATV)

## Added

- MainScreen architecture
- BrowserScreen architecture
- SettingsScreen architecture
- PlaybackInfoScreen architecture
- DeveloperScreen architecture
- Shared Main Menu architecture
- ConfigurationManager architecture
- Screen navigation architecture
- Improved module separation
- Platform abstraction layer

## Changed

- Browser is no longer the application's primary screen.
- MainScreen becomes the application's primary interface.
- Configuration module renamed to config.py.
- Improved Controller responsibilities.
- Standardized module lifecycle logging across every Screen, Controller
  and Core module to the five-stage Created / Initializing / Ready /
  Closing / Closed sequence defined in LOGGER_SPEC.md section 5.
- PVR key now also opens BrowserScreen from MainScreen (in addition to
  OK), and also returns from BrowserScreen to MainScreen.
- BrowserScreen now logs "Enter directory" / "Found" / "Selected" /
  "Starting playback" blocks, matching docs/log_example1.txt. These
  are written only when Developer Mode is VERBOSE.
- Centralized every environment-variable Enigma2 API decision into
  compatibility.py: Components.FileList.FileList construction now
  goes through compatibility.createFileList(), which tries a richer
  parameter set and falls back progressively on TypeError, instead of
  BrowserScreen hardcoding one fixed parameter set. The PVR remote
  key's candidate ActionMap action names are now defined once, in
  compatibility.PVR_KEY_ACTIONS / getPvrKeyActionNames(), instead of
  being duplicated in mainscreen.py and browserscreen.py.

## Fixed

- Improved playback architecture.
- Improved screen separation.
- Improved controller abstraction.
- Reduced platform-specific dependencies.
- BrowserScreen no longer passes unsupported keyword arguments
  (`showMountpoints`, `hideExtensionsInFilelist`) to FileList(),
  which crashed BrowserScreen on startup on device.
- Fixed a real device bug where a subdirectory (e.g. "flac") reached
  via the configured startup directory was misclassified as a file
  and playback was attempted on it instead of opening it. Caused by
  FileList's directory argument lacking a trailing "/"; see
  paths.ensure_trailing_slash().

## Removed

None.

## Deprecated

None.

## Known Issues

- OpenATV compatibility testing pending.
- Additional playback formats planned for future builds.
- Album artwork not yet implemented.
- Lyrics support planned for a future version.

---

# Build 0005

Version

0.5.0-dev

Status

Tested on a real OpenViX 6.8 device across multiple rounds; all
reported issues fixed and re-verified. OpenATV testing pending.

## Added

- Playback Queue: BrowserScreen builds an ordered queue of supported
  media files from the current directory and hands it to
  PlaybackController.playQueue(); PlaybackController owns navigation
  within it from that point on and no longer depends on BrowserScreen
  (PLAYBACK_QUEUE_SPEC.md, new in this build).
- Previous / Next Track navigation, forwarded from MainScreen's remote
  control handling to PlaybackController.nextTrack()/previousTrack().
- Automatic Next Track: when "Automatically play next track" is
  enabled, PlaybackController advances to and plays the next queue
  item when the current track ends; otherwise playback stops normally.
- Graphical progress bar, elapsed time, remaining time and queue
  position display on MainScreen, refreshed once per second by an
  eTimer while playback is active.
- Real elapsed/duration values: compatibility.getPlaybackPosition()
  and ServiceController.getPlaybackPosition() (previously always
  returned None/"Unknown").
- Playback Statistics on DeveloperScreen's Runtime Status page: queue
  position/size, remaining time, codec, sample rate, bitrate, channels
  via the new compatibility.getStreamInfo().
- User Interface settings category: Show progress bar / elapsed time /
  remaining time / playback state -- MainScreen presentation toggles,
  applied immediately on return from SettingsScreen.
- "Automatically play next track" setting is now active (previously
  stored but unused).
- Seeking within the current track: FASTFORWARD/REWIND (30s step) and
  LEFT/RIGHT (10s step), via PlaybackController.seekForward()/
  seekBackward() -> ServiceController.seekRelative() ->
  compatibility.seekRelative(). Requested after a real device test
  showed these keys had no effect at all (device test round 2).
- Cover art: MainScreen now shows cover.jpg/cover.png/folder.jpg/
  folder.png from the current track's directory, when present, as a
  full-window background (behind all text), decoded and scaled to fit
  via ePicLoad. Plain Enigma2 graphics APIs, unrelated to the
  GStreamer playback backend or to ServiceApp (a playback backend,
  not a graphics component).
- Total track duration is now shown before the "Track N / M" text on
  MainScreen, per user feedback.

## Changed

- PlaybackController's public interface extended with setQueue(),
  playQueue(), nextTrack(), previousTrack(), hasNext(), hasPrevious(),
  getCurrentTrack(), getQueueSize(), getQueuePosition(),
  getStreamInfo() and tick(), per PLAYBACK_CONTROLLER_SPEC.md v0.5.
- PlaybackController still never talks to compatibility.py or Enigma2
  directly -- all new playback-position/stream-info queries go through
  ServiceController, which delegates to compatibility.py, preserving
  the Build 0004 layering.
- MainScreen's skin reorganised to fit the new progress bar,
  elapsed/remaining time and queue position widgets.

## Fixed

- _playIndex() (Previous/Next Track) no longer commits a new queue
  position before confirming the corresponding play() call actually
  succeeded, so getQueuePosition() can never point at a track that
  getCurrentTrack() disagrees with.
- Fixed a real device bug where elapsed/total time always showed
  "Unknown": this OpenViX device's iSeekableService.seek() returns a
  *list* `[error_code, pts]`, not a tuple -- compatibility.py's
  `_ptsToSeconds()` only recognised the tuple form. Now accepts both.
- Fixed a real device bug where Previous/Next Track keys had no
  effect at all: the physical track-skip buttons on this remote did
  not fire either "next" or "previous" in any included ActionMap
  context. Added "nextBouquet"/"prevBouquet" (Enigma2 core keymap.xml's
  actual action names for KEY_NEXT/KEY_PREVIOUS) as further
  candidates, via compatibility.getNextTrackKeyActionNames() /
  getPreviousTrackKeyActionNames() -- same pattern as the Build 0004
  PVR key fix.
- Fixed a real device bug where selecting any track in BrowserScreen
  always played the first track in the directory: the Playback Queue
  was matching the selected file by exact full-path string equality,
  which never matched FileList's reported path on this device. Queue
  matching now compares basenames instead.
- Fixed a real device bug where tracks ended audibly a couple of
  seconds early: tick()'s "track finished" check used
  `elapsed >= duration - 1`, but elapsed/duration are already
  floor-truncated to whole seconds, so the extra margin triggered
  Auto Next while real audio was still playing (confirmed on device:
  elapsed=199, duration=200 fired the check). Now `elapsed >= duration`.
- Fixed a real device bug where the cover art background was hidden
  behind each text row's own opaque Label background, and the box's
  native background showed through everywhere else: MainScreen's skin
  now sets transparent="1" on every text widget and an opaque
  backgroundColor="#000000" on the screen itself.
- Added compatibility.connectPictureDataSignal(): checked source code
  from github.com/oe-mirrors/yampmusicplayer and github.com/mx3L/
  mediaplayer2 (per user request) and found their own confirmed-working
  PictureData-connection logic; upgraded to the same 3-way check
  (.connect() / .get().append() / plain .append()).
- Fixed a real device issue where the box's own background was still
  visible around MainScreen's window: MainScreen is now a genuinely
  full-screen window (position 0,0, sized to getDesktop(0).size())
  instead of a small centered box, with its entire skin scaled
  proportionally to whatever resolution is detected at runtime.
- Cover art decoding now requests the real "cover" widget size and
  uses AVSwitch().getFramebufferScale() for setPara()'s aspect ratio,
  matching YampMusicPlayer's/OpenPli MediaPlayer's own confirmed-
  working cover art Pixmap implementations (checked per user request)
  instead of the previous guessed values.
- Fullscreen window confirmed fixed on device (default background no
  longer visible at all). Cover art layout redesigned to a modest
  corner square (down from a full-window background) with text moved
  into its own non-overlapping column, modelled directly on
  YampMusicPlayer's own FHD skin (checked per user request) --
  verified programmatically to have zero widget overlap at any
  resolution.

## Removed

None.

## Deprecated

None.

## Known Issues

- getStreamInfo() (compatibility.py -- codec/sample rate/bitrate/
  channels on DeveloperScreen's Runtime Status page) has not yet been
  exercised on a real device; getPlaybackPosition() (elapsed/duration/
  seeking), by contrast, has been confirmed working across multiple
  device test rounds. getStreamInfo() is defensive/best-effort and
  falls back to "Unknown" on any error, but its exact
  iServiceInformation behaviour still needs device confirmation.
- ID3/metadata extraction (Artist/Album) is still not implemented;
  MainScreen and PlaybackInfoScreen continue to show "Unknown Artist"
  / "Unknown Album" placeholders.
- OpenATV compatibility testing pending.

---

# Build 0006

Version

0.6.0-dev

Status

Confirmed working and tested on a real OpenViX 6.8 device across four
rounds; all reported issues fixed and verified. Build 0006 level
achieved per user confirmation. OpenATV testing still pending.

## Added

- LocalizationManager (localization.py): translation loading,
  language selection, fallback, translation diagnostics. Initial
  languages: English (source/fallback), Finnish. Wired through a
  representative subset of user-visible strings across MainScreen,
  BrowserScreen and Main Menu (not full application-wide coverage --
  see docs/Claude_notes_build0006.txt for exactly which strings).
- SkinManager (skin.py): skin metadata loading, compatibility
  validation with automatic fallback to the default skin, and theme
  (colour palette) loading. Three shipped themes: default, dark,
  high contrast.
- Rich tag metadata (metadata.py): pure-Python FLAC (Vorbis Comment +
  STREAMINFO), ID3v2.3/2.4 (MP3) and Ogg Vorbis Comment parsing --
  no external dependency (mutagen etc.) required. Verified against
  real ffmpeg-generated FLAC/MP3/Ogg test files, including embedded
  artwork extraction (exact byte-for-byte match against the source
  image).
- Album artwork priority chain on MainScreen: embedded artwork (FLAC
  PICTURE / MP3 APIC) -> cover.jpg/folder.jpg in the file's directory
  -> bundled default MediaPlayer3 artwork. Artwork is now always
  shown once media is playing.
- PlaybackInfoScreen expanded into General/Technical/File sections
  using real metadata and stream info, replacing the filename-only
  placeholder display.
- DeveloperScreen: new "Metadata & Artwork" and "Localization"
  diagnostic pages; "Compatibility" page extended with Skin/Theme
  information.
- SettingsScreen: Language, Skin and Theme entries, applied
  immediately to LocalizationManager/SkinManager rather than only on
  restart.
- MainScreen's theme colours (background/text/progress) now come from
  SkinManager instead of being hardcoded.

## Changed

- MainScreen's "meta" label shows real Artist/Album from tag metadata
  when available, falling back to the existing "Unknown Artist" /
  "Unknown Album" placeholders otherwise.
- PlaybackController now caches metadata for the current file
  (getMetadata()/getEmbeddedArtwork()), populated in play() and
  cleared on cleanup. PlaybackController still never talks to
  compatibility.py, LocalizationManager or SkinManager directly.

## Fixed

- Restored ARCHITECTURE.MD, which was accidentally dropped during the
  Build 0004 -> Build 0005 documentation copy (its uppercase .MD
  extension didn't match a lowercase glob pattern in the copy script)
  and had been missing from the docs set for two builds. Brought up
  to date for Build 0006 rather than just restored as-is.
- Fixed a real parsing bug found during Build 0006's own testing: MP3
  COMM (comment) frames were decoded with the 3-byte language code
  leaking into the output (e.g. "engMy comment" instead of "My
  comment") -- COMM's encoding+language+description+text structure
  needs different handling than plain text frames. Verified with a
  hand-built COMM frame after the initial ffmpeg-generated test file
  turned out to use a TXXX frame instead, which never exercised this
  code path.
- Fixed a real bug in LocalizationManager's own translation
  diagnostics: the English catalog intentionally ships identity
  translations (msgid == msgstr), which made every successful English
  lookup register as a "missing translation" under the initial
  `result == text` check. Fixed by checking catalog membership
  directly instead.
- Fixed a variable-shadowing bug (`_ = config_manager.get(...)` in
  browserscreen.py, left over from an earlier build) that broke every
  `_("...")` translation call in that method -- Python's function-
  level scoping makes any `_ = ...` assignment shadow an imported `_`
  for the whole function, not just after the assignment line.
- Fixed a real device bug where MainScreen's progress bar showed the
  fullscreen artwork bleeding through its unfilled (black) portion --
  the ProgressBar widget had no explicit backgroundColor, so it was
  effectively transparent. Now uses the theme's "accent" colour as an
  opaque track background.
- MainScreen's Title now shows the real tag Title (when present)
  instead of always showing the filename, per user feedback after a
  real device test -- matches PLAYBACKINFO_SPEC.md's existing
  Metadata Priority rules, which MainScreen wasn't actually following
  yet despite PlaybackInfoScreen using them correctly.

## Added (continued -- device test round 1)

- EXIT now stops playback first (if active) and only closes
  MediaPlayer3 on a second press with nothing playing, matching
  common media player convention -- requested after a real device
  test.
- Added a "custom" theme: Settings gains a "Custom background color"
  entry (hex text input, shown only when Theme is set to "custom")
  that overrides the theme's background colour immediately.
  SkinManager.setCustomColor() validates the value looks like a
  "#RRGGBB"/"#RRGGBBAA" hex colour before applying it, rejecting
  anything else rather than breaking the theme.

## Added (continued -- device test round 2)

- DeveloperScreen: UP/DOWN now scroll pages whose content is taller
  than the details area, with a "(first-last / total)" indicator in
  the page title when a page doesn't fully fit -- requested after a
  real device screenshot showed System Information cut off vertically
  with no way to see the rest.
- MainScreen's text fields (Title, Artist/Album, Playback status) are
  now tall enough for two lines each, not one -- a real device
  screenshot showed a long filename/status line clipped after the
  first line with no way to see the rest.

## Fixed (continued -- device test round 2)

- Fixed a real device bug where switching tracks briefly displayed
  the PREVIOUS track's elapsed/duration/progress (e.g. "01:35 / 02:49"
  moments after starting a fresh track that was actually 10 seconds
  in): play() never cleared the cached position/duration from the
  track that was playing before it, so the stale values remained
  until the next tick() call overwrote them a moment later. play()
  now clears them immediately.

## Added (continued -- device test round 3)

- MediaPlayer3 now stops whatever's playing (typically live TV)
  immediately on open, via the new
  ServiceController.stopPreviousServiceNow() / PlaybackController
  passthrough, instead of waiting until the first track is played --
  requested after a real device test. Distinct from the existing,
  safety-guarded _stopService() (which only ever stops a service
  MediaPlayer3 itself started); also sets the internal
  "_took_over_playback" flag so TV still restores correctly on close
  even if the user never ends up playing anything.
- SettingsScreen's "Startup directory" is now picked via a directory
  browser (Screens.LocationBox.LocationBox, a standard Enigma2 core
  screen), instead of typed as plain text -- requested after a real
  device test.
- Added a configurable "Seek step (seconds)" setting
  (playback.seek_step_seconds) for FASTFORWARD/REWIND; default
  changed from the previous hardcoded 30s to 60s per that request.
  LEFT/RIGHT's shorter 10s step is unchanged.

## Added (continued -- device test round 4)

- Added plugin.png: the `icon="plugin.png"` reference in plugin.py's
  PluginDescriptor previously had no matching file. Confirmed showing
  correctly in the plugin menu on a real device.
- Directory browser (Startup directory) now shows a clear on-screen
  instruction ("Browse to the desired directory, then press GREEN to
  set it as the startup directory") -- GREEN already worked to
  confirm a selection, but this wasn't documented on screen.

## Changed (device test round 4)

- Seek step default reconsidered back to 30 seconds (was briefly
  changed to 60 in round 3, per that round's request; reverted per
  this round's follow-up request).

## Removed

None.

## Deprecated

None.

## Known Issues

- Tested on a real OpenViX 6.8 device across four rounds: metadata
  extraction, embedded artwork, cover art display, Automatic Next
  Track, the plugin menu icon, live TV stopping at startup, the
  directory browser and the configurable seek step were all confirmed
  working, with no MediaPlayer3-related errors in device logs across
  any round. User confirmed "build_0006 tavoitteet on saavutettu"
  (Build 0006's goals have been achieved). OpenATV testing is still
  pending.
- Genuine alternate-layout skin support (third-party skins changing
  widget positions, not just colours) is not implemented -- SkinManager
  handles metadata/compatibility/fallback and theme colours only; see
  SKIN_MANAGER_SPEC.md section 3 for the scope reasoning.
- Theme changes apply immediately to newly-opened Screens, but
  MainScreen's own already-open skin only picks up a theme change on
  its next creation (Enigma2 fixes a Screen's skin once
  Screen.__init__() has run) -- see THEME_SPEC.md section 6.
- TXXX (user-defined text) ID3 frames are not mapped to any metadata
  field; some encoders use TXXX for "comment" instead of the COMM
  frame metadata.py does support.
- Ogg Vorbis embedded artwork is not extracted (FLAC and MP3 are).
- Full application-wide translation coverage is incremental future
  work -- Build 0006 covers a representative subset, not every string.
- DeveloperScreen's VISIBLE_LINES (page scroll size) is a conservative
  estimate, not dynamically measured against the actual widget/font
  size -- Enigma2 has no simple "how many lines fit" query.

---

# Build 0007

Version

0.7.0-dev

Status

CONFIRMED COMPLETE -- device test rounds 1-13, working across four
Enigma2 images: OpenViX, OpenATV, openPLI and OpenBH. Fixed
RadioBrowser connectivity, a real favicon-crash, and missing INFO
handling across every screen (VU+/OpenATV's EPG-substitutes-INFO key
took two rounds to fully resolve). Confirmed the real RADIO/CH+/CH-
action names via a full raw eActionMap log; RADIO now works, but
CH+/CH- appears architecturally unreachable from plugin code on this
Enigma2 setup (see Known Issues). Round 8: every screen is now
fullscreen with theme-aware backgrounds, added a new Gray theme as
the default, added a startup chooser (Internet Radio/Local Music/
Playlists) with a full radio auto-resume fallback chain, and fixed a
real race condition in RadioBrowserScreen's search UI. Rounds 9-13
were a sequence of attempts to fix the box's own video/background
bleeding through behind screen content -- each got closer but didn't
fully resolve it (round 9: widget transparency; round 10: near-black
instead of pure black, incomplete; round 11: 8-digit opaque-alpha
format per the device's own skin.xml, still incomplete) until round
12 found, empirically, that switching every text-bearing widget to a
fixed white background + near-black text reliably avoids the issue;
round 13 then fixed a real skin-registration defect in round 12's own
fix (a widget referenced in the skin XML but never created in
Python), confirmed by device logs across three images. See "BUILD
0007 -- CONFIRMED COMPLETE" below for the full closing summary.
Launching the whole plugin via a global hardware RADIO key from
outside the app remains explicitly out of scope (see Known Issues).

## Added

- StorageManager (storage.py): creates and validates the
  ".mediaplayer3" working directory and nine subdirectories
  (playlists/radio/artwork/cache/logs/imports/exports/backups/
  userdata), with automatic recovery of any directory that goes
  missing later and a safe fallback location if /media/hdd isn't
  available. Every other module gets its application paths from
  StorageManager rather than hardcoding them.
- PlaylistManager (playlist_manager.py): full Extended M3U playlist
  management -- create/delete/rename/load/save, add track/add folder
  (recursive, filters to supported audio extensions), move/remove
  tracks, import (both Standard and Extended M3U; the original file
  is never modified) and export, plus validation that silently skips
  missing files when generating a playback queue. Verified end to end
  including the exact M3U file format written.
- InternetRadioManager (internetradio_manager.py): RadioBrowser
  (https://api.radio-browser.info/) communication using Python's
  stdlib `urllib` (no third-party HTTP library assumed present on the
  receiver), modelled on the endpoint conventions of the pyradios
  reference project (checked per user request) -- including its
  json/url/<uuid> "click counter" convention for resolving the actual
  playable stream URL rather than using the raw "url" field directly.
  Station search (name/country/language/tag), country/language/tag
  lists, multiple named favorite lists, and listening history are all
  implemented; every RadioBrowser request is defensively wrapped so a
  network failure degrades to an empty result rather than raising.
- PlaybackController.playStream()/isPlayingStream(): plays an Internet
  Radio stream URL, reusing the same eServiceReference construction as
  local files -- Enigma2's GStreamer/MP3 service factory already
  resolves http(s):// URIs the same as local paths, so no separate
  playback path was needed. Builds synthetic metadata (station name as
  Title) instead of attempting local tag parsing on a URL.
- MainScreen Internet Radio navigation: while playing a stream,
  LEFT/RIGHT switch between the favorites list and the history list,
  UP/DOWN step to the previous/next station -- local file seeking
  (Build 0005/0006) is completely unaffected, since the two behaviours
  are gated on PlaybackController.isPlayingStream() and a playback
  session is always either a stream or a local file, never both.
- BrowserScreen context menu, bound to INFO rather than OK
  (deliberately -- OK's existing descend-into-folder/play-file
  behaviour is real-device verified across several Build 0005/0006
  test rounds and must not change; INFO was unbound before this and
  reads naturally as "more options"): folders get Play Folder/Add
  Folder to Playlist/Create Playlist, audio files get Play/Add to
  Playlist/Information, playlist files get Play Playlist/Import
  Playlist/Information. Uses standard Enigma2 ChoiceBox/VirtualKeyBoard
  screens.
- PlaylistScreen (playlistscreen.py): dual-panel playlist management
  (playlists / tracks), with Play/Rename/Delete/Export/Information
  context menu for playlists and Play/Remove/Move Up/Move Down/
  Information for tracks. No colour buttons required.
- RadioBrowserScreen (radiobrowserscreen.py): three-panel station
  browsing (stations / region / language) with an information panel,
  search-by-name (INFO key, opens a text entry), and a station context
  menu (Play/Add to Favorites/Create Favorite List/Information). No
  colour buttons required for navigation; INFO doubles as "search"
  here (RadioBrowserScreen has no separate context-menu-vs-search key
  conflict, unlike BrowserScreen, since OK already opens the station
  context menu here).
- Main Menu: added "Playlists" and "Internet Radio" entries.
- DeveloperScreen: added "Storage", "Playlists" and "Internet Radio"
  diagnostic pages.
- SettingsScreen: added Radio default country/language, navigation
  mode and history size entries, plus a YELLOW-key "Clear radio
  history" action -- a deliberate, limited use of a colour button for
  a genuinely occasional, optional action (per user guidance to use
  colour buttons only when necessary).
- ~35 new translation strings added to both language catalogs (menu
  entries, panel titles, dialog labels) for the new screens.

## Changed

None beyond what's listed under Added.

## Fixed

None -- no real-device testing has happened yet this build to surface
device-specific bugs (see Status above).

## Removed

None.

## Deprecated

None.

## Fixed (device test round 1)

- Fixed a real device bug: every RadioBrowser request returned HTTP
  404. The plain "https://api.radio-browser.info/" hostname does not
  serve API requests directly, contrary to this build's original
  assumption -- confirmed against the official API docs, the pyradios
  reference project, and a user-provided example script
  (serverlist_python3.py). RadioBrowser requires resolving
  "all.api.radio-browser.info" via DNS and reverse-resolving each IP
  to an actual mirror hostname, then calling one of those mirrors.
  InternetRadioManager now discovers mirrors once per process
  lifetime and retries each in turn on failure, caching whichever one
  last answered successfully.

## Added (device test round 2)

- Confirmed working on device: Internet Radio search now returns
  real results after the mirror discovery fix above.
- RadioBrowserScreen: CH+/CH- page-jump (10 entries at once) through
  the focused panel, requested after real device testing showed long
  lists (especially languages/countries) slow to scroll one entry at
  a time.
- RadioBrowserScreen: the app's own configured UI language is moved
  to position 2 in the Language panel (right after "Any"), so it
  doesn't require scrolling through potentially hundreds of entries
  to find.
- MainScreen: INFO now toggles between two views ("seek", the
  existing default, and a new "favorites" view showing the current
  folder/playlist/list name at the top and a "N/M" queue/list
  position instead of a duration) instead of opening
  PlaybackInfoScreen directly -- PlaybackInfoScreen remains reachable
  from Main Menu.
- MainScreen: added a RADIO key to toggle between the last-played
  local file and the last-played Internet Radio station.

## Fixed (device test round 3)

- Fixed CH+/CH- not affecting the Region/Language panels: a device
  log showed zero matching key events for any round-2 candidate
  action name (while every other key's own log line did appear), and
  the user reported CH+/CH- only affecting "channels" -- likely the
  keypress falling through to Enigma2's own native channel-zap
  handling since nothing in RadioBrowserScreen's ActionMap claimed it.
  Added "nextBouquet"/"prevBouquet" as further candidates (the
  confirmed real action names for this device's Next/Previous Track
  keys). Still not confirmed for CH+/CH- specifically.
- Fixed _refreshRadioList() always resolving to the "General"
  favorite list regardless of which list was actually selected (a
  pre-existing bug from Build 0007's original radio navigation,
  surfaced while generalizing list cycling below).

## Added (device test round 3)

- MainScreen displays the current radio station's favicon as cover
  art when available (InternetRadioManager.downloadFavicon(), cached
  by URL hash), before falling back to default artwork.
- Radio list cycling (MainScreen LEFT/RIGHT while streaming) now
  cycles through every favorite list the user has created, plus
  history -- previously a hard-coded favorites/history binary toggle
  that never reached any additional lists the user created.
- Local file playlist cycling: the same LEFT/RIGHT (cycle playlists)
  and UP/DOWN (step tracks) navigation radio already had now works
  for local files too, while MainScreen is in favorites view. Top
  label shows the active playlist name; falls back to folder name
  when playback started from BrowserScreen instead.
- PlaylistScreen now shows local playlists AND Internet Radio favorite
  lists together in its left panel (local first, then radio), with
  type-aware context menus, playback and information dialogs for
  both.
- MainScreen's RADIO key refined: pressing it while already playing a
  stream now opens BrowserScreen, instead of silently resuming the
  last local file as it did in round 2 -- clarified by the user as
  "Kun radiotilassa painaa radio-nappia, niin voisi aueta browser."
- Added an opt-in setting (radio.resume_on_start, off by default)
  that resumes the last-played Internet Radio station automatically
  whenever MediaPlayer3 is launched through its own normal
  Extensions/Plugin menu entry.

## Fixed (device test round 4)

- Fixed a real CRASH confirmed by a device log: the whole enigma2
  process exited after RadioBrowser returned the literal string
  "null" for a station's favicon field (not JSON null/empty). That
  string is truthy in Python, so it passed downloadFavicon()'s
  `if not favicon_url` check and reached urllib.request.Request(),
  which raised an uncaught ValueError ("unknown url type: 'null'").
  Added a shared _cleanUrlField() helper that rejects
  "null"/"none"/"n/a" sentinel strings, applied to downloadFavicon()
  and, as defense in depth, to prepareStream()'s url/url_resolved
  fields too, since they come from the same API. Also moved
  urllib.request.Request() construction inside the try/except as a
  second layer of defense.
- Fixed RADIO key showing Enigma2's native "unhandled key" indicator
  on every launch: a full raw eActionMap/InfoBarGenerics log CONFIRMED
  the real action name is "RADIO" (uppercase) -- none of round 2's
  lowercase-style guesses ("radio"/"keyRadio"/"toggleRadio") were
  correct.
- Fixed CH+/CH- still only affecting the stations panel: the same log
  CONFIRMED the real action names are "BOUQUET+"/"BOUQUET-" -- none of
  the round 2/3 guesses, including "nextBouquet"/"prevBouquet", were
  correct (explaining why the round-2/3 device tests showed zero
  matching key events). Also added "InfobarBouquetActions" to
  RadioBrowserScreen's ActionMap contexts defensively, since the log
  didn't show which context group resolves these actions.

## Fixed (device test round 5)

- Confirmed working on both OpenViX and OpenATV.
- Fixed INFO showing Enigma2's "unhandled key" indicator on OpenATV:
  an audit found PlaylistScreen, SettingsScreen and DeveloperScreen
  had no "InfoActions" context or "info"/"showEventInfo" binding at
  all (BrowserScreen/RadioBrowserScreen/MainScreen/PlaybackInfoScreen
  already had it). Added INFO handling to all three: PlaylistScreen
  shows Information for whichever panel/entry has focus, SettingsScreen
  shows the current entry's name and value, DeveloperScreen restates
  the current page.

## Fixed (device test round 6)

- Fixed INFO still not working in MainScreen on OpenATV, after round
  5's fix covered the other screens: the user correctly diagnosed the
  cause -- VU+ remotes have no physical INFO button at all, EPG
  substitutes for it, generating KEY_EPG rather than KEY_INFO. A
  device log's static context dump (captured in round 5's testing)
  showed KEY_EPG resolving to action "showEventInfoPlugin" via the
  "InfobarEPGActions" context, which no screen included. Added
  compatibility.getInfoKeyActionNames() (covering "showEventInfo"/
  "info" for the real INFO key and "showEventInfoPlugin"/
  "InfoPressed" for the EPG substitute) and updated every screen with
  INFO handling -- MainScreen, BrowserScreen, RadioBrowserScreen,
  PlaylistScreen, SettingsScreen, DeveloperScreen, PlaybackInfoScreen
  -- to use it and include "InfobarEPGActions".

## Fixed (device test round 7)

- Fixed INFO/EPG still not working in MainScreen on OpenATV, after
  round 6's fix. A fresh device log confirmed KEY_EPG events kept
  arriving but no "[MainScreen] INFO pressed." line ever followed,
  even with "showEventInfoPlugin" registered. The same context dump
  showed "InfobarEPGActions" actually defines TWO actions for
  KEY_EPG -- "EPGPressed" and "showEventInfoPlugin" -- added
  "EPGPressed" as a further candidate.
- Added 5 translation strings that a device-uploaded DeveloperScreen
  diagnostic dump showed as missing from the Finnish catalog
  ("Cancel", "Information", "Play", "Remove from Playlist", and
  PlaylistScreen's hint text).

## Added (device test round 8)

- Every screen is now fullscreen -- BrowserScreen, SettingsScreen,
  PlaybackInfoScreen, DeveloperScreen, PlaylistScreen,
  RadioBrowserScreen and MainMenu all now use a dynamic,
  desktop-scaled skin (position="0,0", scaled from their own design
  canvas) with the current theme's background colour filling the
  whole display, matching MainScreen's own approach since Build 0005.
  Added compatibility.getDesktopSize() to share the desktop-size
  lookup across every screen.
- Added a new "Gray" theme (background #A0A0A0, dark text for
  contrast) and made it the default theme (was "default").
- MainScreen's OK, when nothing is playing, now opens a chooser
  (Internet Radio / Local Music / Playlists / Cancel) instead of
  always going straight to BrowserScreen. Choosing Internet Radio
  switches to favorites view and resumes the most recent history
  station, falling back to the first station in the "General"
  favorite list, falling back to opening RadioBrowserScreen to search.
- RadioBrowserScreen's search (initial load, filter changes, and name
  search) now shows a "Searching for stations, please wait..." status
  message immediately, deferring the actual blocking network call to
  the next event-loop iteration so the message is guaranteed to
  render first, then briefly shows "Found N stations" before
  reverting to normal -- fixes a real race condition the user
  observed ("Nyt on joskus auennut ikkuna ennen kuin on kanavat saatu
  haettua").

## Fixed (device test round 9)

- Fixed a real bug confirmed by device screenshots: every text Label
  widget on the seven screens converted to fullscreen in round 8
  showed a solid black backdrop instead of the theme's background
  colour -- visible as black boxes around every piece of text against
  the new Gray theme, and per the user, would show the box's own live
  video/background bleeding through instead of solid colour if TV
  were playing underneath. Root cause: Enigma2 Label widgets paint an
  opaque backdrop by default -- the exact issue MainScreen itself hit
  and fixed back in Build 0005 (transparent="1" +
  foregroundColor on every widget), which round 8's conversion of the
  other seven screens never carried over. Added the same
  transparent="1" + foregroundColor to every Label-type widget on
  BrowserScreen, SettingsScreen, PlaybackInfoScreen, DeveloperScreen,
  PlaylistScreen, RadioBrowserScreen and MainMenu, matching
  MainScreen's own working pattern exactly.

## Fixed (device test round 10)

- Fixed the box's own live video/background still bleeding through
  during playback even after round 9's transparency fix. Per the
  user's own hypothesis: replaced every pure-black (#000000)
  background default with near-black (#0A0A0A) -- shipped themes
  (default/dark/highcontrast; Gray was never black), SkinManager's
  built-in fallback colour set and getColor()'s own default
  parameter, and appearance.custom_background_color's default. Pure
  black (RGB 0,0,0) is a known chroma-key value on many DVB/Enigma2
  receivers, where the OSD plane shows the video plane through an
  exact-black pixel instead of painting it; #0A0A0A is visually
  indistinguishable from black but numerically avoids the exact-match
  key.

## Fixed (device test round 11)

- Round 10's fix didn't actually solve the video-bleed-through issue:
  a device screenshot still showed the box's own live video/background
  behind Main Menu. The user identified the real cause and confirmed
  it directly against the device's own skin.xml: Enigma2 skin colours
  are 8-digit "#AARRGGBB", not 6-digit "#RRGGBB" -- this device's own
  skin.xml defines "black" as "#00000000", not "#000000". A bare
  6-digit backgroundColor value (what every screen was still using
  through round 10, regardless of which RGB value was chosen) leaves
  the alpha channel to be read unpredictably rather than reliably
  opaque. Added skin.to_opaque_skin_color(): prepends an explicit "00"
  (opaque, in Enigma2's inverted alpha convention) alpha byte to any
  6-digit colour, applied everywhere a colour becomes a backgroundColor
  attribute (never to foregroundColor/text, which doesn't have this
  failure mode) across all 8 screens. Theme JSON files stay plain
  "#RRGGBB" for portability; only the skin-XML-generation layer adds
  the alpha byte.

## Fixed (device test round 12)

- Round 11's fix still didn't stop the box's own video/background
  bleeding through, confirmed by a further device screenshot. The
  user found, empirically, that a WHITE background reliably avoids
  the issue where gray/near-black backgrounds don't -- visible
  directly in the screenshot: Main Menu's first rows rendered on a
  solid opaque white bar while the rest of the list showed the
  background through. Added skin.PANEL_BACKGROUND_COLOR ("#FFFFFF")
  and PANEL_TEXT_COLOR ("#1A1A1A"): every text-bearing widget (Label
  AND List types) across every screen now uses this fixed pairing
  instead of the active theme's own background/text colours -- the
  theme's colours are now reserved for the outer screen edges only.
  MainScreen additionally gained a dedicated "header_background"
  widget spanning its whole top text area (version/cover/media/meta/
  status), since that area previously had no widget-level background
  at all.

## Fixed (device test round 13)

- Fixed a real skin error confirmed by device logs across OpenATV,
  OpenViX and OpenBH: round 12's new "header_background" widget was
  added to the generated skin XML but never registered as a Python-
  side component -- Enigma2 requires both; the skin XML only styles/
  positions an already-registered widget, it doesn't create one.
  Every device log showed "Component with name 'header_background'
  was not found in skin of screen" for this exact reason. Didn't
  visibly break the screen (Enigma2 skips the one widget it can't
  construct and continues), but was a real defect. Added the missing
  self["header_background"] = Label("") registration.

---

# BUILD 0007 -- CONFIRMED COMPLETE

Confirmed working across four Enigma2 images/distributions: OpenViX,
OpenATV, openPLI and OpenBH (device test rounds 1-13). Every feature
in this build -- playlists, Internet Radio via RadioBrowser, storage
management, the combined local/radio playlist view, fullscreen
screens with a consistent white-panel text rendering that survived
several rounds of investigation into the box's own video/background
bleed-through, the startup chooser and full radio auto-resume
fallback chain, and INFO/EPG key handling across both physical INFO
buttons and EPG-substitute remotes -- has been exercised on real
hardware and confirmed working by the user.

The two remaining Known Issues below (CH+/CH- in RadioBrowserScreen,
and launching the whole plugin via a global hardware RADIO key) are
both deliberate, documented scope decisions rather than open bugs --
see their entries below and docs/Claude_notes_build0007.txt for the
full reasoning behind each.

One purely cosmetic, non-functional quirk remains: OpenATV's own
ChoiceBox skin shows a generic gear/settings icon next to the startup
chooser (no per-choice icon is supplied by MediaPlayer3) -- confirmed
by the user not to affect usability, and not a MediaPlayer3 rendering
issue to fix.

---

## Known Issues

- CH+/CH- in RadioBrowserScreen still doesn't reach the plugin at all,
  despite the confirmed action names from round 4. A device log
  settled this definitively: with RadioBrowserScreen confirmed open
  and correctly handling every other key, CH+/CH- presses in between
  never produced a matching log line from this plugin -- only
  Enigma2's own native InfoBarGenerics binding line appeared, every
  time. This is strong evidence Enigma2 treats CHANNELUP/CHANNELDOWN
  as privileged, InfoBarGenerics-level keys that bypass an ordinary
  Screen's ActionMap entirely -- the same class of limitation as the
  global RADIO-key launch decision below. No further guessing at
  action/context names is expected to fix this; UP/DOWN (confirmed
  working every round) remains the reliable way to navigate. The
  CH+/CH- bindings are left in place as harmless best-effort for other
  images/skins that might route them differently.
- Since round 12, a theme's own background/text colours only affect
  the outer edges of each screen -- all text areas are now a fixed
  white/near-black regardless of the active theme (default/dark/
  highcontrast/gray/custom). This is a deliberate trade-off to
  guarantee readability and opacity over full theme customisation of
  text areas, after three earlier attempts (rounds 9-11) to fix video/
  background bleed-through while keeping theme-driven text colours
  didn't fully work.
- Launching MediaPlayer3 itself via a GLOBAL hardware RADIO key press
  (i.e. from outside the plugin, e.g. from live TV -- "koko pluginin
  käynnistää radio-napilla") is explicitly NOT implemented. This would
  require intercepting/monkey-patching Enigma2's system-level key
  handling (e.g. InfoBar's own ActionMap), which cannot be verified
  without real hardware and risks breaking the receiver's normal
  TV/radio-bouquet behaviour if done wrong across different Enigma2
  images. What IS implemented instead: MediaPlayer3 auto-resumes the
  last-played station when launched normally (radio.resume_on_start,
  opt-in) -- see docs/Claude_notes_build0007.txt for the full
  reasoning behind this scope decision.
- RadioBrowser mirror discovery and the retry logic are confirmed
  working structurally (tested with mocked mirrors: retry-on-failure,
  last-good-server caching), and search now returns real results on a
  real device (round 2).
- Favicon downloading confirmed working on a real device (round 4),
  after fixing the "null"-string crash above; general reachability
  across arbitrary station-hosted favicon URLs (as opposed to
  RadioBrowser's own API, confirmed working since round 1) is still
  less exercised than the rest of the API surface.
- Playlist folder-add ("Add Folder to Playlist") confirmed working on
  a real device.
- Genuine alternate-layout skin support remains out of scope (Build
  0006 decision, unchanged).
- Full application-wide translation coverage remains incremental
  future work; the new screens' dialog/menu strings are covered, but
  not exhaustively.
- "Information" dialogs (BrowserScreen/PlaylistScreen/
  RadioBrowserScreen) are simple MessageBox popups rather than
  dedicated information screens -- a deliberate scope simplification
  given the size of this build.
- DeveloperScreen's Storage/Playlists/Internet Radio pages have not
  been cross-checked against a real device's actual filesystem
  layout (e.g. whether /media/hdd is genuinely the right default
  parent on every supported receiver).

---

# Build 0008

Version

0.8.0-dev

Status

CONFIRMED COMPLETE -- 9 rounds of real device testing (OpenViX,
OpenATV, two receivers including a VU+ Duo2), confirmed by the user.

## Added

Help system:

- HelpManager: loads resources/help/<screen_id>.md and renders a
  lightweight Markdown subset (headings, lists, code fences) into
  plain text -- Enigma2's Label widgets have no rich Markdown
  rendering, so this is a deliberate, readable plain-text conversion
  rather than raw Markdown passthrough.
- HelpScreen: generic scrollable document viewer, built directly on
  DeveloperScreen's already-proven scroll pattern (UP/DOWN line,
  LEFT/RIGHT page, "(first-last / total)" indicator for long
  documents).
- HELP key wired into every screen -- MainScreen, BrowserScreen,
  PlaylistScreen, RadioBrowserScreen, SettingsScreen, DeveloperScreen,
  MainMenu, MusicLibraryScreen -- each opening HelpScreen with its own
  context-sensitive help document.
- HELP key action names (compatibility.HELP_KEY_ACTIONS) are
  PROVISIONAL and unverified on real hardware -- Build 0008 has had
  no device testing at all yet, unlike RADIO/CH+/CH-/INFO in Build
  0007, which all needed real eActionMap log evidence before guessing
  actually worked.

Lyrics:

- metadata.py extended to read embedded lyrics: ID3v2 USLT frames
  (MP3) and FLAC/Ogg Vorbis "LYRICS"/"UNSYNCEDLYRICS" comment fields,
  both feeding a new metadata["lyrics"] field (not added to FIELDS --
  not surfaced in the generic metadata display, only read directly by
  LyricsManager).
- LyricsManager: getLyrics(filepath) tries embedded lyrics, then an
  external .lrc file (parsed with real timestamp support, sorted, and
  correctly skipping non-timestamp metadata tags like [ar:...]),
  then an external .txt file, in that fixed priority order, falling
  back to "Lyrics not available." getCurrentLine() finds the
  currently active synchronized line for a given playback position.

MainScreen information views:

- New lower-right information panel: TEXT cycles Lyrics -> Metadata
  -> Codec Information -> Lyrics... Lyrics show the synchronized
  current line when a .lrc file is available, otherwise the full
  text. TEXT key action names (compatibility.TEXT_KEY_ACTIONS) are
  also PROVISIONAL/unverified.
- New lower-left Previous/Next queue preview: shows the adjacent
  PlaybackQueue item (local files, via a new
  PlaybackController.getAdjacentFiles()) or the adjacent station in
  the current radio list (Internet Radio).

Music Library:

- LibraryManager: scans library.scan_directory (a new config setting,
  independent of Browser's own general.startup_directory), reads
  every supported audio file's metadata via the existing metadata.py
  reader (no third-party dependency), and builds an in-memory index
  browsable by artist/album/track/genre/year and searchable by
  substring match across all of those fields. Never performs
  playback -- always returns a plain list of file paths (a
  PlaybackQueue) for PlaybackController.playQueue(), the same
  convention BrowserScreen/PlaylistScreen/RadioBrowserScreen already
  follow.
- Fixed an inconsistency caught during testing: untagged files
  initially showed generic "Unknown" (metadata.py's own placeholder,
  which is non-empty and so never triggered LibraryManager's `or`
  fallback) instead of "Unknown Artist"/"Unknown Album"/etc. Added an
  explicit check for both.
- MusicLibraryScreen: three-panel browsing (Artists/Albums/Tracks),
  navigation modeled directly on RadioBrowserScreen -- LEFT/RIGHT
  switches panels, UP/DOWN moves within one, CH+/CH- pages 10 at a
  time (same unverified-on-hardware caveat RadioBrowserScreen's own
  CH+/CH- has carried since Build 0007), OK plays at the selection's
  scope (artist/album/track), INFO searches by name, MENU offers
  "Update Library"/"Main Menu". The initial library load (and every
  rescan) uses the same deferred "please wait" timer pattern that
  fixed RadioBrowserScreen's real race condition in Build 0007 --
  applied proactively here since scanning a whole music collection is
  an even slower, more clearly blocking operation than a network
  search.
- Added "Music Library" to the Main Menu (between Playlists and
  Internet Radio) and to MainScreen's startup chooser (OK with
  nothing playing).

## Changed

- MainScreen's skin gained two new widgets (queue_preview, info_panel)
  in the previously-empty area between the progress bar row and the
  hint bar.

## Known Issues

- Unsynchronized (embedded/.txt) lyrics scroll a fixed 5-line window,
  same as synchronized .lrc lyrics -- confirmed readable and working
  correctly, but the user noted more lines could reasonably fit for
  the unsynchronized case specifically. Deferred to a future build.
- TEXT (like INFO before it, fixed in device test round 8) fires on
  both the Make and Break hardware events on at least one remote --
  since it cycles through three states rather than toggling between
  two, this is far less disruptive (each physical press still moves
  forward, just occasionally two steps instead of one) and the user
  confirmed it works correctly in practice. Left as-is; the same
  _isDebounced() guard already added for INFO could be applied here
  too if it ever becomes a real problem.
- LibraryManager's scan is a simple recursive walk with no caching,
  incremental update, or background scheduling -- a large collection
  will take a correspondingly long time to (re)scan. Explicitly
  deferred to a future build per LIBRARY_MANAGER_SPEC.md's "Library
  Updates" section.

## BUILD 0008 -- CONFIRMED COMPLETE

Closing note (device test round 9): Build 0008 went through 9 rounds
of real device testing across two Enigma2 receivers (including a
VU+ Duo2, whose different remote surfaced the INFO/EPG double-fire
issue above), confirmed complete by the user. The build's three major
features -- context-sensitive Help, Lyrics (embedded/.lrc/.txt, with
scrolling display), and Music Library -- are all confirmed working,
alongside two substantial playback-position correctness fixes that
emerged directly from device testing: a GStreamer race condition that
could report a stale position from whatever played previously
(rounds 1-7, fixed with a wall-clock-anchored sanity check and
absolute-target seeking), and a seek-chain corruption bug from
re-querying GStreamer mid-flush (round 9). See
Claude_notes_build0008.txt for the full, round-by-round record,
including the reasoning behind each fix and what device-log evidence
drove it.

---

# Build 0009

## Added

MainScreen 2.0 (three navigable panels):

- New Core module `information_panel.py` (InformationPanel): builds
  each panel's page list dynamically from whatever the current track
  or station actually has, instead of Build 0008's fixed TEXT-cycled
  Lyrics/Metadata/Codec order. Local files: Lyrics (LRC/embedded/TXT,
  each labelled by source), Metadata, Codec. Internet Radio: Radio
  EPG (current programme plus the next three upcoming, when a
  station has schedule data), Now Playing, Station, Codec. A page is
  only ever shown when it has real content.
- MainScreen's skin rebuilt around three panels -- Player (default),
  Playlist, Information -- cycled via EPG/INFO. Each panel's title
  gets a background-colour highlight when active (two overlapping
  rectangles per title, swapped with hide()/show(); a runtime
  foreground/background colour change was deliberately avoided, see
  Fixed below). Directional keys are dispatched by whichever panel is
  active: Player = seek (local)/switch favourite list (radio) on
  LEFT/RIGHT, previous/next track on UP/DOWN; Playlist = move
  selection on UP/DOWN, switch playlist on LEFT/RIGHT, OK jumps
  playback to the selection; Information = switch page on LEFT/RIGHT,
  scroll (or adjust synchronized-lyrics timing, see below) on
  UP/DOWN. The Playlist panel is skipped entirely in the EPG/INFO
  cycle while streaming radio (Player <-> Information only) since
  seeking/playlist-switching moved to the Player panel's own
  LEFT/RIGHT for radio -- the Playlist widget itself keeps updating
  in the background regardless.
- Synchronized-lyrics timing offset: UP/DOWN on a synchronized lyrics
  page nudges a per-track offset instead of scrolling (which would
  conflict with the view's own auto-following of playback position),
  configurable step size (`playback.lyrics_offset_step_seconds`,
  default 5s), shown in the page title when non-zero (e.g. "(+5s)").
- Three new panel-specific help documents (player.md/playlist.md/
  information.md) replace Build 0008's single mainscreen.md; HELP now
  opens whichever matches the active panel.

Finland Radio EPG:

- `epg_providers/Finland_radio_epg/yle_teletext_provider.py`
  (EPGScheduleProvider): Yle's Teksti-TV API -- the only Yle API still
  open to the public (their purpose-built programme/schedule API was
  deprecated in 2021, confirmed from Yle's own developer
  documentation). Covers Radio 1, YleX, Radio Suomi, Vega, X3M.
  Requires the user's own app_id/app_key (Settings -> Yle EPG
  app_id/app_key; tunnus.yle.fi/api-avaimet), never bundled.
- `epg_providers/Finland_radio_epg/bauer_nowplaying_provider.py`
  (NowPlayingProvider): Bauer Media/Rayo Finland -- no official API
  exists, so this reads a station's rayo.fi page's own embedded
  Next.js state directly. Covers all 18 of Bauer's published Finnish
  stations (Radio Nova, Iskelmä, Radio City, Basso, Ysäri, Kasari,
  SuomiRäp, Radio Classic, NRJ, Radio Nostalgia, Radio Pooki, KISS,
  Radio 957, Auran Aallot, Radio Pori, Fresh, Rodeo, SuomiRock).
  Now-playing only (no schedule data was found embedded).
- `epg_manager.py` gained a second provider interface,
  `NowPlayingProvider`, alongside the existing
  `EPGScheduleProvider` -- `getNowPlaying(station=None)` checks for a
  registered provider first, falling back to ICY stream tags exactly
  as before when none is registered or the station isn't streaming.
- New `finland_radio_epg_registry.py`: the piece connecting a
  played-back RadioBrowser station to the right provider above, since
  RadioBrowser identifies stations by an opaque stationuuid this
  project has no way to know in advance -- matches by normalized
  station name instead (best-effort; see Known Issues). Wired into
  every place Internet Radio playback can start
  (playRadioStation()/_playRadioListEntry()).
- MainScreen's top info line ("meta") now shows Now Playing info for
  Internet Radio (previously always "Unknown Artist \u2013 Unknown
  Album" for every station) -- falls back to the current programme's
  title (Radio EPG data) when Now Playing itself isn't available,
  then to the bare station name.

ExtEplayer3 option:

- `Settings -> Use ExtEplayer3 for radio` (off by default): switches
  Internet Radio playback to ExtEplayer3 (service type 5002,
  FFmpeg-based) instead of the default GStreamer-based service.
  Local file playback is never affected. The setting's own label
  shows whether ExtEplayer3 is actually installed
  (`/usr/bin/exteplayer3` present), a safe filesystem-only check.

## Changed

- `os.path.exists()`-based default artwork fallback: MainScreen's
  cover art now always shows *something* (the bundled default
  artwork) instead of a blank area when nothing else is available,
  including at startup before anything has played.
- Radio History no longer accumulates duplicate entries for the same
  station (de-duplicated by stationuuid, most recent moved to the
  top) and no longer reshuffles the list a user is actively browsing
  in the Playlist panel just because a station from it was played.
- Codec Information now falls back to a locally-computed estimate
  (file extension for format, file-size/duration for bitrate on local
  files; RadioBrowser's own station metadata for streams) when
  getStreamInfo() itself can't answer -- see Fixed below for why that
  was usually the case.

## Fixed

- **Startup crash (device test round 1)**: two of the new skin's own
  XML comments used "--" as prose punctuation -- illegal anywhere
  inside an XML comment except its own closing "-->". Python itself
  never catches this (a malformed-XML f-string still compiles and
  runs fine from Python's own point of view); only Enigma2's own
  skin.py actually parsing the string reveals it, which happens on a
  real device, not in this project's stub-based testing. Fixed both
  comments; now standard practice to parse any generated skin string
  with xml.etree.ElementTree before shipping it.
- **Second startup crash (device test round 6)**: the first fix for
  the cover-art startup race (below) used
  `self.onLayoutFinish.append(a lambda)` to defer a widget-instance
  access until Enigma2 had actually applied the skin -- strong
  circumstantial evidence (exact timing match, no other change that
  round touched screen/skin lifecycle at all) points to this as the
  cause of a `TypeError: exec() arg 1 must be a string, bytes or code
  object` crash inside Enigma2's own Screen.createGUIScreen(),
  triggered the moment MainScreen was opened. Replaced with an
  eTimer-based one-shot retry instead -- the same mechanism this
  class already used safely for its periodic refresh timer, avoiding
  a second unverified Enigma2 API in a row.
- Cover art showing blank at startup: `self["cover"].instance` is
  `None` until Enigma2 has applied the skin, which hadn't happened
  yet the moment `__init__` first tried to show the default artwork
  -- fixed by the eTimer retry above.
- Manual scrolling in the Information Panel appearing not to work:
  `InformationPanel.refresh()` reset the scroll position on every
  call, and it's called roughly once per second (the periodic display
  refresh) regardless of whether anything actually changed -- a
  manual scroll was wiped out again within about a second. Now only
  resets when the active track/station itself changes.
- `getStreamInfo()` never actually working since Build 0005 introduced
  it: confirmed via added diagnostic logging that the
  `iServiceInformation` constants it queried (`sAudioType`,
  `sSampleRate`, `sAudioChannels`) don't exist at all on real hardware
  for GStreamer-based file/stream playback (silently skipped, not even
  an error) -- likely DVB-tuning-specific fields never populated for
  this project's own playback path. `sTransferBPS` (bitrate) does
  exist but was consistently -1 ("not available"). Codec name
  specifically also needed `getInfoString()` (a readable string) where
  `getInfo()` (a numeric type ID) was used before, mirroring the same
  distinction already established for `getStreamTags()`.
- Pressing OK or the dedicated PAUSE key while playing Internet Radio
  stopped the stream outright rather than pausing it -- confirmed
  from a real device log (KEY_OK pressed while Now Playing correctly
  showed the current song, followed immediately by the stream
  stopping) that a live stream apparently can't be cleanly
  paused/resumed through this Enigma2 image's playback backend the
  way a local file can. MediaPlayer3's own state then incorrectly
  showed "paused" against an already-dead service, with a later OK
  press unable to bring it back. Now stops the stream cleanly instead
  (the same path the dedicated STOP key already used) and restarts
  the same station fresh (a new prepareStream() call, not attempting
  to revive the old connection) on the next OK press.
- `playRadioStation()`'s own list-name fallback read
  `cfg.radio.navigation_mode`'s raw value ("favorites"/"history", a
  mode selector) and used it as if it were an actual favourite list's
  name when none was given explicitly -- no favourite list is
  literally named "favorites", so this always produced an empty list.
  Confirmed from a real device log/screenshot: selecting an entry from
  the Playlist Panel (added this same build, and itself the direct
  cause -- it omitted the list name) showed the correct list briefly,
  then flipped to a permanently empty "Playlist: favorites".
- History entries never stored a station's favicon URL, so a station
  played from History always fell back to the default artwork even
  after other list types (whose station dicts come straight from
  RadioBrowser) loaded it correctly. Fixed to store it -- and,
  separately, `prepareStream()` now re-enriches a station missing its
  favicon from RadioBrowser by stationuuid before use, breaking a
  self-perpetuating cycle where playing an already-incomplete History
  entry fed the same incomplete data straight back into History again.
- Yle Vega and Bauer's Radio Nostalgia never matched any known EPG
  source: confirmed via a four-image device-testing round that
  RadioBrowser's real names include "radio" between the station's
  Yle/Bauer brand and its name ("Yle radio Vega Ostnyland", "YLE radio
  Suomi, Jyvaskyla") or drop an expected "Radio" prefix entirely
  ("Nostalgia", not "Radio Nostalgia") -- neither convention was
  accounted for in the original hand-written patterns. Fixed both;
  the equivalent-but-untested case for Bauer's other "Radio <name>"
  stations (Classic/City/Pooki/957/Pori) was fixed the same way as a
  precaution, on the same evidence that at least one of them
  (Nostalgia) definitely drops the prefix.

## Known Issues

- Station-name matching in finland_radio_epg_registry.py is
  inherently best-effort (substring match on a normalized name, since
  RadioBrowser's own stationuuid can't be known in advance) -- fixed
  as real mismatches are found via device logs, not guaranteed
  complete for every possible RadioBrowser listing of a Yle/Bauer
  station.
- Bauer Media's Radio Nova and Radio SuomiRock streams are confirmed
  unreliable on at least one tested image regardless of playback
  backend: both GStreamer (recurring "Not Found"/stream-reconnect
  errors) and ExtEplayer3 (a quieter self-stop within about a second
  of "PLAYBACK_OPEN", no user interaction involved) fail the same way
  for these two specific streams, while every other tested Bauer/Yle
  station works normally -- points at a server/stream-side cause
  outside what either backend or this plugin can route around.
  ExtEplayer3 additionally introduced a new, worse problem of its own
  on the tested hardware (roughly a 10-second delay between the
  software STOP command completing and audio actually going silent,
  confirmed to be audio-buffer drain rather than a MediaPlayer3-side
  delay, and affecting local file playback too) -- accepted as a
  known limitation rather than a MediaPlayer3 defect; the setting is
  left available since it remains the documented fix for this general
  class of issue elsewhere, just not on this specific hardware/stream
  combination.
- Yle's Teksti-TV-based schedule data has no equivalent for Bauer
  stations (now-playing only there), and Bauer's own now-playing data
  has no equivalent schedule/upcoming-programme view (Yle only) --
  each source only provides what it was actually confirmed to have.
- CH+/CH- in MainScreen's Player panel remains unverified on real
  hardware, the same open question RadioBrowserScreen/
  MusicLibraryScreen's own CH+/CH- have carried since Build 0007/0008
  -- may be intercepted at the InfoBarGenerics level before reaching
  a custom Screen's ActionMap at all on some images.

## BUILD 0009 -- CONFIRMED COMPLETE

Closing note (multi-image device test round): Build 0009 went through
13 rounds of real device testing, the most extensive testing history
of any build so far -- initially against a single OpenViX device,
with a closing round additionally confirming zero crashes across
OpenViX, OpenPLI, OpenATV and OpenBH in the same session. Both
headline features (MainScreen's three-panel redesign and Finland
Radio EPG) are confirmed working, alongside a substantial list of
bugs found and fixed directly from device-log evidence rather than
guessed at -- including two crashes that reached real hardware (a
malformed-XML skin comment, and an unverified Enigma2 API used to
work around the first fix), both now documented as standing practice
for future skin/lifecycle changes. See Claude_notes_build0009.txt for
the full, round-by-round record, including the complete investigation
into Bauer Media's Radio Nova/SuomiRock streams (GStreamer vs.
ExtEplayer3, both tried, both inconclusive) and the reasoning behind
every fix.

---

# Build History

| Build | Version | Status |
|--------|---------|--------|
| 0001 | 0.1.0-dev | Initial prototype |
| 0002 | 0.2.0-dev | Architecture improvements |
| 0003 | 0.3.0-dev | Stable controller architecture |
| 0004 | 0.4.0-dev | Screen architecture redesign |
| 0005 | 0.5.0-dev | Playback experience: queue, progress bar, Auto Next |
| 0006 | 0.6.0-dev | Customization & rich metadata: localization, skins/themes, tag metadata, artwork |
| 0007 | 0.7.0-dev | Media collections: playlists, Internet Radio (RadioBrowser), storage management |
| 0008 | 0.8.0-dev | Music discovery & help: Music Library, lyrics, MainScreen info views, context-sensitive help |
| 0009 | 0.9.0-dev | MainScreen 2.0 & Radio EPG: three-panel navigation, Finland (Yle/Bauer) radio EPG, ExtEplayer3 option |

---

# Updating the Changelog

The changelog shall be updated:

- Whenever functionality is added.
- Whenever behaviour changes.
- Whenever bugs are fixed.
- Before every public build.
- Before every release.

Entries should be concise, accurate and written in chronological order.

---

# Guidelines

The changelog is intended for both users and developers.

Implementation details belong in technical documentation.

Only user-visible or architecturally significant changes should be
recorded here.

Minor refactoring without behavioural changes does not normally require
a changelog entry.

---

# End of File

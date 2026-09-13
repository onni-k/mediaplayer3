# ==============================================================================
# MediaPlayer3
#
# File        : project.py
# Description : Project information and build metadata.
#
# Author      : MediaPlayer3 Project
# Copyright   : (C) 2026 MediaPlayer3 Project
# License     : GNU General Public License v3 (GPL-3.0-or-later)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Compatible  : OpenViX, OpenATV (planned)
# Python      : 3.13+
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-07-04  Build 0001
#   - Initial version.
#
# 2026-07-12  Build 0004
#   - Version bumped to 0.4.0-dev / Build 0004 (Screen Layer redesign).
#
# 2026-07-14  Build 0005
#   - Version bumped to 0.5.0-dev / Build 0005 (Playback Experience:
#     Playback Queue, progress bar, Previous/Next, Auto Next).
#
# 2026-07-19  Build 0006
#   - Version bumped to 0.6.0-dev / Build 0006 (Customization & Rich
#     Metadata: LocalizationManager, SkinManager, metadata/artwork,
#     themes, expanded PlaybackInfoScreen, developer diagnostics).
#
# 2026-07-19  Build 0007
#   - Version bumped to 0.7.0-dev / Build 0007 (Media Collections:
#     PlaylistManager, InternetRadioManager, StorageManager,
#     PlaylistScreen, RadioBrowserScreen).
#
# 2026-07-28  Build 0008
#   - Version bumped to 0.8.0-dev / Build 0008 (Music Discovery &
#     Help: LibraryManager, MusicLibraryScreen, LyricsManager,
#     HelpManager, HelpScreen, MainScreen information views).
#
# 2026-08-11  Build 0010
#   - Version bumped to 1.0.0-beta (BUILD_0010_PLAN.md fully
#     implemented and device-confirmed; entering beta). BUILD stays
#     "0010" -- the internal build/round-tracking identifier used
#     throughout CHANGELOG.md and the per-build spec documents is
#     unrelated to the user-facing VERSION string bumped here.
#
# 2026-08-31  Build 0010 (device test round 65)
#   - Version bumped to 1.0.0-beta2 -- per direct request, reflecting
#     the substantial round of changes since 1.0.0-beta (the full
#     background-image skin redesign across all eight screens, rounds
#     32-64). BUILD stays "0010" for the same reason noted above.
#
# 2026-08-31  Build 0010 (device test round 73)
#   - Version bumped to 1.0.0-beta3 -- per direct request, reflecting
#     the GStreamer-position bug fixes (rounds 71-72, device-confirmed
#     on Vu+ Duo2) and PodcastScreen layout fixes (round 73: header
#     title wrapping, footer hint-icon text overlap). BUILD stays
#     "0010" for the same reason noted above.
#
# 2026-09-04  Build 0010 (device test round 106)
#   - Version bumped to 1.0.0 -- per direct request, closing out
#     1.0.0-beta3's own public testing period (rounds 83-106: LRCLIB
#     lyrics/MusicBrainz cover art downloads, the lyrics display
#     overhaul, the project-wide title-hiding-behind-background fix,
#     a real Settings freeze and a multi-round virtual-keyboard/hint-
#     bar fix, Radio's own default language/country settable from
#     Internet Radio, a real "unlimited for own language" fix,
#     Swedish/German/Spanish translations -- see CHANGELOG.md's own
#     "1.0.0 released" entry for the full summary, and
#     Claude_notes_build0010.txt for the round-by-round record).
#     BUILD stays "0010" for the same reason noted above. Versioning
#     convention changes from here on: the Patch component is now
#     zero-padded to three digits and bumped by one for every package
#     built and delivered from now on (public release or not) -- the
#     next one after 1.0.0 is 1.0.001, per direct request.
#
# 2026-09-04  Build 0010 (device test round 108)
#   - Version bumped to 1.0.001 (first package under the round-107
#     convention above). Fixed the real reason Settings' own info
#     text never showed, across two earlier failed attempts:
#     _SETTING_DESCRIPTIONS was a class-level dict, so its own
#     _("...") calls only ever ran once at module-import time,
#     independent of (and possibly in a different language than) the
#     labels _buildList() builds fresh every time -- converted to a
#     method rebuilding the dict fresh on every call instead.
#
# 2026-09-04  Build 0010 (device test round 109)
#   - Version bumped to 1.0.002. Round 108's own fix only went half
#     way: the info text showed correctly for whichever row was
#     selected first, but never updated again afterward --
#     ConfigListScreen's own selectionChanged() wasn't actually firing
#     on plain UP/DOWN navigation on the test receiver. Added explicit
#     keyUp()/keyDown() overrides calling _updateSettingInfo()
#     directly, matching this screen's own existing keyLeft()/
#     keyRight() pattern.
#
# 2026-09-04  Build 0010 (device test round 110)
#   - Version bumped to 1.0.003. New "Test Skin" system: a writable
#     .mediaplayer3/test_skin/ directory (auto-populated from a
#     bundled template on first run) lets someone try a new
#     background-image skin without touching the plugin's own
#     installed files -- deleting/renaming it recovers Light
#     automatically, including the Settings value itself, not just
#     the rendered fallback.
#
# 2026-09-05  Build 0010 (device test round 111)
#   - Version bumped to 1.0.004. Real bug fix: wasTestSkinJustCreated()
#     cached a flag at StorageManager construction time, assuming the
#     module-level singleton is built once per Enigma2 session -- not
#     true on the test receiver, which reconstructs it on every plugin
#     launch, so the Skin setting was silently reset to Light on every
#     single launch, not just the first. Now checks real, on-disk
#     directory emptiness fresh on every call instead of caching
#     anything. Also fixes a more serious, not-yet-reported half of
#     the same bug: the bundled template would have overwritten a
#     user's own already-customised test_skin files on every launch
#     too.
#
# 2026-09-05  Build 0010 (device test round 112)
#   - Version bumped to 1.0.005. Real crash fix: KeyError 'test_skin'
#     in every screen's own colour-palette dict -- round 110 added
#     "test_skin" to each screen's own variant whitelist, letting it
#     become active, but never added a matching palette entry in the
#     separate dict that supplies each variant's colours. Fixed in
#     all eight dict-based palettes plus one direct string-comparison
#     instance of the same gap (lyrics_fullscreen_screen.py).
#
# 2026-09-05  Build 0010 (device test round 113)
#   - Version bumped to 1.0.006. Test Skin's own MainScreen palette
#     changed from a plain alias of Dark to its own values: an
#     Enigma2-transparent panel_background_color ("#FF000000") and
#     amber/brass text colours sampled from the user's own reference
#     image, plus the header row moved lower (test_skin only). New
#     vintage-radio background artwork, redrawn from the real widget
#     geometry read out of _buildSkin() rather than guessed
#     proportions.
#
# 2026-09-05  Build 0010 (device test round 114)
#   - Version bumped to 1.0.007. Real architecture fix: round 113's
#     own "#FF000000" transparency looked correct in a device
#     screenshot but showed live TV/video through every text widget
#     in an actual photo of the screen -- backgroundColor's own alpha
#     punches through Enigma2's whole OSD compositing stack to the
#     video plane on this receiver, not a same-window blend against
#     sibling GUI elements. Switched every affected widget to
#     transparent="1" instead (already used elsewhere in this exact
#     skin, confirmed working on real devices) for test_skin only;
#     Light/Dark keep their own real backgroundColor unchanged.
#
# 2026-09-06  Build 0010 (device test round 115)
#   - Version bumped to 1.0.008. Photo confirmed round 114's own
#     transparency fix working. Per direct request, adopted a
#     user-supplied reference image directly as the vintage-radio
#     background (it happened to be exactly 1808x1024, MainScreen's
#     own HD design canvas) and narrowed the two lower panels'
#     outer edges for test_skin only, so the image's own vacuum-tube
#     and knob illustrations in the side margins are actually visible
#     instead of covered by the panel widgets -- confirmed by
#     overlaying the exact rects on the real reference image before
#     writing any of the change. Light/Dark keep their own existing
#     panel positions exactly.
#
# 2026-09-06  Build 0010 (device test round 116)
#   - Version bumped to 1.0.009. Eight test_skin-only position
#     nudges against a device photo of round 115's own layout: cover
#     art, artist/album+track title, elapsed/remaining time,
#     progress bar, clock, playlist/information titles, the playlist
#     list itself, and the lyrics content box's own bottom edge.
#     Light/Dark untouched -- confirmed programmatically (18 position/
#     size assertions against the generated XML), not just visually.
#
# 2026-09-06  Build 0010 (device test round 117)
#   - Version bumped to 1.0.010. Five further test_skin-only
#     centering nudges (cover art, track title, elapsed, remaining,
#     clock) plus a taller trim of the lyrics content box's own
#     bottom edge, against two more device photos. Light/Dark
#     untouched -- confirmed the same way as round 116.
#
# 2026-09-06  Build 0010 (device test round 118)
#   - Version bumped to 1.0.011. Meta/status aligned with media's
#     own left edge; media moved above the background image's own
#     horizontal line (sampled its exact y from the real image, not
#     guessed); cover moved right further; progress bar narrowed
#     further; lyrics box raised further; and a real, separate bug
#     found along the way: selection_background_color was computed
#     every round but never actually wired into any widget's own XML
#     -- added a brown selection colour to playlist_list for
#     test_skin only, leaving Light/Dark's own confirmed-working
#     appearance untouched.
#
# 2026-09-06  Build 0010 (device test round 119)
#   - Version bumped to 1.0.012. Real structural bug found: the 13
#     scrolling-lyrics row widgets (round 93) were always positioned
#     with hardcoded x/width/y-start, completely ignoring
#     in_content_rect -- so every earlier round's own adjustment to
#     that box (113-118) only ever moved the STATIC placeholder,
#     never the actual rows that replace it once real synced lyrics
#     start scrolling, matching a direct report of text "jumping"
#     once playback began. Fixed to build from in_content_rect
#     directly; also computed the row set's own real total height
#     (392, from MainScreen.LYRICS_WINDOW_ROWS) to confirm test_skin's
#     own box (raised to 400) now actually fits it, instead of an
#     arbitrary number. Cover/clock/player-title also nudged further
#     toward centre; progress bar's own y aligned to the background
#     image's own trough, sampled directly from its pixels.
#
# 2026-09-06  Build 0010 (device test round 120)
#   - Version bumped to 1.0.013. Track title moved higher still.
#     Lyrics box made genuinely shorter (400 -> 340) without
#     reopening round 119's own overflow bug: added a scaled-down
#     row-height table used only for test_skin (real total 335,
#     fits); MainScreen.LYRICS_WINDOW_ROWS itself untouched. Caught a
#     second, closely related runtime bug before shipping:
#     _showLyricsWindow()'s own font-sizing referenced the shared
#     class constant directly, which would have kept applying Light/
#     Dark's own bigger fonts to test_skin's own smaller rows at
#     runtime -- fixed by stashing the actual row set used during
#     _buildSkin() (self._lyrics_window_rows) for that method to read
#     instead, the same way self._lyrics_font_family/_scale already
#     work.
#
# 2026-09-06  Build 0010 (device test round 121)
#   - Version bumped to 1.0.014. Real bug fix, root-caused from a
#     device log's own evidence: a genuine GStreamer decode failure
#     ("Could not determine type of stream", "Internal data stream
#     error") right at a track's own PAUSED->PLAYING transition left
#     that track "playing" silently -- progress bar advancing via
#     tick()'s own wall-clock estimate, built for brief transient
#     glitches, with no upper bound on how long it would keep doing
#     so -- until the user noticed no sound and manually stopped and
#     replayed it. Added a counter that treats a sustained run (8
#     ticks, ~8 seconds) of completely unreadable GStreamer position
#     as a stuck pipeline and automatically replays the current
#     track -- the same action the user was already doing manually.
#
# 2026-09-06  Build 0010 (device test round 122)
#   - Version bumped to 1.0.015. Round 121's own recovery was firing
#     exactly as designed but never actually recovering, looping
#     every 8 ticks forever -- confirmed by a device log. Root cause:
#     it called _playIndex() -> play(), which only ever calls
#     self._service.play(), never self._service.stop() first, unlike
#     the user's own successful manual Stop-then-Play. If the
#     service/pipeline object itself was what's broken, asking it to
#     play again without stopping it first could hand back the same
#     broken state. Now calls self.stop() before replaying, matching
#     the user's own working sequence exactly.
#
# 2026-09-06  Build 0010 (device test round 123)
#   - Version bumped to 1.0.016. Attempted prevention, not just
#     recovery: every normal track transition (nextTrack() and
#     friends) shares the exact same gap round 122 fixed for its own
#     recovery path -- play() never stopped the outgoing track first,
#     relying entirely on navigation.playService()'s own built-in
#     replace behaviour, which this project's own code already
#     documents can race on GStreamer-based audio. ServiceController.
#     play() now stops its own outgoing service first whenever one
#     exists (never on the very first track of a session, never
#     touching a service MediaPlayer3 doesn't own). Honest trade-off
#     flagged, not hidden: this could introduce a brief gap between
#     tracks that wasn't there before -- unconfirmed without a real
#     device.
#
# 2026-09-06  Build 0010 (device test round 124)
#   - Version bumped to 1.0.017. Confirmed the user's own direct
#     hypothesis (a GStreamer timing race, not a missing call) from a
#     further device log: round 123's own stop-before-play WAS
#     running, but a failure's own error burst named the exact same
#     GStreamer element instance numbers just torn down moments
#     earlier -- navigation.stopService() returns to Python
#     immediately, before the underlying pipeline teardown actually
#     finishes. Added a brief, deliberate 200ms blocking pause between
#     stop and the following play, only on this specific internal
#     sequence (not on the recovery path or manual Stop/Play, which
#     already have their own natural gap and haven't shown this
#     symptom). Honest trade-off: this is a reasonable starting-point
#     figure, not one calibrated against a real measurement, and
#     briefly blocks Enigma2's own main thread on every transition.
# ------------------------------------------------------------------------------

# 2026-09-06  Build 0010 (device test round 125)
#   - Version bumped to 1.0.018. Programmer feedback review begins
#     (feedback.txt): HELP should be Enigma2's own native HelpMenu
#     (HelpableActionMap/HelpableScreen, researched via web search
#     against real openatv/OpenViX source), colour buttons currently
#     do nothing, MainScreen has no hint bar at all, translation/po/mo
#     handling doesn't follow Enigma2 convention. A genuinely large,
#     multi-round project -- implemented only the specific swap asked
#     for now: MainScreen's EPG/INFO and BLUE swap roles (BLUE takes
#     the Player<->Information panel cycle, EPG/INFO now opens this
#     project's own existing help content). Everything else logged as
#     open work for upcoming rounds.
# ------------------------------------------------------------------------------

# 2026-09-06  Build 0010 (device test round 126)
#   - Version bumped to 1.0.019. MainScreen's own hint bar (Light/Dark
#     only): reduced the two lower panels' own height (428 -> 330) and
#     filled the freed space with five new hint_text_* widgets (OK,
#     BLUE, MENU, EPG/INFO, EXIT) plus a matching background footer
#     card, regenerated from the real source images (sampled the
#     actual panel top edge from pixels rather than guessing) so the
#     existing cover/header/icon artwork is untouched. Caught and
#     fixed two real mistakes before shipping: hint_bar_xml initially
#     referenced rect() before it was defined (a genuine
#     UnboundLocalError, not just a test-harness artifact), and a bad
#     edit landed code in the wrong if/else branch with a stray
#     duplicate else. Also fixed a stale log message ("EPG/INFO
#     pressed" for what round 125 made the BLUE key).
# ------------------------------------------------------------------------------

# 2026-09-06  Build 0010 (device test round 127)
#   - Version bumped to 1.0.020. Round 126 had a real regression: its
#     own "sample the real panel top" logic picked up the ORIGINAL
#     middle status card's own top edge, not the lower panels' -- its
#     erase-and-redraw wiped that middle card out entirely, leaving
#     elapsed/progress/remaining floating with no dedicated card
#     background, exposed to the gap between the two lower panels at
#     the screen's horizontal centre (confirmed from a device photo
#     showing the progress bar's own slider handle sitting on a
#     visible seam). Fixed per the direct request's own wording --
#     widened the top card to include the whole status row instead of
#     restoring a separate middle card. Also: playlist/information
#     titles moved up (490 -> 475); hint bar text shifted right off
#     its own icon glyphs, which it was directly overlapping. Caught
#     and fixed two more real mistakes before shipping: the wipe step
#     started exactly at the old card's own bottom edge, but a rounded
#     corner's own curve pulls inward well before that, leaving a
#     visible pinch at the edges; and Dark's own card_bg colour was
#     sampled from inside the cover-art placeholder box by mistake.
# ------------------------------------------------------------------------------

# 2026-09-06  Build 0010 (device test round 128)
#   - Version bumped to 1.0.021. User reconsidered round 127's "one
#     wide card" fix and asked for the separate middle status card
#     back, attaching their own saved original background images as
#     ground truth -- sampled directly (TOP 18-335, MIDDLE 348-478,
#     LOWER 490-1006 in the 1024 design) rather than reconstructed
#     from memory. Fitting the middle card + a real footer + the full
#     392px lyrics window (round 119's own number) needed trimming
#     the lower panel's own header/padding/gaps; landed on
#     pl_list_rect/in_content_rect height 400 at y=534, title y
#     reverted to 490. Also fixed a real regression: round 126 had
#     reduced light/dark's own pl_list_rect/in_content_rect height
#     without ever checking the real 392px lyrics content still fit
#     (unlike test_skin, light/dark never got scaled-down row heights)
#     -- this round's own validation explicitly re-runs round 119's
#     fit check for light/dark this time. Redesigned the hint bar's
#     own icons per direct request: BLUE gets the colour-square
#     (moved from its old confusing slot), MENU gets the hamburger,
#     INFO gets a new dedicated info-circle glyph instead of sharing
#     MENU's own icon.
# ------------------------------------------------------------------------------

# 2026-09-06  Build 0010 (device test round 129)
#   - Version bumped to 1.0.022. Positive confirmation on round 128's
#     own layout; one further small request -- playlist/information
#     titles nudged up further (490 -> 484), matching the lower
#     panel's own real card top exactly rather than floating above
#     its visible boundary.
# ------------------------------------------------------------------------------

# 2026-09-06  Build 0010 (device test round 130)
#   - Version bumped to 1.0.023. Native HelpMenu pilot, MainScreen
#     first: mixed in Screens.HelpMenu.HelpableScreen, converted the
#     existing combined ActionMap to HelpableActionMap (help text
#     keyed by handler function, since several action names already
#     share one handler), wrapped in a try/except that falls back to
#     the exact original plain ActionMap if HelpableActionMap's own
#     multi-context support (a real but not universally-present
#     Enigma2 feature, confirmed via OpenViX#253) isn't there --
#     functionality is never at risk, only the native help text.
#     Caught a real bug before shipping: compatibility.
#     HELP_KEY_ACTIONS includes "displayHelp", the exact action name
#     Enigma2's own native help mechanism listens for -- binding it
#     to this project's own helpPressed() in the same context would
#     have silently beaten HelpableScreen's own handler to it every
#     time, defeating the whole point. Excluded "displayHelp"
#     specifically from that loop; every other spelling still falls
#     back to helpPressed() as before.
# ------------------------------------------------------------------------------

# 2026-09-06  Build 0010 (device test round 131)
#   - Version bumped to 1.0.024. Round 130's own MainScreen pilot
#     confirmed working on a real device (photo showed Enigma2's own
#     native HelpMenu opening correctly). Rolled the exact same
#     pattern out to every other screen: BrowserScreen,
#     CoverArtFullscreenScreen, DeveloperScreen, HelpScreen,
#     LyricsFullscreenScreen, MainMenu, MusicLibraryScreen,
#     PlaybackInfoScreen, PlaylistScreen, PodcastScreen,
#     RadioBrowserScreen, SettingsScreen -- 12 screens, same
#     HelpableScreen mixin + HelpableActionMap-with-fallback +
#     "displayHelp" exclusion pattern each time. Caught a real bug:
#     developer_screen.py had never previously imported this
#     project's own _() translation wrapper (confirmed every "_(...)"
#     match in the file, before the fix, was one of the new help-text
#     lines just added) -- would have raised NameError the moment
#     this screen's own __init__ ran, on every box. Fixed by adding
#     it to the existing localization import; checked all other 11
#     files directly for the same mistake (none had it, all already
#     imported _ from prior Label text usage).
# ------------------------------------------------------------------------------

# 2026-09-06  Build 0010 (device test round 132)
#   - Version bumped to 1.0.025. Confirmed via three device photos
#     that HELP correctly opens Enigma2's own native guide on
#     Settings, Internet Radio, and Browser. Per direct follow-up,
#     made EPG/INFO consistently open this app's own help content on
#     every screen where it still did something else: BrowserScreen
#     (playlist picker -> GREEN), MusicLibraryScreen/
#     RadioBrowserScreen/PodcastScreen (search -> YELLOW),
#     PlaylistScreen/SettingsScreen (own info display, already
#     redundant with what the screen already shows -> switched
#     straight to help). Added "ColorActions" to the four screens
#     that needed a colour key for the first time; updated stale
#     hint-bar text where present (BrowserScreen, MusicLibraryScreen);
#     removed now-dead help_text_by_handler entries for infoPressed
#     on the two screens where nothing binds to it anymore.
# ------------------------------------------------------------------------------

# 2026-09-07  Build 0010 (device test round 133)
#   - Version bumped to 1.0.026. Added GREEN/RED (add/remove to/from a
#     playlist) across MainScreen, BrowserScreen (Directories/Files),
#     MusicLibraryScreen (Artists/Albums/Tracks), plus RED/GREEN/
#     YELLOW (clear/create/rename) on PlaylistScreen itself. New
#     playlist_manager capabilities: clearPlaylist(),
#     removeTracksInDirectory(), removeTrackByPath() -- each simulated
#     against real path data first, including a directory-prefix
#     false-positive guard ("/music/rock" vs "/music/rockother").
#     MainScreen and MusicLibraryScreen each gained their own
#     self-contained playlist-picker trio (structurally matching
#     BrowserScreen's own established version), since neither had any
#     playlist-target mechanism before. Caught two real bugs: a track
#     dict's own file-path key is "path", not "file_path" as first
#     written; and musiclibraryscreen.py had never imported
#     playlist_manager or MessageBox before, despite the new code
#     using both extensively -- would have raised NameError on the
#     first GREEN/RED press on every box. Visual hint-bar text for the
#     new colour keys deliberately deferred (needs new artwork/
#     geometry work) -- Enigma2's own native help already documents
#     every action correctly in the meantime.
# ------------------------------------------------------------------------------

# 2026-09-07  Build 0010 (device test round 134)
#   - Version bumped to 1.0.027. Confirmed round 133's own GREEN/RED
#     working on Browser/MusicLibrary/Playlist. Fixed a real gap:
#     MainScreen shared one playlist target between radio and local
#     files -- _requireCurrentPlaylist() now suggests "General
#     (radio)" or _defaultPlayPlaylistName()'s own "Files" as the
#     picker's own top entry depending on self._playback.
#     isPlayingStream(), de-duplicated against real playlist names.
#     Adopted a real programmer correction: colour-button hints should
#     use StaticText()/"key_red" etc. (confirmed against real Enigma2
#     source), not this project's own earlier Label()+made-up-name
#     pattern. Added the correct components to all four screens round
#     133 touched, without yet giving them a skin position -- each
#     screen's own hint bar has too little unused width left for three
#     more full hints without the same background-artwork/geometry
#     work MainScreen's own hint bar needed across many earlier
#     rounds; an unskinned Source component is simply invisible, never
#     an error.
# ------------------------------------------------------------------------------

# 2026-09-08  Build 0010 (device test round 135)
#   - Version bumped to 1.0.028. Programmer feedback item #5: .po/.mo
#     file placement corrected. po/<lang>.po now live at the repo
#     root (outside src/, so do_install()'s own existing "cp -r
#     ${S}/src/*" can never ship them); the previously-committed
#     src/resources/locale/<lang>/LC_MESSAGES/MediaPlayer3.mo files
#     are deleted from the repo -- build output, not source. Added
#     do_compile() to mediaplayer3.bb, running msgfmt against each
#     po/<lang>.po into the exact path localization.py's own
#     LOCALE_PATH expects, before do_install()'s own copy runs.
#     Verified equivalence before deleting anything: a freshly
#     compiled po/fi.po matched the currently-committed .mo it
#     replaces exactly (356 entries both, five spot-checked strings
#     byte-identical). Also validated the exact do_compile() shell
#     fragment standalone against a temp copy, for all five languages.
#     Added .gitignore excluding compiled .mo files (plus the standard
#     Python artifacts) so this can't silently regress. This project's
#     own manual packaging process (no real bitbake build system in
#     this environment) needs the same compile step from now on, into
#     its own staging copy only -- the real working src/ stays exactly
#     as clean as the actual repo now is.
# ------------------------------------------------------------------------------

# 2026-09-08  Build 0010 (device test round 136)
#   - Version bumped to 1.0.029. Removed "About" and "Playback
#     Information" from the Main Menu entirely -- both redundant with
#     what MainScreen already shows directly (version string in its
#     own header; playback info in its own player panel);
#     playbackinfo_screen.py deleted. Replaced "Developer Tools" with
#     a single startup log dump: read all 10 of DeveloperScreen's own
#     page methods first (most already called a standalone manager
#     method needing no live Screen at all), then wrote diagnostics.py's
#     own logStartupDiagnostics(playback_controller), verified every
#     one of 15+ referenced symbols directly in its own source module
#     before trusting the port, and simulated the whole function
#     end-to-end with mock managers in two scenarios (populated
#     controller, and None) before shipping it. Caught a real bug
#     before it could ship: the new import initially pointed at the
#     just-deleted developer_screen.py filename instead of the new
#     diagnostics.py module -- would have raised ImportError on every
#     single startup. developer_screen.py deleted; "developer" removed
#     from mainmenu.py's own MENU_ENTRIES.
# ------------------------------------------------------------------------------

# 2026-09-08  Build 0010 (device test round 137)
#   - Version bumped to 1.0.030. Confirmed the Main Menu now shows
#     only 7 entries and the verbose-log diagnostics dump works. Per
#     direct request, attempted to replace round 124's own blind fixed
#     200ms stop-to-play delay with an actual state check. Researched
#     Enigma2's own eServiceMP3::stop() C++ source first (a real
#     linked commit) rather than assuming Python could query
#     GStreamer's own internal pipeline state directly -- confirmed it
#     cannot: the state Python can observe (navigation.
#     getCurrentService()) reflects a flag eServiceMP3 sets
#     SYNCHRONOUSLY the instant stop() is called, not confirmation the
#     underlying GStreamer teardown has actually finished (the same
#     commit's own comment: "the get state on stop might block
#     forever, so use 5 seconds timeout" -- even Enigma2's own C++
#     layer doesn't have a clean fast answer to this). Implemented the
#     requested polling loop anyway using that best-available proxy:
#     up to 10 checks (30ms apart) for getCurrentService() to clear,
#     re-issuing stopService() on each attempt where it hasn't, exiting
#     as soon as it does. The existing 200ms residual safety pause
#     still runs afterward regardless -- a stated, deliberate
#     trade-off, since confirming the flag doesn't rule out the
#     underlying race. Simulated the loop directly across three
#     scenarios (instant/delayed/never-settles) before trusting it.
# ------------------------------------------------------------------------------

# 2026-09-09  Build 0010 (device test round 138)
#   - Version bumped to 1.0.031. A device log showed round 137's own
#     polling change didn't help, because it targeted the wrong part
#     of the sequence -- the real delay is in tick()'s own DETECTION
#     window, not the stop-to-play transition. Confirmed directly from
#     the log's own timestamps: every "No GStreamer position for 8
#     consecutive ticks" recovery message fired 6.6-8.0 seconds after
#     its own corresponding error burst, repeating every 17-37 seconds
#     across the whole session. Confirmed the tick interval is exactly
#     1000ms (mainscreen.py's own refresh timer), matching
#     STUCK_PLAYBACK_RECOVERY_TICKS = 8's own arithmetic exactly.
#     Lowered to 5 per the direct request -- still 2.5x-5x above the
#     "a second or two" normal settling window round 121's own comment
#     describes, so this shouldn't introduce false positives. Confirmed
#     via grep this constant has exactly one other reference in the
#     whole codebase. Does not attempt to address why the underlying
#     GStreamer failures recur so often -- the direct request was
#     specifically to shorten the delay, not investigate the cause.
# ------------------------------------------------------------------------------

# 2026-09-09  Build 0010 (device test round 139)
#   - Version bumped to 1.0.032. Renamed the project's own custom
#     per-screen documentation from "help" to "Information"/"Tiedot"
#     (item #2 of the programmer feedback review): help_manager.py ->
#     guide_manager.py, help_screen.py -> guide_screen.py,
#     HelpManager -> GuideManager, HelpScreen -> GuideScreen, and
#     helpPressed() -> infoPressed() on all 8 screens that had it.
#     Named "Guide" internally rather than "Information" directly, per
#     direct user choice, to avoid colliding with the unrelated,
#     pre-existing InformationPanel (MainScreen's own lyrics/metadata/
#     codec display). Removed two real pieces of dead code found along
#     the way: round 132's own orphaned infoPressed() in
#     PlaylistScreen and SettingsScreen (unreachable since round 132,
#     never deleted until now). Removed the orphaned resources/help/
#     developerscreen.md (round 136's own leftover). Left every one of
#     Enigma2's own native symbols (HelpableScreen, HelpableActionMap,
#     getHelpKeyActionNames(), HELP_KEY_ACTIONS, "HelpActions")
#     completely untouched -- not this project's own naming. Updated
#     po/<lang>.po for all 5 languages; caught and fixed a real
#     duplicate-msgid bug in the first attempt (both changed strings
#     already existed under those exact English texts elsewhere in the
#     catalog) by reading msgfmt's own error output directly rather
#     than assuming success.
# ------------------------------------------------------------------------------

# 2026-09-09  Build 0010 (device test round 140)
#   - Version bumped to 1.0.033. Simplified translation setup to match
#     the real Enigma2 plugin convention (item #4), confirmed against
#     real plugin source (IMDb, ShareMyBox, FileBrowser) before
#     touching anything: localization.py's own LocalizationManager
#     class replaced with a module-level _() that always follows the
#     receiver's own current system language. A real design conflict
#     was flagged to and resolved by the user first: this project's
#     own independent Settings -> Language choice (cfg.general.
#     language) has no equivalent in the standard convention -- per
#     direct user choice, removed entirely rather than preserved.
#     Touched config.py (removed the setting/resolveLanguageCode()),
#     plugin.py (removed the now-unnecessary startup apply call),
#     settingsscreen.py (removed the UI entry and its own apply-on-
#     change logic), internetradio_manager.py and radiobrowserscreen.py
#     (both had a real, separate dependency on the old setting for
#     radio-station language filtering -- updated to the new
#     getCurrentLanguage()), and diagnostics.py (the removed class's
#     own translation-lookup counters no longer exist). Caught two real
#     bugs before shipping: config.py's own _ENTRIES dict (built at
#     MODULE IMPORT TIME) still referenced the deleted cfg.general.
#     language, which would have crashed the whole app on startup on
#     every box -- py_compile's own syntax check did not catch this;
#     only a targeted grep sweep did. A first sweep for
#     resolveLanguageCode() also missed two genuine call sites in
#     radiobrowserscreen.py entirely, found only on a second, more
#     thorough pass. Also fixed a genuinely user-facing stale
#     reference: resources/help/settingsscreen.md's own intro sentence
#     still described a "language" setting that no longer exists.
# ------------------------------------------------------------------------------

# 2026-09-09  Build 0010 (device test round 141)
#   - Version bumped to 1.0.034. Added test_skin's own footer hint bar
#     (item #3), deferred since round 126's own Light/Dark addition.
#     Measured the reference photo's own real geometry directly with a
#     labelled grid overlay before designing anything: the lower
#     panels' own real visual bottom sits at y~838-840, followed by a
#     decorative speaker-grille strip (y~858-995) large enough for a
#     new footer bar without touching the existing panels. Found and
#     reported (not fixed here) a separate, pre-existing mismatch:
#     pl_list_rect/in_content_rect already extend well past that real
#     boundary (~988/900). Baked a new rounded overlay plate (dark
#     brown fill, brass-gold border matching the tube/knob artwork's
#     own style) into all four background images, visually reviewing
#     each stage before finalizing rather than trusting the numbers
#     alone; added the matching hint_text_* XML to test_skin's own
#     previously-empty hint_bar_xml branch. Caught a second bug along
#     the way: hint_text_info's own Label text still read "EPG/INFO:
#     Help", missed by round 139's own Help->Information rename; fixed
#     to "EPG/INFO: Information". Flagged an important caveat to the
#     user: test_skin_template/ only ever populates a FRESH Test Skin
#     folder (round 110's own logic) -- an already-populated one (which
#     this project's own user has had since round 113) needs manual
#     attention to actually show this change.
# ------------------------------------------------------------------------------

# 2026-09-09  Build 0010 (device test round 142)
#   - Version bumped to 1.0.035. Two real device photos showed round
#     141's own hint bar text sitting directly on the reference
#     image's own centre badge, garbled. Root cause was two
#     compounding mistakes: the new footer plate's own fill was
#     semi-transparent (235/255), letting the badge/grille texture
#     show faintly through even outside the text's own numeric
#     overlap -- now fully opaque (255/255); and the badge's own real
#     position was never actually measured before round 141 placed
#     text near it -- measured properly this round (x~845-965 design
#     units) via a fresh pixel sample against the pre-overlay artwork.
#     Added a genuinely missing HELP entry to the same bar (Enigma2's
#     own native guide, rounds 130-132, never had one on ANY variant)
#     as a real sixth slot rather than just shrinking the existing
#     five to dodge the badge -- three slots on each side of the
#     measured badge zone now. Also fixed the lyrics-scrolling overflow
#     the user confirmed after round 141's own report: in_content_rect/
#     pl_list_rect moved up (y=560->545) and shrunk (340/428->293) to
#     genuinely fit within the real panel boundary round 141 measured;
#     test_skin_lyrics_rows scaled down further to a computed 282px
#     total, an 11px margin inside the new 293px budget.
# ------------------------------------------------------------------------------

# 2026-09-09  Build 0010 (device test round 143)
#   - Version bumped to 1.0.036. Per direct request (with the user's
#     own preserved "before" copies attached), reverted round 141/142's
#     own drawn overlay plate entirely -- this skin reads better with
#     hint text sitting directly on the plain photograph, transparent,
#     matching Light/Dark's own approach, than with a solid card drawn
#     over the grille/badge. Replaced test_skin_template's own HD
#     background images with the user's own uploaded files directly;
#     derived the SD tier by resizing those same files. BLUE/EPG-INFO/
#     EXIT text shifted right per the direct request; OK/MENU/HELP
#     keep their own round 142 positions. Also fixed TXT-format lyrics
#     legibility, a real, separate gap from LRC's own already-fixed
#     sizing: DEFAULT_VISIBLE_LINES (14) and info_content's own
#     hardcoded font size (28) were both applied unconditionally
#     regardless of skin variant, never adapted for test_skin's own
#     smaller 293px box. Set test_skin's own visible_lines to 6
#     (InformationPanel(visible_lines=...), based on self._skin_variant,
#     confirmed _buildSkin() already sets this before InformationPanel
#     is constructed) and info_content's own font size to 32 for
#     test_skin specifically (still 28 for Light/Dark) -- both numbers
#     computed together as an estimate, not an empirically-verified
#     Enigma2 line-height figure, stated as such to the user.
# ------------------------------------------------------------------------------

# 2026-09-10  Build 0010 (device test round 144)
#   - Version bumped to 1.0.037. Confirmed the real root cause of the
#     TXT lyrics font issue, after the user reported round 143's own
#     two fixes had ZERO effect: information_panel.py's own existing
#     comment (~355-367) documents that an earlier round changed the
#     condition to just `elapsed is not None`, so UNSYNCHRONIZED (TXT)
#     lyrics use the exact same 13-widget windowed path as LRC --
#     info_content is hidden entirely, so neither visible_lines nor
#     its font size can affect TXT at all. Round 143's changes were on
#     a dead path from the start. A THIRD fix on that same wrong path
#     (a word-wrap hypothesis) had already been started this round and
#     was fully REVERTED rather than shipped. The correct fix (a
#     test_skin-specific row COUNT) is documented in detail in
#     HANDOFF's own KNOWN ISSUE section, including all three call
#     sites that must change together, and deliberately not started.
#   - Per direct request, added per-language Information/guide
#     documents: getGuide() tries resources/help/<lang>/<screen_id>.md
#     first, falling back to the existing English resources/help/
#     <screen_id>.md otherwise. Never falls back to a DIFFERENT
#     non-English translation (verified by simulation). Translated only
#     MainScreen's own three panel documents into Finnish for now, per
#     the request to hold off while further changes are likely; every
#     other screen keeps showing English with no code change needed.
# ------------------------------------------------------------------------------

# 2026-09-10  Build 0010 (device test round 145)
#   - Version bumped to 1.0.038. Combined MainScreen's own three-way
#     guide (player.md/playlist.md/information.md, switched by self.
#     _active_panel) into a single resources/help/mainscreen.md --
#     confirmed first via direct user confirmation that the Playlist
#     panel is genuinely unreachable now (an earlier UI change means
#     the Player/Information cycle never enters it), so its own guide
#     page could never actually be opened either. infoPressed() now
#     always requests "mainscreen" (confirmed via grep this was the
#     only call site using the three old screen_ids). Content: own
#     heading per section (## Player, ## Information), a new ##
#     Playlist column section describing the always-visible left-hand
#     column, and the requested Keys changes -- "EPG/INFO: switch
#     panel" became "EPG/INFO: open this guide" (its own real current
#     function), plus a new "BLUE: switch between Player/Information"
#     line, since BLUE is what does that switching now. Finnish
#     translation (fi/mainscreen.md) replaces round 144's own three
#     separate Finnish files. Deleted all six now-orphaned files
#     (English + Finnish x player/playlist/information) after
#     confirming via grep nothing else referenced them.
# ------------------------------------------------------------------------------

# 2026-09-10  Build 0010 (device test round 146)
#   - Version bumped to 1.0.039. Systematic colour-button audit across
#     seven screens, per direct request -- went through every screen's
#     own menus looking for real candidates rather than only reacting
#     to individual requests. MainScreen: YELLOW = show lyrics
#     fullscreen. BrowserScreen: YELLOW/BLUE = move playlist track
#     up/down. MusicLibraryScreen: BLUE = update library.
#     RadioBrowserScreen: GREEN = add to favorites. PodcastScreen:
#     GREEN = subscribe/add episode (column-dependent), RED =
#     unsubscribe. PlaylistScreen: BLUE = remove selected single track
#     (distinct from RED's own whole-playlist clear). All six reuse
#     existing menu-handler logic directly, just reachable one key
#     press sooner. Also fixed a genuine, separate gap the user caught
#     while reviewing: PlaylistScreen's own "Move Up"/"Move Down" never
#     worked for radio favourite entries at all (excluded via "and not
#     is_radio"), because internetradio_manager had no reorder
#     capability of its own until now -- added moveFavorite(), mirroring
#     playlist_manager.moveTrack()'s own signature exactly, and wired
#     both _openTrackMenu() and _trackMenuChosen() to use it for radio
#     entries the same way the local branch already worked.
# ------------------------------------------------------------------------------

# 2026-09-11  Build 0010 (device test round 147)
#   - Version bumped to 1.0.040. Revised PlaylistScreen's own round
#     146 colour keys per direct feedback: YELLOW/BLUE now Move Up/
#     Move Down (Tracks column, mirroring BrowserScreen's own
#     shortcuts), replacing Rename (now OK-menu-only) and the
#     single-track-remove shortcut. RED is now context-dependent --
#     delete the whole playlist (Playlists column) or remove the
#     selected track (Tracks column) -- replacing round 133's own
#     Clear, which moved into the playlist-level menu as a new
#     "Clear" choice instead. Added a confirmation dialog for single-
#     track removal (never had one before, for either the menu choice
#     or the colour-key shortcut) via new _confirmRemoveTrack()/
#     _removeTrackConfirmed(), matching the existing whole-playlist
#     delete's own confirmation pattern.
#   - Found and fixed a real, pre-existing bug in BrowserScreen's own
#     directory menu, per direct request/observation: round 30's own
#     comment already described "Play leads when there are playable
#     files, otherwise Open directory leads", but the code underneath
#     never actually implemented that distinction -- it unconditionally
#     put "Play" first whenever a playback controller was available at
#     all, and a second, redundant "if self._files_in_preview" block
#     never touched the genuinely broken case. This bug predates every
#     colour-button round before it. Rewritten as an explicit three-
#     way branch that actually reads self._files_in_preview.
# ------------------------------------------------------------------------------

# 2026-09-11  Build 0010 (device test round 148)
#   - Version bumped to 1.0.041. Implemented the TXT-format lyrics fix
#     rounds 143/144 had already scoped out in HANDOFF's own KNOWN
#     ISSUE section, per direct request. Re-reading _showLyricsWindow()/
#     _hideLyricsWindow() directly found both already iterate self.
#     _lyrics_window_rows (the per-instance, variant-aware stash),
#     not the shared 13-row class constant -- so two of the three
#     originally-planned call sites needed no change. The one real
#     gap: _updateInformationPanel()'s own getCurrentLyricsWindowData()
#     call still passed the fixed 13-row count regardless of variant --
#     fixed to read self._lyrics_window_rows instead. test_skin_lyrics_
#     rows shrunk from 13 small rows to 7 genuinely bigger ones (36px/
#     26pt normal, 52px/37pt current), same 3/1/3 shape, 25px margin
#     inside the real 293px budget. Confirmed via simulation that
#     lyrics_manager.py's own window_size // 2 "current" placement
#     lines up exactly with the new config's own bold row at every
#     window size, nothing 13-specific left anywhere. Scoped to
#     test_skin only, per the direct request; LyricsFullscreenScreen
#     (explicitly meant to stay untouched) references none of the
#     changed constants, confirmed by grep.
# ------------------------------------------------------------------------------

# 2026-09-11  Build 0010 (device test round 149)
#   - Version bumped to 1.0.042. Extended test_skin's own amber/brass
#     colour palette to every other screen (BrowserScreen,
#     MusicLibraryScreen, PlaylistScreen, PodcastScreen,
#     RadioBrowserScreen, SettingsScreen, MainMenu,
#     LyricsFullscreenScreen), per direct request, scoped to colours/
#     text only (not background images/icons, per the user's own
#     choice when asked). Root cause: round 112's own crash-fix
#     aliased every one of these screens' own test_skin palette
#     straight to Dark's (`PALETTES["test_skin"] = PALETTES["dark"]`)
#     to fix a KeyError, back when test_skin's own background images
#     everywhere were still literal Dark copies -- never revisited
#     after MainScreen's own test_skin became a distinct amber/brass
#     look from round 113 onward. LyricsFullscreenScreen had the same
#     gap via a direct string comparison rather than a dict alias.
#     Real, standalone test_skin dicts written for each of the seven
#     screens, colours copied directly from MainScreen's own palette
#     for consistency, each screen's own particular key set read
#     individually first rather than assumed uniform. Confirmed
#     programmatically (a script that extracted and compared each
#     file's own real dark/test_skin dicts) that every one of the
#     seven now has an EXACT key-set match with its own dark palette,
#     ruling out the specific KeyError class round 112 first fixed.
#     Left one open question for the user rather than guessing: a
#     solid blue bar visible behind LyricsFullscreenScreen's own title
#     text in the screenshot that prompted this round has no
#     corresponding background fill anywhere in that file's own
#     generated skin XML.
# ------------------------------------------------------------------------------

# 2026-09-12  Build 0010 (device test round 150)
#   - Version bumped to 1.0.043. Two device photos resolved round
#     149's own open question and surfaced a genuine bug from that
#     round: the blue title bar is baked directly into lyrics_
#     fullscreen_background.png itself (confirmed by the user, who
#     also said it's fine to keep), but round 149 had recoloured
#     panel_background_color for test_skin (old #1C202B -> new
#     #1C1610) without touching that same image's own still-#1C202B
#     body, so the lyrics rows' own small inter-row gaps let the
#     mismatched blue-grey image show through as horizontal seams.
#     Fixed two ways: lyrics_fullscreen_background.png's own body/
#     hint-bar area recoloured to #1C1610 for both tiers (title bar
#     untouched), and the lyrics_line_N/content/hint widgets' own
#     backgroundColor fill replaced with transparent="1" for test_skin
#     specifically, so no fill colour is left to ever drift out of
#     sync with the image again. Built a proper _buildSkin() mock
#     harness for this file (same technique as mainscreen.py's own)
#     and confirmed via direct transparent/opaque counts that Light/
#     Dark are completely unaffected.
# ------------------------------------------------------------------------------

# 2026-09-12  Build 0010 (device test round 151)
#   - Version bumped to 1.0.044. Two more real, pre-existing
#     mismatches found via device photos, the same class of bug round
#     150 fixed for LyricsFullscreenScreen, now in five more places:
#     scrollbarBackgroundColor was hardcoded light grey (#E0E0E0),
#     never part of any palette, on six screens' own list widgets;
#     and every screen's own bottom "info" status widget used an
#     opaque panel_background_color fill that no longer matches
#     test_skin's own brown background image. Fixed both in
#     BrowserScreen, PlaylistScreen, PodcastScreen, RadioBrowserScreen
#     (scrollbar_bg "#3A2E1A" + transparent info, test_skin only) and
#     SettingsScreen (info fix only, confirmed via grep this screen
#     never had the scrollbar issue). Per direct user instruction,
#     musiclibraryscreen.py deliberately left untouched despite having
#     the identical scrollbar pattern -- confirmed by grep it's the
#     only screen still carrying it. Built a proper _buildSkin() mock
#     harness per file and confirmed via direct XML assertions that
#     Light/Dark are unchanged in all five touched files.
# ------------------------------------------------------------------------------

# 2026-09-12  Build 0010 (device test round 152)
#   - Version bumped to 1.0.045. Extended round 151's own scrollbar
#     fix to musiclibraryscreen.py after all (initially left out at
#     the user's own request since the mismatch wasn't visible there
#     yet, then confirmed to have the identical pattern). No "info"
#     widget in this screen, so only the scrollbar half applies.
#   - Found and fixed the real cause behind "radio wants to
#     re-download the station database every time the device
#     restarts": traced a device log showing the "No stations
#     available yet" prompt firing (and the user's own OK confirming
#     it) on a boot whose /media/hdd was independently confirmed
#     writable moments earlier in that same log -- pointing at a
#     startup race rather than a genuinely missing drive.
#     _pickWorkingDirectoryParent() (storage.py) is called once,
#     synchronously, at module-import time via the module-level
#     StorageManager singleton -- often only moments after boot,
#     potentially before a slower USB HDD finishes mounting. The old
#     single, immediate check had no way to tell "unavailable" apart
#     from "not ready yet" and silently chose the non-persistent /tmp
#     fallback for the latter too, losing that boot's own playlists/
#     favorites/radio database the moment anything was written there.
#     Now retries for up to 3 seconds (12 attempts, 250ms apart)
#     before falling back -- deliberately short of the first draft's
#     own 5 seconds, so a receiver with no external drive at all
#     (for which /tmp is legitimate, not a failure) doesn't pay a
#     needless fixed cost every single boot.
# ------------------------------------------------------------------------------

# 2026-09-12  Build 0010 (device test round 153)
#   - Version bumped to 1.0.046. Raised cfg.radio.search_limit's own
#     configurable ceiling from 20000 to 100000, per direct request
#     following round 152's own device log evidence (a real, already-
#     gracefully-handled MemoryError reading back a 58388-station
#     database) -- comfortably above the full RadioBrowser database's
#     own real size, which "unlimited" (0) already implicitly allowed
#     anyway. Added a direct warning to this setting's own hint text
#     ("Values over 50000 may cause problems on some receivers..."),
#     informed by what the log actually showed rather than a generic
#     caution. Updated the existing Finnish translation to match
#     (English source changed, so msgid/msgstr both needed updating
#     together); other languages left untouched, correctly falling
#     back to the updated English text via round 144's own mechanism.
# ------------------------------------------------------------------------------

# 2026-09-12  Build 0010 (device test round 154)
#   - Version bumped to 1.0.047. Started from a narrow direct request
#     (fix RadioBrowserScreen's own guide text for EPG/BLUE) and found
#     the same bug repeated across every screen: rounds 132/139/146/
#     147 had all changed real key behaviour, but the guide text and
#     hint-bar labels describing it were never updated anywhere. Two
#     real code-level bugs (hint_text_info still read "INFO: Search"
#     in radiobrowserscreen.py and podcastscreen.py despite EPG/INFO
#     opening this guide since round 132/139) plus seven stale .md
#     files rewritten to match actual current behaviour: radiobrowser-
#     screen.md/podcastscreen.md/musiclibraryscreen.md (search moved
#     to YELLOW; GREEN/RED/BLUE never documented at all), browser-
#     screen.md (GREEN's own round-133 context-dependent takeover of
#     round-132's INFO-triggered playlist picker, plus RED/YELLOW/
#     BLUE), playlistscreen.md (also corrected a claim round 147 had
#     quietly made false -- "reordering only makes sense for local
#     playlists" -- when round 147 specifically added it to radio
#     favourites too), settingsscreen.md (its own "INFO" line was
#     describing something that, on inspection, was never actually a
#     key action at all -- the info panel updates on selection
#     change, not a keypress), and mainmenu.md (never mentioned EPG/
#     INFO opening this guide at all). Grepped every remaining .md
#     file afterward -- zero stale matches left anywhere.
# ------------------------------------------------------------------------------

# 2026-09-12  Build 0010 (device test round 155)
#   - Version bumped to 1.0.048. Two direct requests before the
#     planned 1.1.000 bump. (1) Translated the last known
#     documentation gap: round 130's own native per-button help text
#     (HelpableActionMap, Enigma2's own remote-control guide) had
#     never been translated into any language -- 61 unique strings
#     extracted across all 11 screens with a help_text_by_handler
#     dict, all missing from po/fi.po despite already being wrapped
#     in _() since round 130; wrote and appended Finnish translations
#     for all 61, confirmed via msgfmt and a direct .mo readback.
#     (2) Vintage Radio graduated from Test Skin into its own fully
#     independent skin choice, per the user's own explicit choice
#     among three possible interpretations offered directly. Checked
#     resolve_skin_asset_path() and plugin.py's own _ensureTestSkin
#     Template() first -- both only special-case the literal string
#     "test_skin", so a new variant name needed no changes to either.
#     Copied resources/skins/test_skin_template/ (38 PNGs) to a new,
#     separate resources/skins/vintage_radio/, added the new choice to
#     config.py's own ConfigSelection, and across nine screens (every
#     one with SKIN_VARIANTS/palette dicts) added "vintage_radio" to
#     each own variants tuple, an independent copy (not a reference)
#     of that file's own test_skin palette, and widened every self.
#     _skin_variant == "test_skin" check to also match "vintage_radio".
#     Confirmed programmatically that every one of the eight dict-
#     based palettes' own test_skin/vintage_radio pairs match exactly
#     on both keys and values, and ran the mandatory skin-XML
#     validation (mainscreen.py, lyrics_fullscreen_screen.py,
#     browserscreen.py as a representative sample) across all four
#     variants, confirming vintage_radio produces structurally
#     identical output to test_skin's own while Light/Dark stay
#     unaffected.
# ------------------------------------------------------------------------------

# 2026-09-13  Build 0010 (device test round 156)
#   - Version bumped to 1.0.049 (still a test build; 1.1.000 follows
#     once confirmed). Round 155's own work confirmed working on
#     OpenViX/OpenBH; OpenATV showed a real, different bug: HELP
#     opened this project's own guide instead of Enigma2's own native
#     button guide. Root cause found from the OpenATV log's own raw
#     ActionMap trace, not guessed: compatibility.py's own
#     HELP_KEY_ACTIONS lists six candidate action names, and round 130
#     excluded only "displayHelp" from each screen's own local
#     ActionMap (routing every other name to infoPressed() as a
#     fallback for images with a different PRIMARY naming convention)
#     -- but the log showed "displayHelp" AND "displayHelpLong" both
#     registered for the SAME physical key on OpenATV, meaning
#     "displayHelpLong" isn't a different image's own alternate
#     primary binding, it's a second action HelpableScreen's own
#     native mechanism also listens for on some images. Excluding
#     only "displayHelp" left "displayHelpLong": infoPressed() live to
#     win the key on exactly the images that fire both. Fixed across
#     all nine screens with this exact pattern (confirmed by grep):
#     mainscreen.py, browserscreen.py, guide_screen.py, mainmenu.py,
#     musiclibraryscreen.py, playlistscreen.py, podcastscreen.py,
#     radiobrowserscreen.py, settingsscreen.py.
#   - Also merged mainscreen.py's own native help text for upPressed/
#     downPressed ("previous/next radio station (internet radio
#     only)" -> "previous/next track/station"), per direct request,
#     updating the matching Finnish translation; the longer guide
#     document's own more detailed phrasing was left alone as a
#     separate, appropriately-detailed context.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 project information.

This module contains all project-wide metadata that may be displayed
in the About dialog, diagnostic reports, log files and package
information.

Other modules should import these values instead of defining their own.
"""

# ------------------------------------------------------------------------------
# Project information
# ------------------------------------------------------------------------------

PROJECT_NAME = "MediaPlayer3"
PROJECT_SHORT_NAME = "mediaplayer3"

APPLICATION_ID = "org.enigma2.mediaplayer3"

# ------------------------------------------------------------------------------
# Version information
# ------------------------------------------------------------------------------

# Round 158: sourced from __init__.py's own __version__ (the single
# source of truth a GitHub Actions autotag workflow reads directly by
# regex) rather than duplicating the literal string here -- see that
# file's own round 158 comment for the full reasoning.
from . import __version__ as VERSION

BUILD = "0010"

# ------------------------------------------------------------------------------
# Author information
# ------------------------------------------------------------------------------

AUTHOR = "MediaPlayer3 Project"

COPYRIGHT = "Copyright (C) 2026 MediaPlayer3 Project"

LICENSE = "GPL-3.0-or-later"

# ------------------------------------------------------------------------------
# Project URLs
# ------------------------------------------------------------------------------

HOMEPAGE = ""

REPOSITORY = ""

ISSUE_TRACKER = ""

# ------------------------------------------------------------------------------
# Compatibility
# ------------------------------------------------------------------------------

SUPPORTED_IMAGES = (
    "OpenViX",
    "OpenATV",
)

MINIMUM_PYTHON = (3, 13)

# ------------------------------------------------------------------------------
# Log file prefix
# ------------------------------------------------------------------------------

LOG_PREFIX = "mediaplayer3"

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

CONFIG_NAMESPACE = "plugins.mediaplayer3"

# ------------------------------------------------------------------------------
# End of file
# ------------------------------------------------------------------------------

#end_of_file

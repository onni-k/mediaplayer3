# MediaPlayer3

# Project History

Version: 0.1

Status: Living Document

---

# 1. Purpose

This document records important architectural decisions made during the
development of MediaPlayer3.

Unlike CHANGELOG.md, this document explains why significant decisions
were made.

Its purpose is to preserve project knowledge for future development.

---

# 2. Document Scope

This document records:

- Architecture decisions
- Design changes
- Naming decisions
- Module responsibilities
- Development milestones

Minor implementation details are intentionally excluded.

---

# 3. Project Timeline

Build 0001

Initial prototype.

Single Browser-based user interface.

Basic playback functionality.

---

Build 0002

Architecture planning begins.

Controllers introduced.

Improved module separation.

Documentation expanded.

---

Build 0003

Controller architecture stabilised.

Compatibility abstraction introduced.

SystemInfo module introduced.

Logging significantly improved.

Project reaches first stable internal architecture.

---

Build 0004

Complete Screen Layer redesign begins.

MainScreen becomes the primary application window.

Browser becomes a temporary navigation screen.

Settings, PlaybackInfo and Developer screens introduced.

---

Build 0005

Playback Experience.

Playback Queue introduced; PlaybackController becomes responsible for
playback navigation (Previous/Next Track, Automatic Next Track).

MainScreen gains a graphical progress bar and elapsed/remaining time
display, refreshed continuously while playback is active.

DeveloperScreen extended with Playback Statistics.

Tested on a real OpenViX 6.8 device across multiple rounds; all
reported issues (queue selection, seeking, cover art, fullscreen
layout, elapsed/duration reporting) fixed and re-verified.

No architectural changes; Build 0004's Screen/Controller/Core layering
is extended, not restructured.

---

Build 0006

Customization & Rich Metadata.

Two new Core modules: LocalizationManager (translation loading,
language selection, fallback) and SkinManager (skin metadata,
compatibility validation with fallback, theme colour palettes).

Rich tag metadata (FLAC, MP3, Ogg Vorbis -- pure Python, no external
dependency) and embedded album artwork, extending MainScreen's
existing artwork display and PlaybackInfoScreen's information display.

PlaybackController gains metadata caching (getMetadata()/
getEmbeddedArtwork()) but stays independent of LocalizationManager,
SkinManager and metadata.py's individual parsers -- only calls
metadata.py's public read() function, per the same "Controller
Independence" principle established in earlier builds.

Verified via an extended stub environment and, for the metadata
parsers specifically, against real ffmpeg-generated audio files, then
tested on a real OpenViX 6.8 device across four rounds: live TV
stopping immediately on open, the Startup directory browser and the
configurable seek step were added during those rounds in response to
real device feedback, alongside fixes for a progress bar transparency
issue, EXIT behaviour, Title priority, a stale position/duration bug
on track change, clipped single-line text fields and DeveloperScreen
pages not fitting vertically. User confirmed Build 0006's level was
reached.

No architectural changes; extends the Core Layer established in
Build 0004, following the same "extends existing modules without
changing the established layered architecture" principle Build 0005
followed.

---

Build 0007

Media Collections: Playlists & Internet Radio.

Three new Core modules: StorageManager (application storage
directories, foundation for the other two), PlaylistManager (Extended
M3U playlist management) and InternetRadioManager (RadioBrowser API
communication, modelled on the pyradios reference project checked per
user request, plus favorites and listening history).

Two new Screens: PlaylistScreen (dual-panel playlist management) and
RadioBrowserScreen (three-panel station browsing/search/favorites),
both following the established "no colour buttons required for
navigation" principle -- colour buttons are used only where genuinely
necessary (BrowserScreen still avoids OK for its new context menu,
using INFO instead, to protect Build 0005/0006's real-device-verified
descend/play behaviour; SettingsScreen's YELLOW "Clear radio history"
is a single, deliberate exception for a genuinely occasional action).

PlaybackController gains playStream()/isPlayingStream() for radio
playback, reusing the existing local-file eServiceReference
construction rather than a separate playback path, and stays
independent of InternetRadioManager/PlaylistManager beyond receiving
a plain URL or file-path queue -- the same Controller Independence
principle Build 0006 followed for metadata.

MainScreen's LEFT/RIGHT/UP/DOWN keys gain a second meaning while
playing a radio stream (station/list navigation) without disturbing
their existing seek meaning for local files, since the two states are
mutually exclusive for any given playback session.

Verified via an extended stub environment, including full playlist
round-trips (create/add/import/export/validate) and InternetRadioManager's
favorites/history/graceful-failure handling. RadioBrowser network
calls themselves could not be exercised (no network egress in the
sandbox this was built in) -- real device testing, including actual
API calls, is the priority for the next round.

No architectural changes; extends the Core and Screen Layers
established in Build 0004, following the same "extends existing
modules without changing the established layered architecture"
principle every build since Build 0005 has followed.

Closing note (device test round 13): Build 0007 went on to 13 rounds
of real device testing across four Enigma2 images (OpenViX, OpenATV,
openPLI, OpenBH), confirmed complete by the user. Beyond what's
described above, that testing added: every screen converted to
fullscreen with a fixed white-panel/near-black text rendering scheme
(after a multi-round investigation into the box's own video/
background bleeding through screen content), a new Gray default
theme, a startup chooser with a full radio auto-resume fallback
chain, and several real remote-control key mapping fixes (RADIO,
INFO/EPG-substitute) resolved only once raw eActionMap log evidence
was available -- guessing candidate action names alone repeatedly
fell short on this platform. Two items remain deliberate, documented
scope decisions rather than open bugs: CH+/CH- in RadioBrowserScreen,
and launching the whole plugin via a global hardware RADIO key. See
CHANGELOG.md's "BUILD 0007 -- CONFIRMED COMPLETE" section and
Claude_notes_build0007.txt for the full, session-by-session record.

---

Build 0008

Music Discovery & Help.

Three new Core modules: LibraryManager (metadata-based music index,
independent of BrowserScreen's filesystem view, reusing metadata.py's
existing pure-Python reader -- no third-party dependency), LyricsManager
(embedded/.lrc/.txt lyrics in that fixed priority order), and
HelpManager (loads resources/help/<screen_id>.md, renders a lightweight
Markdown subset to plain text for Enigma2's Label widgets).

Two new Screens: MusicLibraryScreen (three-panel Artists/Albums/Tracks
browsing, navigation modeled directly on RadioBrowserScreen, including
its deferred "please wait" loading pattern for the library scan) and
HelpScreen (generic scrollable document viewer, built on
DeveloperScreen's already-proven scroll pattern). HELP key wired into
every screen; MainScreen additionally gained a TEXT-cycled information
panel (Lyrics/Metadata/Codec) and a Previous/Next queue preview.

Verified via an extended stub environment first, then through 9
rounds of real device testing across two Enigma2 receivers (OpenViX,
OpenATV, including a VU+ Duo2 with a different remote), confirmed
complete by the user. HELP and TEXT's real action names ("displayHelp"
and "subtitles" respectively) were confirmed from a full static
ActionMap context dump partway through testing, the same technique
that eventually resolved RADIO/CH+/CH-/INFO in Build 0007. Device
testing also drove two substantial playback-position correctness
fixes that had nothing to do with the build's three headline features
directly: a GStreamer race condition where a fresh service could
report a stale position left over from whatever played previously
(affecting elapsed-time display, Automatic Next Track timing, and
seek accuracy alike), and a related seek-chain corruption bug from
re-querying GStreamer immediately after a seek, while it was still
mid-flush. Both were root-caused from device-log evidence rather than
patched by symptom.

No architectural changes; extends the Core and Screen Layers
established in Build 0004, following the same "extends existing
modules without changing the established layered architecture"
principle every build since Build 0005 has followed.

Closing note (device test round 9): user confirmed all three headline
features working correctly, including scrolling lyrics display (added
mid-testing per user request: a windowed view centered on "now,"
computed from real .lrc timestamps when available or proportionally
from track position otherwise) and the Music Library folder picker
(added to Settings after the user pointed out Browser already had
one). Two items left deliberately as known, low-priority behaviour
rather than further fixes: the unsynchronized-lyrics scroll window
could show more lines than the synchronized one does, and TEXT (like
INFO before its round-8 fix) fires on both press and release on at
least one remote -- confirmed far less disruptive for a three-state
cycle than it was for INFO's two-state toggle, and the user confirmed
it already works correctly in practice. See CHANGELOG.md's "BUILD
0008 -- CONFIRMED COMPLETE" section and Claude_notes_build0008.txt for
the full, round-by-round record.

---

Build 0009

MainScreen 2.0 & Radio EPG.

The largest single-build change in the project's history: a full
MainScreen redesign around three navigable panels (Player/Playlist/
Information, cycled via EPG/INFO, replacing Build 0008's TEXT-cycled
info view and INFO's old seek/favorites view-mode toggle entirely),
plus a new Core module (InformationPanel) that builds each panel's
page list dynamically from whatever the current track or station
actually has -- Lyrics/Metadata/Codec for local files, Radio EPG/Now
Playing/Station/Codec for Internet Radio -- rather than a fixed cycle.

Alongside the UI redesign, two new EPG data-source providers back the
Radio EPG/Now Playing pages for Finnish radio specifically: a Yle
Teksti-TV-based EPGScheduleProvider (the only Yle API still open to
the public; their purpose-built programme API was deprecated in 2021)
and a Bauer Media/Rayo NowPlayingProvider (reverse-engineered from a
Next.js page's own embedded state, since Bauer publishes no API at
all) -- together covering 5 Yle and 18 Bauer stations, matched to
whatever real station the user actually plays by a new
finland_radio_epg_registry module (RadioBrowser identifies stations by
an opaque stationuuid this project has no way to know in advance, so
matching is done by normalized station name instead).

Verified via the stub environment first, then through 13 rounds of
real device testing (initially OpenViX, later confirmed additionally
against OpenPLI, OpenATV and OpenBH in a single closing multi-image
round) -- by far the most extensive device-testing history of any
build so far, and the first to catch a crash that reached production
testing at all: two of the new skin's own XML comments used "--" as
prose punctuation, which is illegal anywhere inside an XML comment
except its own closing "-->" -- Python itself never catches this (a
malformed-XML string still compiles and runs fine until Enigma2's own
skin.py actually parses it), so this is now standard practice for any
future skin change: parse the generated string with
xml.etree.ElementTree before shipping it, not just python's own
py_compile. A second crash (this one working around the first fix)
came from using onLayoutFinish for a cover-art timing race, replaced
with the project's own already-proven eTimer-based deferral pattern
instead of a second unverified Enigma2 API in a row.

Device testing also found and root-caused two long-standing but
previously invisible bugs unrelated to Build 0009's own headline
features: compatibility.py's getStreamInfo() had never actually
worked since Build 0005 introduced it (the iServiceInformation
constants it queried don't exist at all on real hardware for
GStreamer-based file/stream playback, confirmed via added diagnostic
logging -- worked around with a computed fallback, file size/duration
for local files and RadioBrowser's own station metadata for streams),
and pause() had no Internet-Radio-specific handling at all --
pressing OK/PAUSE on a live stream stopped it outright rather than
truly pausing it, leaving MediaPlayer3's own state stuck showing
"paused" against an already-dead service with no way back. Both fixes
came directly from device-log evidence, not by symptom.

No changes to the layered architecture itself; InformationPanel and
finland_radio_epg_registry are new Core modules following the same
pattern every Core module before them has (Screens never talk to a
data source directly), and MainScreen's panel system extends rather
than replaces the Screen Layer established in Build 0004.

Closing note (multi-image device test round, OpenViX/OpenPLI/OpenATV/
OpenBH): user confirmed Build 0009's goals achieved across all four
tested images, with zero crashes in any of the four logs. One
station-matching gap found in that same round (Yle Vega's real
RadioBrowser name includes "radio" between "Yle" and "Vega", plus a
regional suffix, which the existing pattern never accounted for -- a
second, related gap for Bauer's Radio Nostalgia listed without its
"Radio" prefix was found and fixed in the same pass) was fixed
immediately rather than deferred, since the underlying registry
module already existed and the fix was a same-shape, low-risk pattern
addition. Bauer Media's Radio Nova and SuomiRock streams remain
confirmed unreliable on at least one tested image regardless of
playback backend (both GStreamer and ExtEplayer3 were tried; both
fail the same way for these two specific streams, pointing at a
server/stream-side cause outside what either backend or this plugin
can route around) -- accepted as a known limitation of those specific
streams rather than a MediaPlayer3 defect. See CHANGELOG.md's "BUILD
0009 -- CONFIRMED COMPLETE" section and Claude_notes_build0009.txt for
the full, round-by-round record.

---

Build 0010

Three-column browsing, File Browser redesign, and a full visual
redesign.

The first ~19 rounds extended the three-panel navigation model Build
0009 established for MainScreen to Podcasts and the file Browser (a
full redesign of the latter around it), added a local, offline-capable
RadioBrowser station database (manual and automatic updates), a
bundled default Podcast Index/Yle Teksti-TV API key pair (obfuscated,
always overridable by the user's own key), Light/Dark themes via the
existing SkinManager/Theme system, MainScreen's own OK Menu, and
Enigma2 main menu integration. Confirmed across 19 rounds of device
testing (OpenViX and Vu+ Duo2), with two previously-invisible bugs
found and fixed as a side effect (a podcast episode URL silently
failing a local-file-assuming playlist check; every panel screen's
column-header highlight colours never actually varying by theme,
since the keys involved were never defined in any theme file) and one
real crash (a missing import, fixed the same session reported).

Starting from a user-provided mockup shortly after, a much larger
second phase (47 further rounds) replaced the OLD SkinManager/Theme-
driven appearance entirely for every one of MediaPlayer3's eight
screens with a new background-image system: pre-rendered PNG cards
(rounded corners, colour-coded active/inactive panel headers) behind
real, translatable text widgets, with matching Light/Dark palettes and
HD/SD resolution tiers. The mechanism was proven on Music Library
first (async decode via ePicLoad, confirmed only that API -- not a
static Pixmap's own `pixmap=` attribute -- actually scales a
mismatched source image) and then reused, with only cosmetic
adjustments per screen (icon set, column count, hint-row wording), for
Internet Radio, the file Browser, Podcasts, Playlists, the Main
Player, the Main Menu, and finally Settings. MainScreen and Settings
each gained an information display that didn't exist before (Now
Playing details; a per-selection description panel).

Two real bugs surfaced during this second phase that had nothing to
do with the redesign's own visual goals: a concurrent background-
image decode race (ePicLoad only supports one decode per instance at
a time; a slow enough decode could overlap with a screen's own
periodic refresh and fail outright -- confirmed directly from a
device log's own "startDecode() reported failure"), and a widget
insertion-order bug specific to Settings (its own background image
painted over the config list's text instead of underneath it, because
ConfigListScreen's own __init__() -- which creates the list widget
internally -- ran before the background widget was created, the
opposite of every other screen's own correct order). Both were
root-caused directly from device-log evidence and a user-run
diagnostic build, not guessed at from symptoms alone. Two crashes
reached a device during this stretch (both from import cleanup
mistakes made while simplifying a screen's own dependencies after its
redesign), both fixed the same session reported.

The build closes with MediaPlayer3 defaulting to the receiver's own
current Enigma2 system language automatically (a new "System" choice
replacing the previous always-Finnish default, resolved fresh every
time the language is actually applied rather than fixed once at
install), and a corrected bitbake recipe added to the project (its
own LIC_FILES_CHKSUM didn't match the project's actual LICENSE file,
which would have failed a real build's own license QA check).

No changes to the layered architecture itself -- the new background-
image system is a Screen Layer concern (each screen's own skin
generation and widget wiring), and doesn't introduce, remove, or
restructure any Core module. See CHANGELOG.md's two "BUILD 0010"
closing notes and Claude_notes_build0010.txt for the full, round-by-
round record.

---

# 4. Major Architecture Decisions

MainScreen

Decision

MainScreen replaces BrowserScreen as the primary application window.

Reason

Playback becomes the central function of the application.

BrowserScreen is used only when media selection is required.

---

BrowserScreen

Decision

BrowserScreen becomes a temporary screen.

Reason

Separates media browsing from playback.

Simplifies navigation.

Reduces screen responsibilities.

---

Platform Abstraction Layer

Decision

Platform-specific functionality is isolated inside Compatibility.

Reason

Improves portability.

Reduces platform-dependent code.

Simplifies future OpenATV and OpenViX support.

---

Configuration Manager

Decision

Configuration is centralized in config.py.

Reason

Provides a single public configuration interface.

Supports future configuration migration.

Improves maintainability.

---

Developer Tools

Decision

Developer functionality is separated from normal user settings.

Reason

Keeps the user interface simple.

Provides powerful diagnostics without affecting normal users.

---

Playback Queue

Decision

PlaybackController owns the Playback Queue once BrowserScreen hands it
over; BrowserScreen never participates in playback navigation
afterwards.

Reason

Keeps playback independent of Browser navigation -- BrowserScreen can
close while playback continues.

Matches the existing rule that Controllers own business logic and
Screens own presentation/browsing only.

Expected benefit

Previous/Next Track and Automatic Next Track work identically
regardless of whether BrowserScreen is open.

Affected modules

PlaybackController, BrowserScreen.

Related Build

Build 0005.

---

Skin/Theme Scope

Decision

SkinManager provides skin metadata, compatibility validation and
theme (colour) support, but not fully external, alternate-*layout*
skin files -- Screens continue to generate their own skin XML in
Python.

Reason

Genuine alternate-layout skin support would mean every Screen's
widget positions becoming externally overridable, a much larger
architectural change than Build 0006's "extends existing modules
without changing the established layered architecture" principle
calls for.

Expected benefit

Real, working skin compatibility validation (with automatic fallback)
and full theme support land in Build 0006 without the risk of a
much larger, untested layout-override rewrite.

Affected modules

SkinManager, MainScreen.

Related Build

Build 0006.

---

Metadata Ownership

Decision

PlaybackController owns the metadata cache (populated by calling
metadata.py's read() in play()); Screens only ever read cached
metadata through PlaybackController, never call metadata.py directly.

Reason

Matches the Controller Independence principle: Screens display,
Controllers own state and coordinate Core modules.

Expected benefit

Metadata is parsed exactly once per track (in play()), not once per
Screen that wants to display it, and a metadata-related bug can never
reach the point of affecting playback startup, since read() itself
never raises and play() wraps the call again regardless.

Affected modules

PlaybackController, MainScreen, PlaybackInfoScreen, DeveloperScreen.

Related Build

Build 0006.

---

BrowserScreen Context Menu Key Binding

Decision

The Build 0007 playlist/folder context menu (Play Folder/Add to
Playlist/Create Playlist/etc.) is bound to INFO, not OK.

Reason

OK's existing descend-into-folder / play-file behaviour is verified
across several real Build 0005/0006 device test rounds (queue
building, basename matching, etc.) and must not change. INFO was
unbound in BrowserScreen before this and reads naturally as "more
options about the selected item". Matches user guidance to avoid
colour buttons where a more natural key is available.

Expected benefit

The new playlist features become reachable without any risk of
regressing already-verified navigation, and without spending a colour
button on it.

Affected modules

BrowserScreen.

Related Build

Build 0007.

---

Internet Radio Navigation Key Reuse

Decision

MainScreen's LEFT/RIGHT/UP/DOWN keys gain a second meaning (station/
list navigation) while playing an Internet Radio stream, instead of
adding new dedicated keys or a colour button.

Reason

Seeking (LEFT/RIGHT/FF/RW's existing meaning) is meaningless for a
live radio stream, so there is no real conflict -- a given playback
session is always either a stream or a local file, gated on
PlaybackController.isPlayingStream(). Matches user guidance to avoid
colour buttons where possible.

Expected benefit

Radio station browsing works from MainScreen without RadioBrowserScreen
needing to stay open, and without consuming any additional physical
keys.

Affected modules

MainScreen, PlaybackController.

Related Build

Build 0007.

---

# 5. Development Principles

MediaPlayer3 follows these principles:

- One responsibility per module.
- Controllers contain business logic.
- Screens contain user interface logic.
- Core modules provide shared services.
- Platform-specific code is isolated.
- Public interfaces remain stable whenever practical.

These principles guide future development.

---

# 6. Future History Entries

Future architectural decisions should include:

Decision

Reason

Expected benefit

Affected modules

Related Build number

This allows future developers to understand why changes were made.

---

# 7. End Goal

The long-term goal of MediaPlayer3 is to provide a modern, modular and
maintainable media player for Enigma2.

Architecture should remain understandable, extensible and well
documented.

Every major architectural decision should be recorded in this document.

---

# End of File

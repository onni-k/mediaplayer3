# ==============================================================================
#
# MediaPlayer3
#
# File        : compatibility.py
#
# Description :
#
#     Platform Abstraction Layer (PAL)
#
#     Provides a unified interface between MediaPlayer3 and different
#     Enigma2 distributions.
#
# Implements :
#
#     COMPATIBILITY_SPEC.md v0.1
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
# 2026-07-10  Build 0003
#   - Initial Platform Abstraction Layer.
#
# 2026-07-12  Build 0004
#   - hasDeveloperMode() now reflects the real "developer.developer_mode"
#     configuration value instead of an always-False placeholder, so
#     DeveloperScreen and Logger can rely on it.
#
# 2026-07-13  Build 0004
#   - Added createFileList(): centralizes Components.FileList.FileList
#     construction here, trying a richer parameter set first and
#     falling back to a minimal, known-safe one -- browserscreen.py no
#     longer constructs FileList() itself or hardcodes a parameter set
#     that might not exist on every image.
#   - Added getPvrKeyActionNames(): single source of truth for the PVR
#     remote key's candidate ActionMap action names, previously
#     duplicated in mainscreen.py and browserscreen.py.
#
# 2026-07-14  Build 0005
#   - Added getPlaybackPosition(): elapsed/duration via the current
#     service's iSeekableService, for MainScreen's progress bar and
#     PlaybackController's progress reporting. Defensive against both
#     observed return shapes ((error_code, pts) tuple and raw pts).
#   - Added getStreamInfo(): best-effort codec/sample-rate/bitrate/
#     channels via iServiceInformation, for DeveloperScreen's Playback
#     Statistics. Each field is independently guarded; not yet
#     confirmed against a real device (see docs/Claude_notes_build0005.txt).
#
# 2026-07-16  Build 0005 (device test round 2)
#   - Added seekRelative(): FASTFORWARD/REWIND/LEFT/RIGHT had no
#     effect at all (Enigma2 showed its native "unhandled key"
#     indicator) because no seeking was implemented in the initial
#     Build 0005 release. Added SEEK_FORWARD_KEY_ACTIONS /
#     SEEK_BACKWARD_KEY_ACTIONS candidate lists, same pattern as the
#     PVR/Next/Previous key fixes.
#
# 2026-07-17  Build 0005 (device test rounds 3-5)
#   - Added connectPictureDataSignal() for MainScreen's cover art
#     decoding, upgraded to a 3-way check (.connect() /
#     .get().append() / plain .append()) matching a confirmed-working
#     reference implementation found in mediaplayer2's compat.py
#     (eConnectCallback()) and YampMusicPlayer's own dpkg-detection
#     fallback -- both checked per user request (see
#     docs/Claude_notes_build0005.txt).
#
# 2026-07-24  Build 0007
#   - Added RADIO_KEY_ACTIONS (toggle Internet Radio/local playback)
#     and CHANNEL_UP_KEY_ACTIONS/CHANNEL_DOWN_KEY_ACTIONS (page-jump
#     through a list), same candidate-list pattern as the earlier
#     PVR/Next/Previous/Seek key fixes. Not yet confirmed against a
#     real device.
#
# 2026-07-24  Build 0007 (device test round 4)
#   - CONFIRMED via a full raw eActionMap/InfoBarGenerics log: RADIO's
#     real action name is "RADIO" (uppercase; round 2's guesses were
#     all lowercase-style, hence the "unhandled key" indicator on
#     round 2). CH+/CH-'s real action names are "BOUQUET+"/"BOUQUET-"
#     (round 2/3's guesses, including "nextBouquet"/"prevBouquet",
#     never matched). Confirmed names moved to the front of each
#     candidate list.
#
# 2026-07-24  Build 0007 (device test round 6)
#   - Added INFO_KEY_ACTIONS: OpenATV on a VU+ remote has no physical
#     INFO button at all -- EPG substitutes for it (KEY_EPG, not
#     KEY_INFO). All screens now bind the same set of candidate action
#     names for both the real INFO key and its EPG substitute.
#
# 2026-07-24  Build 0007 (device test round 7)
#   - Round 6's fix still didn't work on OpenATV. A fresh device log
#     confirmed KEY_EPG events kept arriving but no
#     "[MainScreen] INFO pressed." line ever followed, even with
#     "showEventInfoPlugin" registered. The same context dump shows
#     "InfobarEPGActions" defines TWO actions for KEY_EPG:
#     "EPGPressed" and "showEventInfoPlugin". Added "EPGPressed" as a
#     further candidate.
#
# 2026-07-25  Build 0007 (device test round 8)
#   - Added getDesktopSize(): shared by every Screen's fullscreen skin
#     computation (previously only MainScreen was fullscreen; Build
#     0007 device test round 8 extends this to every screen).
#
# 2026-07-28  Build 0008
#   - Added HELP_KEY_ACTIONS/getHelpKeyActionNames() for the new
#     HelpScreen/HelpManager. PROVISIONAL, unverified on real
#     hardware -- expect this to need correction via real device
#     eActionMap log evidence, the same way RADIO/CH+/CH-/INFO did in
#     Build 0007.
#   - Added TEXT_KEY_ACTIONS/getTextKeyActionNames() for MainScreen's
#     new information panel cycling. Also PROVISIONAL/unverified.
#
# 2026-07-29  Build 0008 (device test round 2)
#   - An OpenATV log's full static ActionMap context dump confirmed
#     the real action names for both keys: HELP is "displayHelp"
#     ("HelpActions" was right, "HELP" as the action name was wrong).
#     TEXT is "subtitles" via "MediaPlayerActions" (already a
#     confirmed-active MainScreen context). Confirmed names moved
#     first in both tuples.
#
# 2026-08-01  Build 0008 (device test round 7)
#   - Added seekTo(): absolute seek (iSeekableService.seekTo(pts))
#     alongside the existing relative seek. A device log proved
#     seeking relative to GStreamer's own reported position is unsafe
#     when that position can itself be stale (rounds 1-6): GStreamer
#     had gotten stuck reporting a position near the end of a 231s
#     track while the track was genuinely only ~84s in, and a "+30s"
#     relative seek request landed at (stale)231 + 30 = 261 -- past
#     the end of the track. PlaybackController now seeks to an
#     absolute target computed from its own trusted position instead.
#
# 2026-08-02  Build 0009 (planning -- EPGManager preparation)
#   - Added getStreamTags(): "now playing" info (artist/title) for the
#     current Internet Radio stream, following getStreamInfo()'s exact
#     per-field-safe iServiceInformation pattern -- sTagTitle/
#     sTagArtist/sTagOrganization instead of sAudioType/sSampleRate/
#     etc, read via getInfoString() instead of getInfo(). This is
#     ICY/Shoutcast stream metadata (a station's live "StreamTitle"),
#     already parsed by GStreamer and exposed through the same service
#     tag interface -- not every station provides it, so an all-
#     "Unknown" result is an expected, normal outcome.
# ------------------------------------------------------------------------------

from __future__ import annotations

import os
import platform
import sys
from typing import Any, Dict, Optional

from .logger import logger


class Compatibility:
    """
    Platform Abstraction Layer.

    This class hides platform-specific implementation details from the
    rest of MediaPlayer3.
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.3"

    # ------------------------------------------------------------------
    # Remote control action names
    # ------------------------------------------------------------------
    #
    # Enigma2's keymap.xml (part of the remote-control profile, not the
    # Python API) decides which ActionMap action name a physical key
    # fires. This cannot be probed at runtime the way a Python import
    # can -- there is no "does this action name exist" check. The safe
    # approach is to bind every plausible candidate name to the same
    # handler; this tuple is the single source of truth for that list,
    # so mainscreen.py and browserscreen.py don't each hardcode it.
    #
    # "showMovies" is PVR's standard action name in Enigma2's core
    # keymap.xml; "showInfobar" was kept as a second candidate after a
    # real device test showed the PVR key having no effect with only
    # "showInfobar" bound.
    PVR_KEY_ACTIONS = ("showMovies", "showInfobar")

    # A real device test (see docs/Claude_notes_build0005.txt) showed
    # that pressing this remote's track-skip buttons (physically
    # labelled/behaving as KEY_FASTFORWARD and KEY_NEXT, the latter
    # bound to 'ARROWRIGHT') produced no ActionMap match at all with
    # only "next"/"previous" bound -- i.e. neither is this keymap's
    # actual action name for those keys. "nextBouquet"/"prevBouquet"
    # are Enigma2's core keymap.xml action names for KEY_NEXT/
    # KEY_PREVIOUS specifically in the "InfobarActions" context, which
    # MainScreen already includes, so they are added here as further
    # candidates alongside the more MediaPlayerActions-style names.
    NEXT_TRACK_KEY_ACTIONS = ("next", "skip_forward", "nextBouquet")
    PREVIOUS_TRACK_KEY_ACTIONS = ("previous", "skip_back", "prevBouquet")

    # Seek within the current track (FASTFORWARD/REWIND remote keys).
    # Enigma2's core keymap.xml commonly binds these in an
    # "InfobarSeekActions" context to "seekFwd"/"seekBack" (long-press
    # variants "seekFwdManual"/"seekBackManual"); "fastforward"/
    # "rewind" are kept as further candidates for images/skins that
    # use MediaPlayerActions-style naming instead. Not yet confirmed
    # against a real device -- see docs/Claude_notes_build0005.txt.
    SEEK_FORWARD_KEY_ACTIONS = ("seekFwd", "seekFwdManual", "fastforward")
    SEEK_BACKWARD_KEY_ACTIONS = ("seekBack", "seekBackManual", "rewind")

    # RADIO remote key (toggles between Internet Radio and local
    # playback, Build 0007).
    #
    # Device test round 4: a fuller log (with raw eActionMap/
    # InfoBarGenerics key-resolution lines, the same kind that
    # confirmed the PVR/Next/Previous key fixes) showed the real
    # binding: "KeyID='KEY_RADIO' Binding='('RADIO',)'." -- i.e. the
    # actual action name is "RADIO" (uppercase), not any of the
    # lowercase-style names guessed in round 2 ("radio"/"keyRadio"/
    # "toggleRadio"), which is also why the round-2 device test showed
    # Enigma2's native "unhandled key" indicator for RADIO. Confirmed
    # candidate moved first; the earlier guesses are kept as further
    # candidates for other images/skins that may name it differently.
    RADIO_KEY_ACTIONS = ("RADIO", "radio", "keyRadio", "toggleRadio")

    # INFO remote key -- used throughout MediaPlayer3's screens for
    # "show more options/information".
    #
    # Device test round 6: OpenATV on a VU+ remote has NO physical
    # INFO button at all -- EPG substitutes for it, generating
    # KEY_EPG rather than KEY_INFO. A device log's static context dump
    # (round 5's test4_openatv.log) showed KEY_EPG resolving via the
    # "InfobarEPGActions" context to action "showEventInfoPlugin" (and
    # KEY_INFO to "InfoPressed"/"showEventInfoPlugin" there too, or
    # plain "info" via the "InfoActions" context already in use).
    # "showEventInfo" is kept as a candidate too since some contexts
    # (e.g. "ChannelSelectInfoActions") bind KEY_INFO to it. Screens
    # bind ALL of these to the same handler and add
    # "InfobarEPGActions" to their context list so the EPG substitute
    # is reachable too.
    #
    # Device test round 7: round 6's fix still didn't work on OpenATV
    # -- a fresh device log confirmed KEY_EPG events kept arriving
    # (InfoBarGenerics logged every Make/Break) but no
    # "[MainScreen] INFO pressed." line ever followed, even with
    # "showEventInfoPlugin" registered. The SAME context dump shows
    # "InfobarEPGActions" actually defines TWO actions for KEY_EPG:
    # "EPGPressed" and "showEventInfoPlugin" -- added "EPGPressed" as
    # a further candidate, since Enigma2 appears to resolve to
    # whichever of a key's multiple bound actions is checked, not
    # necessarily the one this plugin already registered.
    INFO_KEY_ACTIONS = ("showEventInfo", "info", "showEventInfoPlugin", "InfoPressed", "EPGPressed")

    # HELP remote key -- new in Build 0008 (HelpScreen/HelpManager).
    #
    # Device test round 2: an OpenATV log's full static ActionMap
    # context dump CONFIRMED the real action names -- "HelpActions"
    # (my round-1 context guess) genuinely exists and is genuinely
    # correct, but the action name within it is "displayHelp" (and
    # "displayHelpLong" for a long press), NOT "HELP". This explains
    # round 1's failure completely: the confirmed KeyID='KEY_HELP'
    # Binding='('HELP',)' line was InfoBarGenerics' own internal
    # resolution table, not proof of what any particular ActionMap
    # context actually defines the key as -- the same distinction
    # that took several rounds to work out for RADIO/CH+/CH- in
    # Build 0007. Confirmed names moved first; "help" (lowercase) is
    # kept since the same dump also showed a "YampHelpActions"
    # context using it, and "showHelp"/"keyHelp" are kept as further
    # candidates for other images/skins.
    HELP_KEY_ACTIONS = ("displayHelp", "displayHelpLong", "HELP", "help", "showHelp", "keyHelp")

    # TEXT remote key -- new in Build 0008 (MainScreen information
    # panel cycling: Lyrics/Metadata/Codec).
    #
    # Device test round 2: the same OpenATV context dump showed
    # KEY_TEXT resolves to a different action in nearly every context
    # that defines it at all (over a dozen). "MediaPlayerActions" ->
    # "subtitles" is used here specifically because "MediaPlayerActions"
    # is already a confirmed-active context in MainScreen's own
    # ActionMap (used for PLAY/PAUSE/STOP) -- the most likely context
    # to actually apply, unlike the many others in the dump that
    # belong to unrelated screen types (EPG, DVD player, Teletext,
    # movie lists, etc.) MediaPlayer3 never opens. "text"/"TEXT" kept
    # as further candidates for other images/skins.
    TEXT_KEY_ACTIONS = ("subtitles", "text", "TEXT", "showText", "keyText")

    # CHANNEL UP/DOWN remote keys (page-jump through a list, Build
    # 0007).
    #
    # Device test round 4: the same fuller log showed the real
    # bindings: "KeyID='KEY_CHANNELUP' Binding='('BOUQUET+',)'." and
    # "KeyID='KEY_CHANNELDOWN' Binding='('BOUQUET-',)'." -- i.e. the
    # actual action names are "BOUQUET+"/"BOUQUET-", not any of the
    # round-2/round-3 guesses ("channelUp"/"chup"/"zapUp"/
    # "prevBouquet"/etc., none of which ever matched -- round 3's
    # device log showed zero "[RadioBrowser] CH+/CH- pressed." lines
    # for any of them). Confirmed candidates moved first; the earlier
    # guesses are kept as further candidates for other images/skins.
    CHANNEL_UP_KEY_ACTIONS = ("BOUQUET+", "channelUp", "keyChannelUp", "chup", "zapUp", "prevBouquet")
    CHANNEL_DOWN_KEY_ACTIONS = ("BOUQUET-", "channelDown", "keyChannelDown", "chdown", "zapDown", "nextBouquet")

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._platform_name = "Unknown"

        self._python_version = platform.python_version()

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _initialize(self) -> None:
        """Initialize compatibility layer."""

        self._log("Initializing")

        self._detectPlatform()

        self._initialized = True

        self._log(f"Detected platform: {self._platform_name}")

        self._log("Ready")

    # ------------------------------------------------------------------

    def _detectPlatform(self) -> None:
        """
        Detect the current platform.

        Build 0003 performs only basic detection.
        """

        self._platform_name = platform.system()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Compatibility] %s", message)

# End of Part 1
    # ------------------------------------------------------------------
    # Feature Detection
    # ------------------------------------------------------------------

    def hasNavigationInstance(self) -> bool:
        """
        Check whether NavigationInstance is available.
        """

        try:
            import NavigationInstance  # noqa: F401

            return True

        except ImportError:
            return False

    # ------------------------------------------------------------------

    def hasServiceEventTracker(self) -> bool:
        """
        Check whether ServiceEventTracker is available.
        """

        try:
            from Components.ServiceEventTracker import ServiceEventTracker  # noqa: F401

            return True

        except ImportError:
            return False

    # ------------------------------------------------------------------

    def hasBoxInfo(self) -> bool:
        """
        Check whether BoxInfo support is available.
        """

        try:
            from Components.SystemInfo import BoxInfo  # noqa: F401

            return True

        except (ImportError, AttributeError):
            return False

    # ------------------------------------------------------------------

    def hasServiceCenter(self) -> bool:
        """
        Check whether eServiceCenter is available.
        """

        try:
            from enigma import eServiceCenter  # noqa: F401

            return True

        except ImportError:
            return False

    # ------------------------------------------------------------------

    def hasServiceReference(self) -> bool:
        """
        Check whether eServiceReference is available.
        """

        try:
            from enigma import eServiceReference  # noqa: F401

            return True

        except ImportError:
            return False

    # ------------------------------------------------------------------

    def hasPython313(self) -> bool:
        """
        Check whether Python 3.13 or newer is running.
        """

        return sys.version_info >= (3, 13)

    # ------------------------------------------------------------------

    def hasDeveloperMode(self) -> bool:
        """
        Return whether Developer Mode is currently enabled.

        Imported lazily to avoid a module-load-order dependency between
        compatibility.py and config.py (both are imported very early by
        other Core modules).
        """

        try:
            from .config import config_manager

            return config_manager.isDeveloperMode()

        except Exception:
            return False

    # ------------------------------------------------------------------

    def getPvrKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the PVR remote
        key, in preference order. See PVR_KEY_ACTIONS above.
        """

        return self.PVR_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getNextTrackKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the Next Track
        remote key, in preference order. See NEXT_TRACK_KEY_ACTIONS
        above.
        """

        return self.NEXT_TRACK_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getPreviousTrackKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the Previous
        Track remote key, in preference order. See
        PREVIOUS_TRACK_KEY_ACTIONS above.
        """

        return self.PREVIOUS_TRACK_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getSeekForwardKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the Seek
        Forward remote key, in preference order. See
        SEEK_FORWARD_KEY_ACTIONS above.
        """

        return self.SEEK_FORWARD_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getSeekBackwardKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the Seek
        Backward remote key, in preference order. See
        SEEK_BACKWARD_KEY_ACTIONS above.
        """

        return self.SEEK_BACKWARD_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getRadioKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the RADIO
        remote key, in preference order. See RADIO_KEY_ACTIONS above.
        """

        return self.RADIO_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getInfoKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the INFO
        remote key (or its EPG substitute on remotes with no physical
        INFO button), in preference order. See INFO_KEY_ACTIONS above.
        """

        return self.INFO_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getHelpKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the HELP
        remote key, in preference order. See HELP_KEY_ACTIONS above --
        PROVISIONAL, unverified on real hardware (Build 0008).
        """

        return self.HELP_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getTextKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the TEXT
        remote key, in preference order. See TEXT_KEY_ACTIONS above --
        PROVISIONAL, unverified on real hardware (Build 0008).
        """

        return self.TEXT_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getDesktopSize(self, fallback_width, fallback_height):
        """
        Return (width, height) of the actual display, or
        (fallback_width, fallback_height) if it can't be determined.

        Build 0007, device test round 8: every Screen is now
        fullscreen (getDesktop(0).size(), following the pattern
        MainScreen established in Build 0005 for the same reason --
        so the box's own background never shows through around a
        small centered window). Shared here instead of each Screen
        importing `enigma.getDesktop` and duplicating the same
        try/except, per ARCHITECTURE.md's "all platform-variant code
        in compatibility.py" convention.
        """

        try:
            from enigma import getDesktop

            size = getDesktop(0).size()

            return size.width(), size.height()

        except Exception as error:

            logger.warning("[Compatibility] Unable to determine desktop size, using design resolution: %s", error)

            return fallback_width, fallback_height

    # ------------------------------------------------------------------

    def getChannelUpKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the CHANNEL UP
        remote key, in preference order. See CHANNEL_UP_KEY_ACTIONS
        above.
        """

        return self.CHANNEL_UP_KEY_ACTIONS

    # ------------------------------------------------------------------

    def getChannelDownKeyActionNames(self):
        """
        Return the candidate ActionMap action names for the CHANNEL
        DOWN remote key, in preference order. See
        CHANNEL_DOWN_KEY_ACTIONS above.
        """

        return self.CHANNEL_DOWN_KEY_ACTIONS

# End of Part 2
    # ------------------------------------------------------------------
    # Platform Adapter
    # ------------------------------------------------------------------

    def getNavigationInstance(self):
        """
        Return the global NavigationInstance.

        Returns:
            NavigationInstance instance or None.
        """

        try:
            import NavigationInstance

            return NavigationInstance.instance

        except (ImportError, AttributeError):
            self._log("NavigationInstance not available.")
            return None

    # ------------------------------------------------------------------

    def isExtEplayer3Available(self) -> bool:
        """
        Build 0009, device test round 12: purely a filesystem check
        for the ExtEplayer3 binary at its consistent, well-established
        install location -- confirmed across many independent sources
        (Enigma2 IPTV plugin forum threads, an openhdf install script)
        that /usr/bin/exteplayer3 is where every packaging of it
        (opkg install exteplayer3) puts the binary, regardless of
        image. Deliberately doesn't touch any Enigma2-internal API
        (unlike the rest of this class) to stay maximally safe -- used
        only to show an informational "is this installed" hint in
        Settings (cfg.radio.use_exteplayer3's own entry), per user
        request ("Asetuksissa voisi olla ilmoitus, etta onko
        serviceapp asennettu"), never to block or change behaviour.
        """

        return os.path.exists("/usr/bin/exteplayer3")

    # ------------------------------------------------------------------

    def createServiceReference(self, filename: str, use_exteplayer3: bool = False):
        """
        Create an Enigma2 service reference.

        Args:
            filename: File path or stream URL.
            use_exteplayer3: Build 0009, device test round 11 -- use
                service type 5002 (ExtEplayer3, FFmpeg-based) instead
                of the default GStreamer-based type. Requested after a
                real device log showed specific Internet Radio streams
                (Bauer Media's Radio Nova/SuomiRock) repeatedly
                failing with "Gstreamer error: Not Found (3) from
                source" / "Stream doesn't contain enough data" during
                GStreamer's own automatic reconnect handling, with no
                equivalent failure from anything MediaPlayer3 itself
                triggered. Multiple independent sources (several
                Enigma2 forum threads, and directly, a GitHub issue on
                openatv/enigma2 showing the identical "Gstreamer
                error: ... from hlsdemux0" resolved by switching the
                exact same stream from service type 4097 to 5002)
                confirm this is a known, recurring class of issue with
                a known workaround, not something specific to this
                plugin's own code. Not verified against this specific
                real device yet -- requires ExtEplayer3 to actually be
                installed (it depends on FFmpeg, not guaranteed
                present on every image); if it isn't, service
                creation/playback simply fails the same way an
                invalid reference always did, with no worse outcome
                than not having this option at all.

        Returns:
            eServiceReference instance or None.
        """

        try:
            from enigma import eServiceReference

            #
            # Build 0003
            #
            # Service type 4097 is the long-standing, portable service
            # type for local audio file playback in Enigma2 -- it is
            # what eServiceFactoryMP3 (and, on GStreamer-based images,
            # eServiceFactoryGStreamer) registers itself under. Not
            # every image exposes a named eServiceReference.idGST /
            # idServiceMP3 attribute for it (this OpenViX 6.8 build
            # does not -- it only registers eServiceFactoryMP3), so we
            # use the numeric type directly and only prefer a named
            # attribute when the image actually provides one.
            #
            SERVICE_TYPE_AUDIO = 4097

            # Build 0009 -- ExtEplayer3's own well-established numeric
            # service type (confirmed via multiple independent real-
            # world references, e.g. "#SERVICE 5002:0:1:3:..." in the
            # openatv/enigma2 GitHub issue cited above). No named
            # eServiceReference attribute is commonly exposed for this
            # one either, so the numeric type is used directly, same
            # reasoning as SERVICE_TYPE_AUDIO above.
            SERVICE_TYPE_EXTEPLAYER3 = 5002

            if use_exteplayer3:

                service_type = SERVICE_TYPE_EXTEPLAYER3

            else:

                service_type = getattr(
                    eServiceReference, "idGST", SERVICE_TYPE_AUDIO
                )

            reference = eServiceReference(
                service_type,
                0,
                filename,
            )

            return reference

        except Exception as error:
            self._log(
                f"Unable to create service reference: {error}"
            )

            return None

    # ------------------------------------------------------------------

    def createFileList(self, directory: str, showDirectories: bool = True, showFiles: bool = True):
        """
        Create a Components.FileList.FileList instance for `directory`.

        Different Enigma2 images/versions support different FileList()
        constructor keyword arguments (a real device build 0004 crash
        was caused by passing `hideExtensionsInFilelist`, which this
        image's FileList does not accept). This method tries a richer
        parameter set first and falls back to progressively simpler
        ones on TypeError, so BrowserScreen never has to know or guess
        which parameters this image's FileList supports.

        Returns:
            FileList instance. Never raises for a signature mismatch;
            only re-raises if even the minimal, two-argument form
            fails (e.g. `directory` does not exist).
        """

        from Components.FileList import FileList

        attempts = (
            dict(
                directory=directory,
                showDirectories=showDirectories,
                showFiles=showFiles,
                showMountpoints=True,
                hideExtensionsInFilelist=False,
            ),
            dict(
                directory=directory,
                showDirectories=showDirectories,
                showFiles=showFiles,
                showMountpoints=True,
            ),
            dict(
                directory=directory,
                showDirectories=showDirectories,
                showFiles=showFiles,
            ),
        )

        for kwargs in attempts:

            try:
                return FileList(**kwargs)

            except TypeError as error:

                self._log(f"FileList() does not accept {list(kwargs)}: {error}")

                continue

        # Last resort: the minimal, positional-only form every known
        # FileList implementation accepts.
        return FileList(directory)

    # ------------------------------------------------------------------

    def getCurrentServiceReference(self):
        """
        Return the service reference currently playing on the box.

        Used by ServiceController to capture whatever was playing
        (typically live TV) before MediaPlayer3 takes over playback,
        so it can be restored when MediaPlayer3 closes.

        Returns:
            eServiceReference instance, or None if nothing is playing
            or NavigationInstance is unavailable.
        """

        navigation = self.getNavigationInstance()

        if navigation is None:
            return None

        try:
            return navigation.getCurrentlyPlayingServiceReference()

        except Exception as error:
            self._log(
                f"Unable to read current service reference: {error}"
            )

            return None

    # ------------------------------------------------------------------

    def getPlaybackPosition(self):
        """
        Return (elapsed_seconds, duration_seconds) for whatever is
        currently playing.

        Build 0005 -- Progress Bar / Elapsed / Total Time
        (MAINSCREEN_SPEC.md section 5, PLAYBACK_CONTROLLER_SPEC.md
        section 4).

        Enigma2 exposes seek position/length through the current
        service's iSeekableService, in PTS units (90000 per second).
        Different images/versions have been observed to return this
        either as an (error_code, pts) tuple or as a raw pts value, so
        both forms are handled defensively.

        Returns:
            (elapsed_seconds, duration_seconds) -- either element (or
            both) is None when unavailable for any reason (no service,
            service does not support seeking, image-specific API
            differences). Callers must treat None as "Unknown", never
            as zero.
        """

        navigation = self.getNavigationInstance()

        if navigation is None:
            return None, None

        try:
            service = navigation.getCurrentService()

        except Exception as error:
            self._log(f"Unable to get current service: {error}")
            return None, None

        if service is None:
            return None, None

        try:
            seek = service.seek()

        except Exception as error:
            self._log(f"Service does not support seek(): {error}")
            return None, None

        if seek is None:
            return None, None

        position_seconds = self._ptsToSeconds(self._safeSeekCall(seek.getPlayPosition))
        duration_seconds = self._ptsToSeconds(self._safeSeekCall(seek.getLength))

        return position_seconds, duration_seconds

    # ------------------------------------------------------------------

    def _safeSeekCall(self, func):
        """
        Call an iSeekableService query method, returning None instead
        of raising on any error.
        """

        try:
            return func()

        except Exception as error:
            self._log(f"Seek query failed: {error}")
            return None

    # ------------------------------------------------------------------

    def _ptsToSeconds(self, result):
        """
        Normalize an iSeekableService position/length result to whole
        seconds.

        Handles the common `(error_code, pts)` tuple form, images that
        return the raw pts value directly, AND images that return a
        *list* `[error_code, pts]` instead of a tuple -- confirmed on
        a real OpenViX device (see docs/Claude_notes_build0005.txt):
        every seek() result there was a 2-element list, which the
        original `isinstance(result, tuple)` check silently rejected,
        making elapsed/duration always "Unknown".
        """

        if result is None:
            return None

        try:
            if isinstance(result, (tuple, list)) and len(result) == 2:

                error_code, pts = result

                if error_code != 0 or pts is None:
                    return None

            else:
                pts = result

            return int(pts) // 90000

        except (TypeError, ValueError) as error:
            self._log(f"Unable to interpret seek result {result!r}: {error}")
            return None

    # ------------------------------------------------------------------

    def seekTo(self, position_seconds) -> bool:
        """
        Seek the currently playing service to an absolute position
        (seconds from the start of the track), rather than relative to
        wherever GStreamer's own internal position tracking currently
        believes it is.

        Build 0008, device test round 7: a device log proved this
        distinction matters. GStreamer's own reported position had
        gotten stuck near the end of a 231s track (231) while the
        track was actually only ~84s in (per the independent wall-
        clock estimate PlaybackController now tracks). The user then
        pressed the seek-forward key, requesting "+30s" via
        seekRelative() -- which is relative to GStreamer's OWN belief
        about where it is, not the true position -- and landed at
        231 + 30 = 261, past the end of the 231s track, so playback
        simply stopped there. Seeking to an absolute target computed
        from PlaybackController's own trusted position sidesteps this
        category of bug entirely, since it never depends on
        GStreamer's own current-position belief being correct.

        Returns:
            True if a seek was requested. False when there is no
            current service, it does not support seeking, or the
            underlying call raised -- never raises itself.
        """

        navigation = self.getNavigationInstance()

        if navigation is None:
            return False

        try:
            service = navigation.getCurrentService()

        except Exception as error:
            self._log(f"Unable to get current service: {error}")
            return False

        if service is None:
            return False

        try:
            seek = service.seek()

        except Exception as error:
            self._log(f"Service does not support seek(): {error}")
            return False

        if seek is None:
            return False

        pts = max(0, int(position_seconds)) * 90000

        try:
            seek.seekTo(pts)

        except Exception as error:
            self._log(f"seekTo() failed: {error}")
            return False

        return True

    # ------------------------------------------------------------------

    def seekRelative(self, offset_seconds) -> bool:
        """
        Seek the currently playing service by `offset_seconds`
        (positive = forward, negative = backward).

        Build 0005 -- requested after a real device test showed
        FASTFORWARD/REWIND/LEFT/RIGHT had no effect (no seeking was
        implemented at all in the initial Build 0005 release; see
        docs/Claude_notes_build0005.txt).

        Uses iSeekableService.seekRelative(direction, pts), following
        the same pattern Enigma2's own InfoBarGenerics uses
        (direction is +1/-1, pts is always a positive magnitude in
        90000-per-second PTS units).

        Returns:
            True if a seek was requested. False when there is no
            current service, it does not support seeking, or the
            underlying call raised -- never raises itself.
        """

        navigation = self.getNavigationInstance()

        if navigation is None:
            return False

        try:
            service = navigation.getCurrentService()

        except Exception as error:
            self._log(f"Unable to get current service: {error}")
            return False

        if service is None:
            return False

        try:
            seek = service.seek()

        except Exception as error:
            self._log(f"Service does not support seek(): {error}")
            return False

        if seek is None:
            return False

        direction = 1 if offset_seconds >= 0 else -1

        pts = abs(int(offset_seconds)) * 90000

        try:
            seek.seekRelative(direction, pts)

        except Exception as error:
            self._log(f"seekRelative() failed: {error}")
            return False

        return True

    # ------------------------------------------------------------------

    def connectPictureDataSignal(self, picload, callback) -> bool:
        """
        Connect `callback` to an ePicLoad instance's PictureData signal,
        the way MainScreen's cover art decoding needs.

        Enigma2's PictureData signal binding has been observed to take
        three different forms across images:

            1. `picload.PictureData.connect(callback)` -- newer-style
               signal object with its own connect() method.
            2. `picload.PictureData.get().append(callback)` -- the
               form that worked in this build's own device tests.
            3. `picload.PictureData.append(callback)` -- directly
               appendable, no `.get()` available (the form a real
               YampMusicPlayer bug report showed was needed on some
               bindings; both YampMusicPlayer's and OpenPli
               MediaPlayer's own PictureData-connection helpers were
               checked per user request -- see
               docs/Claude_notes_build0005.txt).

        Tries each form in that order; this exact 3-way order matches
        mediaplayer2's own eConnectCallback() helper.

        Returns:
            True if the callback was connected via any of the three
            forms; False if none worked (cover art will simply stay
            hidden).
        """

        if hasattr(picload.PictureData, "connect"):

            try:
                picload.PictureData.connect(callback)

                return True

            except Exception as error:

                self._log(f"PictureData.connect() failed: {error}")

        try:
            picload.PictureData.get().append(callback)

            return True

        except AttributeError:

            self._log("PictureData.get() not available; trying direct append().")

        try:
            picload.PictureData.append(callback)

            return True

        except Exception as error:

            self._log(f"Unable to connect PictureData signal: {error}")

            return False

    # ------------------------------------------------------------------

    def getStreamInfo(self):
        """
        Return best-effort stream information for whatever is
        currently playing: codec, sample rate, bitrate, channels.

        Build 0005 -- Playback Statistics (DeveloperScreen,
        BUILD_0005_PLAN.md "Playback Statistics").

        Every field is queried and defaulted independently, so a
        missing or renamed iServiceInformation constant on a given
        image can only blank that one field, never the whole report.
        This has not yet been verified against a real device (see
        docs -- notes for this build); treat "Unknown" values as
        expected until confirmed otherwise.

        Returns:
            Dict with keys "codec", "sample_rate", "bitrate",
            "channels" -- every value is a display string, "Unknown"
            when not available.
        """

        info_report = {
            "codec": "Unknown",
            "sample_rate": "Unknown",
            "bitrate": "Unknown",
            "channels": "Unknown",
        }

        navigation = self.getNavigationInstance()

        if navigation is None:
            return info_report

        try:
            service = navigation.getCurrentService()

            if service is None:
                return info_report

            info = service.info()

            if info is None:
                return info_report

        except Exception as error:
            self._log(f"Unable to get service info: {error}")
            return info_report

        try:
            from enigma import iServiceInformation

        except ImportError:
            return info_report

        # Build 0009, device test round 2: a device log showed Enigma2
        # itself correctly identifying the codec ("audio stream=0
        # codec=Free Lossless Audio Codec (FLAC)"), but this method
        # reported "Unknown" for every field regardless -- codec was
        # queried with getInfo(), which returns a numeric type ID for
        # sAudioType, not the human-readable string Enigma2's own log
        # line shows. Switched to getInfoString() for codec
        # specifically, the same distinction getStreamTags() already
        # established for its own text fields (sTagTitle/sTagArtist).
        # Not yet confirmed this is the complete fix -- the other
        # three fields (sample_rate/bitrate/channels) are genuinely
        # numeric, so they remain on getInfo(), but whether Enigma2's
        # own eServiceMP3 populates THOSE particular
        # iServiceInformation constants at all for GStreamer-based
        # playback (as opposed to DVB tuning, which is what these
        # constants were originally designed for) is still an open
        # question -- see this method's own getDiagnostics()-style
        # verbose logging below for whatever the next device test
        # actually reveals.
        string_field_queries = (("codec", "sAudioType"),)

        numeric_field_queries = (
            ("sample_rate", "sSampleRate"),
            ("bitrate", "sTransferBPS"),
            ("channels", "sAudioChannels"),
        )

        for field_name, constant_name in string_field_queries:

            try:
                constant = getattr(iServiceInformation, constant_name, None)

                if constant is None:

                    logger.verbose(f"[Compatibility] getStreamInfo() {field_name}: iServiceInformation.{constant_name} does not exist on this image.")

                    continue

                value = info.getInfoString(constant)

                logger.verbose(f"[Compatibility] getStreamInfo() {field_name} ({constant_name}) via getInfoString(): {value!r}")

                if value not in (None, "", "N/A"):
                    info_report[field_name] = value

            except Exception as error:
                self._log(f"Unable to read {field_name}: {error}")

        for field_name, constant_name in numeric_field_queries:

            try:
                constant = getattr(iServiceInformation, constant_name, None)

                if constant is None:

                    logger.verbose(f"[Compatibility] getStreamInfo() {field_name}: iServiceInformation.{constant_name} does not exist on this image.")

                    continue

                value = info.getInfo(constant)

                logger.verbose(f"[Compatibility] getStreamInfo() {field_name} ({constant_name}) via getInfo(): {value!r}")

                if value not in (None, -1, ""):
                    info_report[field_name] = str(value)

            except Exception as error:
                self._log(f"Unable to read {field_name}: {error}")

        return info_report

    # ------------------------------------------------------------------

    def getStreamTags(self):
        """
        Return best-effort "now playing" tag info for whatever is
        currently playing: artist, title, organization (station
        name, when the stream provides one distinct from the
        configured station name).

        For an Icecast/Shoutcast Internet Radio stream, this is the
        ICY metadata the station itself embeds in the stream (the
        "StreamTitle" a DJ/automation system updates live) --
        GStreamer already parses it and exposes it as ordinary
        service tags, through the exact same iServiceInformation
        interface getStreamInfo() above uses for codec/bitrate, just
        different constants (sTagTitle/sTagArtist/sTagOrganization
        instead of sAudioType/sSampleRate/etc). Not every stream
        provides this -- many stations never update ICY metadata at
        all -- so an all-"Unknown" result is an expected, normal
        outcome, not a failure.

        Returns:
            Dict with keys "title", "artist", "organization" -- every
            value is a display string, "Unknown" when not available.
        """

        tag_report = {
            "title": "Unknown",
            "artist": "Unknown",
            "organization": "Unknown",
        }

        navigation = self.getNavigationInstance()

        if navigation is None:
            return tag_report

        try:
            service = navigation.getCurrentService()

            if service is None:
                return tag_report

            info = service.info()

            if info is None:
                return tag_report

        except Exception as error:
            self._log(f"Unable to get service info: {error}")
            return tag_report

        try:
            from enigma import iServiceInformation

        except ImportError:
            return tag_report

        field_queries = (
            ("title", "sTagTitle"),
            ("artist", "sTagArtist"),
            ("organization", "sTagOrganization"),
        )

        for field_name, constant_name in field_queries:

            try:
                constant = getattr(iServiceInformation, constant_name, None)

                if constant is None:
                    continue

                value = info.getInfoString(constant)

                if value not in (None, "", "N/A"):
                    tag_report[field_name] = value

            except Exception as error:
                self._log(f"Unable to read {field_name}: {error}")

        return tag_report

    # ------------------------------------------------------------------

    def getImageName(self) -> str:
        """
        Return image name if available.
        """

        try:
            from Components.SystemInfo import BoxInfo

            return BoxInfo.getItem("displaybrand") or "Unknown"

        except Exception:
            return "Unknown"

    # ------------------------------------------------------------------

    def getImageVersion(self) -> str:
        """
        Return image version if available.
        """

        try:
            from Components.SystemInfo import BoxInfo

            return BoxInfo.getItem("imageversion") or "Unknown"

        except Exception:
            return "Unknown"

    # ------------------------------------------------------------------

    def getReceiverModel(self) -> str:
        """
        Return receiver model.
        """

        try:
            from Components.SystemInfo import BoxInfo

            return BoxInfo.getItem("machinebuild") or "Unknown"

        except Exception:
            return "Unknown"

    # ------------------------------------------------------------------

    def getPythonVersion(self) -> str:
        """
        Return Python version.
        """

        return self._python_version

    # ------------------------------------------------------------------

    def getPlatformName(self) -> str:
        """
        Return detected platform name.

        Part of the diagnostic API defined in COMPATIBILITY_SPEC.md
        section 5.
        """

        return self._platform_name

# End of Part 3
    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def getCompatibilityReport(self) -> Dict[str, Any]:
        """
        Return a compatibility report.

        This information is intended for Developer Mode,
        systeminfo.dump() and diagnostic logging.
        """

        return {
            "platform": self._platform_name,
            "python_version": self.getPythonVersion(),
            "navigation_instance": self.hasNavigationInstance(),
            "service_reference": self.hasServiceReference(),
            "service_center": self.hasServiceCenter(),
            "service_event_tracker": self.hasServiceEventTracker(),
            "boxinfo": self.hasBoxInfo(),
            "python313": self.hasPython313(),
            "developer_mode": self.hasDeveloperMode(),
            "pvr_key_actions": ", ".join(self.PVR_KEY_ACTIONS),
            "next_track_key_actions": ", ".join(self.NEXT_TRACK_KEY_ACTIONS),
            "previous_track_key_actions": ", ".join(self.PREVIOUS_TRACK_KEY_ACTIONS),
        }

    # ------------------------------------------------------------------

    def dump(self) -> Dict[str, Any]:
        """
        Return complete diagnostic information.
        """

        return self.getCompatibilityReport()

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """
        Return readable object representation.
        """

        return (
            "Compatibility("
            f"platform={self._platform_name!r}, "
            f"python={self._python_version})"
        )


# ----------------------------------------------------------------------
# Global compatibility instance
# ----------------------------------------------------------------------

compatibility = Compatibility()


# ==============================================================================
#
# Build Notes
#
# Build 0003 implements the first version of the Platform
# Abstraction Layer (PAL).
#
# Future builds may extend this module with:
#
#   - Additional Enigma2 distributions
#   - Hardware capability detection
#   - Codec capability detection
#   - Automatic feature registry
#   - Extended developer diagnostics
#   - Runtime compatibility validation
#
# Public APIs should remain backward compatible whenever possible.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

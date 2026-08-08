# MediaPlayer3

# Release Checklist

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device tested across OpenViX, OpenATV, openPLI and OpenBH -- rounds 1-13)

---

# 1. Purpose

This document defines the release process for MediaPlayer3.

Its purpose is to ensure that every Build follows a consistent quality
assurance process before being frozen or released.

---

# 2. Documentation Checklist

Verify that the following documents are up to date.

Architecture

☑ ARCHITECTURE.md

Project Plan

☑ BUILD_xxxx_PLAN.md

Navigation

☑ SCREEN_NAVIGATION.md

Specifications

☑ All *_SPEC.md files reviewed

Project History

☑ HISTORY.md updated

Change Log

☑ CHANGELOG.md updated

Release Checklist

☑ RELEASE_CHECKLIST.md reviewed

---

# 3. Version Information

Verify:

☑ Version number updated

☑ Build number updated

☑ Internal revision updated (if used)

☑ Version displayed correctly in MainScreen

☑ Version displayed correctly in DeveloperScreen

☑ Version stored in project.py

---

# 4. Core Module Review

Verify:

☑ config.py

☑ logger.py

☑ compatibility.py

☑ systeminfo.py

☑ constants.py

☑ features.py

☑ version.py

☑ project.py

All Core modules shall follow ARCHITECTURE.md.

---

# 5. Controller Review

Verify:

☑ playback_controller.py

☑ service_controller.py

Controllers shall contain business logic only.

Controllers shall contain no user interface code.

---

# 6. Screen Review

Verify:

☑ MainScreen

☑ BrowserScreen

☑ SettingsScreen

☑ PlaybackInfoScreen

☑ DeveloperScreen

☑ Main Menu

All Screen responsibilities shall follow their corresponding
specifications.

---

# 7. Functional Testing

Verify:

☑ Application starts successfully

☑ MainScreen opens correctly

☑ Browser navigation works

☑ Media playback starts

☐ Pause works

☐ Resume works

☑ Stop works

☑ Playback returns to TV correctly

☑ Settings load correctly

☑ Settings save correctly

☑ Developer tools operate correctly

---

# 8. Compatibility Testing

Verify:

☑ OpenViX

☑ OpenATV

☑ Platform detection

☑ Compatibility layer

☑ Restore TV service

Also confirmed working (not in this checklist's original list):
openPLI (no log captured, confirmed working by the user directly) and
OpenBH.

Platform-specific issues shall be documented before release.

---

# 9. Logging Review

Verify:

☑ Logger initializes correctly

☑ Startup logging

☑ Playback logging

☑ Screen lifecycle logging

☑ Error logging

☑ Shutdown logging

Developer logging shall follow LOGGER_SPEC.md.

---

# 10. Release Approval

A Build may be frozen when:

☑ Documentation is complete.

☑ Architecture review completed.

☐ Functional testing completed. (Pause/Resume specifically remain
  unconfirmed by any device log across all 13 rounds -- everything
  else in section 7 above is now confirmed.)

☑ Known Issues documented.

☑ CHANGELOG updated.

☑ HISTORY updated.

☑ No critical defects remain.

---

# 11. Build Status

Each Build shall have one of the following states.

Planning

Development

Testing

Frozen

Released

Archived

Current state: CONFIRMED COMPLETE -- device tested across four
Enigma2 images (OpenViX, OpenATV, openPLI, OpenBH), 13 rounds.

Build 0007 was implemented and thoroughly tested in an extended stub
environment first (PlaylistManager's full M3U round-trip,
InternetRadioManager's favorites/history/JSON persistence and its
graceful degradation, StorageManager's directory creation and auto-
recovery, BrowserScreen's new context menu, MainScreen's context-
sensitive radio navigation, and both new screens), then underwent 13
rounds of real device testing that found and fixed a real crash
(RadioBrowser's "null"-string favicon field), real connectivity bugs
(RadioBrowser mirror discovery, missing on the first attempt),
multiple real remote-control key mapping issues (RADIO, CH+/CH-,
INFO/EPG-substitute, resolved through raw eActionMap log evidence
where guessing alone repeatedly failed), and a multi-round visual
investigation into the box's own video/background bleeding through
screen content, ultimately resolved by a fixed white-panel/near-black
text scheme after three earlier, real-but-incomplete attempts. See
Claude_notes_build0007.txt for the full, honest session-by-session
history, including the two rounds (10-11) whose fixes turned out not
to fully work and were corrected in the following round rather than
left standing.

Two items are deliberate, documented scope decisions rather than open
bugs: CH+/CH- in RadioBrowserScreen (appears architecturally
unreachable from plugin code on this Enigma2 setup) and launching the
whole plugin via a global hardware RADIO key from outside the app
(would require system-level key interception unverifiable without
risking the receiver's normal TV/radio behaviour). Both are explained
in full in CHANGELOG.md's Known Issues and Claude_notes_build0007.txt.

---

# 12. End of File

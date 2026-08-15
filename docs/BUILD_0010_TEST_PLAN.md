# BUILD_0010_TEST_PLAN.md

MediaPlayer3

Build 0010 Test Plan

---

# Purpose

This document defines the testing requirements for Build 0010.

Build 0010 is intended to complete the planned functionality required
before the MediaPlayer3 1.0-beta release.

Testing shall verify both the new Build 0010 functionality and the
existing functionality carried forward from previous builds.

A successful Build 0010 test shall demonstrate that the application
remains stable across supported Enigma2 versions and hardware.

---

# Test Philosophy

Testing shall continue to follow the incremental approach used during
previous MediaPlayer3 development.

Each major feature shall first be tested independently.

After the feature passes its individual tests, integration testing shall
be performed.

Finally, complete regression testing shall verify that previously
working functionality has not been broken.

The application shall be tested after each significant implementation
step rather than waiting until all Build 0010 functionality has been
implemented.

---

# Test Stages

Build 0010 testing shall use the following stages:

1. Unit and component testing
2. Feature testing
3. Integration testing
4. Error and exception testing
5. Regression testing
6. Multi-version Enigma2 testing
7. Multi-device testing
8. Resolution and UI testing
9. Final release testing

A failure discovered at an earlier stage shall be corrected or
documented before proceeding to the next stage.

---

# Component Testing

The following components shall be tested independently where practical:

- PodcastManager
- PodcastScreen
- PodcastProvider
- MainScreen navigation
- BrowserScreen
- RadioBrowser
- YLE EPG
- Theme system
- Help System

Each component shall be tested with both normal and invalid input where
applicable.

---

# Stability Requirement

No individual feature failure shall cause an uncontrolled termination
of MediaPlayer3.

Expected failures such as:

- Network unavailable
- Missing external data
- Invalid provider data
- Missing files
- Unavailable storage
- Invalid configuration

shall be handled through the documented error-handling mechanisms.

---

# Test Result Recording

Each test stage shall record:

- Test date
- Build number
- Enigma2 version
- Device
- Test result
- Observed problems
- Corrective action
- Retest result

A test shall only be considered passed when the expected behaviour has
been confirmed on the target environment.

---
# Feature Testing

Each new Build 0010 feature shall be tested independently before
integration testing.

---

# Podcast Testing

Podcast functionality shall be tested for:

- Podcast search
- Empty search results
- Podcast metadata
- Episode retrieval
- Episode metadata
- Podcast subscriptions
- Unsubscribe
- Refresh
- Episode playback
- Add episode to playlist
- Provider errors
- Network unavailable
- Invalid podcast data
- Missing podcast feed
- Provider timeout
- Cached podcast data

The PodcastScreen shall remain usable when external podcast services
are unavailable.

Podcast playback shall use the existing playback architecture.

---

# MainScreen Navigation Testing

MainScreen navigation shall be tested from every supported source.

Test entry points shall include:

- Internet Radio
- File Browser
- Favorites
- Music Library
- Podcasts

The following shall be verified:

- MainScreen opens correctly.
- The originating view is remembered.
- EPG / INFO changes the active MainScreen area.
- EPG / INFO does not open Favorites.
- OK opens the MainScreen action menu.
- Back returns to the originating view.
- Stop / Resume controls playback correctly.
- Cancel closes the menu without changing state.
- EXIT behaves correctly.
- TEXT button functionality is no longer used.

---

# Browser Testing

BrowserScreen shall be tested with:

- Local directories
- Local files
- Empty directories
- Unavailable directories
- Playlist operations
- Different directory depths
- Invalid file entries

The three-column navigation shall be verified.

The browser shall remain operational when an individual file or
directory operation fails.

---

# RadioBrowser Testing

RadioBrowser shall be tested for:

- Initial database download
- Manual database update
- Automatic database update
- Successful database replacement
- Failed database update
- Empty database
- Network unavailable
- Invalid station data
- Language filtering
- Region filtering
- Station selection
- Favorites
- Stations removed from the external database

A failed database update shall not destroy a previously valid local
database.

---

# YLE EPG Testing

YLE EPG shall be tested for:

- Valid API key
- Missing API key
- Invalid API key
- Valid programme data
- Empty programme data
- Current programme selection
- Upcoming programmes
- Programme boundary times
- Network unavailable
- EPG service unavailable
- Invalid response
- Missing station mapping
- Cached EPG data

Radio playback shall continue normally when EPG data is unavailable.

---

# Theme Testing

Both Light and Dark themes shall be tested.

The following shall be verified:

- MainScreen
- BrowserScreen
- Information Panel
- Help
- Settings
- Playlist
- Headers
- Active area
- Text readability
- Error messages
- Artwork
- Progress bar

Changing theme shall not change logical layout or navigation.

---
# Error and Exception Testing

Build 0010 shall include deliberate failure testing.

The purpose is to verify that expected exceptional conditions are handled
without terminating MediaPlayer3.

---

# Network Failure

Network-dependent functionality shall be tested with the network
unavailable.

The following shall be tested:

- Podcast search
- Podcast episode retrieval
- RadioBrowser update
- YLE EPG retrieval
- Other network-dependent operations

The application shall remain operational.

Previously available local data shall remain usable where applicable.

---

# Invalid Data

External services shall be tested with invalid or incomplete data where
this can be simulated safely.

Examples include:

- Invalid JSON
- Missing fields
- Invalid URLs
- Empty responses
- Corrupt station data
- Invalid podcast data
- Invalid EPG data

The affected operation shall fail in a controlled manner.

---

# Storage Failure

Local storage failures shall be tested where practical.

Examples include:

- Startup directory unavailable
- USB device removed
- Database unavailable
- Database write failure
- Insufficient storage space

The application shall display an appropriate error and remain
operational.

---

# MainScreen Opening Failure

The top-level MainScreen opening operation shall be tested separately.

The call that opens MainScreen shall have a final exception safety
boundary.

If MainScreen initialization fails:

- The exception shall be caught.
- The error shall be logged.
- The user shall receive a controlled error message.
- Enigma2 shall not be allowed to terminate because of the exception.

This test is specifically intended to protect against failures during
screen construction and layout initialization.

---

# Regression Testing

All functionality that passed Build 0009 shall be retested.

Regression testing shall include:

- Plugin startup
- Plugin shutdown
- Radio playback
- Local file playback
- Playlist handling
- Play
- Pause
- Stop
- Rewind
- Fast forward
- MainScreen
- Information Panel
- Lyrics
- Metadata
- EPG
- Favorites
- File Browser
- Logging
- Settings
- Help

Existing functionality shall continue to work unless explicitly changed
by Build 0010 specifications.

---
# Multi-Version Testing

Build 0010 shall be tested on the supported Enigma2 versions used for
MediaPlayer3 validation.

The same core test suite shall be executed on each supported version.

The test shall verify that:

- MediaPlayer3 starts correctly.
- MediaPlayer3 shuts down correctly.
- MainScreen opens correctly.
- BrowserScreen operates correctly.
- Radio playback works.
- Local file playback works.
- Podcast functionality works.
- EPG works where supported.
- RadioBrowser works.
- Themes work.
- Help works.
- No version-specific crash occurs.

---

# Multi-Device Testing

Build 0010 shall be tested on multiple supported Enigma2 receivers.

Testing shall include different remote controls where available.

Remote-control testing shall verify:

- Navigation keys
- OK
- EXIT
- HELP
- EPG / INFO
- Playback controls
- Volume controls
- Numeric keys where applicable

No essential MediaPlayer3 function shall depend on a specific remote
control implementation.

---

# Resolution Testing

The application shall be tested at different supported screen
resolutions.

Testing shall verify:

- MainScreen layout
- BrowserScreen layout
- Information Panel
- Podcast screens
- Help
- Settings
- Light theme
- Dark theme
- Text readability
- Button and header visibility

The logical layout shall remain usable at small supported resolutions.

---

# Final Regression Test

After all Build 0010 features have passed their individual tests, the
complete MediaPlayer3 test suite shall be executed from start to finish.

The final test shall include:

1. Start MediaPlayer3.
2. Test Internet Radio.
3. Test local file playback.
4. Test Favorites.
5. Test Playlist.
6. Test MainScreen navigation.
7. Test Information Panel.
8. Test Podcast functionality.
9. Test RadioBrowser.
10. Test EPG.
11. Test Help.
12. Test Settings.
13. Test Light and Dark themes.
14. Test error handling.
15. Exit MediaPlayer3.

The final regression test shall be repeated on the selected validation
receivers and Enigma2 versions.

---

# Release Criteria

Build 0010 may be considered complete when:

- All mandatory Build 0010 features pass.
- All known critical errors have been resolved or explicitly accepted.
- No uncontrolled MediaPlayer3 termination occurs during testing.
- Regression testing passes.
- Multi-version testing passes.
- Multi-device testing passes.
- Resolution testing passes.
- Remote-control testing passes.
- Documentation reflects the implemented functionality.

Any remaining known limitation shall be documented before release.

---

# 1.0-beta Readiness

Successful completion of Build 0010 testing shall make MediaPlayer3 a
candidate for the 1.0-beta release.

The 1.0-beta release is intended for public distribution and broader
real-world testing.

Additional issues discovered during public testing may result from:

- Different Enigma2 distributions
- Different receiver hardware
- Different remote controls
- Different screen resolutions
- Different network environments
- Different Internet Radio providers
- Different podcast providers

Such issues shall be recorded and evaluated for subsequent releases.

---

End of BUILD_0010_TEST_PLAN.md

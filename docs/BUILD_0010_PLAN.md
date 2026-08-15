# BUILD_0010_PLAN.md

MediaPlayer3

Build 0010 Development Plan

---

# Build Objective

Build 0010 is the final feature-focused development build before
MediaPlayer3 enters the 1.0-beta phase.

The primary goal is to add Podcast support and complete the remaining
user interface and usability improvements identified during Build 0009
testing.

After Build 0010 has been completed and tested, MediaPlayer3 should be
ready for public beta testing.

---

# Build 0010 Main Goals

Build 0010 focuses on:

- Podcast support
- Improved browser navigation
- Improved MainScreen navigation
- Improved Internet Radio handling
- Improved local file handling
- User interface refinement
- Configuration improvements
- Final pre-beta usability improvements

The existing modular architecture shall be preserved.

No major architectural redesign is planned for Build 0010.

---

# Podcast Support

Podcast support is the main new functional feature of Build 0010.

The Podcast interface shall use a three-column browsing model similar to
the Internet Radio browser.

The planned layout is:

    Available Podcasts | Subscribed Podcasts | Episodes

The left column presents available podcasts.

The middle column presents subscribed podcasts.

The right column presents episodes belonging to the selected podcast.

Podcast functionality shall be integrated with the existing playback
and playlist architecture.

Podcast episodes shall be playable through the existing playback
system.

The podcast implementation should be designed so that additional
podcast sources can be added later.

An initial external source may be Podcast Index.

---

# Podcast Architecture

Podcast functionality shall follow the modular architecture already used
by MediaPlayer3.

Podcast-specific functionality shall not be implemented directly inside
MainScreen.

The implementation should use dedicated podcast components and
interfaces where appropriate.

The existing MainScreen, PlaybackController and playlist architecture
shall remain reusable.

---
# Browser Navigation

Build 0010 introduces a consistent three-column browsing model for
content browsers.

The model shall be used where appropriate for:

- Internet Radio
- Music Library
- Podcasts
- Local Files

The exact contents of each column depend on the browser.

The active column shall be clearly indicated.

Active header rows use the existing blue highlight.

Inactive header rows use a light blue background.

The upper title area shall display the name of the current browser
instead of the current filter information.

Examples:

- Internet Radio
- Music Library
- Files
- Podcasts

---

# Local File Browser

The File Browser shall receive a three-column browsing mode.

The planned layout is:

    Directories | Files | Playlist

The left column is used to browse directories.

The middle column contains files in the selected directory.

The right column displays the current playlist.

---

# File Browser Actions

OK on a directory opens an action menu:

- Add entire directory to playlist
- Cancel

OK on a file opens an action menu:

- Add this file
- Add this file and remaining files in directory
- Add all files from directory
- Cancel

OK on a playlist item opens an action menu:

- Remove
- Move up
- Move down
- Cancel

The existing playback and playlist handling shall remain unchanged.

---

# Internet Radio

Internet Radio shall use the same three-column navigation principles.

Radio browsing shall continue to support:

- Station browsing
- Country / region selection
- Language selection
- Favorites

The navigation model shall remain compatible with the existing
Internet Radio functionality.

---

# RadioBrowser Database

The local RadioBrowser station database shall be maintained locally.

The database shall be updated when:

- No stations are available
- The user selects "Update database" from the menu
- An automatic update interval has expired, if automatic updating is
  enabled

The default automatic update interval may be seven days.

Existing stations shall not be removed during a normal update.

A separate "Clear station list" operation may remove the existing
stations.

If updating the database fails, the existing local station list shall
remain available.

If no stations are available, the user shall be asked whether the
database should be downloaded again.

---
# MainScreen Navigation

Build 0010 shall simplify navigation between MainScreen and the
browser from which playback was started.

The EPG / INFO button shall no longer be used to switch to the
Favorites list when playing local files.

MainScreen shall retain its three-panel navigation model:

- Player
- Playlist
- Information

The active panel is still changed using EPG / INFO.

---

# MainScreen OK Menu

OK in Player mode shall open a small action menu.

The first item shall always be:

- Back

Selecting Back returns the user to the view from which MainScreen was
opened.

Possible previous views include:

- Internet Radio
- File Browser
- Favorites

The remaining menu items shall be:

- Stop / Resume
- Cancel

The menu shall therefore provide a consistent way to leave MainScreen
without requiring source-specific remote-control behaviour.

---

# MainScreen Startup Behaviour

Whenever playback of a new track or radio station begins:

- MainScreen shall become active in Player mode.
- The Information Panel shall automatically select the most relevant
  available information.

For Internet Radio the preferred information order is:

1. Radio EPG
2. Now Playing
3. Station Information
4. Codec Information

For local music the preferred information order is:

1. Lyrics
2. Metadata
3. Codec Information

For podcasts, the Information Panel may later use podcast-specific
information where available.

---

# PVR Button

The PVR button shall open the same source-selection query that is used
when entering playback through OK.

PVR shall no longer directly open BrowserScreen.

The exact available source choices depend on the current MediaPlayer3
configuration.

---

# Visual Refinement

Inactive header rows shall use a light blue background.

The active header row shall continue to use the existing blue
highlight.

The same visual behaviour shall be used when navigating between
columns in three-column browsers.

The implementation shall continue to use colours supplied by the
current Enigma2 skin where appropriate.

---

# Theme Support

Build 0010 shall introduce two supported visual themes:

- Light
- Dark

The Light theme shall remain close to the current appearance.

The Dark theme shall use:

- Dark grey background
- White text

Theme implementation shall not change the logical layout of the
application.

---
# Configuration and Integration

Build 0010 shall add the following configuration options where
appropriate.

## Main Menu Integration

Settings shall provide an option to add MediaPlayer3 to the Enigma2
main menu.

---

## YLE API Key

The YLE API key shall be read from a local file instead of requiring
manual entry into MediaPlayer3.

For example:

    yle.txt

The file may contain the API key copied from the YLE service.

The exact file location shall follow the existing MediaPlayer3
configuration and path conventions.

---

## Internet Radio Filters

Internet Radio shall allow the user to change:

- Language
- Region

The selected values shall be used by the Internet Radio browser.

---

# Compatibility and Reliability

Build 0010 shall preserve the compatibility achieved during Build 0009.

Build 0009 was tested successfully on:

- Four different Enigma2 versions
- Two different receiver models
- Multiple remote-control configurations
- Multiple display resolutions

No display-resolution changes are currently required.

Build 0010 shall retain this compatibility as far as practical.

---

# Known Reliability Improvements

Two issues were identified during the Build 0009 exception audit.

## Unavailable Startup Directory

BrowserScreen currently calls `createFileList(startup_directory)` without
an exception guard.

If the configured startup directory is unavailable, for example because
a USB device has been disconnected, the exception can terminate
BrowserScreen.

Build 0010 shall handle this situation gracefully.

The user shall receive an appropriate error message and the application
shall remain in a controlled state.

---

## MainScreen Startup Protection

The call to:

    session.open(MainScreen)

shall be protected by a top-level exception handler.

Unexpected exceptions during MainScreen construction or layout shall be
logged and reported through the MediaPlayer3 error-handling mechanism
instead of propagating directly to Enigma2.

This protection is intended to prevent unexpected MainScreen
initialisation failures from causing an uncontrolled Enigma2 traceback.

---

# Testing

Build 0010 shall be tested incrementally.

Testing shall include:

- Normal playback
- Internet Radio
- Local files
- Favorites
- Music Library
- Podcasts
- Playlist operations
- MainScreen navigation
- Browser navigation
- Remote-control operation
- Different Enigma2 versions
- Different receiver models
- Different remote controls
- Different display resolutions
- Missing or unavailable storage
- Network failures
- Invalid or unavailable external information

Each major implementation step shall be tested before continuing to the
next step.

---

# 1.0-beta Target

Build 0010 is intended to be the final feature-focused development
build before the 1.0-beta release.

When the Build 0010 objectives have been implemented and successfully
tested, MediaPlayer3 may be released as:

    MediaPlayer3 1.0-beta

The 1.0-beta release shall begin wider public testing.

Further changes are expected after public testing, particularly for:

- Additional Enigma2 versions
- Different receiver models
- Different remote controls
- Different skins
- Different network environments

The beta phase is therefore expected to focus primarily on
compatibility, reliability and usability improvements rather than major
architectural changes.

---

# Development Principle

Build 0010 shall remain focused.

New functionality should only be added when it directly supports the
1.0-beta target.

The existing modular architecture shall be preserved.

Documentation shall be updated together with implementation changes.

---

End of BUILD_0010_PLAN.md

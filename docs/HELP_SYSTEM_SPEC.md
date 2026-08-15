# HELP_SYSTEM_SPEC.md

MediaPlayer3

Help System Specification

---

# Purpose

The Help System provides context-sensitive assistance for MediaPlayer3
screens and functions.

Help shall explain the current screen, available actions and relevant
remote-control keys without requiring the user to consult external
documentation.

---

# Help Access

HELP shall open the help information for the currently active screen.

Supported help contexts include:

- MainScreen
- File Browser
- Internet Radio
- Favorites
- Music Library
- Podcasts
- Settings

The Help System shall determine the appropriate help content from the
current screen context.

---

# Help Presentation

Help shall be presented using the existing MediaPlayer3 screen and
navigation conventions.

The help view shall:

- Be readable on supported screen resolutions.
- Use the currently selected theme.
- Support scrolling when the content exceeds the available display
  area.
- Use the active Enigma2 skin where appropriate.

Help content shall not modify playback state.

---

# MainScreen Help

MainScreen help shall explain:

- Player area
- Playlist area
- Information area
- EPG / INFO navigation
- OK action menu
- Back
- Stop / Resume
- Cancel
- EXIT

The help shall make clear that EPG / INFO changes the active MainScreen
area and does not perform source-specific navigation.

The obsolete TEXT button functionality shall not be documented.

---

# Browser Help

Browser help shall explain:

- Three-column layout
- Active column
- LEFT / RIGHT navigation
- UP / DOWN navigation
- OK actions
- EXIT
- HELP

Where a browser has source-specific actions, those actions may be
included in the help content.

---
# Podcast Help

Podcast help shall explain the podcast browser and its available
actions.

The help shall include:

- Available Podcasts
- Subscribed Podcasts
- Episodes
- Search
- Subscribe
- Unsubscribe
- Refresh
- Play
- Add to playlist
- Cancel
- Navigation between columns

The help shall explain that podcast playback uses the existing
MediaPlayer3 playback architecture.

---

# Internet Radio Help

Internet Radio help shall explain:

- RadioBrowser station browsing
- Language filtering
- Region filtering
- Favorites
- Database update
- Station selection
- Playback

The help shall explain that the local RadioBrowser database may remain
available when the external service cannot be reached.

---

# Information Panel Help

Information Panel help shall explain the available information types,
which may include:

- Lyrics
- Metadata
- Codec information
- Radio EPG
- Now Playing
- Station information
- Podcast information

The help shall explain that the Information Panel automatically selects
the most relevant available information.

Only information containing actual content is presented.

---

# Settings Help

Settings help shall explain the available MediaPlayer3 configuration
options.

This may include:

- Theme
- Language
- Startup directory
- Debug mode
- Developer mode
- Logging options
- RadioBrowser update settings
- Other supported configuration options

Help content shall reflect the actual options available in the
installed version.

---

# Theme Support

Help shall follow the currently selected MediaPlayer3 theme.

Both Light and Dark themes shall provide readable help content.

Changing the theme shall not change the structure or navigation of the
Help System.

---

# Navigation

The Help System shall support normal navigation using the remote
control.

At minimum:

- UP / DOWN scrolls the content.
- EXIT closes Help.
- HELP does not recursively open another Help view.

Where appropriate, LEFT / RIGHT may be used for navigation between
sections.

---
# Help Content Management

Help content shall be maintained separately from application logic.

Screen implementations shall reference the appropriate help context
rather than containing large blocks of help text.

This allows help content to be updated without changing the underlying
screen behaviour.

---

# Context Selection

The Help System shall identify the current context from the active
MediaPlayer3 screen.

The context shall be explicit enough to distinguish between different
browser types and MainScreen states where necessary.

For example:

- MainScreen
- File Browser
- Internet Radio
- Podcast Browser
- Information Panel
- Settings

If no specific help context is available, a general MediaPlayer3 help
page may be displayed.

---

# Missing Help Content

If help content for a specific context is unavailable:

- MediaPlayer3 shall not terminate.
- The missing content shall be logged where appropriate.
- A generic help message may be displayed.

A missing help document shall never prevent the user from continuing to
use MediaPlayer3.

---

# Compatibility

The Help System shall remain compatible with supported Enigma2 versions
and screen resolutions.

Help content shall not depend on functionality unavailable on a
supported receiver.

The Help System shall use the same resolution-independent layout
principles as the rest of MediaPlayer3.

---

# Documentation Consistency

Help content shall correspond to the actual functionality of the
installed MediaPlayer3 version.

Obsolete functionality shall not be documented.

In particular:

- The TEXT button shall not be documented.
- EPG / INFO shall be documented as MainScreen area navigation.
- The MainScreen OK menu shall document Back, Stop / Resume and Cancel.
- Podcast actions shall reflect the implemented podcast functionality.

---

# Design Principles

The Help System shall be:

- Context-sensitive
- Easy to navigate
- Consistent with MediaPlayer3 terminology
- Compatible with Light and Dark themes
- Independent from playback logic
- Independent from external service providers

Help is a presentation and documentation layer.

It shall not contain application business logic.

---

End of HELP_SYSTEM_SPEC.md

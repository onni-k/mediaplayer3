# BROWSER_SCREEN_SPEC.md

MediaPlayer3

Browser Screen Specification

---

# Purpose

BrowserScreen provides a common browsing interface for MediaPlayer3
content sources.

The screen shall support the same general navigation principles for
different content types while allowing each source to define its own
data.

Supported browser sources include:

- Local Files
- Internet Radio
- Music Library
- Podcasts
- Favorites

BrowserScreen is responsible for presentation and user interaction.

Business logic remains in the appropriate managers.

---

# Layout

Where the content source supports hierarchical browsing, BrowserScreen
uses a three-column layout.

```text
Directories / Categories | Items | Playlist
# Local File Browser

The local File Browser uses the following layout:

```text
Directories | Files | Playlist
# Local File Browser

The local File Browser uses the following layout:

```text
Directories | Files | Playlist
```

The Directories column contains available directories.

Selecting a directory updates the Files column.

The Files column contains playable files from the selected directory.

The Playlist column contains the current MediaPlayer3 playlist.

---

# Directory Actions

OK on a directory opens an action menu.

The available actions are:

- Add entire directory to playlist
- Cancel

Adding a directory shall add the supported audio files according to the
existing playlist behaviour.

---

# File Actions

OK on a file opens an action menu.

The available actions are:

- Add this file
- Add this file and remaining files in directory
- Add all files from directory
- Cancel

The selected operation shall use the existing playlist management
logic.

---

# Playlist Actions

OK on a playlist item opens an action menu.

The available actions are:

- Remove
- Move up
- Move down
- Cancel

Playlist modifications shall be handled by PlaylistManager.

BrowserScreen shall not directly manipulate the internal state of
PlaylistManager.

---

# File Navigation

The File Browser shall retain the current directory while navigating
between columns.

Moving from the Files column to the Playlist column shall not change the
selected directory.

Returning to the Files column shall restore the previous file
selection where possible.

The browser shall handle empty directories normally.

An empty directory shall not be treated as an application error.

---

# Startup Directory

BrowserScreen may start from the configured startup directory.

The startup directory may be unavailable, for example because a USB
device has been removed.

The call that creates the initial file list shall be protected against
directory-related exceptions.

If the startup directory cannot be accessed:

- The error shall be logged.
- The user shall receive an appropriate message.
- BrowserScreen shall remain in a controlled state.
- MediaPlayer3 shall not terminate because of the unavailable
  directory.

A safe fallback location may be used where appropriate.

---
# Browser Error Handling

BrowserScreen shall remain operational when individual browser
operations fail.

Possible conditions include:

- Directory unavailable
- File access failure
- Network unavailable
- Invalid source data
- Empty result
- Playlist operation failure

Errors shall be logged through the existing MediaPlayer3 logging
system.

User-facing errors shall be presented where appropriate.

A browser operation failure shall not terminate MediaPlayer3.

---

# Browser Return Behaviour

EXIT shall return to the previous MediaPlayer3 view.

The browser shall preserve its navigation context while it remains
active.

Returning to the browser shall restore the previous logical browsing
context where possible.

The browser shall not assume that the previous screen is a specific
content source.

---

# Help

HELP opens browser-specific help.

The help shall explain:

- Browser layout
- Active column
- Navigation keys
- OK actions
- Playlist actions
- Returning from the browser

Help content may be extended for source-specific browser functions.

---

# Source Independence

BrowserScreen shall not contain source-specific business logic.

Source-specific operations shall be provided by the appropriate manager.

For example:

- File operations → File / Browser manager
- Radio operations → RadioManager
- Podcast operations → PodcastManager
- Playlist operations → PlaylistManager

BrowserScreen presents the information and sends user actions to the
appropriate component.

---

# Design Principles

BrowserScreen provides a common user interface model for MediaPlayer3
content browsers.

The browser:

- Presents content.
- Handles navigation.
- Handles user selections.
- Opens action menus.
- Reports errors to the user.

The browser does not:

- Implement business logic.
- Directly access external services.
- Directly manipulate manager internal state.
- Implement audio playback.

Controllers coordinate application behaviour but avoid direct user
interface implementation.

Business logic remains inside managers and controllers.

This separation keeps BrowserScreen maintainable and allows different
content sources to share the same navigation principles.

---

End of BROWSER_SCREEN_SPEC.md

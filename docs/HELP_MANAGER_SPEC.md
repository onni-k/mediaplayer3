# HELP_MANAGER_SPEC.md

MediaPlayer3

HelpManager Specification

Status

Build 0008 CONFIRMED COMPLETE -- 9 rounds of real device testing, confirmed by the user

---

# Purpose

HelpManager provides a unified help system for MediaPlayer3.

Every user interface screen may display context-sensitive help without
implementing its own help functionality.

HelpManager is responsible for locating, loading and presenting the
appropriate help document for the currently active screen.

---

# Responsibilities

HelpManager is responsible for:

- Opening HelpScreen
- Locating help documents
- Loading help content
- Selecting the correct document
- Providing fallback help pages
- Reporting missing documentation

HelpManager shall not:

- Control playback
- Display application screens
- Modify user settings
- Access media files

---

# Context Sensitive Help

Every screen may request help.

Typical examples include:

- MainScreen
- BrowserScreen
- PlaylistScreen
- MusicLibraryScreen
- RadioBrowserScreen
- SettingsScreen
- DeveloperScreen

Each screen requests help using a unique identifier.

Example:

```
HelpManager.show("mainscreen")
```

HelpManager automatically loads the corresponding help document.

---

# Help Documents

Help documents are stored separately from application code.

Example directory:

```
help/

    mainscreen.md

    browserscreen.md

    playlistscreen.md

    musiclibraryscreen.md

    radiobrowserscreen.md

    settingsscreen.md

    developerscreen.md
```

Separating documentation from source code simplifies maintenance and
future translations.

---

# HelpScreen Integration

HelpManager never renders documentation itself.

Instead it loads the requested document and passes it to HelpScreen.

HelpScreen is responsible for:

- Rendering text
- Scrolling
- Page navigation
- Returning to the previous screen

This keeps responsibilities clearly separated.

---
# Navigation

HelpScreen follows the standard MediaPlayer3 navigation model.

UP / DOWN

Scroll line by line.

LEFT / RIGHT

Scroll page by page.

OK

Activate links when supported by future versions.

HELP

Close HelpScreen.

EXIT

Return to the previous screen.

The navigation model remains consistent with the rest of the
application.

---

# Markdown Support

Help documents are written in Markdown.

Supported content includes:

- Headings
- Paragraphs
- Bullet lists
- Numbered lists
- Code blocks
- Tables (when practical)

Future versions may optionally support:

- Hyperlinks
- Images
- Internal document links

Markdown provides readable source files while remaining easy to edit.

---

# Error Handling

If a requested help document cannot be found,
HelpManager loads a default help page.

If no default page exists, HelpScreen displays:

"No help available."

Missing documentation is written to the application log.

Application operation is never interrupted due to missing help files.

---

# Future Extensions

Possible future additions include:

- Complete user manual
- Release notes viewer
- License viewer
- Keyboard shortcut reference
- Search within help
- Multi-language help documents
- Cross-reference links
- Interactive tutorials

The existing HelpManager interface is designed to support these
features without requiring changes to application screens.

---

# Summary

HelpManager provides a centralized, context-sensitive help system for
MediaPlayer3.

By separating help content from application code and delegating
rendering to HelpScreen, the design remains modular, maintainable and
easy to extend.

The same architecture can later support user manuals, release notes and
other documentation while preserving a consistent user experience.

---

End of HELP_MANAGER_SPEC.md

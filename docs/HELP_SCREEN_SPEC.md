# HELP_SCREEN_SPEC.md

MediaPlayer3

HelpScreen Specification

Status

Build 0008 CONFIRMED COMPLETE -- 9 rounds of real device testing, confirmed by the user

---

# Purpose

HelpScreen provides a unified viewer for application documentation.

The screen displays context-sensitive help requested by HelpManager and
allows the user to read documentation without leaving the application.

HelpScreen is designed as a generic document viewer that may later be
used for additional documentation beyond help pages.

---

# Responsibilities

HelpScreen is responsible for:

- Displaying help documents
- Rendering Markdown content
- Scrolling through documents
- Displaying document titles
- Returning to the previous screen

HelpScreen shall not:

- Locate help files
- Read documentation directly from disk
- Manage playback
- Modify application settings

Help documents are always supplied by HelpManager.

---

# Screen Layout

The screen consists of three primary areas.

```
+------------------------------------------------------+
| Help Title                                           |
+------------------------------------------------------+
|                                                      |
| Markdown document                                    |
|                                                      |
|                                                      |
|                                                      |
|                                                      |
|                                                      |
|                                                      |
+------------------------------------------------------+
| ↑↓ Scroll   ←→ Page   HELP/EXIT Close                |
+------------------------------------------------------+
```

The layout follows the simple visual style used throughout
MediaPlayer3.

---

# Document Rendering

HelpScreen renders Markdown documents supplied by HelpManager.

Supported elements include:

- Headings
- Paragraphs
- Bullet lists
- Numbered lists
- Code blocks
- Simple tables

Unsupported elements are ignored gracefully.

Future versions may extend the renderer while maintaining compatibility.

---

# Context Awareness

HelpScreen always displays the document requested by HelpManager.

Examples:

MainScreen

↓

mainscreen.md

BrowserScreen

↓

browserscreen.md

MusicLibraryScreen

↓

musiclibraryscreen.md

RadioBrowserScreen

↓

radiobrowserscreen.md

The user never selects help documents manually during normal
operation.

---
# Navigation

HelpScreen follows the standard MediaPlayer3 navigation model.

UP / DOWN

Scroll one line.

LEFT / RIGHT

Scroll one page.

OK

Reserved for future interactive help functions.

HELP

Close HelpScreen.

EXIT

Close HelpScreen.

The user always returns to the screen from which help was requested.

---

# Error Handling

If the requested document cannot be displayed,
HelpScreen presents a simple informational message.

Example

```
No help available.
```

The application continues operating normally.

Any loading errors are reported through the application log.

---

# Future Extensions

The generic document viewer architecture allows HelpScreen to display
additional documentation in future builds.

Possible additions include:

- User Manual
- Release Notes
- GPL License
- Third-party Licenses
- Developer Documentation
- Keyboard Reference
- Searchable documentation
- Internal document links
- Embedded images

These additions require little or no modification to the existing
screen layout.

---

# User Experience

HelpScreen is designed to be simple and predictable.

Users should always be able to:

- Open help with HELP
- Read using the navigation keys
- Leave help using HELP or EXIT
- Continue exactly where they left off

The help system should never interrupt normal application workflow.

---

# Summary

HelpScreen provides a lightweight Markdown document viewer used by
HelpManager to display context-sensitive application documentation.

By separating document presentation from document management,
MediaPlayer3 maintains a modular architecture that is easy to extend
and maintain.

The same screen can later present user manuals, release notes,
licenses and other documentation without introducing additional user
interface components.

---

End of HELP_SCREEN_SPEC.md

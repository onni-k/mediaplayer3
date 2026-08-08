# MediaPlayer3

# Skin Manager Specification

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

SkinManager loads skin metadata, validates skin compatibility, and
loads theme colour palettes.

Skin management is implemented in skin.py.

---

# 2. Responsibilities

SkinManager is responsible for:

- Loading skins
- Validating compatibility
- Loading themes
- Providing colours
- Providing fonts
- Falling back to the default skin
- Reporting compatibility status

SkinManager is NOT responsible for:

- Screen widget positions or layout
- Playback
- Configuration storage

---

# 3. Scope Note (Build 0006)

MediaPlayer3's Screens still generate their own skin XML in Python
(the `_buildSkin()`-style pattern introduced in Build 0005 for
MainScreen's fullscreen/resolution scaling).

Build 0006 does not replace that with fully external, alternate-
*layout* skin files -- doing so would mean every Screen's widget
positions becoming externally overridable, a much larger
architectural change than "extends existing modules without changing
the established layered architecture" calls for.

What SkinManager provides for real:

- Skin metadata and compatibility validation, with the exact fallback
  behaviour described below.
- Full theme (colour palette) support, which Screens apply to their
  existing layouts.

Genuine alternate-layout skin support is left for a future build; see
docs/Claude_notes_build0006.txt for the reasoning behind this scope
decision.

---

# 4. Skin vs Theme

Skin

Defines (conceptually; Build 0006's skins only carry metadata, not
layout overrides -- see section 3):

- Metadata: name, version, compatibility, author, description
- Font family

Theme

Defines:

- Background colour
- Text colour
- Highlight colour
- Progress bar colour
- Accent colour

A single skin may support multiple themes. Themes never modify
layout; skins never define colour schemes.

---

# 5. Directory Structure

    resources/skins/
        default/
            skin.json
    resources/themes/
        default.json
        dark.json
        highcontrast.json

Skin metadata is JSON, not the XML `skin.xml`/per-screen-file layout
BUILD_0006_PLAN.md's example shows -- a deliberate simplification
given section 3's scope note.

---

# 6. Skin Metadata Format

    {
        "name": "Default",
        "version": "1.0",
        "compatible": "0.6.0",
        "author": "MediaPlayer3 Project",
        "description": "Default MediaPlayer3 skin.",
        "font_family": "Regular"
    }

`compatible` is the minimum MediaPlayer3 version the skin requires.

---

# 7. Theme Format

    {
        "name": "Dark",
        "background": "#000000",
        "text": "#A4A4A5",
        "highlight": "#0085E5",
        "progress": "#565050",
        "accent": "#191618"
    }

---

# 8. Compatibility Checking

loadSkin(name) validates the skin's `compatible` field against the
running MediaPlayer3 version.

On any problem -- missing skin, unreadable/invalid skin.json,
incompatible version:

Write warning to log

&darr;

Load default skin

&darr;

Continue application startup

The application never fails to start because of an incompatible skin.
loadSkin() and loadTheme() never raise.

---

# 9. Public Interface

    loadSkin(name) -> bool
    getSkinName() -> str
    getSkinInfo() -> dict
    getAvailableSkins() -> tuple
    getFont(default="Regular") -> str

    loadTheme(name) -> bool
    getThemeName() -> str
    getAvailableThemes() -> tuple
    getColor(key, default="#000000") -> str

    getCompatibilityReport() -> dict

---

# 10. Acceptance Criteria

- An incompatible or missing skin never prevents startup.
- getColor()/getFont() always return a usable value, even when no
  skin/theme has been explicitly selected.
- Theme changes made in SettingsScreen apply to newly-opened Screens
  without a restart.
- Skin/theme diagnostics are available on DeveloperScreen's
  Compatibility page.

---

# End of File

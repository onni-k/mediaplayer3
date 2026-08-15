# ==============================================================================
#
# MediaPlayer3
#
# File        : skin.py
#
# Description :
#
#     SkinManager
#
#     Loads skin metadata, validates skin compatibility (falling back
#     to the default skin on any problem), and loads theme colour
#     palettes. Contains no user interface code -- Screens ask
#     SkinManager for colours/fonts, they never read skin/theme files
#     themselves.
#
#     Scope note (Build 0006): MediaPlayer3's Screens still generate
#     their own skin XML in Python (the _buildSkin()-style pattern
#     introduced in Build 0005 for MainScreen's fullscreen/resolution
#     scaling). Build 0006 does not replace that with fully external,
#     alternate-*layout* skin files -- doing so would mean rewriting
#     every Screen's widget positions to be externally overridable,
#     a much larger architectural change than this build's "extends
#     existing modules without changing the established layered
#     architecture" principle calls for. What SkinManager DOES provide
#     for real: skin metadata + compatibility validation with the
#     exact fallback behaviour BUILD_0006_PLAN.md specifies, and full
#     theme (colour palette) support that Screens apply to their
#     existing layouts. See docs/Claude_notes_build0006.txt.
#
# Implements :
#
#     SKIN_MANAGER_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md v0.4 (Build 0006 -- new Core module)
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
# 2026-07-19  Build 0006
#   - Initial version.
#
# 2026-07-19  Build 0006 (device test round 1)
#   - Added a "custom" theme (CUSTOM_THEME_NAME) with no JSON file --
#     starts from the default theme's palette; setCustomColor() lets
#     SettingsScreen apply a user-entered hex colour on top of it.
#     Requested after a real device test.
#
# 2026-07-26  Build 0007 (device test round 10)
#   - Replaced pure-black (#000000) with near-black (#0A0A0A) in
#     _FALLBACK_THEME and getColor()'s own default parameter -- pure
#     black is a known chroma-key value on many DVB/Enigma2 receivers
#     (video plane shows through instead of a solid black pixel);
#     #0A0A0A avoids that while looking visually identical.
#
# 2026-07-26  Build 0007 (device test round 11)
#   - Round 10's fix didn't hold: a device screenshot still showed the
#     box's own video/background behind Main Menu. The real cause,
#     confirmed against the device's own skin.xml: Enigma2 skin
#     colours are 8-digit "#AARRGGBB", and a bare 6-digit "#RRGGBB"
#     value (what every screen's backgroundColor was still using)
#     leaves the alpha channel to be read unpredictably rather than
#     reliably opaque. Added to_opaque_skin_color(): prepends an
#     explicit "00" (opaque) alpha byte to any 6-digit colour, used
#     everywhere a colour becomes a backgroundColor attribute.
#
# 2026-07-27  Build 0007 (device test round 12)
#   - Round 11's fix still didn't stop the video/background bleeding
#     through. Added PANEL_BACKGROUND_COLOR ("#FFFFFF") and
#     PANEL_TEXT_COLOR ("#1A1A1A") -- a white background reliably
#     avoids the issue where gray/near-black backgrounds don't
#     (confirmed empirically by the user directly in a device
#     screenshot). Every text-bearing widget across every screen now
#     uses this fixed pairing instead of the active theme's own
#     background/text colours; only the outer screen edges still use
#     the theme colour.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 skin and theme management.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .logger import logger
from .paths import SKIN_PATH
from .project import VERSION

THEME_PATH = os.path.join(os.path.dirname(SKIN_PATH), "themes")

DEFAULT_SKIN_NAME = "default"
DEFAULT_THEME_NAME = "default"

# A "custom" theme has no JSON file -- its colours come from
# SettingsScreen's "Custom background color" text entry instead (Build
# 0006, requested after real device testing). loadTheme("custom")
# starts from the default theme's palette and setCustomColor()
# overrides individual keys from there.
CUSTOM_THEME_NAME = "custom"

# Used whenever a skin/theme file is missing, unreadable, or invalid --
# SkinManager must always have *something* to hand back rather than
# raising (BUILD_0006_PLAN.md "The application shall never fail to
# start because of an incompatible skin.").
_FALLBACK_THEME = {
    "name": "Default (built-in fallback)",
    "background": "#0A0A0A",
    "text": "#E6E6E6",
    "highlight": "#FF6A00",
    "progress": "#E6E6E6",
    "accent": "#4C4449",
    "inactive_highlight": "#ADD8E6",
    "selection_background": "#0056B3",
}

_FALLBACK_SKIN_INFO = {
    "name": "Default (built-in fallback)",
    "version": "1.0",
    "compatible": "0.0.0",
    "author": "MediaPlayer3 Project",
    "description": "Built-in fallback skin metadata.",
    "font_family": "Regular",
}


def _parseVersion(version_string: str):
    """
    Parse a "0.6.0"-style version string into a comparable tuple,
    ignoring any non-numeric suffix (e.g. "0.6.0-dev" -> (0, 6, 0)).
    Returns (0,) on anything unparseable, so comparisons stay safe
    rather than raising.
    """

    parts = []

    for piece in version_string.split("."):

        digits = ""

        for char in piece:

            if char.isdigit():
                digits += char
            else:
                break

        parts.append(int(digits) if digits else 0)

    return tuple(parts) if parts else (0,)


# Build 0007, device test round 12: round 11's 8-digit opaque-alpha
# fix (to_opaque_skin_color()) still didn't stop the box's own video/
# background showing through behind text (confirmed by a further
# device screenshot). The user found, empirically, that a WHITE
# background reliably avoids the issue where gray/near-black
# backgrounds don't -- visible directly in the screenshot itself, where
# MainMenu's selected/first rows render on a solid opaque white bar
# while the rest of the list shows the box's background through. Every
# text-bearing widget (Label AND List types) across every screen now
# uses this fixed white/near-black pairing instead of the active
# theme's own background/text colours, which stay reserved for the
# outer screen edges only ("Reunat saavat jäädä harmaiksi").
PANEL_BACKGROUND_COLOR = "#FFFFFF"
PANEL_TEXT_COLOR = "#1A1A1A"


def to_opaque_skin_color(hex_color: str) -> str:
    """
    Convert a "#RRGGBB" theme colour to Enigma2's 8-digit
    "#AARRGGBB" skin colour format with an explicit, fully-opaque
    alpha prefix ("00" -- Enigma2 inverts the usual ARGB convention:
    00 = opaque, FF = fully transparent).

    Build 0007, device test round 11: a real device screenshot (Main
    Menu) showed the box's own live video/background still visible
    behind a screen whose backgroundColor was a plain 6-digit
    "#RRGGBB" value, even after round 10's pure-black-avoidance fix --
    the RGB value itself was never the problem. The user-provided
    reference confirmed this directly: this device's own skin.xml
    defines every windowstyle/widget colour in 8-digit "#AARRGGBB"
    form (e.g. `<color name="black" value="#00000000"/>`), and
    Enigma2's skin engine reads a *missing* alpha channel on a bare
    6-digit value unpredictably rather than reliably as opaque.
    Applied to every backgroundColor attribute this project emits
    (never to foregroundColor/text, which doesn't have this failure
    mode).

    Already-8-digit input is returned unchanged (idempotent, so this
    is always safe to call regardless of where a colour string came
    from).
    """

    digits = hex_color.lstrip("#")

    if len(digits) == 8:
        return f"#{digits}"

    return f"#00{digits}"


class SkinManager:
    """
    Loads and validates skins; loads theme colour palettes.
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.4"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._skin_name = DEFAULT_SKIN_NAME
        self._skin_info = dict(_FALLBACK_SKIN_INFO)

        self._theme_name = DEFAULT_THEME_NAME
        self._theme_colors = dict(_FALLBACK_THEME)

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Skin] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self.loadSkin(DEFAULT_SKIN_NAME)

        self.loadTheme(DEFAULT_THEME_NAME)

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Skin
    # ------------------------------------------------------------------

    def loadSkin(self, name: str) -> bool:
        """
        Load skin `name`'s metadata and validate its compatibility.

        On any problem (missing skin, unreadable/invalid skin.json,
        incompatible version), logs a warning and falls back to the
        default skin -- per BUILD_0006_PLAN.md "Skin Compatibility":
        Write warning to log -> Load default skin -> Continue
        application startup. Never raises.

        Returns:
            True if `name` loaded and validated successfully; False if
            it fell back to the default skin instead.
        """

        self._log(f"Selected skin: {name}")

        info = self._readSkinInfo(name)

        if info is None:

            self._log(f"Skin '{name}' not found or invalid; loading default skin.")

            return self._loadDefaultSkin()

        if not self._validateCompatibility(info):

            self._log(
                f"Skin '{name}' is incompatible "
                f"(requires MediaPlayer3 >= {info.get('compatible', '?')}, "
                f"this is {VERSION}); loading default skin."
            )

            return self._loadDefaultSkin()

        self._skin_name = name
        self._skin_info = info

        self._log(f"Compatibility check passed: {name}")

        return True

    # ------------------------------------------------------------------

    def _loadDefaultSkin(self) -> bool:

        info = self._readSkinInfo(DEFAULT_SKIN_NAME)

        self._skin_name = DEFAULT_SKIN_NAME

        self._skin_info = info if info is not None else dict(_FALLBACK_SKIN_INFO)

        self._log("Default skin fallback: default")

        return False

    # ------------------------------------------------------------------

    def _readSkinInfo(self, name: str) -> Optional[Dict[str, Any]]:

        skin_json_path = os.path.join(SKIN_PATH, name, "skin.json")

        try:
            with open(skin_json_path, encoding="utf-8") as handle:

                return json.load(handle)

        except (OSError, ValueError) as error:

            logger.verbose(f"[Skin] Unable to read {skin_json_path}: {error}")

            return None

    # ------------------------------------------------------------------

    def _validateCompatibility(self, info: Dict[str, Any]) -> bool:

        required = info.get("compatible")

        if not required:
            # No requirement stated -- treat as always compatible.
            return True

        compatible = _parseVersion(VERSION) >= _parseVersion(required)

        self._log(f"Compatibility check: requires >= {required}, running {VERSION} -> {compatible}")

        return compatible

    # ------------------------------------------------------------------

    def getSkinName(self) -> str:
        return self._skin_name

    # ------------------------------------------------------------------

    def getSkinInfo(self) -> Dict[str, Any]:
        return dict(self._skin_info)

    # ------------------------------------------------------------------

    def getAvailableSkins(self):
        """
        Return the names of every skin with a readable skin.json under
        SKIN_PATH.
        """

        try:
            return tuple(
                entry for entry in sorted(os.listdir(SKIN_PATH))
                if self._readSkinInfo(entry) is not None
            )

        except OSError as error:

            logger.verbose(f"[Skin] Unable to list skins: {error}")

            return (DEFAULT_SKIN_NAME,)

    # ------------------------------------------------------------------

    def getFont(self, default: str = "Regular") -> str:
        """
        Return the current skin's font family (SkinManager
        responsibility: "Providing fonts").
        """

        return self._skin_info.get("font_family", default)

# End of Part 1
    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def loadTheme(self, name: str) -> bool:
        """
        Load theme `name`'s colour palette.

        `name` == CUSTOM_THEME_NAME ("custom") is special: it has no
        JSON file -- it starts from the default theme's palette, and
        SettingsScreen calls setCustomColor() afterwards to apply the
        user's own hex colour entry (Build 0006).

        Falls back to the default theme's palette on any other
        problem, the same way loadSkin() falls back to the default
        skin. Never raises.

        Returns:
            True if `name` loaded successfully; False if it fell back.
        """

        self._log(f"Selected theme: {name}")

        if name == CUSTOM_THEME_NAME:

            self._theme_name = CUSTOM_THEME_NAME

            self._theme_colors = self._readThemeColors(DEFAULT_THEME_NAME) or dict(_FALLBACK_THEME)

            return True

        colors = self._readThemeColors(name)

        if colors is None:

            self._log(f"Theme '{name}' not found or invalid; loading default theme.")

            colors = self._readThemeColors(DEFAULT_THEME_NAME)

            name = DEFAULT_THEME_NAME

            if colors is None:

                self._log("Default theme fallback: built-in colors.")

                colors = dict(_FALLBACK_THEME)

            fell_back = True

        else:

            fell_back = False

        self._theme_name = name

        self._theme_colors = colors

        return not fell_back

    # ------------------------------------------------------------------

    def _readThemeColors(self, name: str) -> Optional[Dict[str, str]]:

        theme_json_path = os.path.join(THEME_PATH, f"{name}.json")

        try:
            with open(theme_json_path, encoding="utf-8") as handle:

                return json.load(handle)

        except (OSError, ValueError) as error:

            logger.verbose(f"[Skin] Unable to read {theme_json_path}: {error}")

            return None

    # ------------------------------------------------------------------

    def getThemeName(self) -> str:
        return self._theme_name

    # ------------------------------------------------------------------

    def getAvailableThemes(self):
        """
        Return the names of every theme with a readable *.json under
        THEME_PATH, plus CUSTOM_THEME_NAME (which has no file -- see
        loadTheme()).
        """

        try:
            file_themes = tuple(
                os.path.splitext(entry)[0]
                for entry in sorted(os.listdir(THEME_PATH))
                if entry.endswith(".json")
            )

        except OSError as error:

            logger.verbose(f"[Skin] Unable to list themes: {error}")

            file_themes = (DEFAULT_THEME_NAME,)

        return file_themes + (CUSTOM_THEME_NAME,)

    # ------------------------------------------------------------------

    def setCustomColor(self, key: str, value: str) -> bool:
        """
        Override a single colour in the *custom* theme (Build 0006,
        requested after real device testing: "Settings kohdassa voisi
        olla taustavärin valinta mahdollisuus kirjoittamalla värikoodi,
        jos valitsee teemaksi custom").

        Only takes effect while the custom theme is active -- a no-op
        (returns False) otherwise, so a stray call can never corrupt
        one of the named, file-based themes. Validates `value` looks
        like a "#RRGGBB" hex colour before applying it; an invalid
        value is rejected (returns False) rather than silently
        applied, leaving the previous colour in place.
        """

        if self._theme_name != CUSTOM_THEME_NAME:

            self._log("setCustomColor() ignored: custom theme is not active.")

            return False

        if not self._isValidHexColor(value):

            self._log(f"setCustomColor() rejected invalid colour: {value!r}")

            return False

        self._theme_colors[key] = value

        self._log(f"Custom {key} color set: {value}")

        return True

    # ------------------------------------------------------------------

    @staticmethod
    def _isValidHexColor(value: str) -> bool:

        if not isinstance(value, str) or not value.startswith("#"):
            return False

        digits = value[1:]

        if len(digits) not in (6, 8):
            return False

        try:
            int(digits, 16)

            return True

        except ValueError:
            return False

    # ------------------------------------------------------------------

    def getColor(self, key: str, default: str = "#0A0A0A") -> str:
        """
        Return the current theme's color for `key`
        ("background"/"text"/"highlight"/"progress"/"accent"/
        "inactive_highlight"/"selection_background"), or `default`
        when the current theme doesn't define it.

        Build 0010, THEME_SPEC.md "Active Area" -- inactive_highlight/
        selection_background back every three-column/panel screen's
        column-header highlighting (Round 6 onward). Every existing
        theme file now defines both; a theme that doesn't (a custom
        or hand-edited one) simply falls back to whatever `default`
        the caller passed, exactly as before this round.
        """

        return self._theme_colors.get(key, default)

    # ------------------------------------------------------------------
    # Diagnostics (Build 0006 -- Developer Mode "Skin information" /
    # "Theme information" / "Compatibility information")
    # ------------------------------------------------------------------

    def getCompatibilityReport(self) -> Dict[str, Any]:

        return {
            "skin": self._skin_name,
            "skin_version": self._skin_info.get("version", "?"),
            "skin_compatible": self._skin_info.get("compatible", "?"),
            "skin_author": self._skin_info.get("author", "?"),
            "available_skins": ", ".join(self.getAvailableSkins()),
            "theme": self._theme_name,
            "available_themes": ", ".join(self.getAvailableThemes()),
        }

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"SkinManager(skin={self._skin_name!r}, theme={self._theme_name!r})"


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

skin_manager = SkinManager()


# ==============================================================================
#
# Build Notes
#
# SkinManager is independent of PlaybackController and ServiceController
# (BUILD_0006_PLAN.md "Design Principles"). Screens read colors/fonts
# from it; it never reads Screen state.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

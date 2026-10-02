# ==============================================================================
#
# MediaPlayer3
#
# File        : enigma_skin.py
#
# Description :
#
#     Adapter onto the currently active Enigma2 system skin.
#
#     Round 164, per direct request, replacing rounds 160-163's own
#     System Skin attempt (OpenViX-only Components.Addons.
#     ButtonSequence/ColorButtonsSequence "addon" widgets) entirely.
#     Three full device-test rounds found ButtonSequence never
#     rendered anything under any tested configuration (confirmed
#     valid key names, alphatest="blend" added to match the one real
#     working example found, z-order confirmed not the cause) and
#     ColorButtonsSequence only ever rendered two of its own four
#     connection entries regardless of their order in that attribute
#     -- both genuinely unresolved after exhausting the evidence this
#     project had access to.
#
#     This module reads colours and buttonbar icons from whatever
#     Enigma2 skin is actually active, using only standard, widely-
#     supported Enigma2 APIs (Components.Skin.skinVariables, Tools.
#     Directories.resolveFilename with SCOPE_SKIN_IMAGE) rather than
#     an OpenViX-only mechanism -- the same approach works on OpenATV,
#     OpenBH and OpenPLi as well as OpenViX, and degrades to this
#     project's own fixed fallback colours/icons cleanly on any image
#     or skin that doesn't provide something in particular, rather
#     than requiring an all-or-nothing capability check the way the
#     addon widgets did.
#
#     skinVariables is not a fully standardised interface across
#     images, and colour/icon variable names are not consistent
#     across skins even on the same image -- every lookup here tries
#     several plausible names in turn (see the alias lists below)
#     before falling back to this project's own defaults, and every
#     external call is wrapped so a missing or unexpected value never
#     raises out of this module.
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-09-17  Build 0010
#   - Initial version (round 164).
# ------------------------------------------------------------------------------

"""
Adapter onto the active Enigma2 skin, for MainScreen's own System Skin
variant. All dependency on Enigma2's own skin system is confined to
this file -- everything else in this project reaches it only through
the shared skin_adapter instance at the bottom.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from .logger import logger

try:
    from Components.Skin import skinVariables

except ImportError:
    skinVariables = {}

try:
    from Tools.Directories import (
        SCOPE_SKIN_IMAGE,
        SCOPE_SKIN,
        fileExists,
        resolveFilename,
    )

except ImportError:

    SCOPE_SKIN_IMAGE = None
    SCOPE_SKIN = None

    def resolveFilename(scope: Any, filename: str) -> str:
        return filename

    def fileExists(filename: str) -> bool:
        return os.path.exists(filename)


# This project's own fallback colours -- used whenever the active
# skin doesn't provide a usable value of its own for a given semantic
# name. Deliberately close to MainScreen's own existing "light"
# palette (mainscreen.py's own MAINSCREEN_SKIN_PALETTES["light"]) so
# a receiver whose skin offers nothing in particular still gets a
# coherent, already-proven appearance rather than something new and
# untested.
FALLBACK_COLORS = {
    "background": "#F9F9F9",
    "panel": "#F9F9F9",
    "text": "#1A1A1A",
    "text_secondary": "#6E6E6E",
    "foreground": "#1A1A1A",
    "highlight": "#036DFA",
    "selected": "#C08A45",
}


class Enigma2SkinAdapter:
    """
    Reads colours and buttonbar icons from the active Enigma2 skin.

    Skin variable names are not standardised across images or even
    across skins on the same image, so alias lists and an always-
    working fallback are used throughout rather than a single
    expected name.
    """

    def __init__(self) -> None:

        self.variables = self._getSkinVariables()

    # ------------------------------------------------------------------

    @staticmethod
    def _getSkinVariables() -> dict:
        """
        Return skinVariables safely as a plain dict.

        Confirmed present as a dict-like object in mainline Enigma2's
        own Components/Skin.py; wrapped regardless since this
        project has no way to verify its exact shape on every image
        it may run on.
        """

        if isinstance(skinVariables, dict):
            return dict(skinVariables)

        try:
            return dict(skinVariables)

        except (TypeError, ValueError):
            return {}

    # ------------------------------------------------------------------

    def variable(self, *names: str, default: Any = None) -> Any:
        """
        Return the first non-empty skin variable found among names,
        checked in the given order.
        """

        for name in names:

            value = self.variables.get(name)

            if value is not None and str(value).strip():
                return value

        return default

    # ------------------------------------------------------------------

    def color(self, semantic_name: str, default: Optional[str] = None) -> str:
        """
        Return a colour for one of this project's own semantic names
        ("background", "panel", "text", "text_secondary",
        "foreground", "highlight", "selected"), trying several
        plausible active-skin variable names first.
        """

        aliases = {
            "background": (
                "background",
                "Background",
                "BackgroundColor",
                "screenBackground",
                "ScreenBackground",
                "windowBackground",
            ),
            "panel": (
                "panelBackground",
                "PanelBackground",
                "listBackground",
                "ListboxBackground",
                "background",
            ),
            "text": (
                "foreground",
                "Foreground",
                "text",
                "Text",
                "ButtonText",
                "ListboxText",
            ),
            "text_secondary": (
                "secondaryText",
                "SecondaryText",
                "ListboxSecondText",
                "descriptionText",
            ),
            "foreground": (
                "foreground",
                "Foreground",
                "ButtonText",
                "buttonText",
                "Text",
            ),
            "highlight": (
                "highlight",
                "Highlight",
                "selection",
                "Selection",
                "ListboxSelectedBackground",
                "selectedBackground",
            ),
            "selected": (
                "selectedBackground",
                "SelectedBackground",
                "ListboxSelectedBackground",
                "selection",
                "highlight",
            ),
        }

        names = aliases.get(semantic_name, (semantic_name,))

        value = self.variable(*names)

        if value is None:
            value = default or FALLBACK_COLORS.get(semantic_name, FALLBACK_COLORS["text"])

        return self._normalizeColor(value)

    # ------------------------------------------------------------------

    @staticmethod
    def _normalizeColor(value: Any) -> str:
        """
        Normalize a skin colour value (#RRGGBB, #AARRGGBB, 0xAARRGGBB,
        or a bare name Enigma2 itself recognises) toward the plain
        #RRGGBB form this project's own code expects elsewhere.
        """

        value = str(value).strip()

        if value.startswith("0x"):
            value = "#" + value[2:]

        if not value.startswith("#"):
            return value

        if len(value) == 9:
            # #AARRGGBB -> #RRGGBB
            return "#" + value[3:]

        return value

    # ------------------------------------------------------------------

    def skinImage(self, filename: str) -> Optional[str]:
        """
        Resolve an image filename against the active skin's own
        directory, trying a few common layout conventions. Returns
        None if nothing exists at any of them.
        """

        candidates = [
            filename,
            "skin_default/" + filename,
            "buttons/" + filename,
            "skin_default/buttons/" + filename,
        ]

        for candidate in candidates:

            try:
                path = resolveFilename(SCOPE_SKIN_IMAGE, candidate)

            except Exception:
                continue

            if path and fileExists(path):
                return path

        return None

    # ------------------------------------------------------------------

    def buttonbarImage(self, button: str, fallback: Optional[str] = None) -> Optional[str]:
        """
        Return the active skin's own icon for a colour button
        ("red"/"green"/"yellow"/"blue") if one can be found, else
        fallback.
        """

        button = button.lower()
        capitalized = button[:1].upper() + button[1:]

        variable_value = self.variable(
            "Button" + capitalized,
            "button" + capitalized,
            "button_" + button,
            "Button_" + button,
            default=None,
        )

        if variable_value:

            value = str(variable_value).strip()

            if "/" in value or value.endswith((".png", ".jpg", ".svg")):

                path = self.skinImage(value)

                if path:
                    return path

        filenames = (
            f"{button}.png",
            f"button_{button}.png",
            f"key_{button}.png",
            # Round 183, per direct device confirmation: this device's
            # own /usr/share/enigma2/skin_default/buttons/ uses a
            # HYPHEN for "exit" specifically (key-exit.png), not the
            # underscore every other key here uses (key_ok.png,
            # key_menu.png, ...) -- found directly (the user checked
            # the real file on the device), not guessed. Added as a
            # general extra candidate rather than an "exit"-only
            # special case, in case another key on another image uses
            # the same hyphenated convention.
            f"key-{button}.png",
            f"{button}_button.png",
        )

        for filename in filenames:

            path = self.skinImage(filename)

            if path:
                return path

        return fallback

    # ------------------------------------------------------------------

    def fixedButtonbarImage(self, button: str, fallback: Optional[str] = None) -> Optional[str]:
        """
        Round 172, per direct request: return a colour-button icon
        from a fixed, well-known location -- ViX-Common's own buttons/
        first, then Enigma2's own base skin_default -- independent of
        whatever specific skin happens to be active, rather than
        buttonbarImage()'s own active-skin-adaptive lookup above.

        Vintage Radio wants the same, consistent colour-button
        artwork other plugins on the same box already show (per
        direct comparison against OpenWebif's/the EPG downloader's
        own icons), not something that changes depending on which
        specific OpenViX skin variant happens to be selected -- the
        opposite intent from System Skin's own buttonbarImage() use,
        which deliberately does adapt to the active skin.

        Uses plain os.path.exists() rather than resolveFilename(),
        since these are fixed, absolute filesystem paths already,
        not filenames to be resolved against whatever skin is active.
        """

        candidates = (
            f"/usr/share/enigma2/ViX-Common/buttons/{button}.png",
            f"/usr/share/enigma2/skin_default/buttons/{button}.png",
            f"/usr/share/enigma2/skin_default/{button}.png",
        )

        for path in candidates:

            try:
                if os.path.exists(path):
                    return path

            except Exception:
                continue

        return fallback

    # ------------------------------------------------------------------

    def currentSkinXml(self) -> Optional[str]:
        """
        Return the active skin.xml's own path, for diagnostics only.
        """

        if SCOPE_SKIN is None:
            return None

        try:
            path = resolveFilename(SCOPE_SKIN, "skin.xml")

        except Exception:
            return None

        return path if fileExists(path) else None

    # ------------------------------------------------------------------

    def logDiagnostics(self) -> None:
        """
        Log the active skin's own path, its own variable names, and
        which buttonbar icon (if any) was found for each colour
        button -- the same information a device log needs to explain
        what this adapter actually saw on that specific receiver.
        """

        try:
            logger.info(f"[EnigmaSkin] Active skin.xml: {self.currentSkinXml()}")
            logger.info(f"[EnigmaSkin] Skin variables: {sorted(self.variables.keys())}")

            for button in ("red", "green", "yellow", "blue"):
                logger.info(f"[EnigmaSkin] Buttonbar '{button}': {self.buttonbarImage(button)}")

            # Round 182, per direct device report ("exit ei nay --
            # onkohan se jaanyt latautumatta"): system_skin's own
            # right-edge OK/EXIT icons (mainscreen.py's own
            # lookupIcon()) go through this same buttonbarImage(), but
            # weren't logged here -- the device log's own "Skin is
            # missing element 'hint_icon_exit'" warning already showed
            # EXIT resolved to nothing, this just makes *why* (and
            # whether OK/MENU/INFO/HELP found something real, not just
            # "happened to render") visible directly in the log without
            # needing to cross-reference a Screen warning against the
            # generated skin XML by hand.
            for button in ("ok", "menu", "info", "help", "exit"):
                logger.info(f"[EnigmaSkin] Buttonbar '{button}': {self.buttonbarImage(button)}")

        except Exception as error:
            logger.verbose(f"[EnigmaSkin] logDiagnostics() failed: {error!r}")


skin_adapter = Enigma2SkinAdapter()

#end_of_file

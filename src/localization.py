# ==============================================================================
#
# MediaPlayer3
#
# File        : localization.py
#
# Description :
#
#     LocalizationManager
#
#     Loads translations and provides translated strings to the
#     Screen Layer. Owns language selection and fallback; contains no
#     user interface code.
#
# Implements :
#
#     LOCALIZATION_MANAGER_SPEC.md v0.1
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
#   - Initial version. Uses Python's stdlib gettext against .mo files
#     compiled from resources/locale/<lang>/LC_MESSAGES/MediaPlayer3.po
#     -- a base, long-standing Enigma2/Python binding (gettext ships
#     with Python itself), so no compatibility.py involvement is
#     needed here, matching the eTimer/ePicLoad precedent.
#   - Initial languages: English (source language, also shipped as its
#     own catalog) and Finnish. Only a representative subset of
#     user-visible strings is wired through translate() so far (see
#     docs/Claude_notes_build0006.txt for exactly which); full
#     app-wide coverage is intentionally left as incremental future
#     work rather than attempted in one pass.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 localization.

Other modules should never call Python's gettext directly -- they go
through the shared `localization_manager` instance's translate()
method (usually aliased locally as `_`), so language selection and
fallback stay centralized here.
"""

from __future__ import annotations

import gettext
from typing import Optional

from .logger import logger
from .paths import LOCALE_PATH

DOMAIN = "MediaPlayer3"

# Languages MediaPlayer3 ships translations for. Additional languages
# can be added by dropping a new resources/locale/<code>/LC_MESSAGES/
# MediaPlayer3.mo file in -- no source changes required
# (BUILD_0006_PLAN.md "Localization").
AVAILABLE_LANGUAGES = ("en", "fi")

FALLBACK_LANGUAGE = "en"


class LocalizationManager:
    """
    Loads translations and serves translated strings.
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.4"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._current_language = FALLBACK_LANGUAGE

        self._translation = None

        # Diagnostics (Build 0006 -- "Translation diagnostics",
        # DEVELOPER_SCREEN_SPEC.md-style counters).
        self._lookup_count = 0
        self._missing_count = 0
        self._missing_keys = set()

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Localization] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self.setLanguage(FALLBACK_LANGUAGE)

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def setLanguage(self, language_code: str) -> bool:
        """
        Load `language_code`'s catalog and make it current.

        Falls back to FALLBACK_LANGUAGE ("en") if `language_code` is
        not in AVAILABLE_LANGUAGES or its .mo file cannot be loaded --
        never raises, and MediaPlayer3 always has *some* working
        translation catalog after this returns.

        Returns:
            True if `language_code` itself loaded successfully; False
            if it fell back to FALLBACK_LANGUAGE instead (still usable,
            just not the requested language).
        """

        if language_code not in AVAILABLE_LANGUAGES:

            self._log(f"Unsupported language '{language_code}'; using fallback '{FALLBACK_LANGUAGE}'.")

            language_code = FALLBACK_LANGUAGE

        try:
            self._translation = gettext.translation(
                DOMAIN,
                localedir=LOCALE_PATH,
                languages=[language_code],
            )

            self._current_language = language_code

            self._log(f"Selected language: {language_code}")

            self._log(f"Translation loaded: {language_code}")

            return True

        except (FileNotFoundError, OSError) as error:

            self._log(f"Unable to load '{language_code}' translation: {error}")

            if language_code != FALLBACK_LANGUAGE:

                self._log(f"Falling back to '{FALLBACK_LANGUAGE}'.")

                return self.setLanguage(FALLBACK_LANGUAGE)

            # Even the fallback catalog is missing -- degrade to a
            # passthrough (translate() returns its input unchanged)
            # rather than leaving the application without any strings.
            self._translation = gettext.NullTranslations()

            self._current_language = FALLBACK_LANGUAGE

            return False

    # ------------------------------------------------------------------

    def getLanguage(self) -> str:
        """
        Return the currently active language code.
        """

        return self._current_language

    # ------------------------------------------------------------------

    def getFallbackLanguage(self) -> str:
        """
        Return the fallback language code (always "en").
        """

        return FALLBACK_LANGUAGE

    # ------------------------------------------------------------------

    def getAvailableLanguages(self):
        """
        Return the tuple of language codes MediaPlayer3 ships
        translations for.
        """

        return AVAILABLE_LANGUAGES

    # ------------------------------------------------------------------

    def translate(self, text: str, default: Optional[str] = None) -> str:
        """
        Return `text` translated into the current language.

        Returns `default` (or `text` itself if `default` is None) when
        no translation exists for `text` -- a missing translation is
        never allowed to surface as an empty or broken string, and is
        tracked for translate diagnostics (see getTranslationStats()).
        """

        self._lookup_count += 1

        if self._translation is None:
            return default if default is not None else text

        result = self._translation.gettext(text)

        # Check catalog membership directly rather than comparing
        # `result == text` -- the English catalog intentionally ships
        # identity translations (msgid == msgstr for readability), so
        # a naive equality check would flag every successful English
        # lookup as "missing".
        catalog = getattr(self._translation, "_catalog", None)

        if catalog is not None and text not in catalog:

            self._missing_count += 1

            self._missing_keys.add(text)

            logger.verbose(f"[Localization] Missing translation: '{text}' ({self._current_language})")

        return result

    # ------------------------------------------------------------------
    # Diagnostics (Build 0006 -- Developer Mode "Translation diagnostics")
    # ------------------------------------------------------------------

    def getTranslationStats(self) -> dict:
        """
        Return translation diagnostics for DeveloperScreen.
        """

        return {
            "language": self._current_language,
            "fallback_language": FALLBACK_LANGUAGE,
            "available_languages": ", ".join(AVAILABLE_LANGUAGES),
            "lookups": self._lookup_count,
            "missing": self._missing_count,
            "missing_keys": ", ".join(sorted(self._missing_keys)) or "None",
        }

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"LocalizationManager(language={self._current_language!r})"


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

localization_manager = LocalizationManager()


def _(text: str) -> str:
    """
    Shorthand translate() -- the conventional gettext alias. Screens
    import this as `from .localization import _`.
    """

    return localization_manager.translate(text)


# ==============================================================================
#
# Build Notes
#
# LocalizationManager is deliberately independent of every other
# module except logger.py and paths.py -- PlaybackController and
# ServiceController must never depend on it (BUILD_0006_PLAN.md
# "Design Principles": "PlaybackController remains independent of
# ... LocalizationManager").
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

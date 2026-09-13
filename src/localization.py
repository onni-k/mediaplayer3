# ==============================================================================
#
# MediaPlayer3
#
# File        : localization.py
#
# Description :
#
#     MediaPlayer3 localization.
#
#     Round 140, per direct request (programmer feedback: "Translation
#     setup is over-complicated versus Enigma2 convention -- typically
#     a handful of lines directly in __init__.py, not a dedicated
#     LocalizationManager module/class"): rewritten to match the real,
#     widely-used Enigma2 plugin convention confirmed against several
#     real plugins' own __init__.py (IMDb, ShareMyBox, FileBrowser) --
#     a module-level _() using gettext directly against the receiver's
#     own current system language (Components.config's config.osd.
#     language.value, read fresh on every call, matching this
#     project's own established "always live, never baked in once"
#     precedent from config.py's own ConfigYesNoLocalized).
#
#     This also means MediaPlayer3 no longer offers an independent
#     language choice of its own -- a direct, deliberate decision made
#     when this rewrite was scoped, not an oversight: every other
#     Enigma2 plugin surveyed for this rewrite follows the box's own
#     OSD language exclusively, and MediaPlayer3 now does the same.
#     The removed Settings -> Language choice, config.py's own
#     resolveLanguageCode()/_AVAILABLE_LANGUAGE_CODES, and every
#     caller of the old LocalizationManager's own setLanguage()/
#     getLanguage() were all removed together with this file's own
#     rewrite -- see this round's own Claude_notes entry for the full
#     list of touched files.
#
# Implements :
#
#     LOCALIZATION_MANAGER_SPEC.md v0.1 (superseded by this rewrite --
#     see this file's own Description above)
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
#
# 2026-09-09  Build 0010 (device test round 140)
#   - Rewritten from a dedicated LocalizationManager class down to a
#     module-level _() following the box's own system language
#     directly (see this file's own Description block above for the
#     full reasoning). Independent language selection removed
#     entirely, project-wide.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 localization.

Other modules import `_` directly: `from .localization import _`.
"""

from __future__ import annotations

import gettext

from .compatibility import compatibility
from .paths import LOCALE_PATH

DOMAIN = "MediaPlayer3"

# Languages MediaPlayer3 ships a translation catalog for. A new
# language needs both its own resources/locale/<code>/LC_MESSAGES/
# MediaPlayer3.mo file (compiled from po/<code>.po -- see round 135's
# own mediaplayer3.bb do_compile()) AND its code added here.
AVAILABLE_LANGUAGES = ("en", "fi", "sv", "de", "es")

FALLBACK_LANGUAGE = "en"

# Cache of already-loaded gettext translation objects, keyed by
# language code -- avoids re-reading the .mo file from disk on every
# single _() call while still checking the box's own current system
# language fresh every time (so a live language change, e.g. from
# Enigma2's own Settings, takes effect on this app's own very next
# translated string, no restart needed).
_translation_cache = {}


def _loadTranslation(language_code: str):

    if language_code in _translation_cache:

        return _translation_cache[language_code]

    try:
        translation = gettext.translation(DOMAIN, localedir=LOCALE_PATH, languages=[language_code])

    except (FileNotFoundError, OSError):

        if language_code != FALLBACK_LANGUAGE:

            return _loadTranslation(FALLBACK_LANGUAGE)

        # Even the fallback catalog is missing -- degrade to a
        # passthrough (gettext() returns its input unchanged) rather
        # than leaving the application without any strings at all.
        translation = gettext.NullTranslations()

    _translation_cache[language_code] = translation

    return translation


def getCurrentLanguage() -> str:
    """
    Return the language code MediaPlayer3 is actually translating
    into right now -- the receiver's own current system language if
    MediaPlayer3 ships a catalog for it, FALLBACK_LANGUAGE otherwise.
    """

    system_language = compatibility.getSystemLanguage(fallback_language_code=FALLBACK_LANGUAGE)

    return system_language if system_language in AVAILABLE_LANGUAGES else FALLBACK_LANGUAGE


def _(text: str) -> str:
    """
    Translate `text` into the receiver's own current system language.

    Always returns a usable string -- an untranslated `text` when no
    catalog entry exists, exactly matching gettext's own standard
    behaviour.
    """

    return _loadTranslation(getCurrentLanguage()).gettext(text)


# ==============================================================================
#
# Build Notes
#
# localization.py is deliberately independent of every other module
# except compatibility.py and paths.py -- PlaybackController and
# ServiceController must never depend on it (BUILD_0006_PLAN.md
# "Design Principles": "PlaybackController remains independent of
# ... LocalizationManager").
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

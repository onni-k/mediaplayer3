# MediaPlayer3

# Localization Manager Specification

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

LocalizationManager provides centralized translation of user-visible
text.

It is responsible for loading translation catalogs, selecting the
active language, providing translated strings and reporting
translation diagnostics.

Localization is implemented in localization.py.

---

# 2. Responsibilities

LocalizationManager is responsible for:

- Loading translations
- Selecting language
- Providing translated strings
- Language fallback
- Translation diagnostics

LocalizationManager is NOT responsible for:

- Screen layout
- Playback
- Configuration storage (it reads "general.language" through
  ConfigurationManager like any other module would)

---

# 3. Architecture

LocalizationManager is a Core module.

It depends only on logger.py and paths.py.

PlaybackController and ServiceController never depend on
LocalizationManager (BUILD_0006_PLAN.md "Design Principles").

Screens import the shared translate() alias as `from .localization
import _` and wrap user-visible strings with `_("...")`.

---

# 4. Implementation

LocalizationManager uses Python's standard library `gettext` module
against compiled `.mo` catalogs -- gettext ships with Python itself,
so no compatibility.py involvement is needed, matching the
eTimer/ePicLoad precedent (base bindings used directly, not
platform-variable APIs).

Catalog files live under:

    resources/locale/<language>/LC_MESSAGES/MediaPlayer3.mo
    resources/locale/<language>/LC_MESSAGES/MediaPlayer3.po

The `.po` file is the human-editable source; `.mo` is the compiled
binary catalog Python's gettext actually loads. Both are shipped so
translators can find and edit the source directly.

---

# 5. Public Interface

    setLanguage(language_code) -> bool

    getLanguage() -> str

    getFallbackLanguage() -> str

    getAvailableLanguages() -> tuple

    translate(text, default=None) -> str

    getTranslationStats() -> dict

`translate()` is normally called through the shared `_()` alias.

---

# 6. Languages

Initial languages:

- English (en) -- also the fallback language
- Finnish (fi)

Additional languages may be added by dropping a new
`resources/locale/<code>/LC_MESSAGES/MediaPlayer3.mo` file in --  no
source changes required.

---

# 7. Fallback Behaviour

setLanguage() never raises.

If the requested language is not in AVAILABLE_LANGUAGES, or its `.mo`
file cannot be loaded, LocalizationManager falls back to English.

If even English cannot be loaded, LocalizationManager degrades to a
passthrough (translate() returns its input unchanged) rather than
leaving the application without any strings.

translate() itself never raises and never returns an empty string for
a non-empty input -- a missing translation returns the original text
(or an explicit `default` argument, if given).

Device test round 66: LocalizationManager itself is unchanged by the
new "System" language option (Settings -> Language) -- setLanguage()
still only ever receives an actual 2-letter code ("en"/"fi"), never
the literal string "system". Resolving "System" to a real language
code is config.py's own responsibility (resolveLanguageCode()), one
layer above LocalizationManager; see SETTINGSSCREEN_SPEC.md's own
Language section for how and when that resolution happens.

---

# 8. Translation Diagnostics

getTranslationStats() returns:

- Current language
- Fallback language
- Available languages
- Total lookups performed
- Missing translation count
- Missing translation keys

Diagnostics are exposed on DeveloperScreen's Localization page.

A lookup counts as "missing" only when the requested string is not
present in the loaded catalog at all -- not when the translated value
happens to equal the original text (the English catalog intentionally
ships identity translations, msgid == msgstr, so this distinction
matters; see docs/Claude_notes_build0006.txt for the bug this caught
during implementation).

---

# 9. Coverage

Build 0006 wires translate() through a representative subset of
user-visible strings across MainScreen, BrowserScreen and Main Menu --
not literally every string in the application. Full application-wide
coverage is intentionally left as incremental future work rather than
attempted in one pass; docs/Claude_notes_build0006.txt lists exactly
which strings are covered.

---

# 10. Acceptance Criteria

- setLanguage() never raises, always leaves a working catalog loaded.
- Missing translations degrade to the original text, never to an
  empty or broken string.
- Language changes made in SettingsScreen apply to newly-opened
  Screens without a restart.
- Translation diagnostics are available on DeveloperScreen.

---

# End of File

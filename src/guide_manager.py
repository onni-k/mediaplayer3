# ==============================================================================
#
# MediaPlayer3
#
# File        : guide_manager.py
#
# Description :
#
#     GuideManager
#
#     Loads a screen's context-sensitive help document
#     (resources/help/<screen_id>.md) and renders it into the plain,
#     line-based text GuideScreen can display -- Enigma2's Label
#     widgets have no rich Markdown rendering, so headings/code
#     fences/etc. are converted to a readable plain-text layout rather
#     than passed through as raw Markdown syntax.
#
#     GuideManager never opens GuideScreen itself (HELP_MANAGER_SPEC.md
#     "GuideManager shall not: Display application screens") -- each
#     screen's own infoPressed() calls getGuide() for its own content,
#     then opens GuideScreen itself, matching how every other manager
#     in this project (PlaylistManager, InternetRadioManager, ...)
#     never calls session.open() either.
#
#     Round 139, per direct request: renamed from HelpManager/
#     help_manager.py once every screen's own HELP button started
#     opening Enigma2's own native help guide instead (rounds 130-131)
#     -- this module's own content is what EPG/INFO opens now, so its
#     own identity moved to match ("Tiedot"/"Information" to the user).
#     Named GuideManager rather than something built on "Information"
#     specifically to avoid colliding with the unrelated, pre-existing
#     InformationPanel (MainScreen's own lyrics/metadata/codec display)
#     -- two different things called "Information" in the same
#     codebase would be confusing, so this one uses a different word
#     internally while still presenting as "Information"/"Tiedot" to
#     the user.
#
# Implements :
#
#     HELP_MANAGER_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md (Build 0008 -- new Core module)
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
# 2026-07-28  Build 0008
#   - Initial version.
#
# 2026-09-09  Build 0010 (device test round 139)
#   - Renamed from HelpManager/help_manager.py (see this file's own
#     Description block above for the full reasoning). getHelp()
#     renamed to getGuide(); _fallbackHelp() renamed to
#     _fallbackGuide(); the fallback title/message strings changed
#     from "Help"/"No help available." to "Information"/"No
#     information available." (translations updated to match).
# ------------------------------------------------------------------------------

"""
GuideManager -- loads and renders context-sensitive help documents.
"""

from __future__ import annotations

import os
from typing import Tuple

from .localization import _, getCurrentLanguage
from .logger import logger
from .paths import HELP_PATH


class GuideManager:
    """
    Loads Markdown help documents from resources/help/ and renders
    them into plain text suitable for GuideScreen's Label-based
    viewer.
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Guide] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Public interface (HELP_MANAGER_SPEC.md "Context Sensitive Help")
    # ------------------------------------------------------------------

    def getGuide(self, screen_id: str) -> Tuple[str, str]:
        """
        Return (title, rendered_text) for `screen_id`
        (e.g. "mainscreen"). Falls back to a generic "no help
        available" message if the document is missing or unreadable
        -- never raises (HELP_MANAGER_SPEC.md "Application operation
        is never interrupted due to missing help files.").

        Round 144, per direct request: looks for a translated document
        first (resources/help/<lang>/<screen_id>.md, e.g. help/fi/
        mainscreen.md), falling back to the existing untranslated
        English path (resources/help/<screen_id>.md) whenever no
        translation exists for the receiver's own current system
        language -- so a partially-translated set is genuinely safe to
        ship (any screen without its own translation simply keeps
        showing English), and adding a language later needs no code
        change at all, just new files in the right folder.

        Deliberately does NOT fall back to a DIFFERENT non-English
        translation: only the current language or English, nothing
        else, so a user never sees a language they didn't ask for.
        """

        candidate_paths = []

        language = getCurrentLanguage()

        # English is the untranslated source language these documents
        # are written in, so its own files live directly in help/ --
        # no help/en/ subfolder is expected or looked for.
        if language != "en":

            candidate_paths.append(os.path.join(HELP_PATH, language, f"{screen_id}.md"))

        candidate_paths.append(os.path.join(HELP_PATH, f"{screen_id}.md"))

        for path in candidate_paths:

            try:

                with open(path, "r", encoding="utf-8") as help_file:

                    markdown_text = help_file.read()

            except OSError:

                continue

            title, body = self._splitTitle(markdown_text)

            return title, self._renderMarkdown(body)

        self._log(f"No help document for '{screen_id}' (tried: {', '.join(candidate_paths)})")

        return self._fallbackGuide()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fallbackGuide(self) -> Tuple[str, str]:

        return _("Information"), _("No information available.")

    # ------------------------------------------------------------------

    def _splitTitle(self, markdown_text: str) -> Tuple[str, str]:
        """
        A help document's own leading "# Title" line (if present)
        becomes GuideScreen's title bar instead of being rendered as
        part of the body -- avoids showing the same title twice.
        """

        lines = markdown_text.split("\n")

        title = _("Information")

        body_start = 0

        for index, line in enumerate(lines):

            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("# "):

                title = stripped[2:].strip()

                body_start = index + 1

            break

        return title, "\n".join(lines[body_start:])

    # ------------------------------------------------------------------

    def _renderMarkdown(self, markdown_text: str) -> str:
        """
        Convert a lightweight Markdown subset (headings, bullet/
        numbered lists, code fences, "---" rules, paragraphs) into
        plain, readable lines -- HELP_MANAGER_SPEC.md/HELP_SCREEN_SPEC.md
        both note that unsupported elements should be ignored
        gracefully rather than shown as raw syntax.
        """

        rendered_lines = []

        in_code_block = False

        for raw_line in markdown_text.split("\n"):

            line = raw_line.rstrip()

            stripped = line.strip()

            if stripped.startswith("```"):

                in_code_block = not in_code_block

                continue

            if in_code_block:

                rendered_lines.append(line)

                continue

            if stripped == "---":
                continue

            if stripped.startswith("### "):

                rendered_lines.append("")
                rendered_lines.append(stripped[4:].strip())
                continue

            if stripped.startswith("## "):

                rendered_lines.append("")
                rendered_lines.append(stripped[3:].strip())
                continue

            if stripped.startswith("# "):

                heading = stripped[2:].strip().upper()

                rendered_lines.append("")
                rendered_lines.append(heading)
                continue

            rendered_lines.append(line)

        return self._collapseBlankLines(rendered_lines)

    # ------------------------------------------------------------------

    def _collapseBlankLines(self, lines) -> str:

        collapsed = []

        blank_run = 0

        for line in lines:

            if line == "":

                blank_run += 1

                if blank_run > 1:
                    continue

            else:

                blank_run = 0

            collapsed.append(line)

        return "\n".join(collapsed).strip("\n")

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> dict:

        try:

            available = sorted(
                entry[:-3]
                for entry in os.listdir(HELP_PATH)
                if entry.endswith(".md")
            )

        except OSError:

            available = []

        # Round 144: also report which translated document sets are
        # actually present (help/<lang>/ subfolders), so a support log
        # shows at a glance whether a user's own language has its own
        # documents or is falling back to English. os.listdir()'s own
        # ".md" filter above already excludes these subfolders from
        # available_documents itself, so that list stays exactly as
        # it was.
        try:

            translated = sorted(
                entry
                for entry in os.listdir(HELP_PATH)
                if os.path.isdir(os.path.join(HELP_PATH, entry))
            )

        except OSError:

            translated = []

        return {
            "help_path": HELP_PATH,
            "available_documents": available,
            "document_count": len(available),
            "current_language": getCurrentLanguage(),
            "translated_document_sets": translated,
        }


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

guide_manager = GuideManager()

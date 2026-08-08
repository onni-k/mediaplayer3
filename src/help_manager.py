# ==============================================================================
#
# MediaPlayer3
#
# File        : help_manager.py
#
# Description :
#
#     HelpManager
#
#     Loads a screen's context-sensitive help document
#     (resources/help/<screen_id>.md) and renders it into the plain,
#     line-based text HelpScreen can display -- Enigma2's Label
#     widgets have no rich Markdown rendering, so headings/code
#     fences/etc. are converted to a readable plain-text layout rather
#     than passed through as raw Markdown syntax.
#
#     HelpManager never opens HelpScreen itself (HELP_MANAGER_SPEC.md
#     "HelpManager shall not: Display application screens") -- each
#     screen's own helpPressed() calls getHelp() for its own content,
#     then opens HelpScreen itself, matching how every other manager
#     in this project (PlaylistManager, InternetRadioManager, ...)
#     never calls session.open() either.
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
# ------------------------------------------------------------------------------

"""
HelpManager -- loads and renders context-sensitive help documents.
"""

from __future__ import annotations

import os
from typing import Tuple

from .localization import _
from .logger import logger
from .paths import HELP_PATH


class HelpManager:
    """
    Loads Markdown help documents from resources/help/ and renders
    them into plain text suitable for HelpScreen's Label-based
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

        logger.info("[Help] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------
    # Public interface (HELP_MANAGER_SPEC.md "Context Sensitive Help")
    # ------------------------------------------------------------------

    def getHelp(self, screen_id: str) -> Tuple[str, str]:
        """
        Return (title, rendered_text) for `screen_id`
        (e.g. "mainscreen"). Falls back to a generic "no help
        available" message if the document is missing or unreadable
        -- never raises (HELP_MANAGER_SPEC.md "Application operation
        is never interrupted due to missing help files.").
        """

        path = os.path.join(HELP_PATH, f"{screen_id}.md")

        try:

            with open(path, "r", encoding="utf-8") as help_file:

                markdown_text = help_file.read()

        except OSError as error:

            self._log(f"No help document for '{screen_id}': {error}")

            return self._fallbackHelp()

        title, body = self._splitTitle(markdown_text)

        return title, self._renderMarkdown(body)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fallbackHelp(self) -> Tuple[str, str]:

        return _("Help"), _("No help available.")

    # ------------------------------------------------------------------

    def _splitTitle(self, markdown_text: str) -> Tuple[str, str]:
        """
        A help document's own leading "# Title" line (if present)
        becomes HelpScreen's title bar instead of being rendered as
        part of the body -- avoids showing the same title twice.
        """

        lines = markdown_text.split("\n")

        title = _("Help")

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

        return {
            "help_path": HELP_PATH,
            "available_documents": available,
            "document_count": len(available),
        }


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

help_manager = HelpManager()

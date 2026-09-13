# ==============================================================================
# MediaPlayer3 -- diagnostics.py
# ==============================================================================
#
# Round 136, per direct request ("Kehittajatyokalut -sivu voidaan myos
# poistaa. Siella nakyvat tiedot saisi kaikki tulla lokiin
# verbose-asetuksella." -- the Developer Tools screen can be removed
# too; the information it showed should all come to the log at the
# verbose setting instead): this module replaces the whole interactive
# DeveloperScreen (a Screen with its own ActionMap, scrollable page
# list, and skin) with a single function, logStartupDiagnostics(),
# called once from MainScreen's own startup. Every one of
# DeveloperScreen's own 10 diagnostic pages is preserved here --
# nothing about WHAT gets reported changed, only that it's written to
# the log (only actually appearing when Logging Level is set to
# Verbose, exactly matching the request) instead of requiring a
# dedicated menu entry and screen to view interactively.
#
# Most of DeveloperScreen's own page methods already called a
# standalone manager method (playlist_manager.getDiagnostics(),
# storage_manager.getDiagnostics(), internetradio_manager.
# getDiagnostics(), systeminfo.getSummary(), compatibility.
# getCompatibilityReport(), skin_manager.getCompatibilityReport())
# that needed no live Screen instance at all -- confirmed by reading
# each one directly before
# assuming this refactor was even feasible. Only the runtime/metadata
# sections needed a PlaybackController instance, which
# logStartupDiagnostics() below takes as its own parameter (the same
# one MainScreen already owns for its own entire lifetime), and the
# build section, which needed no live state at all.
#
# ==============================================================================

from __future__ import annotations

from . import metadata as md
from .compatibility import compatibility
from .config import config_manager
from .internetradio_manager import internetradio_manager
from .localization import AVAILABLE_LANGUAGES, getCurrentLanguage
from .logger import logger
from .paths import LOG_PATH
from .playlist_manager import playlist_manager
from .project import APPLICATION_ID, AUTHOR, COPYRIGHT, LICENSE, PROJECT_NAME
from .skin import skin_manager
from .storage import storage_manager
from .systeminfo import systeminfo
from .version import get_build, get_version

# ------------------------------------------------------------------


def logStartupDiagnostics(playback_controller) -> None:
    """
    Writes every one of DeveloperScreen's own former 10 diagnostic
    sections to the log via logger.verbose() -- a no-op unless Logging
    Level is set to Verbose (Settings -> Logger), exactly matching the
    direct request this replaces the old interactive screen with.

    Args:
        playback_controller: MainScreen's own PlaybackController
            instance, needed for the runtime/metadata sections. Safe
            to call before any media has ever been loaded -- both
            sections handle a controller with nothing loaded yet the
            same way DeveloperScreen's own versions always did.
    """

    logger.verbose("[Diagnostics] ---- Build Information ----")

    for line in _buildSection(playback_controller):

        logger.verbose(f"[Diagnostics] {line}")

    logger.verbose("[Diagnostics] ---- Runtime Status ----")

    for line in _runtimeSection(playback_controller):

        logger.verbose(f"[Diagnostics] {line}")

    logger.verbose("[Diagnostics] ---- Metadata & Artwork ----")

    for line in _metadataSection(playback_controller):

        logger.verbose(f"[Diagnostics] {line}")

    logger.verbose("[Diagnostics] ---- Localization ----")

    # Round 140: LocalizationManager's own getTranslationStats()
    # (lookup/missing-key counters) no longer exists -- removed along
    # with the class itself when localization.py was simplified to
    # match the standard Enigma2 plugin convention (see that file's
    # own round 140 comment). Reports just the language actually in
    # use now.
    logger.verbose(f"[Diagnostics] language: {getCurrentLanguage()}")
    logger.verbose(f"[Diagnostics] available_languages: {', '.join(AVAILABLE_LANGUAGES)}")

    logger.verbose("[Diagnostics] ---- Storage ----")

    for key, value in storage_manager.getDiagnostics().items():

        logger.verbose(f"[Diagnostics] {key}: {value}")

    logger.verbose("[Diagnostics] ---- Playlists ----")

    for key, value in playlist_manager.getDiagnostics().items():

        logger.verbose(f"[Diagnostics] {key}: {value}")

    logger.verbose("[Diagnostics] ---- Internet Radio ----")

    for key, value in internetradio_manager.getDiagnostics().items():

        logger.verbose(f"[Diagnostics] {key}: {value}")

    logger.verbose("[Diagnostics] ---- Logger ----")

    logger.verbose(
        f"[Diagnostics] Developer Mode: "
        f"{'On' if config_manager.isDeveloperMode() else 'Off'} (derived from Logging Level)"
    )
    logger.verbose(f"[Diagnostics] Logging level: {config_manager.getDeveloperLogLevel()}")
    logger.verbose(f"[Diagnostics] Log directory: {LOG_PATH}")

    logger.verbose("[Diagnostics] ---- System Information ----")

    for section, values in systeminfo.getSummary().items():

        logger.verbose(f"[Diagnostics] {section}:")

        if isinstance(values, dict):

            for key, value in values.items():

                logger.verbose(f"[Diagnostics]     {key}: {value}")

        else:

            logger.verbose(f"[Diagnostics]     {values}")

    logger.verbose("[Diagnostics] ---- Compatibility ----")

    for key, value in compatibility.getCompatibilityReport().items():

        logger.verbose(f"[Diagnostics] {key}: {value}")

    logger.verbose("[Diagnostics] Skin & Theme:")

    for key, value in skin_manager.getCompatibilityReport().items():

        logger.verbose(f"[Diagnostics]   {key}: {value}")


# ------------------------------------------------------------------


def _buildSection(playback_controller) -> list:

    return [
        f"Application: {PROJECT_NAME}",
        f"Application ID: {APPLICATION_ID}",
        f"Version: {get_version()}",
        f"Build: {get_build()}",
        f"Author: {AUTHOR}",
        f"{COPYRIGHT}",
        f"License: {LICENSE}",
    ]


# ------------------------------------------------------------------


def _runtimeSection(playback_controller) -> list:

    if playback_controller is not None:

        current_file = playback_controller.getCurrentFile() or "None"
        state = playback_controller.getState()
        elapsed = playback_controller.getElapsedTime()
        duration = playback_controller.getDuration()
        queue_size = playback_controller.getQueueSize()
        queue_position = playback_controller.getQueuePosition()
        stream_info = playback_controller.getStreamInfo()

    else:

        current_file = "Unknown"
        state = "Unknown"
        elapsed = None
        duration = None
        queue_size = 0
        queue_position = 0
        stream_info = {
            "codec": "Unknown",
            "sample_rate": "Unknown",
            "bitrate": "Unknown",
            "channels": "Unknown",
        }

    if elapsed is not None and duration is not None:
        remaining = max(0, duration - elapsed)
    else:
        remaining = None

    return [
        f"Current media: {current_file}",
        f"Playback state: {state}",
        f"Queue position: {queue_position if queue_size else 'Unknown'}",
        f"Queue size: {queue_size}",
        f"Elapsed: {elapsed if elapsed is not None else 'Unknown'}",
        f"Remaining: {remaining if remaining is not None else 'Unknown'}",
        f"Duration: {duration if duration is not None else 'Unknown'}",
        f"Codec: {stream_info['codec']}",
        f"Sample rate: {stream_info['sample_rate']}",
        f"Bitrate: {stream_info['bitrate']}",
        f"Channels: {stream_info['channels']}",
    ]


# ------------------------------------------------------------------


def _metadataSection(playback_controller) -> list:

    if playback_controller is None:

        return ["No metadata available (no PlaybackController)."]

    metadata = playback_controller.getMetadata()

    if metadata is None:

        return ["No metadata loaded (no media played yet)."]

    lines = [f"Metadata source: {metadata.get('source', 'None')}"]

    for field in md.FIELDS:

        lines.append(f"{field}: {metadata.get(field, 'Unknown')}")

    lines.append(f"Bit depth: {metadata.get('bit_depth', 'Unknown')}")
    lines.append(f"File size: {metadata.get('file_size', 'Unknown')}")

    embedded = playback_controller.getEmbeddedArtwork()

    if embedded is not None:

        mime_type, image_bytes = embedded

        lines.append(f"Embedded artwork: {mime_type}, {len(image_bytes)} bytes")

    else:

        lines.append("Embedded artwork: None")

    return lines

# ------------------------------------------------------------------
# End of file
# ------------------------------------------------------------------

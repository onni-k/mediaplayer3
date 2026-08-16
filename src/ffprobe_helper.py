# ==============================================================================
#
# MediaPlayer3
#
# File        : ffprobe_helper.py
#
# Description :
#
#     ffprobe_helper
#
#     Runs ffprobe (part of the ffmpeg project, distinct from the
#     gstreamer/exteplayer3 machinery PlaybackController itself uses
#     for actual playback) against a local file path or a stream URL,
#     and returns real, measured codec/sample-rate/bitrate/channel
#     information -- confirmed present on at least one real device
#     (device test round 27) but NOT guaranteed on every Enigma2
#     image, so every public function here degrades to None on any
#     failure: missing binary, timeout, unreachable stream, malformed
#     output. Never raises.
#
#     This exists because none of MediaPlayer3's existing codec
#     information sources are a real measurement: Enigma2's own
#     getStreamInfo() API is frequently unavailable for GStreamer-
#     based playback (see information_panel.py's own _buildCodecPage()
#     docstring), the local-file fallback only guesses from the file
#     extension, and the streaming fallback only repeats whatever
#     RadioBrowser itself was told about a station, not what the
#     stream actually is. ffprobe, where available, is an actual
#     measurement of the real audio data.
#
#     Deliberately a thin, single-purpose wrapper -- no caching, no
#     scheduling, no UI. Callers (information_panel.py,
#     radiobrowserscreen.py) own those decisions for their own
#     contexts, since a local file probe and a live-stream probe have
#     very different performance/UX tradeoffs (see probe()'s own
#     docstring).
#
# Implements :
#
#     Device test round 27 (user request, with a link to
#     https://ottverse.com/ffprobe-comprehensive-tutorial-with-examples/
#     for reference)
#
# Project :
#
#     MediaPlayer3
#
# License :
#
#     GPL-3.0-or-later
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-08-16  Build 0010 (round 27)
#   - Initial version.
# ------------------------------------------------------------------------------

"""
ffprobe_helper -- real, measured codec information via ffprobe, where
available. Every public function degrades to None on any failure
(missing binary, timeout, malformed output) rather than raising.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Optional

from .logger import logger

# Conservative -- a live stream needs time to connect and buffer
# enough data to identify itself; a local file resolves almost
# instantly. Long enough to be useful, short enough that a single
# unresponsive stream can't hang the caller for an unreasonable time
# (this call is expected to run on Enigma2's own single GUI thread --
# see probe()'s own docstring for why callers must keep this in mind).
DEFAULT_TIMEOUT_SECONDS = 6

_availability_checked = False
_is_available = False


def isAvailable() -> bool:
    """
    Whether the ffprobe binary is actually present on this system.
    Checked once per process and cached -- repeatedly spawning a
    process just to answer this would defeat the point of caching it.
    """

    global _availability_checked, _is_available

    if _availability_checked:
        return _is_available

    _availability_checked = True

    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )

        _is_available = result.returncode == 0

    except (OSError, subprocess.TimeoutExpired) as error:

        logger.info(f"[FFprobe] Not available: {error}")

        _is_available = False

    logger.info(f"[FFprobe] Availability: {_is_available}")

    return _is_available


def probe(path_or_url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Optional[Dict[str, Any]]:
    """
    Run ffprobe against `path_or_url` (a local file path or a stream
    URL) and return real, measured info from its first audio stream:

        {"codec": "mp3", "sample_rate": "44100 Hz", "bitrate": "128 kbps",
         "channels": "2"}

    Any field ffprobe didn't report is simply absent from the
    returned dict -- callers already treat a missing field as
    "unknown" (see information_panel.py's own values.get(...,
    metadata_module.UNKNOWN) pattern).

    Returns None if ffprobe isn't available (isAvailable() is checked
    first), the process times out, the target has no audio stream, or
    the output can't be parsed. Never raises.

    Blocking: this runs ffprobe synchronously and waits up to
    `timeout` seconds. Fine for an occasional, deliberate action (a
    local file, or a user explicitly opening the Codec information
    page); NOT fine to call on every list-navigation keypress against
    a live stream URL without a caller-side debounce -- Enigma2's own
    GUI runs on a single thread, so this call blocks the whole
    interface for however long it takes. Every current caller debounces
    or gates this appropriately in its own way; any future caller
    needs to do the same.
    """

    if not isAvailable():
        return None

    command = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "a:0",
        "-timeout", str(timeout * 1_000_000),  # ffprobe's own network timeout, microseconds
        path_or_url,
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )

    except subprocess.TimeoutExpired:

        logger.info(f"[FFprobe] Probe timed out: {path_or_url}")

        return None

    except OSError as error:

        logger.info(f"[FFprobe] Probe failed to start: {error}")

        return None

    if result.returncode != 0 or not result.stdout:

        logger.verbose(f"[FFprobe] No usable output for: {path_or_url}")

        return None

    try:
        data = json.loads(result.stdout)

    except (json.JSONDecodeError, UnicodeDecodeError) as error:

        logger.info(f"[FFprobe] Could not parse output: {error}")

        return None

    streams = data.get("streams") or []

    if not streams:

        logger.verbose(f"[FFprobe] No audio stream found: {path_or_url}")

        return None

    stream = streams[0]

    info: Dict[str, Any] = {}

    codec_name = stream.get("codec_name")

    if codec_name:
        info["codec"] = codec_name.upper()

    sample_rate = stream.get("sample_rate")

    if sample_rate:

        try:
            info["sample_rate"] = f"{int(sample_rate)} Hz"

        except (TypeError, ValueError):
            pass

    bit_rate = stream.get("bit_rate") or data.get("format", {}).get("bit_rate")

    if bit_rate:

        try:
            info["bitrate"] = f"{int(bit_rate) // 1000} kbps"

        except (TypeError, ValueError):
            pass

    channels = stream.get("channels")

    if channels:
        info["channels"] = str(channels)

    return info or None


# ==============================================================================
# End of file
# ==============================================================================

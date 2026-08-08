# ==============================================================================
#
# MediaPlayer3
#
# File        : metadata.py
#
# Description :
#
#     MetadataReader
#
#     Extracts tag metadata (artist/album/title/... and embedded
#     artwork) from supported audio files. Pure Python, no external
#     dependencies (mutagen etc. cannot be assumed present on the
#     receiver) -- reads the FLAC, ID3v2 (MP3) and Ogg Vorbis Comment
#     binary formats directly.
#
#     Metadata providers own extraction; PlaybackController only
#     calls read() and caches the result (BUILD_0006_PLAN.md
#     "Metadata Design Principles").
#
# Implements :
#
#     METADATA_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md v0.4 (Build 0006)
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
#   - Initial version: FLAC (Vorbis Comment + STREAMINFO + PICTURE
#     blocks), ID3v2.3/2.4 (MP3, text frames + APIC), Ogg Vorbis
#     Comment (page/packet reconstruction + comment header).
#   - Every parser is wrapped so a malformed or unsupported file can
#     never raise past read() -- it just returns whatever fields were
#     successfully parsed (BUILD_0006_PLAN.md "If metadata is
#     unavailable, MediaPlayer3 shall display sensible default
#     values." / "Metadata processing shall never block playback
#     startup unnecessarily.").
#
# 2026-07-28  Build 0008
#   - Added embedded lyrics support for LyricsManager
#     (LYRICS_MANAGER_SPEC.md "Embedded Lyrics"): ID3v2 USLT frames
#     (reusing _decodeCommentFrame(), since USLT and COMM share the
#     same encoding+language+description+text structure) and FLAC/Ogg
#     Vorbis "LYRICS"/"UNSYNCEDLYRICS" comment fields both now
#     populate metadata["lyrics"]. Not added to FIELDS -- it's not
#     surfaced in the generic metadata display (DeveloperScreen etc.),
#     only read directly by LyricsManager.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 metadata extraction.

Returns a plain dict from read(); PlaybackController is the only
caller that matters in practice, but this module has no dependency on
it (or on anything else in this codebase besides logger.py) -- it is
pure file parsing.
"""

from __future__ import annotations

import os
import struct
from typing import Any, Dict, Optional

from .logger import logger

# ------------------------------------------------------------------------------
# Public field names (METADATA_SPEC.md "Typical metadata fields")
# ------------------------------------------------------------------------------

FIELDS = (
    "artist",
    "album",
    "title",
    "album_artist",
    "track_number",
    "disc_number",
    "genre",
    "year",
    "composer",
    "comment",
)

UNKNOWN = "Unknown"


def _emptyMetadata() -> Dict[str, Any]:

    metadata = {field: UNKNOWN for field in FIELDS}

    metadata["source"] = "None"
    metadata["bit_depth"] = UNKNOWN
    metadata["duration_seconds"] = None
    metadata["file_size"] = None
    metadata["has_embedded_artwork"] = False
    metadata["lyrics"] = ""

    return metadata


# ------------------------------------------------------------------------------
# Vorbis Comment parsing (shared by FLAC and Ogg Vorbis)
# ------------------------------------------------------------------------------

# Maps common Vorbis Comment field names (case-insensitive) to our
# FIELDS names.
_VORBIS_FIELD_MAP = {
    "artist": "artist",
    "album": "album",
    "title": "title",
    "albumartist": "album_artist",
    "album artist": "album_artist",
    "tracknumber": "track_number",
    "discnumber": "disc_number",
    "genre": "genre",
    "date": "year",
    "year": "year",
    "composer": "composer",
    "comment": "comment",
    "description": "comment",
    "lyrics": "lyrics",
    "unsyncedlyrics": "lyrics",
}


def _parseVorbisComments(data: bytes, offset: int, metadata: Dict[str, Any]) -> None:
    """
    Parse a Vorbis Comment block starting at `offset` within `data`
    (the FLAC VORBIS_COMMENT block body, or the payload following the
    "\\x03vorbis" packet header in an Ogg Vorbis comment header
    packet) into `metadata`, in place.
    """

    vendor_length = struct.unpack_from("<I", data, offset)[0]

    offset += 4 + vendor_length

    comment_count = struct.unpack_from("<I", data, offset)[0]

    offset += 4

    for _ in range(comment_count):

        length = struct.unpack_from("<I", data, offset)[0]

        offset += 4

        raw = data[offset:offset + length].decode("utf-8", errors="replace")

        offset += length

        if "=" not in raw:
            continue

        key, value = raw.split("=", 1)

        field = _VORBIS_FIELD_MAP.get(key.strip().lower())

        if field is not None and value:

            metadata[field] = value


# ------------------------------------------------------------------------------
# FLAC
# ------------------------------------------------------------------------------

def _readFLAC(filepath: str, metadata: Dict[str, Any]) -> None:

    with open(filepath, "rb") as handle:

        if handle.read(4) != b"fLaC":
            return

        metadata["source"] = "FLAC"

        while True:

            header = handle.read(4)

            if len(header) < 4:
                break

            is_last = bool(header[0] & 0x80)

            block_type = header[0] & 0x7F

            block_length = struct.unpack(">I", b"\x00" + header[1:4])[0]

            block_data = handle.read(block_length)

            if len(block_data) < block_length:
                break

            if block_type == 0 and len(block_data) >= 34:

                # STREAMINFO: sample_rate(20 bits)/channels(3 bits)/
                # bits_per_sample(5 bits)/total_samples(36 bits) packed
                # starting at byte offset 10.
                packed = int.from_bytes(block_data[10:18], "big")

                sample_rate = (packed >> 44) & 0xFFFFF

                bits_per_sample = ((packed >> 36) & 0x1F) + 1

                total_samples = packed & 0xFFFFFFFFF

                metadata["bit_depth"] = f"{bits_per_sample}-bit"

                if sample_rate:

                    metadata["duration_seconds"] = total_samples // sample_rate

            elif block_type == 4:

                try:
                    _parseVorbisComments(block_data, 0, metadata)

                except (struct.error, IndexError, UnicodeDecodeError) as error:

                    logger.verbose(f"[Metadata] Malformed FLAC VORBIS_COMMENT block: {error}")

            elif block_type == 6:

                metadata["has_embedded_artwork"] = True

                metadata["_embedded_artwork"] = _parseFlacPicture(block_data)

            if is_last:
                break


def _parseFlacPicture(block_data: bytes):
    """
    Parse a FLAC PICTURE block, returning (mime_type, image_bytes) or
    None on any parse failure.
    """

    try:
        offset = 4  # picture type

        mime_length = struct.unpack_from(">I", block_data, offset)[0]

        offset += 4

        mime_type = block_data[offset:offset + mime_length].decode("ascii", errors="replace")

        offset += mime_length

        description_length = struct.unpack_from(">I", block_data, offset)[0]

        offset += 4 + description_length

        offset += 4 + 4 + 4 + 4  # width, height, color depth, colors used

        data_length = struct.unpack_from(">I", block_data, offset)[0]

        offset += 4

        image_bytes = block_data[offset:offset + data_length]

        return (mime_type, image_bytes)

    except (struct.error, IndexError):
        return None

# End of Part 1
# ------------------------------------------------------------------------------
# ID3v2 (MP3)
# ------------------------------------------------------------------------------

_ID3_FRAME_MAP = {
    "TIT2": "title",
    "TPE1": "artist",
    "TALB": "album",
    "TPE2": "album_artist",
    "TRCK": "track_number",
    "TPOS": "disc_number",
    "TCON": "genre",
    "TYER": "year",
    "TDRC": "year",
    "TCOM": "composer",
    "COMM": "comment",
    "USLT": "lyrics",
}


def _decodeID3Text(raw: bytes) -> str:

    if not raw:
        return ""

    encoding_byte = raw[0]

    body = raw[1:]

    try:
        if encoding_byte == 0:
            text = body.decode("latin-1", errors="replace")

        elif encoding_byte == 1:
            text = body.decode("utf-16", errors="replace")

        elif encoding_byte == 2:
            text = body.decode("utf-16-be", errors="replace")

        else:
            text = body.decode("utf-8", errors="replace")

    except (UnicodeDecodeError, LookupError):
        text = body.decode("latin-1", errors="replace")

    return text.replace("\x00", "").strip()


def _decodeCommentFrame(raw: bytes) -> str:
    """
    Decode a COMM frame's actual comment text.

    Unlike plain text frames, COMM is structured as: encoding byte(1)
    + language(3, e.g. "eng") + short description (encoding-dependent,
    null-terminated) + the actual comment text. Passing a raw COMM
    frame to _decodeID3Text() leaks the language code into the
    output (confirmed with a hand-built COMM frame during Build 0006
    testing -- see docs/Claude_notes_build0006.txt); this skips both
    the language code and the short description properly.
    """

    if len(raw) < 5:
        return ""

    encoding_byte = raw[0]

    offset = 4  # encoding byte + 3-byte language code

    if encoding_byte in (1, 2):

        # UTF-16 short description, null-terminated on an even
        # boundary (same convention as APIC's description field).
        end = offset

        while end + 1 < len(raw) and raw[end:end + 2] != b"\x00\x00":
            end += 2

        offset = end + 2

    else:

        terminator = raw.find(b"\x00", offset)

        offset = (terminator + 1) if terminator != -1 else offset

    # Reuse _decodeID3Text for the actual text, by re-prefixing it
    # with the original encoding byte so its own encoding handling
    # still applies.
    return _decodeID3Text(raw[0:1] + raw[offset:])


def _readSyncsafeInt(data: bytes) -> int:

    value = 0

    for byte in data:

        value = (value << 7) | (byte & 0x7F)

    return value


def _readID3v2(filepath: str, metadata: Dict[str, Any]) -> None:

    with open(filepath, "rb") as handle:

        header = handle.read(10)

        if len(header) < 10 or header[0:3] != b"ID3":
            return

        metadata["source"] = "ID3v2"

        major_version = header[3]

        tag_size = _readSyncsafeInt(header[6:10])

        body = handle.read(tag_size)

    offset = 0

    while offset + 10 <= len(body):

        frame_id = body[offset:offset + 4]

        if frame_id == b"\x00\x00\x00\x00":
            break

        try:
            frame_id_str = frame_id.decode("ascii")

        except UnicodeDecodeError:
            break

        if major_version >= 4:
            frame_size = _readSyncsafeInt(body[offset + 4:offset + 8])
        else:
            frame_size = struct.unpack(">I", body[offset + 4:offset + 8])[0]

        offset += 10

        if frame_size <= 0 or offset + frame_size > len(body):
            break

        frame_data = body[offset:offset + frame_size]

        offset += frame_size

        if frame_id_str == "APIC":

            metadata["has_embedded_artwork"] = True

            metadata["_embedded_artwork"] = _parseID3Picture(frame_data)

            continue

        field = _ID3_FRAME_MAP.get(frame_id_str)

        if field is None:
            continue

        try:
            text = (
                _decodeCommentFrame(frame_data)
                if frame_id_str in ("COMM", "USLT")
                else _decodeID3Text(frame_data)
            )

        except Exception as error:

            logger.verbose(f"[Metadata] Malformed ID3 frame {frame_id_str}: {error}")

            continue

        if text:
            metadata[field] = text


def _parseID3Picture(frame_data: bytes):
    """
    Parse an ID3v2 APIC frame, returning (mime_type, image_bytes) or
    None on any parse failure.
    """

    try:
        encoding_byte = frame_data[0]

        offset = 1

        terminator = frame_data.index(b"\x00", offset)

        mime_type = frame_data[offset:terminator].decode("ascii", errors="replace")

        offset = terminator + 1

        offset += 1  # picture type byte

        if encoding_byte in (1, 2):

            # UTF-16 description is null-terminated by a double zero
            # byte on an even boundary.
            end = offset

            while end + 1 < len(frame_data) and frame_data[end:end + 2] != b"\x00\x00":
                end += 2

            offset = end + 2

        else:

            terminator = frame_data.index(b"\x00", offset)

            offset = terminator + 1

        return (mime_type, frame_data[offset:])

    except (IndexError, ValueError):
        return None

# End of Part 2
# ------------------------------------------------------------------------------
# Ogg Vorbis
# ------------------------------------------------------------------------------

def _readOggVorbis(filepath: str, metadata: Dict[str, Any]) -> None:

    packets = []

    current_packet = bytearray()

    with open(filepath, "rb") as handle:

        while len(packets) < 2:

            capture = handle.read(4)

            if capture != b"OggS":
                break

            page_header = handle.read(23)

            if len(page_header) < 23:
                break

            segment_count = page_header[22]

            segment_table = handle.read(segment_count)

            if len(segment_table) < segment_count:
                break

            for segment_length in segment_table:

                current_packet += handle.read(segment_length)

                if segment_length < 255:

                    packets.append(bytes(current_packet))

                    current_packet = bytearray()

                    if len(packets) >= 2:
                        break

    if len(packets) < 2:
        return

    identification, comment_header = packets[0], packets[1]

    if not identification.startswith(b"\x01vorbis") or not comment_header.startswith(b"\x03vorbis"):
        return

    metadata["source"] = "Ogg Vorbis"

    if len(identification) >= 16:

        # Vorbis identification header: version(4)+channels(1)+
        # sample_rate(4, little-endian) starting at byte 7.
        sample_rate = struct.unpack_from("<I", identification, 12)[0]

        if sample_rate:
            metadata["_ogg_sample_rate"] = sample_rate

    try:
        _parseVorbisComments(comment_header, len(b"\x03vorbis"), metadata)

    except (struct.error, IndexError, UnicodeDecodeError) as error:

        logger.verbose(f"[Metadata] Malformed Ogg comment header: {error}")

# End of Part 3
# ------------------------------------------------------------------------------
# Public interface
# ------------------------------------------------------------------------------

_READERS = {
    ".flac": _readFLAC,
    ".mp3": _readID3v2,
    ".ogg": _readOggVorbis,
    ".oga": _readOggVorbis,
}


class MetadataReader:
    """
    Reads tag metadata and embedded artwork from a supported audio
    file.
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------

    def read(self, filepath: str) -> Dict[str, Any]:
        """
        Read metadata for `filepath`.

        Returns a dict with every key in FIELDS (each defaulting to
        "Unknown" -- METADATA_SPEC.md "sensible default values"),
        plus "source", "bit_depth", "duration_seconds", "file_size"
        and "has_embedded_artwork". Never raises -- any parse failure
        just leaves the corresponding field(s) at their default.
        """

        metadata = _emptyMetadata()

        try:
            metadata["file_size"] = os.path.getsize(filepath)

        except OSError as error:

            logger.verbose(f"[Metadata] Unable to stat {filepath}: {error}")

        extension = os.path.splitext(filepath)[1].lower()

        reader = _READERS.get(extension)

        if reader is None:

            logger.verbose(f"[Metadata] No metadata reader for extension: {extension}")

            return metadata

        try:
            reader(filepath, metadata)

            logger.verbose(f"[Metadata] Metadata loaded\n\nSource: {metadata['source']}\n\nFile: {filepath}\n")

        except Exception as error:

            logger.info(f"[Metadata] Unable to read metadata from {filepath}: {error}")

            logger.verbose(f"[Metadata] Metadata unavailable\n\nFile: {filepath}\n\nReason: {error}\n")

        return metadata

    # ------------------------------------------------------------------

    def getEmbeddedArtwork(self, metadata: Dict[str, Any]):
        """
        Return (mime_type, image_bytes) for the artwork embedded in a
        previously-read metadata dict, or None if it has none.
        """

        return metadata.get("_embedded_artwork")


# ------------------------------------------------------------------------------
# Shared instance
# ------------------------------------------------------------------------------

metadata_reader = MetadataReader()


# ==============================================================================
#
# Build Notes
#
# metadata.py has no dependency on Enigma2 at all -- it is pure file
# parsing and belongs entirely to the Core Layer. PlaybackController
# is the only module that calls it; Screens never call it directly
# (BUILD_0006_PLAN.md "Metadata Design Principles").
#
# WAV and other unsupported formats simply get no reader entry and
# fall through to all-"Unknown" fields plus file_size -- this matches
# METADATA_SPEC.md's "sensible default values" requirement without
# needing a special case.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================

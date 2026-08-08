# MediaPlayer3

# Metadata Specification

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

MetadataReader extracts tag metadata and embedded artwork from
supported audio files.

Metadata handling is implemented in metadata.py.

---

# 2. Responsibilities

MetadataReader is responsible for:

- Reading tag metadata from supported formats
- Extracting embedded artwork
- Providing sensible default values when metadata is unavailable

MetadataReader is NOT responsible for:

- Playback
- Screen rendering
- Enigma2 service handling
- Caching (PlaybackController owns the cache -- see section 6)

---

# 3. Architecture

metadata.py has no dependency on Enigma2 at all -- it is pure file
parsing (stdlib `struct`/`os` only) and belongs entirely to the Core
Layer.

No third-party library (e.g. mutagen) can be assumed present on the
receiver, so every supported format is parsed directly against its
published binary layout.

PlaybackController is the only caller; Screens never call
MetadataReader directly (BUILD_0006_PLAN.md "Metadata Design
Principles": "PlaybackController owns playback. Metadata providers
own metadata extraction. PlaybackInfoScreen displays information
only.").

---

# 4. Supported Sources

- FLAC -- STREAMINFO (bit depth, duration), VORBIS_COMMENT (tags),
  PICTURE (embedded artwork) metadata blocks.
- MP3 -- ID3v2.3/2.4 text frames, APIC (embedded artwork).
- Ogg Vorbis -- identification header (sample rate) and comment
  header (tags), reconstructed from Ogg page/packet framing.

Unsupported extensions (including .wav) get no reader and return all
fields at their default -- this is intentional, not an error path;
see section 7.

Future formats may be added without modifying existing architecture
-- each format is a self-contained reader function dispatched by file
extension.

---

# 5. Metadata Fields

    artist
    album
    title
    album_artist
    track_number
    disc_number
    genre
    year
    composer
    comment

Plus:

    source            -- "FLAC" / "ID3v2" / "Ogg Vorbis" / "None"
    bit_depth         -- FLAC only; "Unknown" otherwise
    duration_seconds  -- FLAC only (from STREAMINFO); None otherwise
    file_size         -- bytes, from the filesystem
    has_embedded_artwork -- bool

---

# 6. Caching

PlaybackController caches the result of `read()` for the current file
(populated in `play()`, cleared on `stop()`/cleanup), exposed through
`getMetadata()`/`getEmbeddedArtwork()`.

MetadataReader itself does not cache -- every `read()` call re-parses
the file from disk.

---

# 7. Failure Behaviour

`read()` never raises.

Every field defaults to "Unknown" (or the documented default for
non-string fields) and stays there if the corresponding data cannot
be parsed -- a truncated, corrupted, empty, or entirely wrong-format
file never prevents `read()` from returning a complete, well-formed
dict.

Metadata processing never blocks or fails playback startup: `play()`
wraps the (already-safe) `read()` call in an additional try/except so
a metadata bug can never be the reason playback fails to start.

---

# 8. Embedded Artwork

`getEmbeddedArtwork(metadata)` returns `(mime_type, image_bytes)` or
`None`.

Since ePicLoad (used for on-screen display) needs a filesystem path,
not raw bytes, MainScreen writes embedded artwork to CACHE_PATH before
handing it to ePicLoad -- see MAINSCREEN_SPEC.md's artwork priority
section.

---

# 9. Known Limitations

- COMM (MP3 comment) frames are decoded correctly (language code and
  short description are skipped); TXXX (user-defined text) frames,
  which some encoders use for a "comment" tag instead of COMM, are
  not currently mapped to any field.
- Ogg Vorbis embedded artwork (base64 METADATA_BLOCK_PICTURE comment)
  is not extracted -- only FLAC and MP3 embedded artwork are
  supported in Build 0006.
- Multi-value tags (e.g. multiple artists) are not specially handled;
  the first occurrence of a mapped field wins.

---

# 10. Acceptance Criteria

- Reading a well-formed FLAC/MP3/Ogg file with tags returns correct
  values for every field the format supports.
- Reading embedded artwork from FLAC PICTURE and MP3 APIC blocks
  returns the exact original image bytes.
- Reading a truncated, corrupted, empty, or unsupported-format file
  never raises and returns sensible defaults.

---

# End of File

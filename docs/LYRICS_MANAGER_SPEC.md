# LYRICS_MANAGER_SPEC.md

MediaPlayer3

LyricsManager Specification

Status

Build 0008 CONFIRMED COMPLETE -- 9 rounds of real device testing, confirmed by the user

---

# Purpose

LyricsManager provides a unified interface for retrieving lyrics for the
currently playing track.

Lyrics may originate from embedded metadata or external lyric files.

MainScreen never accesses lyric files directly.

Instead it requests lyrics from LyricsManager, which selects the best
available source.

---

# Responsibilities

LyricsManager is responsible for:

- Detecting available lyrics
- Reading embedded lyrics
- Reading external lyric files
- Selecting the preferred lyric source
- Providing synchronized lyrics when available
- Providing plain text lyrics when synchronization is unavailable

LyricsManager shall not:

- Control playback
- Decode media
- Read playlist information
- Display user interface

---

# Supported Sources

Build 0008 supports the following lyric sources.

Embedded Lyrics

Lyrics stored directly inside supported media files.

External LRC

Synchronized lyrics stored in .lrc files.

External TXT

Plain text lyrics stored in .txt files.

Future builds may optionally support online lyric providers.

---

# Source Priority

LyricsManager searches for lyrics in the following order.

1. Embedded Lyrics

2. External .lrc

3. External .txt

4. Lyrics not available

The first available source is always selected.

This guarantees predictable behavior regardless of file type.

---

# Embedded Lyrics

When supported by the media format, embedded lyrics are preferred over
external files.

Supported formats depend on the metadata capabilities of the underlying
audio format.

LyricsManager automatically detects whether embedded lyrics are present.

If embedded lyrics exist, external lyric files are ignored.

---
# External Lyrics

LyricsManager searches for external lyric files in the same directory
as the currently playing media file.

Typical examples:

```
song.flac
song.lrc
song.txt
```

Only files matching the current media filename are considered.

---

# LRC Synchronization

When an external LRC file is available, synchronized lyrics are
provided.

The MainScreen may highlight the currently active lyric line according
to playback position.

If synchronized playback is not supported, LyricsManager shall fall
back to plain text presentation.

Future builds may improve synchronization effects without changing the
LyricsManager interface.

---

# MainScreen Integration

MainScreen requests lyrics through LyricsManager.

Example interface:

```
getLyrics(currentTrack)
```

LyricsManager returns:

- Embedded lyrics
- LRC lyrics
- Plain text lyrics
- No lyrics available

MainScreen does not need to know which source was used.

---

# Error Handling

Unreadable or invalid lyric files are ignored.

Errors are written to the application log.

Playback is never interrupted due to lyric errors.

If no usable lyrics are found, LyricsManager reports:

"Lyrics not available."

---

# Future Extensions

Possible future additions include:

- Online lyric providers
- Multiple language lyrics
- Karaoke highlighting
- Automatic lyric downloads
- User edited lyrics
- Cached online lyrics

These additions should require no changes to the MainScreen user
interface.

---

# Summary

LyricsManager provides a unified interface for obtaining lyrics from
multiple sources.

By prioritizing embedded lyrics, synchronized LRC files and finally
plain text lyrics, the manager delivers the best available listening
experience while hiding implementation details from the rest of the
application.

The modular design allows future lyric sources to be added without
modifying existing playback or user interface components.

---

End of LYRICS_MANAGER_SPEC.md

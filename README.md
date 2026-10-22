# MediaPlayer3

**A modern audio player for Enigma2 receivers.**

Version 1.4.001 &middot; Build 0010 &middot; GPL-3.0-or-later

Local music, Internet Radio, Podcasts, a Music Library, playlists, lyrics,
and Finnish radio EPG (Yle/Bauer) &mdash; in one plugin, with no external
Python dependencies beyond the standard library.

---

## Features

- **Local playback** &mdash; browse and play local audio files, with tag
  metadata, album artwork, and synchronized or plain-text lyrics that
  scroll automatically with the track.
- **Music Library** &mdash; browse your local collection by Artist /
  Album / Track.
- **Internet Radio** &mdash; search and browse via [RadioBrowser](https://www.radio-browser.info/),
  with a local station database (works offline, updates automatically),
  Favorites, and listening history.
- **Podcasts** &mdash; search (up to 1000 results), fetch popular
  podcasts, choose the podcast language, subscribe, and listen via
  [Podcast Index](https://podcastindex.org/); episode descriptions are
  shown on the main screen, also fullscreen.
- **Radio time shift** &mdash; the playing station (also HLS streams) is
  buffered on disk, so you can pause, rewind and jump back to live; the
  buffer can be recorded afterwards.
- **Radio recording** &mdash; record a station from now or from the time
  shift buffer, including HLS (.m3u8) streams.
- **Identify song** &mdash; OK menu &gt; *Identify song* recognises the
  playing song from the radio broadcast or a local file via
  [AcoustID](https://acoustid.org/) (Chromaprint fingerprint).
- **Track details in playlists** &mdash; artist, album, title and length
  (files), podcast episode info, or the radio station details.
- **Front panel text** &mdash; the receiver's front display (also
  lcd4linux) shows the artist and title that is playing.
- **Playlists** &mdash; build and manage playlists from local files,
  podcast episodes, or radio stations, all in the same list.
- **Finland Radio EPG** &mdash; programme schedules for Yle and Bauer
  Media (Radio Nova, Iskelmä, ...) stations, automatically matched.
- **Redesigned Light / Dark skins** across every screen &mdash; Music
  Library, Internet Radio, the file Browser, Podcasts, Playlists, the
  Main Player, and Settings all share the same visual language
  (rounded cards, colour-coded active panels, a two-row hint bar
  separating button names from the colour-action row, consistent
  iconography), independent of the resolution tier. Vintage Radio is
  available too, for a different, warm amber-on-wood-and-brass look.
- A Main Menu entry (optional).
- Works out of the box: bundled default API keys for Podcast Index and
  Yle EPG, with the option to use your own in Settings.

## Screenshots

Screenshots from real device testing are collected under
[`docs/images`](docs/images).

## Installation

### Option 1 &mdash; .ipk package (recommended)

1. Download the latest `mediaplayer3_<version>_all.ipk` from
   [Releases](../../releases).
2. Copy it to your receiver (e.g. via FTP, or a USB stick), then install
   it:

   ```sh
   opkg install mediaplayer3_<version>_all.ipk
   ```

3. Restart Enigma2's GUI (or the receiver) if MediaPlayer3 doesn't
   immediately appear under **Extensions**.

### Option 2 &mdash; manual copy

Copy the contents of `src/` to:

```
/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer3/
```

then restart Enigma2's GUI.

## Requirements

- Enigma2, Python 3.13+ (matches current OpenViX/OpenATV/OpenPLI/OpenBH
  images).
- No external Python packages required &mdash; MediaPlayer3 uses only
  the standard library and Enigma2's own built-in modules.
- *Identify song* additionally needs an audio decoder on the receiver:
  `gst-launch-1.0` (present on the standard images) or `ffmpeg`. The
  fingerprint tool itself is included in the released .ipk (ARM, MIPS,
  AArch64; the source tree has none &mdash; build them with
  `tools/fpraw/build.sh`, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)).

## Tested on

OpenViX 6.9, OpenPLI 9.2, OpenATV 8.0, OpenBH 5.6 &mdash; on Vu+ Duo2 and
Vu+ Uno4K SE.
See [CHANGELOG.md](docs/CHANGELOG.md) for the full device-testing
history.

## Configuration

Settings (press MENU from the main player screen) covers:

- Startup/Music Library directories, hidden files
- Skin (Light/Dark/Vintage Radio), Theme, show/hide the upper hint row
- Radio: default country/language, navigation mode, history size,
  automatic station-database updates, resume/auto-play behaviour
- Podcast search limit (default 1000)
- Radio time shift on/off and its length (5-480 minutes; the buffer is
  kept in the recording folder, so a disk or USB stick is needed)
- AcoustID application key (optional; a default key is bundled) and the
  path of an own `fpcalc` (optional)
- Your own Podcast Index or Yle EPG API key, if you'd rather not use
  the bundled default
- Show MediaPlayer3 in Enigma2's own Main Menu (restart required)

## Known limitations

- Radio time shift needs a recording folder on a disk or USB stick.
- On OpenATV, starting a station with time shift on can take about 6 s
  before the sound starts (the image's player buffers the stream first).
- *Identify song* works best when the sample starts at the beginning of the
  song (press it right after the song changes; it waits for ~30 s of the
  song). Broadcast audio is recognised less reliably than studio
  recordings, and an internet connection is required.

## Documentation

Full architecture and specification documents live under
[`docs/`](docs/) &mdash; start with [`docs/README.md`](docs/README.md)
for a guided index, or [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the overall design.

## License

MediaPlayer3 is released under the GNU General Public License v3.0 or
later (GPL-3.0-or-later). See [`LICENSE`](LICENSE).

## Acknowledgements

MediaPlayer3 builds on the Enigma2 ecosystem, [RadioBrowser](https://www.radio-browser.info/),
[Podcast Index](https://podcastindex.org/), and Yle's Teksti-TV service,
and benefits from ideas and experience gained from the wider open-source
Enigma2 community.

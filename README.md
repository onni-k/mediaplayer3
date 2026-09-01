# MediaPlayer3

**A modern audio player for Enigma2 receivers.**

Version 1.0.0-beta3 &middot; Build 0010 &middot; GPL-3.0-or-later

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
- **Podcasts** &mdash; search, subscribe, and listen via [Podcast Index](https://podcastindex.org/).
- **Playlists** &mdash; build and manage playlists from local files,
  podcast episodes, or radio stations, all in the same list.
- **Finland Radio EPG** &mdash; programme schedules for Yle and Bauer
  Media (Radio Nova, Iskelmä, ...) stations, automatically matched.
- **Redesigned Light / Dark skins** across every screen &mdash; Music
  Library, Internet Radio, the file Browser, Podcasts, Playlists, the
  Main Player, the Main Menu, and Settings all share the same visual
  language (rounded cards, colour-coded active panels, consistent
  iconography), independent of the resolution tier.
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

## Tested on

OpenViX, OpenATV, OpenPLI, OpenBH &mdash; on Vu+ Duo2 and Vu+ Uno4K SE.
See [CHANGELOG.md](docs/CHANGELOG.md) for the full device-testing
history.

## Configuration

Settings (accessible from MediaPlayer3's own Main Menu, or Enigma2's
Main Menu if enabled) covers:

- Startup/Music Library directories, hidden files
- Language (Suomi / English, or **System** to automatically follow
  the receiver's own Enigma2 language), Skin (Light/Dark), Theme
- Radio: default country/language, navigation mode, history size,
  automatic station-database updates
- Your own Podcast Index or Yle EPG API key, if you'd rather not use
  the bundled default
- Show MediaPlayer3 in Enigma2's own Main Menu (restart required)

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

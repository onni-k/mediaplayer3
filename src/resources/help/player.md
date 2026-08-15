# Player Panel

Shows what is currently playing -- local files or an Internet Radio
station -- along with cover art, playback progress and status.

This is MainScreen's default panel. Press EPG/INFO to switch to the
Playlist panel (local music only) or Information panel instead; press
it again to cycle back. While listening to Internet Radio, EPG/INFO
only cycles between Player and Information -- the Playlist panel
isn't part of that cycle for radio, since LEFT/RIGHT already covers
switching favorite lists here instead.

## Keys

- OK: if nothing is playing, opens a chooser (Internet Radio / Local
  Music / Music Library / Playlists / Podcasts). Otherwise, opens a
  small menu: Back (return to wherever playback was started from),
  Stop/Resume, Cancel -- plus, while listening to Internet Radio:
  Clear history, Add to Favorites, Remove from Favorites.
- PLAY / PAUSE / STOP: control playback directly.
- LEFT / RIGHT: seek a short step back/forward for local files.
  Switches the active favorite list instead while listening to
  Internet Radio, since a live stream can't be seeked anyway.
- FF / RW: seek a longer step back/forward (local files only).
- UP / DOWN: previous/next track (or previous/next radio station,
  while listening to Internet Radio).
- CH+ / CH-: previous/next track (may not work on every remote/image).
- PVR: opens the same chooser as OK (Internet Radio / Local Music /
  Music Library / Playlists / Podcasts).
- RADIO: switch between radio and local playback, or open the radio
  station search.
- EPG / INFO: switch to the Playlist panel (local music) or
  Information panel (radio).
- MENU: open the Main Menu.
- HELP: show this help.
- EXIT: stop playback and return to live TV.

## Notes

Internet Radio stations resume automatically from your most recent
history entry when you choose Internet Radio from the startup
chooser, falling back to your "General" favorites list, and finally
to the station search if neither has anything yet.

The top info line shows the current track's tags for local files, or
the station's Now Playing info (when available) for Internet Radio,
falling back to just the station name when now-playing data isn't
available for that particular station.

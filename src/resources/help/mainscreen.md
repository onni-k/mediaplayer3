# Player & Information

MainScreen's own default view. Shows what is currently playing --
local files or an Internet Radio station -- along with cover art,
playback progress and status, plus a Playlist column and a Player/
Information column shown side by side underneath.

Press BLUE to switch the right-hand column between Player and
Information; press it again to switch back.

## Player

The right-hand column's own default state, showing the current
track's own playback status alongside the top info line.

## Information

Shows extra information about what's currently playing. Which pages
are available depends entirely on what the current track or station
actually has -- an empty page is never shown.

For local music, possible pages are Lyrics (synchronized, embedded or
plain text), Metadata and Codec Information. For Internet Radio,
possible pages are Radio EPG (the current programme plus the next few
upcoming ones, when a station has schedule data), Now Playing, Station
Information and Codec Information.

LEFT/RIGHT switches between the available Information pages; UP/DOWN
scrolls the currently displayed page (or, on synchronized lyrics
specifically, nudges the lyrics earlier/later relative to the song, in
case the timing feels slightly off).

## Playlist column

The left-hand column, always visible regardless of whether the
right-hand one is showing Player or Information. Shows the previous,
current and next track (local music) or radio station (Internet
Radio), the current one highlighted.

## Keys

- OK: if nothing is playing, opens a chooser (Internet Radio / Local
  Music / Music Library / Playlists / Podcasts). Otherwise, opens a
  small menu: Back (return to wherever playback was started from),
  Stop/Resume, Cancel -- plus, while listening to Internet Radio:
  Clear history, Add to Favorites, Remove from Favorites.
- PLAY / PAUSE / STOP: control playback directly.
- LEFT / RIGHT: seek a short step back/forward for local files (Player
  view), or switch between Information pages (Information view).
  Switches the active favorite list instead while listening to
  Internet Radio, since a live stream can't be seeked anyway.
- FF / RW: seek a longer step back/forward (local files only).
- UP / DOWN: previous/next track (or previous/next radio station,
  while listening to Internet Radio) in the Player view; scrolls the
  current page in the Information view.
- CH+ / CH-: previous/next track (may not work on every remote/image).
- PVR: opens the same chooser as OK (Internet Radio / Local Music /
  Music Library / Playlists / Podcasts).
- RADIO: switch between radio and local playback, or open the radio
  station search.
- BLUE: switch between the Player view and the Information view.
- EPG / INFO: open this guide.
- MENU: open the Main Menu.
- HELP: show the remote control's own button guide.
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

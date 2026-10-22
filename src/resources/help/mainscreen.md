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
plain text), Metadata and Codec Information. For a podcast episode
played from the Podcasts screen, the first page is its Description. For Internet Radio,
possible pages are Radio EPG (the current programme plus the next few
upcoming ones, when a station has schedule data), Now Playing, Station
Information and Codec Information.

When the track or station changes, the panel shows the page you last
chose if the new item has it, and otherwise the best available page
(for example programme information for a radio station that has it,
or lyrics when a track has them) -- so it never stays on a page that
no longer applies.

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
  Clear history, Add to Favorites, Remove from Favorites, Start
  recording / Stop recording (records the station to a file; see Notes).
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
- RED: add the current track to a playlist or remove it from one, or
  open the Playlist screen to edit playlists.
- GREEN: open the source menu (the same as PVR).
- YELLOW: show lyrics fullscreen -- or, for a podcast episode, its
  description fullscreen (scrolled with UP / DOWN). YELLOW, OK or
  EXIT closes the fullscreen view again.
- BLUE: switch between the Player view and the Information view.
- EPG / INFO: open this guide.
- MENU: open Settings.
- HELP: show the remote control's own button guide.
- EXIT: stops playback; pressing it again closes MediaPlayer3 and
  returns to live TV.

## Notes

Radio recording: Start recording copies the playing station's stream to
a file (name YYYY-MM-DD-hh.mm_station) in the recording folder set in
Settings, and adds it to the "Recordings (Radio)" playlist when it
ends. Recording stops when you change station, stop playback or close
MediaPlayer3. While recording, the status line shows REC and the
elapsed time.

HLS (.m3u8) stations can be recorded too; the audio is saved as a plain
.aac / .mp3 file. Encrypted streams cannot be recorded.

Identify song: OK menu > Identify song fingerprints a sample of the
playing station (or the current file) and looks it up from AcoustID. It
uses a fingerprint tool bundled with the plugin and needs an audio
decoder on the receiver (ffmpeg or gst-launch-1.0). A bundled AcoustID key
is used unless you enter your own in Settings.

Radio time shift: while a station plays it is buffered on disk (in the
recording folder), so the total time grows and the remaining time shows
how far behind live you are. PAUSE freezes the playhead, FF / RW move
through the buffer, and OK menu > Jump to live returns to live. Start
recording while behind live asks whether to record from the start of
the time shift or from now. Turn it off or change its length in
Settings (Radio time shift, Time shift length).

Internet Radio stations resume automatically from your most recent
history entry when you choose Internet Radio from the startup
chooser, falling back to your "General" favorites list, and finally
to the station search if neither has anything yet.

For a podcast episode played from the Podcasts screen, the top info
box shows the podcast's name with the episode's title below it.

The top info line shows the current track's tags for local files, or
the station's Now Playing info (when available) for Internet Radio,
falling back to just the station name when now-playing data isn't
available for that particular station.

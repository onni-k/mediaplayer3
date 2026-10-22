# BUILD_0011_PLAN.md

MediaPlayer3

Next-version plan (1.3.x and 1.4.000). Agreed with the user 2026-10-17.

---

# 1. Order of work

1. 1.3.001 -- YELLOW closes the fullscreen lyrics/description view.
   DONE (pending device confirmation).
2. 1.3.002+ -- Recording of Internet Radio and podcast episodes.
3. 1.3.006 -- Radio timeshift (version stays in 1.3.x until all functions are tested on all images). Implemented as a local relay + segmented disk buffer, see src/timeshift_manager.py.

---

# 2. Recording

## Behaviour

- Radio: while a station plays, the OK menu offers "Start recording" /
  "Stop recording". The main screen shows a REC marker while recording.
- (Podcast download implemented in 1.3.003.) Podcast: in PodcastScreen, the OK menu on an episode offers "Record
  episode" (downloads the whole episode in the background).
- Recording runs in its own worker thread, copying the stream bytes to
  a file as-is (no re-encoding; original mp3/aac/ogg extension chosen
  from the response Content-Type, falling back to the URL). Playback
  continues normally. Enigma2 main thread is never blocked.
- Stopping: OK menu "Stop recording", leaving the station, station
  change, or EXIT. A short confirmation is shown when saving finished.

## File names

- Radio: `YYYY-MM-DD-hh.mm_<station>.<ext>`
- Podcast: `<Podcast>_<Episode>.<ext>`
- Names are sanitised (no `/ : * ? " < > |`), shortened to a safe
  length, and made unique if a file already exists.

## Location

- New setting "Recording folder". Default: first mounted disk/USB
  found (e.g. /media/hdd/MediaPlayer3/Recordings); if none, a clear
  warning and no recording. Sub-folders `Radio` and `Podcast`.
- Free-space check before starting; stop and warn if space runs out.

## Playlists

- (Implemented in 1.3.002 for radio as a normal local playlist that the
  recorder appends to, rather than a folder-backed one -- simpler and
  keeps every playlist action working.) Two automatic playlists, "Recordings (Radio)" and "Recordings
  (Podcast)", shown in PlaylistScreen. They list the files in the
  matching recording sub-folder (newest first), update when a recording
  finishes, and support the normal playlist actions (play, remove from
  list; deleting the file itself is an explicit separate action).
- Because they are folder-backed, they need no M3U maintenance.

## Technical outline

- New module `recording_manager.py` (thread worker, state, progress,
  logging; no UI code). Uses urllib with timeouts and reconnect logic
  for radio streams; honours HTTP redirects (podcast CDNs).
- Hooks: MainScreen OK menu (radio), PodcastScreen OK menu (episode),
  PlaylistScreen (auto playlists), SettingsScreen (folder),
  `po/*.po` translations, docs/help updates.
- Risks: some stations use HLS or per-session tokens (handled by the
  same URL InternetRadioManager.prepareStream() resolves; HLS streams
  are reported as "recording not supported" in the first version).

---

# 3. Radio timeshift (1.4.000)

- While a radio station plays, the stream is copied to a buffer file
  in the recording folder's `.timeshift` sub-folder (disk/USB only),
  limited to a configurable length (default 2 h), oldest data dropped.
- Seeking back (LEFT / FF-RW) switches playback from the live URL to
  the buffer file at the wanted offset; a "Live" action returns to the
  live stream. Rewind is possible back to the start of playing.
- Reuses the recording worker; the buffer is deleted when playback
  stops or the station changes.
- Main risk: Enigma2's GStreamer service may stop at the current end of
  a growing file. Prototype first (1.3.x diagnostic build) before
  committing to the design; fallback is a segmented buffer (many small
  files played in sequence).

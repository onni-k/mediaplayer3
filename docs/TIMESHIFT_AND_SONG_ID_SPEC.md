# MediaPlayer3

# Radio time shift, HLS recording and song identification

Version: 1.4.001

Status: implemented and device tested (OpenViX, OpenPLI, OpenATV, OpenBH)

---

# 1. Radio time shift (`timeshift_manager.py`)

`TimeshiftSession` captures the playing station into a ring of 4 MB
segment files under `<recording folder>/.timeshift/` and serves it back
through a local HTTP relay (`http://127.0.0.1:<port>/play?offset=N`). The
player (service) always plays from the relay, never from the station, which
is what makes pause, rewind and "jump to live" possible.

* Capture: plain HTTP streams (Icy metadata is stripped when stored and
  re-inserted per playhead position) and HLS streams (`hls_support.follow`).
* FLAC and Ogg streams keep their stream header; a restart in the middle of
  the buffer sends the header first (Ogg pages are re-synchronised).
* Pause = stop the service; resume/seek = restart the service on the relay
  at the buffer offset. Forward seeking within `LIVE_MARGIN_SECONDS` (3 s)
  of the live edge jumps to live.
* The buffer length is `radio.timeshift_minutes` (5-480); old buffers are
  removed at start-up (`purgeStaleBuffers`).
* Recording from the buffer: `recordingUrl(from_start)` gives a one-shot
  relay URL that `RecordingManager` records (`source_url`).

# 2. HLS recording (`hls_support.py`, `recording_manager.py`)

`hls_support.follow(url, text, stop, write, ...)` follows a playlist
(master or media), extracts the audio from MPEG-TS/ADTS or raw segments,
and feeds it to a writer. It is shared by the recorder and by the time
shift capture. Encrypted playlists end with `hls_encrypted`.

# 3. Song identification (`song_identifier.py`)

OK menu > *Identify song*:

1. Sample: local file (first 60 s), or for radio the time shift buffer from
   the last Icy title change (28-38 s; waits until 28 s of the song are
   buffered), else the last 40 s, else a fresh capture without time shift.
2. Fingerprint: a real `fpcalc` when found, otherwise the bundled
   `fpraw-<cpu>` (static Chromaprint, raw 11025 Hz mono PCM on stdin). The
   PCM comes from `gst-launch-1.0` (decodebin) or `ffmpeg` (WAV output).
   The tools are in the released .ipk as `bin/fpraw-<cpu>` (not in the source tree; `.gz` variants are unpacked at first use into the plugin folder, else /var/volatile/tmp or /tmp). The CPU build is chosen from the ELF header and test-run with `-v`.
3. Lookup: AcoustID `lookup` (POST). `duration` must be the length of the
   whole track: known for files, guessed for radio (typical song lengths
   tried in turn, 0.4 s apart).
4. Result: best match (score >= 0.5) in a message box; errors map to
   `_SONG_ID_MESSAGES` in MainScreen.

The AcoustID key comes from Settings or the bundled obfuscated default.
Log lines are prefixed `[SongID]` (build, CPU, decoder, PCM size,
fingerprint, AcoustID reply).

# 4. Settings

`radio.timeshift`, `radio.timeshift_minutes`, `recognition.acoustid_key`,
`recognition.fpcalc_path`.

# 5. Known limitations

* OpenATV: ~6 s delay before a time-shifted station starts to play (the
  image's player pre-buffers the relay stream).
* Song identification: broadcast audio matches less reliably than studio
  audio; the sample should start at the beginning of the song.
* fMP4/m4a HLS init segments are not prepended in the time shift buffer.

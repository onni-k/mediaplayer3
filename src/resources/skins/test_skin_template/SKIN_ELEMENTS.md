# MediaPlayer3 -- Test Skin element reference

This file describes every background-image file MediaPlayer3 loads,
what each one is for, its exact pixel size, and where the important
on-screen regions sit within it (so you know where to leave room for
readable text, and where the "active panel" highlight should visually
land). It ships alongside the Test Skin template so you can create a
new skin without having to read the plugin's own source code.

## How Test Skin works

- The very first time MediaPlayer3 runs, it copies this whole folder
  (all the PNGs plus this file) into `.mediaplayer3/test_skin/` on
  your own storage -- a writable location, separate from the plugin's
  own installed files.
- Edit or replace the files there directly (FTP, a USB stick, however
  you prefer). Nothing you do there can damage the plugin itself.
- In Settings -> Skin, choose "Test Skin" to see your changes.
- If something goes wrong, or you're happy with the result and want
  to make it permanent, either:
  - **Recover Light**: delete (or rename) the `.mediaplayer3/test_skin/`
    folder and restart MediaPlayer3. It's recreated empty, and if
    "Test Skin" was the selected Skin, it's reset to "Light"
    automatically.
  - **Make it permanent**: copy the finished files from
    `.mediaplayer3/test_skin/` into the plugin's own
    `resources/skins/<your-name>/` folder as a proper new variant.
- A single missing file falls back to Light automatically too (per
  file, not just per skin) -- you can replace files one at a time and
  leave the rest as the Light originals meanwhile.

## File naming and folders

Every screen's images live in two folders, `hd/` and `sd/` -- same
filenames in both, just sized differently (see each screen's own
section below for exact pixel sizes). `sd/` images are roughly 60% of
their own `hd/` counterpart's width and height, same aspect ratio.

Most screens have one image per "active panel" state (whichever part
of the screen currently has focus/highlight) -- when you switch focus
with LEFT/RIGHT, the background image swaps to the matching state
file. A screen with 3 panels needs 3 separate image files, one per
state, all the same size.

## Fonts and colours

`skin.json`'s own `font_family` field sets the font used for most
text across the whole app while this skin is active (`"Bold"` in this
template, matching Light and Dark). Text colours themselves are
**not** controlled by these image files or by `skin.json` -- they're
set directly in the plugin's own code per screen, independent of
which background-image skin is active. If you want different text
colours to match your own background art, that needs a source-code
change (not something Test Skin alone can do) -- get in touch with
whoever maintains the plugin.

---

## MainScreen (Player / Now Playing)

Design canvas: 1808 x 1024. `hd/` images: 1808x1024 px. `sd/` images:
1084x613 px.

Two states, switched with LEFT/RIGHT between the Player and
Information panels:

- `mainscreen_player_active.png` -- Player panel focused (the
  transport controls / seek bar / track info column).
- `mainscreen_info_active.png` -- Information panel focused (Lyrics /
  Metadata / Codec / Radio EPG sub-pages).

Layout: a header strip across the top (~80px tall at hd scale) holds
the "MediaPlayer3" branding text (left) and a live clock (right) --
both recolour to follow which panel is active, so leave visual room
for that recolour to read clearly against your own background in
either state. Below the header, the screen splits into a left column
(cover art + track title/artist/album) and a right column (whichever
panel -- Player controls or Information content -- is currently
focused). A synced-lyrics view (Information panel, Lyrics page) can
also show a 13-row scrolling text block centred in the right column,
with the current line rendered larger and bold -- leave enough
contrast/space there for that to stay readable.

## MainMenu

Design canvas: 1672 x 941. `hd/`: 1672x941 px. `sd/`: 1000x562 px.

One state -- `mainmenu_background.png` -- covering the whole menu
(no active-panel variants). A centred "MediaPlayer3" branding text
sits near the top; the menu's own list of options (Local Music,
Internet Radio, Podcasts, Playlists, Settings, About, Exit) occupies
the centre of the screen.

## Browser (file browser)

Design canvas: 1672 x 941. `hd/`: 1672x941 px. `sd/`: 1000x562 px.

Three states, switched with LEFT/RIGHT across three panels:

- `browser_directories_active.png` -- Directories panel focused (left
  column).
- `browser_files_active.png` -- Files panel focused (right column).
- `browser_playlist_active.png` -- current Playlist panel focused (a
  third, narrower column).

Layout: directories and files sit side by side as two list columns;
the playlist panel, when present, sits alongside them. A header strip
across the top shows the current path/title.

## Music Library

Design canvas: 1672 x 941. `hd/`: 1672x941 px. `sd/`: 1000x562 px.

Three states, switched between three panels:

- `musiclibrary_artists_active.png` -- Artists panel focused.
- `musiclibrary_albums_active.png` -- Albums panel focused.
- `musiclibrary_tracks_active.png` -- Tracks panel focused.

Layout: three list columns side by side (Artists / Albums / Tracks),
each narrowing the next as you drill down.

## Playlist

Design canvas: 1672 x 941. `hd/`: 1672x941 px. `sd/`: 1000x562 px.

Two states:

- `playlist_playlists_active.png` -- the list of saved playlists
  focused (left column).
- `playlist_tracks_active.png` -- the currently open playlist's own
  tracks focused (right column).

## Podcast

Design canvas: 1672 x 941. `hd/`: 1672x941 px. `sd/`: 1000x562 px.

Three states:

- `podcast_subscribed_active.png` -- your subscribed podcasts list
  focused.
- `podcast_available_active.png` -- podcast search results focused.
- `podcast_episodes_active.png` -- a podcast's own episode list
  focused.

## Internet Radio

Design canvas: 1672 x 941. `hd/`: 1672x941 px. `sd/`: 1000x562 px.

Three states, switched between three panels:

- `radiobrowser_stations_active.png` -- the station results list
  focused (main, widest column).
- `radiobrowser_language_active.png` -- the Language filter column
  focused (narrow column).
- `radiobrowser_region_active.png` -- the Region filter column
  focused (narrow column).

Layout: Language and Region are two narrow columns (one holds "Any"
plus every language/region RadioBrowser returns); Stations is the
wide column showing the actual search results.

## Settings

Design canvas: 1672 x 941. `hd/`: 1672x941 px. `sd/`: 1000x562 px.

One state -- `settings_background.png` -- no active-panel variants
(Settings is a single scrolling list). A header strip across the top
shows "Asetukset"/"Settings". Below the list, a card-shaped info
panel shows a one-line help description for whichever setting is
currently selected -- leave that region legible against your own
background, since its own text colour is fixed (not something a skin
recolours).

## Lyrics fullscreen

Design canvas: 1920 x 1080 (this one screen uses 1080p directly,
unlike the others' 1672x941/1808x1024). `hd/`: 1920x1080 px. `sd/`:
1000x562 px.

One state -- `lyrics_fullscreen_background.png` -- the entire
fullscreen synced-lyrics view. A title bar near the top shows the
track title; the centre of the screen shows the scrolling lyrics text
(13 rows, current line largest/bold, matching MainScreen's own Lyrics
page). Leave the vertical centre of the image relatively uncluttered
so the lyrics text stays readable over it.

# File Browser

Browse local storage and build playlists, in three columns:
Directories | Files | Playlist.

## Keys

- LEFT/RIGHT: switch between the Directories, Files and Playlist
  columns.
- UP/DOWN: move within the current column. CH+/CH- jumps 10 rows at
  a time.
- Moving within Directories updates the Files column with a preview
  of the highlighted directory's contents.
- OK: open the action menu for the current selection.
  - Directories: Play, Open directory (descend, or ".." to go up), or
    Add entire directory to playlist.
  - Files: Play, Add this file, Add this file and remaining files in
    directory, or Add all files from directory.
  - Playlist: Play (from the selected track onward), Remove, Move up,
    or Move down.
- PLAY: start playback directly -- the previewed directory
  (Directories), the previewed directory starting at the selected
  file (Files), or the current playlist starting at the selected
  track (Playlist).
- INFO: choose which playlist the Playlist column and "Add" actions
  target (or create a new one).
- MENU: open the Main Menu.
- HELP: show this help.
- EXIT: return to Main Screen.

## Notes

Adding files or a directory requires a target playlist -- if none has
been chosen yet, the playlist picker (INFO) opens automatically the
first time you add something.

Directories/Files "Play" creates (or replaces) a playlist named after
the folder or file and starts playing it -- unlike the PLAY hardware
key, which plays the folder/file directly without creating a stored
playlist. Both return here via Back afterwards either way.

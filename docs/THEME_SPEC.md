# THEME_SPEC.md

MediaPlayer3

Theme Specification

Status: Build 0010 CONFIRMED COMPLETE with one documented limitation
(see "Dark Theme" below) -- device test rounds 12, 15 (OpenViX,
Vu+ Duo2).

---

# Purpose

Theme support defines the visual appearance of MediaPlayer3 without
changing the logical layout or navigation behaviour of the application.

Build 0010 introduces two supported themes:

- Light
- Dark

The same functional layout shall be used in both themes.

---

# Theme Selection

The user may select the active MediaPlayer3 theme from Settings.

Supported values are:

- Light
- Dark

The selected theme shall be stored in the MediaPlayer3 configuration.

The theme shall remain active between MediaPlayer3 sessions.

---

# Light Theme

The Light theme shall remain close to the current MediaPlayer3
appearance.

It shall use:

- Light background areas
- Dark readable text
- Light blue inactive headers
- Blue active headers

Existing Enigma2 skin colours may be used where appropriate.

---

# Dark Theme

The Dark theme shall use:

- Dark grey background
- White text
- Darker inactive areas
- Blue active headers

The Dark theme shall maintain sufficient contrast for all displayed
information.

Known limitation (device test round 14): every screen's own panel
content areas (directory/file/station/track lists, and their text)
use a fixed white background regardless of theme -- a deliberate,
device-confirmed fix from Build 0007 for a real "video/background
bleeding through" rendering bug on darker panel colours on some
skin/hardware combinations, not an oversight. A literal fully-dark
Dark theme would need to darken exactly these colours, risking
reintroducing that bug on hardware this project cannot test against
in every session. Dark theme therefore only darkens the outer screen
edges, text, and header highlight colours; panel content stays white
in every theme, Dark included. Confirmed via device screenshots
(device test round 15) that no bleed-through occurred with this
approach across Default/Light/Dark/Gray/High Contrast.

---

# Layout Independence

Changing the theme shall not change:

- Screen layout
- Column positions
- Area sizes
- Navigation
- Button functions
- Information Panel behaviour
- Playlist behaviour
- Playback behaviour

Theme handling shall only affect presentation.

---
# Enigma2 Skin Integration

MediaPlayer3 shall remain compatible with the active Enigma2 skin.

Theme implementation shall use MediaPlayer3 presentation settings
without requiring changes to the active Enigma2 skin.

Where possible, colours and visual properties that are already provided
by the current Enigma2 skin may be reused.

MediaPlayer3-specific theme settings shall take precedence where a
specific MediaPlayer3 element requires a defined appearance.

---

# Active Area

The currently active MainScreen or BrowserScreen area shall be visually
distinguishable from inactive areas.

The active area shall use the standard MediaPlayer3 blue highlight.

The inactive area shall use the corresponding inactive background.

The same visual rule shall apply to:

- Player
- Playlist
- Information
- Browser columns

The active-area indication shall remain consistent between Light and
Dark themes.

Implementation note (device test round 14): the inactive/active
header colours behind this section were found not to be reading from
the theme at all before this round -- every theme file was missing
the two keys involved, so every screen's own hardcoded fallback value
was silently the only one ever used, regardless of the selected
theme. Fixed by adding both keys to every theme file (including
_FALLBACK_THEME itself); confirmed via device screenshots (round 15)
that the active-area colour is now visually identical across Light
and Dark as required above, while High Contrast correctly shows its
own distinct colour (outside this consistency requirement).

---

# Information Panel

The Information Panel shall follow the selected theme.

The information type header may use the active-area highlight when the
Information area is active.

Information content shall remain readable in both themes.

Lyrics scrolling and other Information Panel functionality shall not
change when the theme changes.

---

# Text and Contrast

All MediaPlayer3 text shall remain readable against its background.

The theme shall provide sufficient contrast for:

- Titles
- Metadata
- Lyrics
- Playlist entries
- Browser entries
- Headers
- Status information
- Error messages

The implementation shall avoid relying on colour alone to communicate
critical information.

---

# Artwork

Album artwork, station artwork and podcast artwork shall not be
modified by theme selection.

Artwork shall retain its original colours.

The surrounding area may change according to the selected theme.

---

# Progress Bar

The MainScreen progress bar shall remain at the bottom of the screen.

Its logical function and position shall not change between themes.

The active playback state shall remain visually distinguishable.

---
# Resolution and Scaling

Theme implementation shall remain compatible with different Enigma2
screen resolutions.

The logical MediaPlayer3 layout shall not depend on a specific screen
resolution.

Theme elements shall scale or adapt to the available screen dimensions
where required.

Small supported resolutions shall remain usable without requiring a
separate theme layout.

---

# Theme Resources

Theme-specific visual definitions should be kept separate from
application logic.

Theme resources may contain:

- Background definitions
- Text colours
- Header colours
- Highlight colours
- Border definitions
- Progress bar appearance

Application components shall not contain duplicated Light and Dark
colour definitions where a shared theme resource can be used instead.

---

# Runtime Theme Changes

Changing the selected theme does not require changes to application
logic.

If the Settings implementation supports changing the theme while
MediaPlayer3 is running, affected screens may be refreshed to apply the
new theme.

Playback state shall not be affected by a theme change.

---

# Compatibility

Theme implementation shall remain compatible with supported Enigma2
versions and devices.

Theme resources shall not require functionality unavailable on older
supported Enigma2 versions.

Where an optional visual feature is unavailable, MediaPlayer3 shall use
a safe fallback appearance.

---

# Design Principles

The theme system shall provide visual consistency without introducing
new application logic.

Theme implementation shall not change the logical layout of the
application.

The same navigation and functional behaviour shall be available in both
Light and Dark themes.

The active area shall remain clearly identifiable.

Information shall remain readable.

Artwork shall remain unchanged.

Playback shall not be affected by theme selection.

The theme system should remain reusable for future MediaPlayer3 visual
themes.

---

End of THEME_SPEC.md

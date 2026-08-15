# MAINSCREEN_NAVIGATION_SPEC.md

MediaPlayer3

MainScreen Navigation Specification

---

# Purpose

This document defines the navigation behaviour of MainScreen.

MainScreen provides a common playback interface regardless of the
source from which playback was started.

The navigation model shall remain consistent when MainScreen is opened
from:

- Internet Radio
- File Browser
- Favorites
- Music Library
- Podcasts

MainScreen navigation shall not depend on the implementation details of
the source screen.

---

# MainScreen Areas

MainScreen contains three navigable areas:

1. Player
2. Playlist
3. Information

Only one area is active at a time.

The active area's header shall use the standard blue highlight.

Inactive headers shall use the normal inactive background.

---

# Area Selection

The EPG / INFO button is used to change the active MainScreen area.

The selection cycles through the three areas:

```text
Player
  ↓
Playlist
  ↓
Information
  ↓
Player
# Information Area

The Information area displays the currently available information for
the active playback source.

Possible information types include:

- Lyrics
- Metadata
- Codec
- Radio EPG
- Now Playing
- Station Information
- Podcast information

Only information containing actual content shall be displayed.

When multiple information types are available, the Information area
shall select the most relevant type according to the current playback
source.

The Information area may provide additional navigation for content such
as lyrics.

---

# MainScreen OK Menu

OK in MainScreen shall open the MainScreen action menu.

The menu shall contain the following items in this order:

1. Back
2. Stop / Resume
3. Cancel

The Back action is always the first menu item.

---

# Back

Selecting Back shall close MainScreen and return the user to the view
from which MainScreen was opened.

The previous view shall be retained by MainScreen when it is opened.

Possible return targets include:

- Internet Radio
- File Browser
- Favorites
- Music Library
- Podcasts

MainScreen shall not make assumptions about which source screen is
currently active.

The return target shall be determined by the context in which
MainScreen was opened.

---

# Stop / Resume

The Stop / Resume action shall control the current playback state.

If playback is active:

    Stop

shall stop playback.

If playback is stopped and the current media item can be resumed:

    Resume

shall resume playback according to the existing playback behaviour.

The action label shall reflect the current playback state where
appropriate.

The operation shall use the existing playback controller.

---

# Cancel

Cancel closes the MainScreen action menu without changing playback or
navigation state.

The user remains in MainScreen with the same active area.

---
# MainScreen Startup and Return Context

When MainScreen is opened, the originating view shall be stored as part
of the MainScreen navigation context.

The context shall identify the screen to which the Back action must
return.

MainScreen shall not permanently own or replace the originating screen.

---

# Return Behaviour

Selecting:

    OK → Back

shall:

1. Close MainScreen.
2. Stop any MainScreen-specific navigation state.
3. Restore the previously active source screen.
4. Return the user to the same logical context from which playback was
   started.

The return operation shall work consistently for:

- Internet Radio
- File Browser
- Favorites
- Music Library
- Podcasts

---

# EPG / INFO Behaviour

The EPG / INFO button has one responsibility within MainScreen:

    Change active MainScreen area.

It shall not:

- Open Favorites.
- Open File Browser.
- Open Internet Radio.
- Close MainScreen.
- Stop playback.

This removes source-specific behaviour from the EPG / INFO button.

The TEXT button is no longer used by MediaPlayer3.

All previous MainScreen navigation functionality based on the TEXT button
shall be removed.

---

# Navigation Consistency

The same navigation principles shall be used regardless of the
playback source.

The user should not need to remember different MainScreen navigation
rules for:

- Music
- Radio
- Favorites
- Podcasts

MainScreen provides one consistent playback environment.

---

# Error Handling

If the stored return context is no longer available, MainScreen shall
close safely and return to the safest available MediaPlayer3 view.

An invalid return target shall not terminate MediaPlayer3.

Navigation errors shall be logged through the existing MediaPlayer3
logging system.

---

# Design Principle

MainScreen navigation shall be based on context rather than the source
implementation.

The screen that opened MainScreen determines where Back returns.

The EPG / INFO button controls MainScreen area selection.

The OK menu controls MainScreen actions.

This creates a clear separation between:

- Area navigation
- Playback actions
- Returning to the previous screen

---

End of MAINSCREEN_NAVIGATION_SPEC.md

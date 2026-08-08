# MediaPlayer3

# Theme Specification

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

A theme defines MediaPlayer3's colour scheme: background, text,
highlight, progress bar and accent colours.

Themes are loaded and managed by SkinManager (skin.py) -- see
SKIN_MANAGER_SPEC.md. This document describes the theme data format
and how Screens apply it; it does not introduce a separate
ThemeManager module (Build 0006's Core Layer lists SkinManager only).

---

# 2. Skin vs Theme

Skin defines layout, fonts and structure.

Theme defines colours only.

Changing a theme never changes screen layout. A single skin may
support multiple themes.

---

# 3. Directory Structure

    resources/themes/
        default.json
        dark.json
        highcontrast.json

---

# 4. Theme Format

    {
        "name": "Dark",
        "background": "#0A0A0A",
        "text": "#A4A4A5",
        "highlight": "#0085E5",
        "progress": "#565050",
        "accent": "#191618"
    }

All colour values are `#RRGGBB` strings, matching Enigma2 skin colour
conventions.

None of the shipped themes use pure black (#000000) for `background`
(Build 0007, device test round 10) -- see section 7 for why.

---

# 5. Shipped Themes

- default -- neutral light-grey text on near-black.
- dark -- lower-contrast blue-grey palette.
- highcontrast -- pure white text, yellow highlight, red accent, for
  maximum legibility.
- gray (Build 0007, device test round 8) -- background #A0A0A0 with
  dark text (#1A1A1A) for contrast; requested as the new default
  theme.

---

# 6. How Screens Apply a Theme

Screens read colours through SkinManager's public interface --
`skin_manager.getColor(key, default)` -- never by reading theme files
themselves.

Every screen's `_buildSkin()` reads `background` (and, where relevant,
`text`/`progress`) once per Screen build and applies it as a
`backgroundColor` skin attribute. Build 0007 (device test round 8)
extended this from MainScreen alone to every screen in the
application -- each is now fullscreen (position="0,0", scaled from
its own design canvas to the actual desktop size via
compatibility.getDesktopSize()) with the theme's background colour
filling the whole display, matching MainScreen's own approach since
Build 0005.

Device test round 9: that round-8 conversion missed one detail
MainScreen already got right back in Build 0005 -- Enigma2 Label
widgets paint an opaque (black) backdrop by default, so every text
widget on the newly-converted screens showed a solid black box
instead of the theme's background colour (visible clearly against the
new Gray theme; confirmed by device screenshots), and would show the
box's own live video/background bleeding through instead of solid
colour if TV were playing underneath. Every Label-type widget on
every screen now sets `transparent="1"` and
`foregroundColor="{text_color}"`, matching MainScreen's own widgets
exactly. List-type widgets (file lists, menu lists, station/region/
language lists) don't need this -- they already rendered correctly.

Because Enigma2 fixes a Screen's skin once `Screen.__init__()` has
run, a theme change only affects a *currently open* screen on its
next creation (i.e. after closing and reopening it) -- newly-opened
Screens pick up the change immediately since they read colours at
their own open time. This is a real Enigma2 Screen/skin limitation,
not something SettingsScreen can work around from outside.

---

# 7. Fallback Behaviour

A missing or invalid theme file falls back to the default theme's
colours, and if even that is unavailable, to a small built-in colour
set -- SkinManager.getColor() always returns a usable colour string,
never raises, never returns None.

Colours that become a `backgroundColor` skin attribute are passed
through `to_opaque_skin_color()` before being written into the skin
XML (Build 0007, device test round 11). Device testing showed the
box's own live video/background bleeding through behind every screen,
even with backgroundColor and every widget's transparent="1" set
correctly (round 9's fix) and even after avoiding pure black in
favour of #0A0A0A (round 10). The user identified the real cause and
confirmed it against the device's own skin.xml: Enigma2 skin colours
are 8-digit "#AARRGGBB", not 6-digit "#RRGGBB" -- a bare 6-digit
value (what every backgroundColor was still using through round 10)
leaves the alpha channel to be read unpredictably rather than
reliably opaque, regardless of which RGB value was chosen.
`to_opaque_skin_color()` prepends an explicit "00" alpha byte (opaque,
in Enigma2's inverted alpha convention where 00 = opaque and FF =
fully transparent) to any 6-digit colour; 8-digit input is returned
unchanged. Round 10's near-black RGB choice (#0A0A0A, still used as
the underlying colour value) turned out not to be the actual fix, but
is harmless to keep -- theme JSON files stay plain "#RRGGBB" for
portability/readability; only the skin-XML-generation layer adds the
alpha byte, and only for backgroundColor, never foregroundColor/text.

Round 11's fix still didn't stop the video/background bleeding
through, confirmed by a further device screenshot (Build 0007, device
test round 12). The user found, empirically, that a WHITE background
reliably avoids the issue where gray/near-black backgrounds don't --
visible directly in the screenshot itself, where Main Menu's first
rows rendered on a solid opaque white bar while the rest of the list
showed the background through. `PANEL_BACKGROUND_COLOR` ("#FFFFFF")
and `PANEL_TEXT_COLOR` ("#1A1A1A") are now used by every text-bearing
widget (Label AND List types) on every screen, instead of the active
theme's own `background`/`text` colours -- the theme's own colours are
now reserved for the outer screen background (edges) only, per the
user's own framing ("Reunat saavat jäädä harmaiksi" -- the edges can
stay grey). MainScreen additionally gained a dedicated
"header_background" widget spanning its whole top text area (version/
cover/media/meta/status), since that area previously had no widget-
level background at all and relied entirely on the screen's own
background showing through.

This means a theme's `background`/`text` values now only affect the
narrow strip of screen visible around the edges of each screen's
white text panels -- not the text itself, which is always white-on-
near-black regardless of the active theme. This is a deliberate,
pragmatic trade-off to guarantee readability and opacity over full
theme colour customisation of text areas.

---

# 8. Acceptance Criteria

- Every shipped theme parses and applies without error.
- Switching theme in Settings changes newly-opened Screens'
  appearance without a restart.
- A missing/invalid theme file never prevents startup.
- No shipped theme or built-in fallback colour uses pure black
  (#000000) for a background.
- Every backgroundColor attribute emitted into a screen's skin XML is
  8-digit "#AARRGGBB" with an explicit opaque ("00") alpha byte.

---

# End of File

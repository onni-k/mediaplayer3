# PODCAST_SCREEN_SPEC.md

MediaPlayer3

Podcast Screen Specification

---

# Purpose

PodcastScreen provides the user interface for discovering, browsing and
managing podcasts.

PodcastScreen presents podcast information supplied by PodcastManager
and provides access to podcast subscriptions and episodes.

PodcastScreen does not implement podcast business logic.

PodcastScreen does not communicate directly with external podcast
providers.

---

# Layout

PodcastScreen uses a three-column layout.

```text
Available Podcasts | Subscribed Podcasts | Episodes
# Available Podcasts

The Available Podcasts column provides podcast discovery.

The user may search for podcasts using the available search function.

Search results are displayed in the left column.

Selecting a podcast updates the Episodes column with the available
episodes for that podcast.

The selected podcast remains the current podcast while the user moves
between columns.

---

# Subscribed Podcasts

The Subscribed Podcasts column contains locally stored subscriptions.

Selecting a subscribed podcast updates the Episodes column.

Subscriptions remain available even when the external podcast provider
is temporarily unavailable, provided that sufficient cached information
exists.

---

# Episodes

The Episodes column displays episodes belonging to the currently
selected podcast.

Each episode may display information such as:

- Episode title
- Publication date
- Duration

Additional information may be displayed when available.

Selecting an episode makes it the current episode.

---

# Podcast Actions

## Available Podcast

OK on a podcast opens an action menu.

Possible actions include:

- Subscribe
- Open podcast
- Cancel

The exact available actions depend on whether the podcast is already
subscribed.

---

## Subscribed Podcast

OK on a subscribed podcast opens an action menu.

Possible actions include:

- Open podcast
- Refresh
- Unsubscribe
- Cancel

---

## Episode

OK on an episode opens an action menu.

Possible actions include:

- Play
- Add to playlist
- Cancel

The selected action shall use the existing MediaPlayer3 playback and
playlist architecture.

---

# Popular Podcasts, Language and Result Limit

(Added in 1.3.000.)

OK in the Available column always offers "Fetch popular podcasts"
(Podcast Index's trending list) and "Search", in addition to Subscribe /
Open podcast when a podcast is selected. YELLOW opens the same menu from
every column (only Fetch popular / Search outside the Available column).

BLUE chooses the podcast language: the receiver's system language by
default (config key podcast.language empty), "All languages" ("all"),
or a language code. The language is sent to Podcast Index's trending
endpoint and used to filter search results client-side by each
podcast's declared language, since the search endpoint has no
language parameter.

Both search and popular requests ask the provider for up to
podcast.search_limit podcasts (Settings: "Podcast search limit",
10-1000, default 1000).

The top line shows what the column lists and the number found. The
last Available result (list, query/label and selected row) is kept for
the running session and shown again when the screen is reopened.
Descriptions are shown with HTML removed
(PodcastManager.cleanDescription()).

---

# Search

Podcast search shall be available from the Available Podcasts column.

Search results replace or update the current list of available podcasts.

An empty search result shall be handled normally and shall not produce
an error.

Search failures shall be reported to the user without terminating
PodcastScreen.
# Playback Integration

PodcastScreen uses the existing MediaPlayer3 playback architecture.

When an episode is selected for playback:

- The episode is passed to the existing playlist/playback system.
- MainScreen is opened for playback.
- MainScreen starts in Player mode.
- The Information Panel selects the most relevant available podcast
  information.

PodcastScreen does not implement audio playback.

---

# Playlist Integration

Podcast episodes may be added to the existing playlist.

Adding an episode to the playlist shall not start playback unless the
user explicitly selects Play.

The existing playlist behaviour remains unchanged.

Podcast episodes shall be treated as normal playable media items by the
playback system.

---

# Help

HELP opens podcast-specific help documentation.

The help documentation shall explain:

- Podcast browser layout
- Available Podcasts
- Subscribed Podcasts
- Episodes
- Search
- Subscription actions
- Episode actions
- Navigation keys

The user shall not need to select help documents manually.

---

# Error Handling

PodcastScreen shall remain usable when podcast information is
temporarily unavailable.

Possible conditions include:

- Network unavailable
- Podcast provider unavailable
- Search failure
- Invalid podcast data
- Missing episode data
- Empty search results

Errors shall be presented to the user where appropriate.

Previously available local subscription information shall remain usable
when possible.

PodcastScreen shall not terminate because of an external podcast
service failure.

---

# Design Principles

PodcastScreen is responsible for presentation and user interaction.

PodcastManager is responsible for podcast business logic.

Podcast providers are responsible for communication with external
services.

Playback remains the responsibility of the existing playback
architecture.

This separation keeps PodcastScreen consistent with the architecture of
the other MediaPlayer3 screens.

The three-column design also provides a common browsing model that can
be reused by other MediaPlayer3 content browsers.

---

End of PODCAST_SCREEN_SPEC.md

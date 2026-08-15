# PODCAST_MANAGER_SPEC.md

MediaPlayer3

Podcast Manager Specification

---

# Purpose

PodcastManager provides podcast discovery, subscription and episode
management for MediaPlayer3.

PodcastManager separates podcast functionality from the user interface
and playback implementation.

Podcast content is presented through the existing browser and
MainScreen architecture.

---

# Design Goals

PodcastManager shall:

- Support podcast discovery.
- Support podcast subscriptions.
- Provide access to podcast episodes.
- Allow episodes to be added to the existing playlist.
- Use the existing playback system for episode playback.
- Handle unavailable network services gracefully.
- Allow additional podcast providers to be added later.

PodcastManager shall not implement user interface presentation.

PodcastManager shall not implement audio playback.

---

# Architecture

Podcast functionality follows the modular architecture used elsewhere
in MediaPlayer3.

```text
                 Podcast Browser
                       │
                       ▼
                 PodcastManager
                       │
              ┌────────┴────────┐
              │                 │
       Podcast Provider    Local Subscriptions
              │
              ▼
       External Podcast Service
# Podcast Data

PodcastManager shall work with the following logical information.

## Podcast

A podcast may contain:

- Podcast ID
- Title
- Description
- Author
- Artwork
- Language
- Category
- Feed URL
- Website URL

Not every provider is required to supply every field.

Unavailable fields shall remain empty rather than causing an error.

---

## Subscription

A subscription represents a podcast selected by the user.

Subscriptions shall be stored locally.

A subscription shall retain enough information to retrieve the podcast
and its episodes without requiring the user to search for it again.

The subscription list shall be available to the Podcast browser.

---

## Episode

An episode may contain:

- Episode ID
- Podcast ID
- Title
- Description
- Publication date
- Duration
- Artwork
- Episode URL
- Playback URL

Only episodes with a valid playable URL shall be offered for playback.

---

# Podcast Browser

The Podcast browser shall use a three-column layout.

```text
Available Podcasts | Subscribed Podcasts | Episodes
- Missing podcast feed
- Missing episode data
- Invalid episode playback URL
- Provider timeout
- Provider authentication or request failure
- Empty search result
- Podcast no longer available

Invalid or incomplete provider data shall not cause MediaPlayer3 to
terminate.

---

# Subscription Persistence

Subscriptions shall be stored independently from the external
provider.

Removing or changing a provider shall not corrupt the local
subscription data.

If a subscribed podcast cannot currently be retrieved, the subscription
shall remain stored and may be retried later.

---

# Refresh Behaviour

The user shall be able to refresh podcast information.

Refreshing a podcast shall update:

- Podcast metadata
- Artwork where available
- Episode list

Existing subscription information shall be preserved.

A failed refresh shall not remove previously stored valid information.

---

# Provider Independence

PodcastManager shall not depend on a specific external podcast service.

The provider interface shall make it possible to add additional
providers later.

For example:

- Podcast Index
- RSS feed provider
- Other compatible podcast services

Provider-specific implementation details shall remain outside
PodcastManager.

---

# Future Extensions

The architecture should allow future support for:

- Episode download
- Offline podcast playback
- Automatic episode updates
- Played/unplayed episode status
- Resume position
- Podcast categories
- Search history

These features are outside the scope of Build 0010 unless explicitly
added to the implementation plan.

---

# Responsibilities Summary

PodcastManager:

- Manages podcast application state.
- Manages subscriptions.
- Provides podcast and episode data.
- Coordinates podcast providers.
- Integrates podcast episodes with the existing playlist and playback
  architecture.
- Handles podcast-related errors.

Podcast providers:

- Communicate with external podcast services.
- Search and retrieve podcast information.
- Retrieve episode information.
- Convert provider-specific data into the common podcast data model.

Screens:

- Present podcast information.
- Handle user interaction.
- Do not implement podcast business logic.

PlaybackController:

- Controls playback.
- Does not contain podcast-specific retrieval logic.

This keeps podcast functionality separated from presentation, playback
and external service implementation.

---

End of PODCAST_MANAGER_SPEC.md

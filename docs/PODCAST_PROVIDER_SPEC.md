# PODCAST_PROVIDER_SPEC.md

MediaPlayer3

Podcast Provider Specification

---

# Purpose

Podcast providers provide access to external podcast services for
PodcastManager.

A provider converts service-specific data into the common podcast data
model used by MediaPlayer3.

Podcast providers do not implement user interface functionality.

Podcast providers do not manage subscriptions.

Podcast providers do not control playback.

---

# Provider Responsibilities

A podcast provider is responsible for:

- Podcast search
- Podcast discovery
- Podcast metadata retrieval
- Episode retrieval
- Feed information retrieval
- Conversion of provider-specific data
- Provider-specific network communication
- Provider-specific error handling

The provider shall return data using the common interfaces expected by
PodcastManager.

---

# Provider Independence

PodcastManager shall not contain provider-specific implementation
details.

The provider interface shall allow multiple external podcast services
to be used without modifying PodcastManager.

Possible providers include:

- Podcast Index
- RSS feed services
- Other compatible podcast services

The initial Build 0010 implementation may use a single provider.

Additional providers may be added later.

---

# Common Podcast Data

Providers shall convert external data into the common MediaPlayer3
podcast representation.

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

Provider-specific fields may be retained where useful, but the common
fields shall remain independent of the provider.

---

# Search Interface

A provider shall support podcast search where the external service
provides search functionality.

The search operation shall accept a user-provided search query.

The provider shall return:

- Zero results
- One result
- Multiple podcast results

An empty result is a valid response.

Search failures shall be reported to PodcastManager without terminating
MediaPlayer3.

---
# Episode Retrieval

A provider shall support retrieval of episodes for a selected podcast.

The operation shall accept the provider-specific podcast identifier.

The provider shall return:

- Episode list
- Episode metadata
- Playback information where available

Episodes without a valid playback URL may be returned as metadata, but
PodcastManager shall not offer them as playable items.

Provider-specific episode limits and pagination shall be handled inside
the provider.

PodcastManager shall receive a normalized episode list.

---

# Podcast Metadata

A provider shall be able to retrieve detailed information for a
selected podcast where supported.

The returned information may include:

- Title
- Description
- Author
- Artwork
- Language
- Category
- Feed URL
- Website URL

Missing fields shall not be treated as provider failure.

---

# Pagination

External podcast services may limit the number of search results or
episodes returned in a single request.

Pagination shall be handled by the provider.

PodcastManager shall not need to know how the external service
implements pagination.

The provider may retrieve additional pages when necessary.

If additional pages cannot be retrieved, already retrieved valid data
may still be returned.

---

# Network Communication

Providers communicate directly with their external service.

Network operations shall have appropriate timeout handling.

A provider shall not wait indefinitely for an external service.

Network errors shall be converted into provider-level errors that can be
handled by PodcastManager.

The provider shall not terminate MediaPlayer3 because of a network
failure.

---

# Authentication

If an external podcast service requires authentication, credentials
shall be handled by the provider.

Authentication details shall not be exposed to PodcastScreen.

PodcastManager shall not need to know provider-specific authentication
mechanisms.

Provider credentials shall not be written to normal application logs.

---

# Caching

Provider implementations may use local caching where appropriate.

Caching may reduce unnecessary network requests and improve response
time.

Cached data shall not prevent explicit refresh operations.

A cache failure shall not terminate MediaPlayer3.

---
# Error Handling

Providers shall handle external service failures without terminating
MediaPlayer3.

The following situations shall be handled:

- Network unavailable
- Provider timeout
- HTTP request failure
- Invalid response
- Invalid JSON or XML data
- Missing required fields
- Authentication failure
- Rate limiting
- Podcast no longer available
- Episode no longer available

Provider errors shall be returned to PodcastManager in a form that can
be presented appropriately to the user or written to the application
log.

Provider errors shall not be silently converted into valid podcast
data.

---

# Logging

Provider operations shall use the MediaPlayer3 logging system.

Useful diagnostic information may include:

- Provider name
- Operation
- Request status
- Error type
- Error description
- Timestamp

Authentication credentials and other sensitive provider information
shall never be written to normal logs.

---

# Provider Interface

The provider interface shall expose only the operations required by
PodcastManager.

The exact implementation may vary between providers.

Conceptually, the interface provides operations equivalent to:

```text
searchPodcasts(query)
getPodcast(podcast_id)
getEpisodes(podcast_id)
refreshPodcast(podcast_id)
Provider-specific request formats, URLs, authentication and response
parsing remain inside the provider implementation.

---

# Podcast Index

Podcast Index may be used as the initial Build 0010 podcast provider.

Podcast Index specific implementation details shall remain isolated from
PodcastManager.

If Podcast Index is replaced or another provider is added, the common
PodcastManager interface shall remain unchanged.

---

# Future Providers

The provider architecture shall allow additional podcast sources to be
added later.

Possible future sources include:

- RSS feeds
- Other podcast indexes
- Regional podcast services
- User-defined podcast feeds

Adding a provider should require implementation of the provider
interface rather than changes to the PodcastScreen.

---

# Design Principles

Podcast providers are adapters between external podcast services and
MediaPlayer3.

They:

- Know how to communicate with an external service.
- Know how to parse its responses.
- Convert external data into the common MediaPlayer3 data model.
- Report external service failures.

They do not:

- Present user interface elements.
- Manage subscriptions.
- Control playback.
- Directly manipulate MainScreen.
- Directly manipulate PodcastScreen.

This keeps external service dependencies isolated and allows
PodcastManager and PodcastScreen to remain provider-independent.

---

End of PODCAST_PROVIDER_SPEC.md

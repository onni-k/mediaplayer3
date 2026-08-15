# YLE_EPG_SPEC.md

MediaPlayer3

YLE Radio EPG Specification

---

# Purpose

YLE_EPG provides electronic programme guide information for supported
YLE radio stations.

The EPG data is used by MediaPlayer3 to provide additional information
for the currently playing radio station.

The EPG information is presented through the existing Information Panel.

YLE_EPG does not implement radio playback.

---

# Supported Stations

The initial implementation shall support the YLE radio channels for
which reliable EPG data can be retrieved.

The list of supported channels shall be configurable or maintainable
without changes to the Information Panel.

Additional YLE radio channels may be added later.

A channel without available EPG data shall continue to function normally
as a radio station.

---

# EPG Data

The EPG provider shall retrieve programme information for a radio
station.

A programme may contain:

- Programme title
- Start time
- End time
- Description
- Station identifier
- Additional programme information where available

Missing optional programme information shall not cause the EPG
operation to fail.

---

# Current Programme

The Information Panel shall be able to display the currently active
radio programme.

Where available, the displayed information may include:

- Programme title
- Programme description
- Start time
- End time

The current programme shall be selected according to the current time.

---

# Upcoming Programmes

Where available, upcoming radio programmes may also be displayed.

The Information Panel shall prioritize the currently active programme.

Upcoming programmes may be presented as additional EPG information when
there is sufficient available space.

---
# EPG Retrieval

YLE_EPG shall retrieve programme information through the configured YLE
EPG data source.

The retrieval mechanism shall remain separated from the Information
Panel.

The EPG component shall provide normalized programme information to the
rest of MediaPlayer3.

---

# API Key

MediaPlayer3 ships with a bundled default app_id/app_key pair
(obfuscated -- see yle_credentials.py's own header for why this is not
real security, just avoiding a plaintext credential string in a
publicly distributed project), so Yle Radio EPG works without any
per-user setup. This supersedes this section's original file-based
(yle.txt) design, amended directly by the user (device test round 16):
the same bundled-credential approach podcast_providers/podcastindex
already used for Podcast Index was preferred over adding a second,
different "read a credential from a file" mechanism.

Settings still provides an app_id/app_key entry (Settings -> Yle EPG
app_id/app_key, tunnus.yle.fi/api-avaimet) for anyone who wants to use
their own key instead -- a user-provided key always takes priority
over the bundled default.

The API key shall not be written to normal application logs, whether
it is the bundled default or a user-provided one.

---

# Update Behaviour

EPG information may be retrieved when:

- A supported YLE station starts playback.
- The current EPG information has expired.
- The user requests an update where such an operation is available.

The implementation should avoid unnecessary repeated requests.

Currently valid EPG data may be cached locally where appropriate.

---

# Time Handling

Programme selection shall use the current time when determining the
currently active programme.

Start and end times shall be interpreted consistently.

The implementation shall handle programme boundaries correctly.

If there is no programme matching the current time, the EPG component
shall report that no current programme is available.

---

# Data Availability

YLE EPG information may be unavailable because of:

- Network failure
- YLE service unavailable
- Missing API key
- Invalid API response
- Missing station information
- Missing programme information

These conditions shall not prevent radio playback.

If EPG data cannot be retrieved, the Information Panel shall
automatically fall back to other available information.

---

# Information Panel Integration

YLE EPG is one information source used by the existing Information
Panel.

When YLE EPG data is available, it shall be preferred for supported YLE
radio stations.

If no usable EPG information exists, the Information Panel shall
automatically fall back to other available information.

The Information Panel shall not contain YLE-specific retrieval logic.

---
# Error Handling

YLE_EPG shall handle EPG service failures without terminating
MediaPlayer3.

Possible conditions include:

- Network unavailable
- EPG service unavailable
- Request timeout
- Invalid response
- Invalid programme data
- Missing API key
- Missing station mapping
- Empty programme list

Errors shall be logged through the existing MediaPlayer3 logging
system.

The user shall not be required to resolve an EPG failure before
continuing radio playback.

---

# Caching

Previously retrieved EPG information may be cached locally.

Cached information may be used when the EPG service is temporarily
unavailable.

Cached data shall have an appropriate validity period.

Expired data shall not be presented as current programme information
unless no better information is available and the user is informed
appropriately.

---

# Provider Independence

YLE EPG shall be implemented as a provider-specific component.

The Information Panel and other presentation components shall use the
common EPG information interface.

This allows additional radio EPG providers to be added later.

Possible future providers include:

- Bauer Media
- Other Finnish radio providers
- Other regional radio EPG services

Provider-specific retrieval logic shall remain outside the Information
Panel.

---

# Station Mapping

The EPG component shall map MediaPlayer3 radio stations to the
corresponding YLE station identifiers.

The mapping shall be maintained separately from presentation logic.

If a station has no known YLE EPG mapping, the station shall continue to
operate normally without EPG information.

---

# Logging

Useful diagnostic information may include:

- Station
- EPG provider
- Request status
- Number of programmes received
- Cache status
- Error type
- Error description
- Timestamp

The API key and other sensitive configuration data shall never be
written to normal logs.

---

# Design Principles

YLE EPG is an information provider, not a playback component.

It:

- Retrieves programme information.
- Normalizes EPG data.
- Provides current and upcoming programme information.
- Handles provider-specific errors.
- May maintain a local cache.

It does not:

- Control radio playback.
- Present its own user interface.
- Directly manipulate MainScreen.
- Directly manipulate Information Panel presentation.

The Information Panel receives EPG information from the appropriate
manager or provider and automatically falls back to other available
information.

This keeps the EPG architecture reusable and allows additional radio
EPG providers to be introduced later.

---

End of YLE_EPG_SPEC.md

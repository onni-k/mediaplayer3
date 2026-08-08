# EPG_MANAGER_SPEC.md

MediaPlayer3

EPG Manager Specification

Status: Build 0009 -- CONFIRMED COMPLETE (13 rounds of real device
testing across OpenViX, OpenPLI, OpenATV and OpenBH; both providers
below confirmed working against real Yle/Bauer data. See
CHANGELOG.md's "BUILD 0009 -- CONFIRMED COMPLETE" and
Claude_notes_build0009.txt for the full record).

---

# Purpose

EPGManager provides programme and playback information for Internet
Radio.

EPGManager presents a unified interface regardless of the underlying
programme information provider.

The manager is completely independent from MainScreen and InternetRadio
Manager.

MainScreen accesses programme information only through EPGManager.

---

# Design Goals

EPGManager shall:

- Support multiple programme information providers.
- Operate independently of radio station implementation.
- Return only valid information.
- Gracefully handle unavailable programme information.
- Allow future providers to be added without changing existing code.

---

# Responsibilities

EPGManager is responsible for:

- Detecting the currently playing station.
- Selecting the appropriate provider.
- Retrieving programme information.
- Retrieving "Now Playing" information.
- Returning station information.
- Caching programme data when appropriate.

EPGManager does not perform playback.

EPGManager does not control InternetRadioManager.

---

# Architecture

```
                   MainScreen
                        │
                        │
                Information Panel
                        │
                        │
                  EPGManager
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        │               │                │
   YLE Provider    Bauer Provider   Future Providers
```

Each provider is responsible only for retrieving information from its
own service.

EPGManager provides a common interface to all providers.

---
# Providers

EPGManager supports multiple independent providers.

Each provider determines whether it can supply information for the
currently playing station.

Initially supported providers include:

YLE Provider

Provides:

- Radio EPG
- Current programme
- Upcoming programmes

Bauer Provider

Provides:

- Now Playing
- Station information

Additional providers may be added without modifying EPGManager or
MainScreen.

Providers register themselves through the EPGManager interface.

---

# Information Types

EPGManager may return the following information:

Radio EPG

Current programme.

Upcoming programmes.

Programme start time.

Programme end time.

Now Playing

Artist.

Title.

Programme name.

Station Information

Station name.

Broadcaster.

Genre.

Bitrate.

Codec.

Not every provider supplies every information type.

Unavailable information is omitted.

---

# Information Retrieval

EPGManager automatically selects the appropriate provider according to
the currently playing station.

Provider selection is transparent to the user.

When no provider supports the current station:

- No error is generated.
- Empty information is returned.
- Information Panel automatically displays other available information.

This behaviour ensures reliable playback regardless of programme
information availability.

---
# Information Panel Integration

EPGManager supplies programme information exclusively through the
Information Panel.

Possible Information Panel pages include:

Information: Radio EPG

Information: Now Playing

Information: Station

Only pages containing actual information are presented.

If Radio EPG is unavailable, the Information Panel automatically falls
back to other available information such as Now Playing or Station
Information.

MainScreen never communicates directly with individual providers.

---

# Future Providers

The provider architecture is intentionally extensible.

Future providers may include:

- Additional Finnish broadcasters
- International broadcasters
- RadioDNS services
- DVB programme information
- Internet programme guides

New providers should implement the common EPGManager provider interface.

No modifications to MainScreen or Information Panel should be required
when adding new providers.

---

# Design Principles

EPGManager separates programme information retrieval from user interface
presentation.

Providers remain independent from each other.

MainScreen remains independent from provider implementation.

The Information Panel provides the unified presentation layer for all
radio-related information.

This architecture allows MediaPlayer3 to support additional programme
information services without affecting playback functionality or user
interface behaviour.

---

End of EPG_MANAGER_SPEC.md

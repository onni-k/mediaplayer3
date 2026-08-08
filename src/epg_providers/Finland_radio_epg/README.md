# Finland_radio_epg

EPGScheduleProvider and NowPlayingProvider implementations
(epg_manager.py) for Finnish radio stations. Each provider file
targets one broadcaster/platform's own data source -- there is no
single, universal API covering Finnish radio, so this folder collects
them one broadcaster at a time as they're built and confirmed working
against real data.

## Providers in this folder

### yle_teletext_provider.py -- CONFIRMED WORKING

Yle (Yleisradio) -- Radio 1, YleX, Radio Suomi, Vega, X3M -- via Yle's
Teksti-TV (Teletext) API, the only Yle API currently open to the
public for this purpose (their older, purpose-built programme/
schedule API was deprecated in 2021). Confirmed end to end against
real API responses using the user's own registered app_id/app_key.
See EPG_MANAGER_SPEC.md's "Yle Radio Schedule Provider" section for
the full detail, known limitations, and station page numbers.

### bauer_nowplaying_provider.py -- CONFIRMED WORKING (now-playing only, ALL 18 stations)

Bauer Media Finland (Rayo, formerly RadioPlay) -- their entire
published Finnish roster, complete: Radio Nova, Iskelmä, Radio City,
Basso, Ysäri, Kasari, SuomiRäp, Radio Classic, NRJ, Radio Nostalgia,
Radio Pooki, KISS, Radio 957, Auran Aallot, Radio Pori, Fresh, Rodeo,
SuomiRock. No official API exists (unlike Yle); confirmed working via
a different path: rayo.fi's own station pages embed real, current
now-playing data directly in their Next.js __NEXT_DATA__ payload.
Confirmed end to end against real, live data for all 18 stations
(2026-08-02) -- page slugs follow a simple, guessable
lowercase/hyphenated pattern from Bauer's own published station names
(SuomiRock was the one exception needing a hyphen its simple no-
separator guess lacked; confirmed genuinely correct via the page's
own stationBrandCode, not just a successful fetch). Now-playing only
-- no equivalent embedded schedule/song-history data was found (the
site fetches those separately, client-side, via a call this
investigation didn't identify). See EPG_MANAGER_SPEC.md's "Bauer
Media Now-Playing Provider" section for the full detail, what was
ruled out first (RadioDNS SPI -- confirmed real but UK-only), and
known limitations.

## Adding a new provider

1. Confirm real data can actually be fetched (a test script the user
   runs themselves, since this environment has no outbound network
   access) before writing any parsing logic against assumed formats.
2. Implement `EPGScheduleProvider` and/or `NowPlayingProvider` (see
   epg_manager.py -- whichever fits what was actually found; a
   broadcaster may only have one of the two) in its own file here.
3. Register it: `epg_manager.registerScheduleProvider(station_key, provider_instance)`
   and/or `epg_manager.registerNowPlayingProvider(station_key, provider_instance)`.
4. Update EPG_MANAGER_SPEC.md with the new provider's own section
   (data source, known limitations, confirmed station identifiers).

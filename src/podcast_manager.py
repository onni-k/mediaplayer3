# ==============================================================================
#
# MediaPlayer3
#
# File        : podcast_manager.py
#
# Description :
#
#     PodcastManager
#
#     Podcast discovery, subscription and episode management
#     (PODCAST_MANAGER_SPEC.md). Follows InternetRadioManager's own
#     established pattern closely (local JSON persistence under
#     storage_manager's own path convention, load/save helpers that
#     never raise, a coordinator that owns application state while
#     delegating actual external communication to a provider).
#
#     PodcastManager does not implement podcast provider network
#     communication itself (podcast_providers/podcastindex/ does that
#     -- see PODCAST_PROVIDER_SPEC.md) and does not implement
#     playback or user interface presentation (PodcastScreen, not yet
#     built as of this file's creation, will do that -- see
#     PODCAST_SCREEN_SPEC.md).
#
# Implements :
#
#     PODCAST_MANAGER_SPEC.md
#
# Project :
#
#     MediaPlayer3
#
# License :
#
#     GPL-2.0-or-later
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-08-08  Build 0010 (round 2)
#   - Initial version. Subscription persistence and provider
#     coordination confirmed via stub-environment testing; not yet
#     exercised by a real PodcastScreen (not yet built).
# ------------------------------------------------------------------------------

"""
podcast_manager -- podcast discovery, subscription and episode
management (PODCAST_MANAGER_SPEC.md). See podcast_providers/ for the
actual external-service communication this delegates to.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from .logger import logger
from .podcast_providers.podcastindex.podcastindex_provider import podcastindex_provider
from .storage import storage_manager


class PodcastManager:
    """
    Owns podcast application state: subscriptions (persisted
    locally) and coordination of the podcast provider for search and
    episode/metadata retrieval. See PODCAST_MANAGER_SPEC.md
    "Responsibilities Summary".
    """

    SPECIFICATION_VERSION = "0.1"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        # Build 0010 -- a single provider for now
        # (PODCAST_PROVIDER_SPEC.md "The initial Build 0010
        # implementation may use a single provider"), referenced by a
        # short name so a future multi-provider PodcastManager could
        # route by it without PodcastScreen needing to change at all.
        self._provider = podcastindex_provider

        self._subscriptions: List[Dict[str, Any]] = []

        # Build 0010 -- podcast_id -> list of episode dicts, populated
        # by getEpisodes() as podcasts are actually browsed. Not
        # persisted (PODCAST_MANAGER_SPEC.md "Subscription
        # Persistence" only requires the subscription itself to
        # survive, not its full episode list) -- refetched from the
        # provider each time a subscribed podcast's episodes are
        # needed, same as a search result would be.
        self._episode_cache: Dict[str, List[Dict[str, Any]]] = {}

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[Podcast] %s", message)

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._subscriptions = self._loadJSON(self._subscriptionsPath(), default=[])

        self._initialized = True

        self._log(f"Ready ({len(self._subscriptions)} subscription(s))")

    # ------------------------------------------------------------------
    # Local storage
    # ------------------------------------------------------------------

    def _subscriptionsPath(self) -> str:
        return os.path.join(storage_manager.getPodcastPath(), "subscriptions.json")

    # ------------------------------------------------------------------

    def _loadJSON(self, path: str, default: Any) -> Any:

        try:
            with open(path, encoding="utf-8") as handle:

                return json.load(handle)

        except (OSError, ValueError) as error:

            logger.verbose(f"[Podcast] Unable to read {path}: {error}")

            return default

    # ------------------------------------------------------------------

    def _saveJSON(self, path: str, data: Any) -> bool:

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding="utf-8") as handle:

                json.dump(data, handle, indent=2, ensure_ascii=False)

            return True

        except OSError as error:

            self._log(f"Unable to save {path}: {error}")

            return False

    # ------------------------------------------------------------------
    # Discovery (PODCAST_MANAGER_SPEC.md "Podcast Browser" -- Available
    # Podcasts column)
    # ------------------------------------------------------------------

    def searchPodcasts(self, query: str) -> List[Dict[str, Any]]:
        """
        Delegates to the provider. Always returns a list -- see
        PodcastIndexProvider.searchPodcasts()'s own guarantee (never
        raises, empty list on any failure).
        """

        try:
            return self._provider.searchPodcasts(query)

        except Exception as error:

            # Build 0010 -- PodcastIndexProvider.searchPodcasts()
            # itself never raises (PODCAST_PROVIDER_SPEC.md "Error
            # Handling"), but this guards PodcastManager against a
            # future/different provider that doesn't follow that
            # convention, same defense-in-depth EPGManager already
            # applies around its own provider calls.
            self._log(f"Search failed: {error}")

            return []

    # ------------------------------------------------------------------
    # Subscriptions (PODCAST_MANAGER_SPEC.md "Subscription")
    # ------------------------------------------------------------------

    def getSubscriptions(self) -> List[Dict[str, Any]]:
        """
        Returns the locally stored subscription list (Subscribed
        Podcasts column). Available even when the provider/network is
        currently unreachable -- PODCAST_MANAGER_SPEC.md "Subscription
        Persistence": "Subscriptions remain available even when the
        external podcast provider is temporarily unavailable."
        """

        return list(self._subscriptions)

    # ------------------------------------------------------------------

    def isSubscribed(self, podcast_id: str) -> bool:

        return any(entry.get("podcast_id") == podcast_id for entry in self._subscriptions)

    # ------------------------------------------------------------------

    def subscribe(self, podcast: Dict[str, Any]) -> bool:
        """
        Adds `podcast` (the common podcast dict -- see
        PODCAST_PROVIDER_SPEC.md "Common Podcast Data", typically one
        returned by searchPodcasts()) to the local subscription list
        and persists it. Does nothing (returns True) if already
        subscribed -- subscribing twice is not an error.
        """

        podcast_id = podcast.get("podcast_id")

        if not podcast_id:

            self._log("subscribe() called with no podcast_id.")

            return False

        if self.isSubscribed(podcast_id):

            return True

        entry = dict(podcast)

        entry["subscribed_at"] = time.time()

        self._subscriptions.append(entry)

        if not self._saveJSON(self._subscriptionsPath(), self._subscriptions):

            # Build 0010 -- keep the in-memory subscription even if
            # the write failed (matches InternetRadioManager's own
            # favicon-cache-write behaviour: a disk failure degrades,
            # it doesn't undo what already succeeded logically), but
            # the caller should know persistence didn't happen.
            self._log(f"Subscribed to {entry.get('title', podcast_id)}, but saving to disk failed.")

            return False

        self._log(f"Subscribed: {entry.get('title', podcast_id)}")

        return True

    # ------------------------------------------------------------------

    def unsubscribe(self, podcast_id: str) -> bool:

        before = len(self._subscriptions)

        self._subscriptions = [entry for entry in self._subscriptions if entry.get("podcast_id") != podcast_id]

        if len(self._subscriptions) == before:

            return False

        self._episode_cache.pop(podcast_id, None)

        self._saveJSON(self._subscriptionsPath(), self._subscriptions)

        self._log(f"Unsubscribed: {podcast_id}")

        return True

    # ------------------------------------------------------------------
    # Episodes (PODCAST_MANAGER_SPEC.md "Episode")
    # ------------------------------------------------------------------

    def getEpisodes(self, podcast_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Returns episodes for `podcast_id` (Episodes column, for either
        an Available or a Subscribed podcast). Cached in memory per
        podcast_id after the first successful fetch within this
        session, refetched only when `force_refresh` is set (explicit
        refresh -- PODCAST_MANAGER_SPEC.md "Refresh Behaviour") or
        nothing has been fetched yet. A failed refresh keeps whatever
        was already cached rather than clearing it -- spec: "A failed
        refresh shall not remove previously stored valid information."
        """

        if not force_refresh and podcast_id in self._episode_cache:

            return list(self._episode_cache[podcast_id])

        try:
            episodes = self._provider.getEpisodes(podcast_id)

        except Exception as error:

            self._log(f"getEpisodes({podcast_id}) failed: {error}")

            episodes = []

        if episodes:

            self._episode_cache[podcast_id] = episodes

        elif podcast_id in self._episode_cache:

            # Empty/failed refresh, but we already had something --
            # keep the old data rather than replacing it with nothing.
            return list(self._episode_cache[podcast_id])

        return list(episodes)

    # ------------------------------------------------------------------
    # Refresh (PODCAST_MANAGER_SPEC.md "Refresh Behaviour")
    # ------------------------------------------------------------------

    def refreshPodcast(self, podcast_id: str) -> bool:
        """
        Refreshes a subscribed podcast's metadata and episode list.
        Existing subscription data is preserved on failure -- only
        overwritten with genuinely new data from the provider.
        """

        try:
            updated = self._provider.refreshPodcast(podcast_id)

        except Exception as error:

            self._log(f"refreshPodcast({podcast_id}) failed: {error}")

            updated = None

        if updated is not None:

            for entry in self._subscriptions:

                if entry.get("podcast_id") == podcast_id:

                    subscribed_at = entry.get("subscribed_at")

                    entry.clear()

                    entry.update(updated)

                    entry["subscribed_at"] = subscribed_at

                    break

            self._saveJSON(self._subscriptionsPath(), self._subscriptions)

        # Episode list refresh is independent of whether the metadata
        # refresh itself succeeded -- getEpisodes() already preserves
        # previously cached data on its own failure.
        self.getEpisodes(podcast_id, force_refresh=True)

        return updated is not None

    # ------------------------------------------------------------------
    # Diagnostics (Build 0007-onward convention -- Developer Mode)
    # ------------------------------------------------------------------

    def getDiagnostics(self) -> Dict[str, Any]:

        return {
            "provider": type(self._provider).__name__,
            "subscription_count": len(self._subscriptions),
            "subscriptions": ", ".join(entry.get("title", "?") for entry in self._subscriptions) or "None",
            "episode_cache_entries": len(self._episode_cache),
        }

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"PodcastManager(subscriptions={len(self._subscriptions)})"


# ------------------------------------------------------------------------------
# Shared manager instance
# ------------------------------------------------------------------------------

podcast_manager = PodcastManager()

# -*- coding: utf-8 -*-
"""
Plain RSS podcast feeds (1.4.009): any feed URL can be added as a podcast, e.g. Yle Areena series
(https://feeds.yle.fi/areena/v1/series/1-50438875.rss). Parsed with xml.etree (no dependencies)
into the same podcast / episode dicts the Podcast Index provider returns. Podcast ids are
"rss:<hash of the URL>", the URL is kept in `feed_url`.
"""

import hashlib
import re
import urllib.request
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from .project import PROJECT_NAME, VERSION

USER_AGENT = f"{PROJECT_NAME}/{VERSION} (Enigma2 podcast RSS)"
TIMEOUT_SECONDS = 20
MAX_BYTES = 8 * 1024 * 1024
MAX_EPISODES = 100

ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"

PREFIX = "rss:"


def isRssId(podcast_id: str) -> bool:
    return str(podcast_id or "").startswith(PREFIX)


def podcastIdFor(url: str) -> str:
    return PREFIX + hashlib.sha1(url.strip().encode("utf-8")).hexdigest()[:16]


def normalizeUrl(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("feed://"):
        url = "https://" + url[len("feed://"):]
    return url


def isValidUrl(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s/]+\.[^\s/]+", normalizeUrl(url)))


def _text(element: Optional[ET.Element], default: str = "") -> str:
    if element is None or element.text is None:
        return default
    return element.text.strip()


def _duration(value: str) -> Optional[int]:
    """'3600', '59:30' or '1:02:03' -> seconds."""

    value = (value or "").strip()

    if not value:
        return None

    try:
        parts = [int(float(part)) for part in value.split(":")]
    except ValueError:
        return None

    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part

    return seconds


def _published(value: str) -> Optional[int]:
    try:
        return int(parsedate_to_datetime(value).timestamp())
    except (TypeError, ValueError, IndexError):
        return None


def _image(element: ET.Element) -> str:
    image = element.find(ITUNES + "image")
    if image is not None and image.get("href"):
        return image.get("href", "")
    url = element.find("image/url")
    return _text(url)


def parseFeed(xml_bytes: bytes, url: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """(podcast dict, playable episodes) of an RSS document; raises ValueError when it is not a podcast feed."""

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as error:
        raise ValueError(f"not an RSS feed ({error})")

    channel = root.find("channel")

    if channel is None:
        raise ValueError("not an RSS feed (no channel)")

    podcast_id = podcastIdFor(url)

    podcast = {
        "podcast_id": podcast_id,
        "title": _text(channel.find("title")) or url,
        "description": _text(channel.find("description")) or _text(channel.find(ITUNES + "summary")),
        "author": _text(channel.find(ITUNES + "author")),
        "artwork": _image(channel),
        "language": _text(channel.find("language")),
        "category": "",
        "feed_url": url,
        "website_url": _text(channel.find("link")),
    }

    category = channel.find(ITUNES + "category")
    if category is not None and category.get("text"):
        podcast["category"] = category.get("text", "")

    episodes: List[Dict[str, Any]] = []

    for item in channel.findall("item"):

        enclosure = item.find("enclosure")
        playback_url = enclosure.get("url", "").strip() if enclosure is not None else ""

        if not playback_url:
            continue

        guid = _text(item.find("guid")) or playback_url

        episodes.append(
            {
                "episode_id": guid,
                "podcast_id": podcast_id,
                "title": _text(item.find("title")),
                "description": _text(item.find("description")) or _text(item.find(CONTENT + "encoded")),
                "published": _published(_text(item.find("pubDate"))),
                "duration": _duration(_text(item.find(ITUNES + "duration"))),
                "artwork": _image(item) or podcast["artwork"],
                "episode_url": _text(item.find("link")) or playback_url,
                "playback_url": playback_url,
            }
        )

        if len(episodes) >= MAX_EPISODES:
            break

    return podcast, episodes


def fetch(url: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Download and parse a feed (blocking: run it in a background thread)."""

    url = normalizeUrl(url)

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"})

    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        data = response.read(MAX_BYTES + 1)

    if len(data) > MAX_BYTES:
        raise ValueError("feed is too large")

    return parseFeed(data, url)

# -*- coding: utf-8 -*-
"""
HLS (.m3u8) audio follower shared by radio recording and time shift
(Round 246/247). Pure Python, no ffmpeg: the playlist is followed,
segments are downloaded as they appear and their audio is handed to a
sink as one continuous elementary stream (ADTS AAC / MP3, or fragmented
MP4). MPEG-TS segments are unpacked; ID3 tags between segments are
dropped.
"""

import re
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import urljoin

CONNECT_TIMEOUT_SECONDS = 15
MAX_FAILURES = 5
RECONNECT_DELAY_SECONDS = 2.0


class TsAudioExtractor:
    """Pulls the audio elementary stream out of MPEG-TS HLS segments."""

    def __init__(self) -> None:
        self.pmt_pid = None
        self.audio_pid = None
        self.kind = ""

    @staticmethod
    def _section(payload: bytes, start: bool) -> bytes:
        return payload[1 + payload[0]:] if start and payload else payload

    def feed(self, data: bytes) -> bytes:

        out = bytearray()

        for i in range(0, len(data) - 187, 188):

            packet = data[i:i + 188]

            if packet[0] != 0x47:
                continue

            start = bool(packet[1] & 0x40)
            pid = ((packet[1] & 0x1F) << 8) | packet[2]
            control = (packet[3] >> 4) & 3
            offset = 4

            if control & 2:
                offset += 1 + packet[4]

            if not control & 1 or offset >= 188:
                continue

            payload = packet[offset:]

            if pid == 0:

                section = self._section(payload, start)

                if len(section) >= 12:
                    length = ((section[1] & 0xF) << 8) | section[2]
                    pos, end = 8, min(len(section), 3 + length - 4)
                    while pos + 4 <= end:
                        program = (section[pos] << 8) | section[pos + 1]
                        if program != 0:
                            self.pmt_pid = ((section[pos + 2] & 0x1F) << 8) | section[pos + 3]
                            break
                        pos += 4

            elif self.pmt_pid is not None and pid == self.pmt_pid:

                section = self._section(payload, start)

                if len(section) >= 16 and self.audio_pid is None:
                    length = ((section[1] & 0xF) << 8) | section[2]
                    info = ((section[10] & 0xF) << 8) | section[11]
                    pos, end = 12 + info, min(len(section), 3 + length - 4)
                    while pos + 5 <= end:
                        stream_type = section[pos]
                        stream_pid = ((section[pos + 1] & 0x1F) << 8) | section[pos + 2]
                        es_info = ((section[pos + 3] & 0xF) << 8) | section[pos + 4]
                        if stream_type == 0x0F:
                            self.audio_pid, self.kind = stream_pid, ".aac"
                            break
                        if stream_type in (0x03, 0x04):
                            self.audio_pid, self.kind = stream_pid, ".mp3"
                            break
                        pos += 5 + es_info

            elif self.audio_pid is not None and pid == self.audio_pid:

                if start and payload[:3] == b"\x00\x00\x01" and len(payload) >= 9:
                    payload = payload[9 + payload[8]:]

                out += payload

        return bytes(out)


def stripId3(data: bytes) -> bytes:

    while data[:3] == b"ID3" and len(data) >= 10:
        size = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        data = data[10 + size:]

    return data


def audioFromSegment(data: bytes, extractor: TsAudioExtractor, fragmented: bool) -> Tuple[bytes, str]:
    """(audio bytes to append, file extension if known) for one segment."""

    if fragmented:
        return data, ".m4a"

    if data[:1] == b"\x47":
        return extractor.feed(data), extractor.kind

    data = stripId3(data)

    if len(data) >= 2 and data[0] == 0xFF:
        if (data[1] & 0xF6) == 0xF0:
            return data, ".aac"
        if (data[1] & 0xE0) == 0xE0:
            return data, ".mp3"

    return data, ""


CONTENT_TYPES = {".aac": "audio/aac", ".mp3": "audio/mpeg", ".m4a": "audio/mp4"}


def fetch(url: str, limit: int, user_agent: str) -> bytes:

    request = urllib.request.Request(url, headers={"User-Agent": user_agent})

    with urllib.request.urlopen(request, timeout=CONNECT_TIMEOUT_SECONDS) as response:
        return response.read(limit)


def _attributes(line: str) -> Dict[str, str]:

    result: Dict[str, str] = {}

    for match in re.finditer(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)', line.split(":", 1)[-1]):
        result[match.group(1)] = match.group(2).strip('"')

    return result


def pickMedia(text: str, base_url: str) -> str:
    """For a master playlist: the URL of the media playlist to follow."""

    lines = [line.strip() for line in text.splitlines()]

    variants = []
    audio_rendition = ""

    for index, line in enumerate(lines):

        if line.startswith("#EXT-X-STREAM-INF"):

            attributes = _attributes(line)
            uri = next((c for c in lines[index + 1:] if c and not c.startswith("#")), "")

            if uri:
                try:
                    bandwidth = int(attributes.get("BANDWIDTH", "0"))
                except ValueError:
                    bandwidth = 0
                codecs = attributes.get("CODECS", "")
                video = "RESOLUTION" in attributes or any(c in codecs for c in ("avc1", "hvc1", "hev1"))
                variants.append((video, bandwidth, urljoin(base_url, uri)))

        elif line.startswith("#EXT-X-MEDIA") and not audio_rendition:

            attributes = _attributes(line)

            if attributes.get("TYPE") == "AUDIO" and attributes.get("URI"):
                audio_rendition = urljoin(base_url, attributes["URI"])

    if not variants:
        return base_url

    audio_only = [v for v in variants if not v[0]]

    if audio_only:
        return max(audio_only, key=lambda v: v[1])[2]

    if audio_rendition:
        return audio_rendition

    return min(variants, key=lambda v: v[1])[2]


def parseMedia(text: str, base_url: str) -> Dict[str, Any]:

    sequence = 0
    target = 6.0
    endlist = False
    encrypted = False
    init_uri = ""
    segments = []
    duration = 0.0
    pending = False

    for raw in text.splitlines():

        line = raw.strip()

        if not line:
            continue

        if line.startswith("#EXT-X-MEDIA-SEQUENCE:"):
            try:
                sequence = int(line.split(":", 1)[1])
            except ValueError:
                sequence = 0
        elif line.startswith("#EXT-X-TARGETDURATION:"):
            try:
                target = float(line.split(":", 1)[1])
            except ValueError:
                pass
        elif line.startswith("#EXT-X-ENDLIST"):
            endlist = True
        elif line.startswith("#EXT-X-KEY") and "METHOD=NONE" not in line:
            encrypted = True
        elif line.startswith("#EXT-X-MAP"):
            match = re.search(r'URI="([^"]+)"', line)
            if match:
                init_uri = urljoin(base_url, match.group(1))
        elif line.startswith("#EXTINF"):
            pending = True
            try:
                duration = float(line.split(":", 1)[1].split(",", 1)[0])
            except ValueError:
                duration = target
        elif not line.startswith("#") and pending:
            segments.append((sequence + len(segments), urljoin(base_url, line), duration))
            pending = False

    return {"target": target, "endlist": endlist, "encrypted": encrypted, "init": init_uri, "segments": segments}


def follow(
    url: str,
    text: str,
    stop: Any,
    write: Callable[[bytes, float], None],
    user_agent: str,
    on_kind: Optional[Callable[[str, float], None]] = None,
    check: Optional[Callable[[], str]] = None,
) -> Tuple[str, str]:
    """
    Follow the HLS playlist until `stop` (a threading.Event) is set, the
    playlist ends or an error occurs. `write(chunk, duration)` receives
    the audio of each segment; `on_kind(extension, target_duration)` is
    called once the format is known and again when the target changes.
    `check()` may return an error code to abort. Returns
    (extension, error code or '').
    """

    media_url = url

    try:

        if "#EXT-X-STREAM-INF" in text:

            media_url = pickMedia(text, url)

            text = fetch(media_url, 1024 * 1024, user_agent).decode("utf-8", "replace")

    except (urllib.error.URLError, OSError, ValueError):

        return "", "connection_lost"

    extension = ""
    announced = False
    extractor = TsAudioExtractor()
    last_sequence = None
    first = True
    failures = 0

    while not stop.is_set():

        parsed = parseMedia(text, media_url)

        if parsed["encrypted"]:
            return extension, "hls_encrypted"

        segments = parsed["segments"]

        if first:

            if parsed["init"]:

                try:
                    write(fetch(parsed["init"], 4 * 1024 * 1024, user_agent), 0.0)
                    extension = ".m4a"
                except (urllib.error.URLError, OSError, ValueError):
                    return extension, "connection_lost"

            segments = segments[-2:]

        else:

            if segments and last_sequence is not None and segments[-1][0] < last_sequence:
                last_sequence = segments[0][0] - 1

            segments = [s for s in segments if last_sequence is None or s[0] > last_sequence]

        fetched_any = False

        for sequence, segment_url, duration in segments:

            if stop.is_set():
                break

            data = None

            for _attempt in range(2):
                try:
                    data = fetch(segment_url, 32 * 1024 * 1024, user_agent)
                    break
                except (urllib.error.URLError, OSError, ValueError):
                    stop.wait(1.0)

            last_sequence = sequence

            if data is None:
                failures += 1
                continue

            failures = 0
            fetched_any = True

            chunk, kind = audioFromSegment(data, extractor, bool(parsed["init"]))

            if not extension and kind:
                extension = kind

            if not chunk:
                continue

            if on_kind is not None and extension and not announced:
                announced = True
                on_kind(extension, parsed["target"])

            try:
                write(chunk, duration or parsed["target"])
            except OSError as error:
                return extension, "no_space" if getattr(error, "errno", None) in (28, 30) else "write_failed"

            if check is not None:
                problem = check()
                if problem:
                    return extension, problem

        first = False

        if parsed["endlist"]:
            return extension, ""

        if failures > MAX_FAILURES:
            return extension, "connection_lost"

        if stop.wait(max(1.0, min(parsed["target"], 10.0) / 2)):
            break

        try:
            text = fetch(media_url, 1024 * 1024, user_agent).decode("utf-8", "replace")
            if fetched_any:
                failures = 0
        except (urllib.error.URLError, OSError, ValueError):
            failures += 1
            if failures > MAX_FAILURES:
                return extension, "connection_lost"
            stop.wait(RECONNECT_DELAY_SECONDS)

    return extension, ""

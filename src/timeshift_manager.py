# -*- coding: utf-8 -*-
"""
Radio timeshift (Round 244, version 1.3.006).

While an Internet Radio station plays, the stream is copied into a
segmented ring buffer on disk (a hidden ".timeshift" folder inside the
recording folder). The player itself is pointed at a tiny HTTP relay on
127.0.0.1 that serves the buffer from any byte offset, so "pause",
"rewind" and "jump to live" are only a matter of restarting the service
at another offset. Icy titles are stripped from the stored audio and
re-inserted by the relay according to the playhead, so the station /
song title shown by the player stays in sync with what is heard.

Time axis: "stream time" is seconds since the session started
(monotonic). The live edge is now_t(); the playhead is tracked by wall
clock bookkeeping (playheadT()), never by asking the player.
delay = now_t() - playheadT().
"""

import bisect
import os
import shutil
import threading
import time
import urllib.error
import uuid
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

try:
    from .project import PROJECT_NAME, VERSION
except Exception:  # pragma: no cover - tests
    PROJECT_NAME, VERSION = "MediaPlayer3", "0"

try:
    from .logger import logger
except Exception:  # pragma: no cover - tests
    logger = None

try:
    from . import hls_support
except Exception:  # pragma: no cover - tests
    hls_support = None

USER_AGENT = f"{PROJECT_NAME}/{VERSION} (Enigma2 timeshift)"

CONNECT_TIMEOUT_SECONDS = 15
CHUNK_SIZE = 16 * 1024
SEGMENT_BYTES = 4 * 1024 * 1024
MAX_RECONNECTS = 8
RECONNECT_DELAY_SECONDS = 2.0
MIN_FREE_BYTES_TO_START = 100 * 1024 * 1024
MIN_FREE_BYTES_TO_CONTINUE = 20 * 1024 * 1024
DEFAULT_BYTES_PER_SECOND = 40000
ICY_INTERVAL = 16000
READY_TIMEOUT_SECONDS = 25
LIVE_MARGIN_SECONDS = 3.0
FOLDER_NAME = ".timeshift"

STATE_CONNECTING = "connecting"
STATE_OK = "ok"
STATE_FAILED = "failed"


def _log(message: str) -> None:

    if logger is not None:
        try:
            logger.verbose("[Timeshift] %s", message)
        except Exception:
            pass


def _unsupportedReason(content_type: str, first_bytes: bytes) -> str:

    head = first_bytes[:16].lstrip()

    if head.startswith(b"#EXT") or "mpegurl" in content_type:
        return "hls"

    if content_type in ("audio/x-scpls", "application/pls+xml") or head.startswith(b"[playlist]"):
        return "playlist"

    if content_type.startswith("text/") or head.lower().startswith((b"<!doc", b"<html")):
        return "not_audio"

    return ""


def _freeBytes(path: str) -> int:

    try:
        return shutil.disk_usage(path).free
    except Exception:
        return 0


HEADER_MAX_BYTES = 1024 * 1024


def _detectHeader(buf: bytes) -> Optional[bytes]:
    """
    Stream header that must precede data played from the middle of a
    stream: FLAC metadata blocks or Ogg header pages. Returns b'' when
    none is needed and None while more bytes are needed.
    """

    if buf[:4] == b"fLaC":

        pos = 4

        while True:

            if len(buf) < pos + 4:
                return None

            flags = buf[pos]
            pos += 4 + int.from_bytes(buf[pos + 1:pos + 4], "big")

            if flags & 0x80:
                return buf[:pos] if len(buf) >= pos else None

    if buf[:4] == b"OggS":

        pos = 0

        while True:

            if len(buf) < pos + 27:
                return None

            if buf[pos:pos + 4] != b"OggS":
                return buf[:pos]

            segments = buf[pos + 26]

            if len(buf) < pos + 27 + segments:
                return None

            size = 27 + segments + sum(buf[pos + 27:pos + 27 + segments])

            if len(buf) < pos + size:
                return None

            if int.from_bytes(buf[pos + 6:pos + 14], "little", signed=True) > 0:
                return buf[:pos]

            pos += size

    if len(buf) < 4:
        return None

    return b""


def _syncOgg(data: bytes) -> Tuple[bytes, bytes]:
    """Drop bytes before the first complete-packet Ogg page; returns (data, carry)."""

    start = 0

    while True:

        index = data.find(b"OggS", start)

        if index < 0:
            return b"", data[-3:]

        if len(data) < index + 6:
            return b"", data[index:]

        if data[index + 5] & 1:
            start = index + 4
            continue

        return data[index:], b""


class _Handler(BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.0"

    def log_message(self, *args: Any) -> None:  # silence
        pass

    def do_GET(self) -> None:

        session: "TimeshiftSession" = self.server.session  # type: ignore[attr-defined]

        try:
            session._serve(self)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError):
            pass
        except OSError:
            pass
        except Exception as error:
            _log(f"relay handler error: {error}")


class TimeshiftSession:
    """One buffered radio stream plus its local relay."""

    def __init__(self, url: str, folder: str, max_seconds: int) -> None:

        self.url = url
        self.max_seconds = max(60, int(max_seconds))
        self.state = STATE_CONNECTING
        self.fail_reason = ""
        self.content_type = "audio/mpeg"
        self.live_margin = LIVE_MARGIN_SECONDS
        self.is_hls = False

        self._root = folder
        self._dir = ""

        self._cond = threading.Condition()
        self._stop = threading.Event()

        self._end = 0  # logical end offset (bytes written)
        self._start = 0  # logical offset of oldest retained byte
        self._index_t: List[float] = []
        self._index_o: List[int] = []
        self._last_index_t = -1.0
        self._title_o: List[int] = []
        self._titles: List[str] = []
        self._first_title_o: Optional[int] = None

        self._pins: Dict[int, int] = {}
        self._pin_counter = 0
        self._rec_tokens: Dict[str, int] = {}
        self._token_counter = 0

        self._t0 = time.monotonic()
        self._first_data_t: Optional[float] = None

        # Playhead bookkeeping
        self._ref_t = 0.0
        self._ref_wall = time.monotonic()
        self._paused = False

        self._seg_handle = None
        self._seg_no = -1

        self._header: Optional[bytes] = None
        self._head_buf = b""

        self._metaint = 0
        self._to_meta = 0
        self._meta_len: Optional[int] = None
        self._meta_buf = b""

        self._response = None
        self._server: Optional[ThreadingHTTPServer] = None
        self.port = 0
        self._threads: List[threading.Thread] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:

        try:
            self._dir = os.path.join(self._root, FOLDER_NAME, "s%s" % uuid.uuid4().hex[:10])
            os.makedirs(self._dir, exist_ok=True)

            if _freeBytes(self._dir) < MIN_FREE_BYTES_TO_START:
                _log("not enough free space for timeshift")
                self._cleanupDir()
                return False

            self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
            self._server.daemon_threads = True
            self._server.session = self  # type: ignore[attr-defined]
            self.port = self._server.server_address[1]
        except Exception as error:
            _log(f"start failed: {error}")
            self._cleanupDir()
            return False

        for target, name in ((self._server.serve_forever, "relay"), (self._capture, "capture")):
            thread = threading.Thread(target=target, name="MP3Timeshift-" + name, daemon=True)
            thread.start()
            self._threads.append(thread)

        self._t0 = time.monotonic()
        self._ref_wall = self._t0

        _log(f"started for {self.url} on port {self.port}")
        return True

    def stop(self) -> None:

        self._stop.set()

        with self._cond:
            self._cond.notify_all()

        server = self._server
        self._server = None

        if server is not None:
            def _close(srv=server):
                try:
                    srv.shutdown()
                    srv.server_close()
                except Exception:
                    pass

            threading.Thread(target=_close, daemon=True).start()

        response = self._response

        # Never block the GUI thread (closing an https response can
        # take seconds): close the connection and clean up in the
        # background.
        def _finish(threads=list(self._threads), response=response):
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
            for thread in threads:
                if thread.name.endswith("capture"):
                    thread.join(6.0)
            self._cleanupDir()

        threading.Thread(target=_finish, name="MP3Timeshift-cleanup", daemon=True).start()

        _log("stopped")

    def _cleanupDir(self) -> None:

        try:
            if self._seg_handle is not None:
                self._seg_handle.close()
        except Exception:
            pass

        self._seg_handle = None

        if self._dir:
            shutil.rmtree(self._dir, ignore_errors=True)

            parent = os.path.dirname(self._dir)
            try:
                os.rmdir(parent)  # only when empty
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Time / offsets
    # ------------------------------------------------------------------

    def nowT(self) -> float:
        return time.monotonic() - self._t0

    def isUsable(self) -> bool:
        return self.state != STATE_FAILED and not self._stop.is_set()

    def bytesPerSecond(self) -> float:

        with self._cond:
            end = self._end

        elapsed = self.nowT()

        if elapsed < 10 or end <= 0:
            return float(DEFAULT_BYTES_PER_SECOND)

        return max(2000.0, end / elapsed)

    def oldestT(self) -> float:

        with self._cond:
            if self._index_t:
                return self._index_t[0]

        return 0.0

    def bufferedSeconds(self) -> float:
        """Seconds of audio available behind the live edge."""

        return max(0.0, self.nowT() - self.oldestT())

    def offsetAt(self, stream_t: float) -> int:

        with self._cond:

            if not self._index_t:
                return self._start

            position = bisect.bisect_right(self._index_t, stream_t) - 1

            if position < 0:
                return self._start

            offset = self._index_o[position]

            # Interpolate between this sample and the next one (or the
            # live edge) so a seek is accurate to well under a second.
            if position + 1 < len(self._index_t):
                span_t = self._index_t[position + 1] - self._index_t[position]
                span_o = self._index_o[position + 1] - offset
            else:
                span_t = self.nowT() - self._index_t[position]
                span_o = self._end - offset

            if span_t > 0 and span_o > 0:
                offset += int(span_o * min(1.0, (stream_t - self._index_t[position]) / span_t))

            return max(self._start, offset)

    def liveOffset(self) -> int:

        with self._cond:
            end = self._end
            start = self._start

        return max(start, end - int(self.live_margin * self.bytesPerSecond()))

    def playUrl(self, offset: Optional[int] = None) -> str:

        return "http://127.0.0.1:%d/play?offset=%d" % (self.port, self._start if offset is None else offset)

    # Playhead -----------------------------------------------------------

    def playheadT(self) -> float:

        if self._paused:
            return self._ref_t

        return min(self.nowT(), self._ref_t + (time.monotonic() - self._ref_wall))

    def delay(self) -> float:
        return max(0.0, self.nowT() - self.playheadT())

    def isPaused(self) -> bool:
        return self._paused

    def setPlayhead(self, stream_t: float) -> None:

        self._ref_t = max(0.0, min(stream_t, self.nowT()))
        self._ref_wall = time.monotonic()

    def pausePlayhead(self) -> None:

        if not self._paused:
            self._ref_t = self.playheadT()
            self._paused = True

    def resumePlayhead(self) -> None:

        if self._paused:
            self._ref_wall = time.monotonic()
            self._paused = False

    def clampTarget(self, target_t: float) -> float:
        """Clamp a requested playhead time to the buffered range."""

        low = self.oldestT()
        high = max(low, self.nowT() - self.live_margin)

        return max(low, min(target_t, high))

    def startOffsetForPlayhead(self) -> int:

        if self.delay() <= self.live_margin:
            return self.liveOffset()

        return self.offsetAt(self.playheadT())

    def exportSong(self, path: str, min_seconds: float = 28.0, max_seconds: float = 38.0, stop=None) -> bool:
        """
        Song identification sample that starts at the beginning of the
        current song (AcoustID matches best from the start): the point
        where the last Icy title change was seen. Waits (up to ~45 s) until
        `min_seconds` of the song are buffered. Without a title change
        (HLS, no Icy) the last 40 s are used.
        """

        deadline = time.monotonic() + 45

        while True:

            if self.state != STATE_OK:
                return False

            with self._cond:
                start = None
                if self._title_o and self._titles and self._titles[-1].strip():
                    candidate = self._title_o[-1]
                    if candidate != self._first_title_o and candidate >= self._start:
                        start = candidate
                end = self._end

            if start is None:
                return self.exportSample(path, 40.0)

            bps = max(1.0, self.bytesPerSecond())
            have = (end - start) / bps

            if have >= min_seconds or time.monotonic() > deadline or (stop is not None and stop.is_set()):
                break

            time.sleep(1.0)

        start = max(self._start, start - int(2 * bps))

        return self.exportSample(path, 0.0, start_offset=start, max_bytes=int(max_seconds * bps))

    def exportSample(self, path: str, seconds: float, start_offset: Optional[int] = None, max_bytes: int = 0) -> bool:
        """
        Write the last `seconds` of buffered audio into `path` as a
        stand-alone file (stream header included) -- the sample used for
        song identification. Returns False when there is nothing usable.
        """

        if self.state != STATE_OK:
            return False

        if start_offset is not None:
            offset = start_offset
        else:
            offset = self.offsetAt(max(self.oldestT(), self.nowT() - seconds))

        with self._cond:
            end = self._end

        if max_bytes > 0:
            end = min(end, offset + max_bytes)

        header = self._header or b""
        need_sync = False
        carry = b""
        written = 0

        try:
            with open(path, "wb") as handle:

                if header and offset > len(header):
                    handle.write(header)
                    need_sync = header[:4] == b"OggS"
                elif header and offset > 0:
                    offset = len(header)

                while offset < end:

                    data, new_offset = self._read(offset, 65536)

                    if not data and new_offset == offset:
                        break

                    offset = new_offset

                    if need_sync:
                        data, carry = _syncOgg(carry + data)
                        if not data:
                            continue
                        need_sync = False

                    handle.write(data)
                    written += len(data)

        except OSError as error:
            _log(f"sample export failed: {error}")
            return False

        return written > 0

    # Recording ------------------------------------------------------------

    def recordingUrl(self, from_start: bool) -> str:
        """One-shot URL that streams the buffer (from its start) or live."""

        offset = self._start if from_start else self.liveOffset()

        with self._cond:
            self._token_counter += 1
            token = "t%d" % self._token_counter
            self._rec_tokens[token] = offset

        return "http://127.0.0.1:%d/rec?token=%s" % (self.port, token)

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------

    def _capture(self) -> None:

        reconnects = 0

        while not self._stop.is_set():

            response = None
            received = False

            try:
                request = urllib.request.Request(
                    self.url, headers={"User-Agent": USER_AGENT, "Icy-MetaData": "1"}
                )
                response = urllib.request.urlopen(request, timeout=CONNECT_TIMEOUT_SECONDS)
                self._response = response

                content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                first = response.read(CHUNK_SIZE)

                reason = _unsupportedReason(content_type, first)

                if reason == "hls" and hls_support is not None:
                    self._captureHls(response, first)
                    return

                if reason:
                    self._fail(reason)
                    return

                try:
                    self._metaint = int(response.headers.get("icy-metaint") or 0)
                except ValueError:
                    self._metaint = 0

                self._to_meta = self._metaint
                self._meta_len = None
                self._meta_buf = b""

                with self._cond:
                    if self.state == STATE_CONNECTING:
                        self.content_type = content_type or "audio/mpeg"
                        self.state = STATE_OK
                        self._cond.notify_all()

                chunk = first

                while chunk and not self._stop.is_set():

                    received = True
                    self._feed(chunk)
                    chunk = response.read(CHUNK_SIZE)

            except _DiskFull:
                self._fail("no_space")
                return
            except (urllib.error.URLError, OSError, ValueError) as error:
                _log(f"capture error: {error}")
            except Exception as error:
                _log(f"capture failure: {error}")
            finally:
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        pass

            if self._stop.is_set():
                return

            if received:
                reconnects = 0

            reconnects += 1

            if reconnects > MAX_RECONNECTS:
                self._fail("connection_lost")
                return

            self._stop.wait(RECONNECT_DELAY_SECONDS)

        return

    def _captureHls(self, response: Any, first: bytes) -> None:
        """Fill the buffer from an HLS playlist (see hls_support.py)."""

        text = (first + response.read(1024 * 1024)).decode("utf-8", "replace")

        if "#EXT-X-" not in text:
            self._fail("playlist")
            return

        url = response.geturl()

        try:
            response.close()
        except Exception:
            pass

        def on_kind(extension: str, target: float) -> None:
            with self._cond:
                self.is_hls = True
                self.content_type = hls_support.CONTENT_TYPES.get(extension, "audio/aac")
                # Playing from the start of the newest segment keeps the
                # player fed until the next segment is published.
                self.live_margin = max(LIVE_MARGIN_SECONDS, float(target) + 1.0)
                if self.state == STATE_CONNECTING:
                    self.state = STATE_OK
                    self._cond.notify_all()

        def write(chunk: bytes, duration: float) -> None:
            self._writeSegment(chunk, duration)

        def check() -> str:
            return "no_space" if _freeBytes(self._dir) < MIN_FREE_BYTES_TO_CONTINUE else ""

        try:
            _extension, error = hls_support.follow(
                url, text, self._stop, write, USER_AGENT, on_kind=on_kind, check=check
            )
        except _DiskFull:
            error = "no_space"
        except Exception as exception:
            _log(f"hls capture failure: {exception}")
            error = "connection_lost"

        if self._stop.is_set():
            return

        self._fail(error or "connection_lost")

    def _writeSegment(self, chunk: bytes, duration: float) -> None:
        """Store one HLS segment, indexing it across the time it covers."""

        start_offset = self._end
        arrival = self.nowT()

        self._write(chunk, index=False)

        length = len(chunk)
        span = max(1.0, float(duration))
        begin = max(arrival - span, self._last_index_t + 0.05, 0.0)

        steps = max(1, int(round(arrival - begin)))

        with self._cond:
            for k in range(steps):
                moment = begin + (arrival - begin) * k / steps
                if moment <= self._last_index_t:
                    continue
                self._index_t.append(moment)
                self._index_o.append(start_offset + length * k // steps)
                self._last_index_t = moment
            self._cond.notify_all()

    def _fail(self, reason: str) -> None:

        _log(f"failed: {reason}")

        with self._cond:
            self.fail_reason = reason
            self.state = STATE_FAILED
            self._cond.notify_all()

    # Icy stripping --------------------------------------------------------

    def _feed(self, data: bytes) -> None:

        if not self._metaint:
            self._write(data)
            return

        view = data

        while view:

            if self._to_meta > 0:
                part = view[: self._to_meta]
                self._write(part)
                self._to_meta -= len(part)
                view = view[len(part):]
                continue

            if self._meta_len is None:
                self._meta_len = view[0] * 16
                view = view[1:]
                self._meta_buf = b""

            need = self._meta_len - len(self._meta_buf)
            self._meta_buf += view[:need]
            view = view[need:]

            if len(self._meta_buf) >= self._meta_len:
                self._handleMeta(self._meta_buf)
                self._meta_len = None
                self._meta_buf = b""
                self._to_meta = self._metaint

    def _handleMeta(self, block: bytes) -> None:

        text = block.rstrip(b"\0")

        if not text:
            return

        try:
            decoded = text.decode("utf-8")
        except UnicodeDecodeError:
            decoded = text.decode("latin-1", "replace")

        marker = "StreamTitle='"
        position = decoded.find(marker)

        if position < 0:
            return

        title = decoded[position + len(marker):]
        stop = title.find("';")
        title = title[:stop] if stop >= 0 else title.rstrip("';")

        with self._cond:
            if not self._titles or self._titles[-1] != title:
                if self._first_title_o is None:
                    self._first_title_o = self._end
                self._title_o.append(self._end)
                self._titles.append(title)

    # Disk ring --------------------------------------------------------------

    def _segPath(self, number: int) -> str:
        return os.path.join(self._dir, "%08d.seg" % number)

    def _write(self, data: bytes, index: bool = True) -> None:

        if self._header is None:

            self._head_buf += bytes(data)

            found = _detectHeader(self._head_buf)

            if found is None and len(self._head_buf) > HEADER_MAX_BYTES:
                found = b""

            if found is not None:
                self._header = found
                self._head_buf = b""

        view = memoryview(data)

        while len(view):

            number = self._end // SEGMENT_BYTES
            room = SEGMENT_BYTES - (self._end % SEGMENT_BYTES)
            part = view[:room]

            try:
                if number != self._seg_no:
                    if self._seg_handle is not None:
                        self._seg_handle.close()
                    if _freeBytes(self._dir) < MIN_FREE_BYTES_TO_CONTINUE:
                        raise _DiskFull()
                    self._seg_handle = open(self._segPath(number), "wb")
                    self._seg_no = number

                self._seg_handle.write(part)
                self._seg_handle.flush()
            except OSError as error:
                if getattr(error, "errno", None) in (28, 30, 122):
                    raise _DiskFull()
                raise

            now = self.nowT()

            with self._cond:
                self._end += len(part)

                if index and now - self._last_index_t >= 1.0:
                    self._index_t.append(now)
                    self._index_o.append(self._end - len(part))
                    self._last_index_t = now

                self._cond.notify_all()

            view = view[len(part):]

            if self._end % SEGMENT_BYTES == 0:
                self._trim()

    def _trim(self) -> None:

        rate = self.bytesPerSecond()
        keep = max(int(self.max_seconds * rate), 2 * SEGMENT_BYTES)

        with self._cond:
            pin_floor = min(self._pins.values()) if self._pins else self._end
            floor_seg = min(pin_floor, self._end) // SEGMENT_BYTES
            first = self._start // SEGMENT_BYTES
            removed = []

            while first < floor_seg and (self._end - first * SEGMENT_BYTES) > keep + SEGMENT_BYTES:
                removed.append(first)
                first += 1

            if not removed:
                return

            self._start = first * SEGMENT_BYTES

            cut = bisect.bisect_left(self._index_o, self._start)
            del self._index_t[:cut]
            del self._index_o[:cut]

            cut = bisect.bisect_right(self._title_o, self._start) - 1
            if cut > 0:
                del self._title_o[:cut]
                del self._titles[:cut]

        for number in removed:
            try:
                os.remove(self._segPath(number))
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Relay
    # ------------------------------------------------------------------

    def _waitReady(self) -> bool:

        deadline = time.monotonic() + READY_TIMEOUT_SECONDS

        with self._cond:
            while self.state == STATE_CONNECTING and not self._stop.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._cond.wait(min(1.0, remaining))

            return self.state == STATE_OK

    def _read(self, offset: int, size: int) -> Tuple[bytes, int]:
        """Block until data at `offset` exists; returns (data, new offset)."""

        with self._cond:

            while True:
                if self._stop.is_set() or self.state == STATE_FAILED:
                    return b"", offset

                if offset < self._start:
                    offset = self._start

                if offset < self._end:
                    break

                self._cond.wait(1.0)

            available = self._end - offset

        number = offset // SEGMENT_BYTES
        position = offset % SEGMENT_BYTES
        wanted = min(size, SEGMENT_BYTES - position, available)

        try:
            with open(self._segPath(number), "rb") as handle:
                handle.seek(position)
                data = handle.read(wanted)
        except OSError:
            time.sleep(0.2)
            return b"", offset

        return data, offset + len(data)

    def _titleAt(self, offset: int) -> str:

        with self._cond:
            position = bisect.bisect_right(self._title_o, offset) - 1
            return self._titles[position] if position >= 0 else ""

    def _serve(self, handler: BaseHTTPRequestHandler) -> None:

        parsed = urlparse(handler.path)
        query = parse_qs(parsed.query)

        is_rec = parsed.path == "/rec"

        if parsed.path not in ("/play", "/rec"):
            handler.send_error(404)
            return

        if not self._waitReady():
            if is_rec:
                handler.send_error(404)
            else:
                handler.send_response(302)
                handler.send_header("Location", self.url)
                handler.end_headers()
            return

        if is_rec:
            token = (query.get("token") or [""])[0]
            with self._cond:
                if token not in self._rec_tokens:
                    gone = True
                    offset = 0
                else:
                    gone = False
                    offset = self._rec_tokens.pop(token)
            if gone:
                handler.send_error(410)
                return
            with self._cond:
                self._pin_counter += 1
                pin_id = self._pin_counter
                self._pins[pin_id] = offset
        else:
            try:
                offset = int((query.get("offset") or ["0"])[0])
            except ValueError:
                offset = 0
            pin_id = 0

        want_icy = (not is_rec) and handler.headers.get("Icy-MetaData") == "1"

        try:
            handler.connection.settimeout(120)
        except Exception:
            pass

        handler.send_response(200)
        handler.send_header("Content-Type", self.content_type)
        handler.send_header("Cache-Control", "no-cache")
        if want_icy:
            handler.send_header("icy-metaint", str(ICY_INTERVAL))
        handler.end_headers()

        to_meta = ICY_INTERVAL
        last_title: Optional[str] = None

        # Playing from the middle of a FLAC / Ogg stream needs the stream
        # header first, and Ogg must start at a page boundary.
        prefix = b""
        need_sync = False
        carry = b""
        header = self._header or b""

        if header and offset > 0:

            offset = max(offset, self._start)

            if offset > len(header):
                prefix = header
                need_sync = header[:4] == b"OggS"
            elif offset < len(header):
                offset = len(header)

        try:
            while not self._stop.is_set():

                data, offset = self._read(offset, CHUNK_SIZE)

                if not data:
                    if self.state == STATE_FAILED or self._stop.is_set():
                        break
                    continue

                if need_sync:
                    data, carry = _syncOgg(carry + data)
                    if not data:
                        continue
                    need_sync = False

                if prefix:
                    data = prefix + data
                    prefix = b""

                if pin_id:
                    with self._cond:
                        self._pins[pin_id] = offset

                if not want_icy:
                    handler.wfile.write(data)
                    continue

                view = data
                base = offset - len(data)

                while view:
                    if to_meta == 0:
                        title = self._titleAt(base)
                        if title != last_title and title:
                            payload = ("StreamTitle='%s';" % title.replace("'", "’")).encode("utf-8")[:4080]
                            padded = payload + b"\0" * (-len(payload) % 16)
                            handler.wfile.write(bytes([len(padded) // 16]) + padded)
                            last_title = title
                        else:
                            handler.wfile.write(b"\0")
                        to_meta = ICY_INTERVAL
                    part = view[:to_meta]
                    handler.wfile.write(part)
                    to_meta -= len(part)
                    base += len(part)
                    view = view[len(part):]
        finally:
            if pin_id:
                with self._cond:
                    self._pins.pop(pin_id, None)


class _DiskFull(Exception):
    pass


def timeshiftFolder(recording_folder: Optional[str]) -> Optional[str]:
    """Folder that may hold the buffer, or None when timeshift cannot run."""

    if not recording_folder:
        return None

    try:
        os.makedirs(recording_folder, exist_ok=True)
        return recording_folder if os.access(recording_folder, os.W_OK) else None
    except OSError:
        return None


def purgeStaleBuffers(recording_folder: Optional[str]) -> None:
    """Remove buffers left behind by a crashed earlier run."""

    if not recording_folder:
        return

    shutil.rmtree(os.path.join(recording_folder, FOLDER_NAME), ignore_errors=True)

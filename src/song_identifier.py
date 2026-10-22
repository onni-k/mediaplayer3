# -*- coding: utf-8 -*-
"""
Song identification (Round 255/256, versions 1.3.017-1.3.023) -- modelled on
pyacoustid: an audio sample is fingerprinted with Chromaprint and looked up
from the AcoustID web service. Unlike pyacoustid this module has no
third-party Python dependencies (urllib + subprocess only).

Fingerprinting (1.3.018): receivers do not ship `fpcalc`, so the plugin
bundles `fpraw` (src/bin/fpraw-<arch>, static Chromaprint build that reads
raw 11025 Hz mono PCM from stdin). The PCM comes from a decoder found on
the receiver: gst-launch-1.0 first, otherwise ffmpeg. A real `fpcalc`
(configured path / PATH) is still preferred when it exists.

AcoustID wants the length of the WHOLE track as `duration`: known for files,
guessed (typical song lengths) for radio, where several sample windows
(different start offsets) are tried as well (1.3.023).

The work runs in a background thread; the result is collected by
MainScreen with popResult().
"""

import base64
import json
import os
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from .logger import logger
from .project import PROJECT_NAME, VERSION

API_URL = "https://api.acoustid.org/v2/lookup"
USER_AGENT = f"{PROJECT_NAME}/{VERSION} (Enigma2 song identification)"
SAMPLE_SECONDS = 40
FILE_SAMPLE_SECONDS = 60
MIN_SCORE = 0.5
FPCALC_TIMEOUT = 60
PCM_RATE = 11025

# Typical song lengths (s), tried one by one when the track length is unknown (radio).
GUESS_DURATIONS = (210, 180, 240, 195, 225, 255, 168, 270, 150, 300, 135, 330, 120, 360, 420)

# Radio: (skip seconds from sample start, fingerprint length). 1.3.023 device log:
# every match came from the first window and 23-41 s were equally good (same score),
# while the shifted windows never matched, so only one window is used (1.3.024).
RADIO_WINDOWS = ((0, 38),)
MIN_WINDOW_SECONDS = 12

# Bundled default AcoustID application key (obfuscated, like the other
# bundled keys; a key in Settings always takes priority).
_OBFUSCATION_PAD = b"MediaPlayer3-AcoustID-Build0010"
_DEFAULT_KEY_OBFUSCATED = "IA8vHhERHVQRKQ=="


def _deobfuscate(value: str) -> str:
    xored = base64.b64decode(value)
    return bytes(b ^ _OBFUSCATION_PAD[i % len(_OBFUSCATION_PAD)] for i, b in enumerate(xored)).decode("utf-8")


def resolveKey(configured: str = "") -> str:
    """User's own key when set, otherwise the bundled default."""

    configured = (configured or "").strip()

    if configured:
        return configured

    try:
        return _deobfuscate(_DEFAULT_KEY_OBFUSCATED)
    except Exception:
        return ""


# Result / error codes (MainScreen maps them to messages)
OK = "ok"
NOT_FOUND = "not_found"
NO_KEY = "no_key"
NO_FPCALC = "no_fpcalc"  # no way to fingerprint at all (kept for the old name)
NO_DECODER = "no_decoder"
NO_TOOL = "no_tool"
NO_SAMPLE = "no_sample"
NETWORK = "network"
BUSY = "busy"
FAILED = "failed"

_SEARCH_DIRS = ("/usr/bin", "/usr/local/bin", "/bin", "/opt/bin", "/usr/sbin")


def _log(message: str) -> None:
    try:
        logger.verbose("[SongID] %s", message)
    except Exception:
        pass


def findFpcalc(configured: str = "") -> Optional[str]:
    """Path of the fpcalc tool (configured path, $FPCALC, PATH, usual folders)."""

    candidates = [configured, os.environ.get("FPCALC", "")]

    found = shutil.which("fpcalc")

    if found:
        candidates.append(found)

    candidates += [os.path.join(folder, "fpcalc") for folder in _SEARCH_DIRS]

    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "fpcalc"))

    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None


def _parseFpOutput(text: str) -> Optional[Dict[str, Any]]:
    duration = None
    fingerprint = ""
    for line in text.splitlines():
        if line.startswith("DURATION="):
            try:
                duration = int(float(line.split("=", 1)[1]))
            except ValueError:
                pass
        elif line.startswith("FINGERPRINT="):
            fingerprint = line.split("=", 1)[1].strip()
    if not fingerprint or not duration:
        return None
    return {"duration": duration, "fingerprint": fingerprint}


def fingerprintFile(fpcalc: str, path: str, length: int) -> Optional[Dict[str, Any]]:
    """{"duration", "fingerprint"} of an audio file made with a real fpcalc, or None."""

    try:
        completed = subprocess.run(
            [fpcalc, "-length", str(length), path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=FPCALC_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as error:
        _log(f"fpcalc failed to run: {error}")
        return None

    if completed.returncode != 0:
        _log(f"fpcalc exit {completed.returncode}: {completed.stderr[-200:]!r}")
        return None

    return _parseFpOutput(completed.stdout.decode("utf-8", "replace"))


_ELF_MACHINES = {8: "mipsel", 40: "arm", 183: "aarch64", 62: "x86"}

_working_fpraw: Optional[str] = None


def detectArch() -> str:
    """CPU family from the ELF header of the Python executable ('' if unknown)."""

    import sys

    for candidate in (os.path.realpath(sys.executable or ""), "/bin/sh", "/bin/busybox"):
        try:
            with open(candidate, "rb") as handle:
                head = handle.read(20)
        except OSError:
            continue
        if len(head) < 20 or head[:4] != b"\x7fELF":
            continue
        little = head[5] == 1
        machine = struct.unpack("<H" if little else ">H", head[18:20])[0]
        arch = _ELF_MACHINES.get(machine, "")
        if arch == "mipsel" and not little:
            return "mips"  # big-endian MIPS: no bundled build
        if arch:
            return arch
    return ""


def _unpack(gz_path: str, name: str) -> Optional[str]:
    """
    The tools are shipped gzip-compressed (`bin/fpraw-<cpu>.gz`) so that the
    package contains no architecture-specific files (Yocto's allarch QA
    check). Unpack once into the plugin folder, or a temp folder when that
    is read-only, and return the executable.
    """

    import gzip

    folder = os.path.dirname(gz_path)

    for target_dir in (folder, "/var/volatile/tmp", "/tmp", tempfile.gettempdir()):

        target = os.path.join(target_dir, name)

        try:
            if not os.path.isfile(target) or os.path.getmtime(target) < os.path.getmtime(gz_path):
                partial = target + ".part"
                with gzip.open(gz_path, "rb") as source, open(partial, "wb") as handle:
                    shutil.copyfileobj(source, handle)
                os.chmod(partial, 0o755)
                os.replace(partial, target)
            os.chmod(target, 0o755)
            return target
        except OSError as error:
            _log(f"cannot unpack {name} to {target_dir}: {error}")

    return None


def findFpraw() -> Optional[str]:
    """Path of a bundled fpraw build that actually runs on this receiver."""

    global _working_fpraw

    if _working_fpraw and os.path.isfile(_working_fpraw):
        return _working_fpraw

    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
    arch = detectArch()

    order = [arch] if arch else []
    order += [a for a in ("arm", "mipsel", "aarch64", "x86") if a not in order]

    for name in order:

        path = os.path.join(folder, f"fpraw-{name}")

        if os.path.isfile(path + ".gz"):
            unpacked = _unpack(path + ".gz", f"fpraw-{name}")
            if not unpacked:
                continue
            path = unpacked
        elif not os.path.isfile(path):
            continue

        try:
            os.chmod(path, 0o755)
        except OSError:
            pass
        try:
            completed = subprocess.run([path, "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        except (OSError, subprocess.SubprocessError) as error:
            _log(f"fpraw-{name} cannot run: {error}")
            continue
        if completed.returncode == 0 and completed.stdout.strip():
            _log(f"using fpraw-{name} (Chromaprint {completed.stdout.decode('ascii', 'replace').strip()}, cpu {arch or '?'})")
            _working_fpraw = path
            return path
        _log(f"fpraw-{name} exit {completed.returncode}")

    _log(f"no bundled fpraw runs here (cpu {arch or 'unknown'})")
    return None


def findDecoder() -> Optional[str]:
    """'gst' or 'ffmpeg' (whichever exists), else None."""

    if shutil.which("gst-launch-1.0"):
        return "gst"
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    return None


def _decoderCommand(decoder: str, path: str, length: int) -> list:
    if decoder == "ffmpeg":
        # WAV output: some receiver ffmpeg builds have no raw s16le muxer
        return [
            shutil.which("ffmpeg") or "ffmpeg", "-v", "error", "-nostdin", "-i", path, "-t", str(length),
            "-vn", "-ac", "1", "-ar", str(PCM_RATE), "-c:a", "pcm_s16le", "-f", "wav", "-",
        ]
    return [
        shutil.which("gst-launch-1.0") or "gst-launch-1.0", "-q", "filesrc", f"location={path}", "!", "decodebin",
        "!", "audioconvert", "!", "audioresample", "!",
        f"audio/x-raw,format=S16LE,channels=1,rate={PCM_RATE}", "!", "fdsink", "fd=1",
    ]


def fingerprintViaDecoder(fpraw: str, decoder: str, path: str, length: int, skip: int = 0) -> Optional[Dict[str, Any]]:
    """Decode `path` to raw PCM with `decoder`, drop the first `skip` seconds and fingerprint `length` s with fpraw."""

    command = _decoderCommand(decoder, path, length + skip)

    try:
        size = os.path.getsize(path)
    except OSError:
        size = -1

    _log(f"decoder {decoder}: {command[0]} on {size} bytes (skip {skip} s, length {length} s)")

    wanted = (length + skip + 2) * PCM_RATE * 2
    err_file = tempfile.TemporaryFile()

    try:
        dec = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=err_file)
    except OSError as error:
        _log(f"decoder failed to start: {error}")
        err_file.close()
        return None

    pcm = bytearray()
    deadline = time.monotonic() + FPCALC_TIMEOUT

    try:
        while len(pcm) < wanted and time.monotonic() < deadline:
            chunk = dec.stdout.read(min(65536, wanted - len(pcm)))
            if not chunk:
                break
            pcm += chunk
    except Exception as error:
        _log(f"decoder read failed: {error}")
    finally:
        try:
            dec.kill()
        except Exception:
            pass
        try:
            dec.wait(timeout=5)
        except Exception:
            pass
        try:
            dec.stdout.close()
        except Exception:
            pass

    try:
        err_file.seek(0)
        err_text = err_file.read()[-400:].decode("utf-8", "replace").strip()
    except Exception:
        err_text = ""
    err_file.close()

    _log(f"decoder {decoder} gave {len(pcm)} bytes of PCM (exit {dec.returncode})" + (f"; stderr: {err_text!r}" if err_text else ""))

    if decoder == "ffmpeg":
        # drop the WAV header
        index = bytes(pcm[:512]).find(b"data")
        pcm = pcm[index + 8:] if index >= 0 else bytearray()

    if skip > 0:
        pcm = pcm[skip * PCM_RATE * 2:]

    if len(pcm) < PCM_RATE * 2 * 3:
        return None

    try:
        completed = subprocess.run(
            [fpraw, "-r", str(PCM_RATE), "-c", "1", "-l", str(length)],
            input=bytes(pcm),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=FPCALC_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as error:
        _log(f"fpraw failed: {error}")
        return None

    if completed.returncode != 0:
        _log(f"fpraw exit {completed.returncode}: {completed.stderr[-200:]!r}")
        return None

    result = _parseFpOutput(completed.stdout.decode("utf-8", "replace"))

    if result is not None:
        _log(f"fingerprint ok: duration {result['duration']} s, {len(result['fingerprint'])} chars, starts {result['fingerprint'][:24]}")
    else:
        _log(f"fpraw produced no fingerprint: {completed.stdout[-100:]!r} {completed.stderr[-100:]!r}")

    return result


def fingerprint(path: str, length: int, fpcalc_path: str = "", skip: int = 0) -> "tuple[Optional[Dict[str, Any]], str]":
    """(fingerprint dict or None, error code). Tries real fpcalc (skip 0 only), then bundled fpraw + decoder."""

    if skip == 0:

        fpcalc = findFpcalc(fpcalc_path)

        if fpcalc:
            result = fingerprintFile(fpcalc, path, length)
            if result:
                return result, OK

    fpraw = findFpraw()

    if not fpraw:
        return None, NO_TOOL

    decoder = findDecoder()

    if not decoder:
        return None, NO_DECODER

    result = fingerprintViaDecoder(fpraw, decoder, path, length, skip)

    if result is None:
        other = "ffmpeg" if decoder == "gst" else "gst"
        if shutil.which("ffmpeg" if other == "ffmpeg" else "gst-launch-1.0"):
            result = fingerprintViaDecoder(fpraw, other, path, length, skip)

    if result is None:
        return None, NO_SAMPLE

    return result, OK


def lookup(api_key: str, fingerprint: str, duration: int) -> Dict[str, Any]:
    """Query AcoustID; returns the best match dict or {} when nothing matches."""

    body = urllib.parse.urlencode(
        {
            "client": api_key,
            "duration": str(duration),
            "fingerprint": fingerprint,
            "meta": "recordings releasegroups",
            "format": "json",
        }
    ).encode("ascii")

    request = urllib.request.Request(
        API_URL, data=body, headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8", "replace"))

    try:
        summary = [
            (round(float(r.get("score") or 0), 2), len(r.get("recordings") or []))
            for r in (data.get("results") or [])[:5]
        ]
        _log(f"AcoustID duration {duration} status {data.get('status')}, results (score, recordings): {summary}")
    except Exception:
        pass

    if data.get("status") != "ok":
        message = (data.get("error") or {}).get("message", "error")
        raise RuntimeError(message)

    best: Dict[str, Any] = {}
    best_score = 0.0

    for result in data.get("results") or []:

        score = float(result.get("score") or 0)

        for recording in result.get("recordings") or []:

            title = recording.get("title")

            if not title or score <= best_score:
                continue

            artists = ", ".join(a.get("name", "") for a in (recording.get("artists") or []) if a.get("name"))

            groups = recording.get("releasegroups") or []

            album = ""

            for group in groups:
                if group.get("title") and (group.get("type") in (None, "Album") or not album):
                    album = group["title"]
                    if group.get("type") == "Album":
                        break

            best_score = score
            best = {
                "title": title,
                "artist": artists,
                "album": album,
                "score": score,
                "recording_id": recording.get("id", ""),
                "duration": recording.get("duration"),
            }

    if best and best_score >= MIN_SCORE:
        return best

    return {}


def captureStreamSample(url: str, path: str, seconds: int, stop: threading.Event) -> bool:
    """Record about `seconds` of a plain (non-HLS) stream into `path`."""

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Icy-MetaData": "0"})

    started = time.monotonic()

    try:
        with urllib.request.urlopen(request, timeout=15) as response, open(path, "wb") as handle:

            content_type = (response.headers.get("Content-Type") or "").lower()

            if "mpegurl" in content_type or content_type.startswith("text/"):
                return False

            while time.monotonic() - started < seconds and not stop.is_set():

                chunk = response.read(16384)

                if not chunk:
                    break

                handle.write(chunk)

    except (urllib.error.URLError, OSError, ValueError) as error:
        _log(f"stream sample failed: {error}")
        return False

    return os.path.getsize(path) > 16384


class SongIdentifier:
    """Runs one identification at a time in a background thread."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._result: Optional[Dict[str, Any]] = None
        self._stop = threading.Event()

    def isBusy(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def popResult(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            result, self._result = self._result, None
        return result

    def cancel(self) -> None:
        self._stop.set()

    def start(
        self,
        api_key: str,
        fpcalc_path: str,
        file_path: str = "",
        stream_url: str = "",
        sample_provider=None,
        track_duration: int = 0,
    ) -> str:
        """
        Start identification. Exactly one source: an existing audio file
        (`file_path`), a callable writing a sample file (`sample_provider(path, stop) -> bool`,
        used for the time shift buffer) or a stream URL to capture from.
        `track_duration` is the whole track length in seconds when known.
        Returns OK when started, otherwise an error code.
        """

        if self.isBusy():
            return BUSY

        api_key = resolveKey(api_key)

        if not api_key:
            return NO_KEY

        self._stop.clear()

        self._thread = threading.Thread(
            target=self._run,
            args=(api_key, fpcalc_path, file_path, stream_url, sample_provider, track_duration),
            name="MP3SongID",
            daemon=True,
        )

        self._thread.start()

        return OK

    def _finish(self, status: str, **extra: Any) -> None:
        with self._lock:
            self._result = {"status": status, **extra}

    def _guessLookup(self, api_key: str, fp: Dict[str, Any]) -> Dict[str, Any]:
        """Radio: the track length is unknown, so try typical lengths."""

        for guess in GUESS_DURATIONS:
            if self._stop.is_set():
                return {}
            match = lookup(api_key, fp["fingerprint"], guess)
            if match:
                return match
            time.sleep(0.4)

        return {}

    def _run(
        self,
        api_key: str,
        fpcalc_path: str,
        file_path: str,
        stream_url: str,
        sample_provider,
        track_duration: int = 0,
    ) -> None:

        temp_dir = None

        try:

            length = FILE_SAMPLE_SECONDS
            path = file_path

            if not path:

                temp_dir = tempfile.mkdtemp(prefix="mp3_songid_")
                path = os.path.join(temp_dir, "sample.bin")

                if sample_provider is not None:
                    ok = bool(sample_provider(path, self._stop))
                elif stream_url:
                    ok = captureStreamSample(stream_url, path, SAMPLE_SECONDS, self._stop)
                else:
                    ok = False

                if not ok or not os.path.isfile(path) or os.path.getsize(path) < 16384:
                    self._finish(NO_SAMPLE)
                    return

            if self._stop.is_set():
                return

            match: Dict[str, Any] = {}

            if track_duration > 0:

                # A local file: whole-track length known.
                fp, error = fingerprint(path, length, fpcalc_path)

                if fp is None:
                    self._finish(error)
                    return

                match = lookup(api_key, fp["fingerprint"], int(track_duration))

            else:

                # Radio: several windows of the sample x guessed track lengths.
                tried = 0

                for skip, window in RADIO_WINDOWS:

                    if self._stop.is_set():
                        return

                    fp, error = fingerprint(path, window, fpcalc_path, skip)

                    if fp is None:
                        if tried == 0:
                            self._finish(error)
                            return
                        break

                    if fp["duration"] < MIN_WINDOW_SECONDS:
                        break

                    tried += 1
                    _log(f"radio window skip {skip} s: {fp['duration']} s of audio")

                    match = self._guessLookup(api_key, fp)

                    if match:
                        break

            if not match:
                self._finish(NOT_FOUND)
                return

            _log(f"identified: {match.get('artist')} - {match.get('title')} ({match.get('score')})")

            self._finish(OK, match=match)

        except urllib.error.HTTPError as error:
            _log(f"lookup HTTP error {error.code}")
            self._finish(NETWORK, detail=f"HTTP {error.code}")
        except (urllib.error.URLError, OSError, ValueError) as error:
            _log(f"lookup failed: {error}")
            self._finish(NETWORK, detail=str(error))
        except RuntimeError as error:
            _log(f"AcoustID error: {error}")
            self._finish(FAILED, detail=str(error))
        except Exception as error:
            _log(f"unexpected failure: {error}")
            self._finish(FAILED, detail=str(error))
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)


song_identifier = SongIdentifier()

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
SUBMIT_URL = "https://api.acoustid.org/v2/submit"
SUBMIT_STATUS_URL = "https://api.acoustid.org/v2/submission_status"
SUBMIT_SECONDS = 120  # fingerprint length for submissions (what fpcalc uses by default)
EXISTS_SCORE = 0.9  # a lookup match at least this good means "already in the database"
USER_AGENT = f"{PROJECT_NAME}/{VERSION} (Enigma2 song identification)"
SAMPLE_SECONDS = 40
FILE_SAMPLE_SECONDS = 60
MIN_SCORE = 0.5
FPCALC_TIMEOUT = 60
PCM_RATE = 11025
PYTHON_TIMEOUT = 300  # the pure Python fingerprint on a slow receiver

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
NO_USER_KEY = "no_user_key"  # 1.5.000: submitting needs the user's own AcoustID key
NO_TAGS = "no_tags"  # nothing to describe the file with (no MusicBrainz ID, no artist+title)
NO_DURATION = "no_duration"
EXISTS = "exists"  # the fingerprint is already in the AcoustID database
SUBMITTED = "submitted"

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


def findPython() -> Optional[str]:
    """A python3 interpreter for the pure Python fingerprint (sys.executable may be the enigma2 binary)."""

    for candidate in (shutil.which("python3"), "/usr/bin/python3", "/usr/bin/python"):
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def fingerprintTools() -> list:
    """
    Fingerprint tools to try, best first: [(label, command prefix, timeout s)].
    The bundled C tool when it exists and runs (fast), then the pure Python port
    (chromaprint_py.py, run as a low-priority separate process -- 1.4.003).
    """

    tools = []

    fpraw = findFpraw()

    if fpraw:
        tools.append(("fpraw", [fpraw], FPCALC_TIMEOUT))

    python = findPython()
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromaprint_py.py")

    if python and os.path.isfile(script):
        tools.append(("python", [python, script], PYTHON_TIMEOUT))

    return tools


_system_logged = False


def _logSystem() -> None:
    """Once per run: CPU / memory / load, to put the timings in the log in context."""

    global _system_logged

    if _system_logged:
        return

    _system_logged = True

    model = ""
    cores = 0

    try:
        with open("/proc/cpuinfo") as handle:
            for line in handle:
                key = line.split(":", 1)[0].strip().lower()
                if key in ("processor",):
                    cores += 1
                if not model and key in ("model name", "hardware", "cpu model", "system type", "cpu"):
                    model = line.split(":", 1)[1].strip()
    except OSError:
        pass

    mem = ""

    try:
        with open("/proc/meminfo") as handle:
            for line in handle:
                if line.startswith(("MemTotal", "MemAvailable")):
                    mem += " " + line.split(":")[0] + "=" + line.split(":")[1].strip()
    except OSError:
        pass

    import sys

    _log(f"system: cpu '{model}' x{cores}, arch {detectArch() or '?'},{mem}, python {sys.version.split()[0]}")


def _load() -> str:
    try:
        return "%.2f" % os.getloadavg()[0]
    except (OSError, AttributeError):
        return "?"


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


def fingerprintViaDecoder(tool: tuple, decoder: str, path: str, length: int, skip: int = 0) -> Optional[Dict[str, Any]]:
    """Decode `path` to raw PCM with `decoder`, drop the first `skip` seconds and fingerprint `length` s with `tool`."""

    command = _decoderCommand(decoder, path, length + skip)

    try:
        size = os.path.getsize(path)
    except OSError:
        size = -1

    _log(f"decoder {decoder}: {command[0]} on {size} bytes (skip {skip} s, length {length} s)")

    wanted = (length + skip + 2) * PCM_RATE * 2
    err_file = tempfile.TemporaryFile()
    decode_started = time.monotonic()

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

    _log(f"decoder {decoder} gave {len(pcm)} bytes of PCM in {time.monotonic() - decode_started:.2f} s (exit {dec.returncode})" + (f"; stderr: {err_text!r}" if err_text else ""))

    if decoder == "ffmpeg":
        # drop the WAV header
        index = bytes(pcm[:512]).find(b"data")
        pcm = pcm[index + 8:] if index >= 0 else bytearray()

    if skip > 0:
        pcm = pcm[skip * PCM_RATE * 2:]

    if len(pcm) < PCM_RATE * 2 * 3:
        return None

    label, prefix, timeout = tool

    cpu_before = os.times()
    wall_before = time.monotonic()
    load_before = _load()

    try:
        completed = subprocess.run(
            prefix + ["-r", str(PCM_RATE), "-c", "1", "-l", str(length)],
            input=bytes(pcm),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as error:
        _log(f"{label} failed: {error} (after {time.monotonic() - wall_before:.1f} s)")
        return None

    cpu_after = os.times()
    child_cpu = (cpu_after.children_user + cpu_after.children_system) - (cpu_before.children_user + cpu_before.children_system)
    stats = completed.stderr.decode("utf-8", "replace").strip().splitlines()
    stats = stats[-1] if stats else ""

    _log(
        f"{label} finished: wall {time.monotonic() - wall_before:.2f} s, child cpu {child_cpu:.2f} s, "
        f"load {load_before} -> {_load()}, exit {completed.returncode}"
        + (f"; {stats[-300:]}" if stats else "")
    )

    if completed.returncode != 0:
        return None

    result = _parseFpOutput(completed.stdout.decode("utf-8", "replace"))

    if result is not None:
        _log(f"fingerprint ok ({label}): duration {result['duration']} s, {len(result['fingerprint'])} chars, starts {result['fingerprint'][:24]}")
    else:
        _log(f"{label} produced no fingerprint: {completed.stdout[-100:]!r}")

    return result


def fingerprint(path: str, length: int, fpcalc_path: str = "", skip: int = 0) -> "tuple[Optional[Dict[str, Any]], str]":
    """(fingerprint dict or None, error code). Tries real fpcalc (skip 0 only), then bundled fpraw + decoder."""

    if skip == 0:

        fpcalc = findFpcalc(fpcalc_path)

        if fpcalc:
            result = fingerprintFile(fpcalc, path, length)
            if result:
                return result, OK

    tools = fingerprintTools()

    if not tools:
        _log("no fingerprint tool available (no fpraw for this CPU and no python3)")
        return None, NO_TOOL

    decoder = findDecoder()

    if not decoder:
        return None, NO_DECODER

    _logSystem()

    for tool in tools:

        result = fingerprintViaDecoder(tool, decoder, path, length, skip)

        if result is None:
            other = "ffmpeg" if decoder == "gst" else "gst"
            if shutil.which("ffmpeg" if other == "ffmpeg" else "gst-launch-1.0"):
                result = fingerprintViaDecoder(tool, other, path, length, skip)

        if result is not None:
            return result, OK

        _log(f"{tool[0]} gave no fingerprint, trying the next tool" if tool is not tools[-1] else f"{tool[0]} gave no fingerprint")

    return None, NO_SAMPLE


def lookup(api_key: str, fingerprint: str, duration: int, info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Query AcoustID; returns the best match dict or {} when nothing matches.

    `info` (optional) receives "unlinked_score": the best score of a fingerprint match that has
    no MusicBrainz recording attached (known to AcoustID but not linked).
    """

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

        if info is not None and not (result.get("recordings") or []):
            info["unlinked_score"] = max(score, float(info.get("unlinked_score") or 0))

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
        run_started = time.monotonic()
        run_cpu = os.times()

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
            cpu_now = os.times()
            _log(
                f"identification took {time.monotonic() - run_started:.1f} s wall; "
                f"cpu in this process {cpu_now.user + cpu_now.system - run_cpu.user - run_cpu.system:.2f} s, "
                f"in child processes {cpu_now.children_user + cpu_now.children_system - run_cpu.children_user - run_cpu.children_system:.2f} s; "
                f"load {_load()}"
            )


song_identifier = SongIdentifier()

# ------------------------------------------------------------------------------
# 1.5.000: submitting fingerprints of the user's own music to AcoustID
# (https://acoustid.org/webservice#submit). Needs the application key (client)
# and the user's own key (user, from https://acoustid.org/api-key).
# ------------------------------------------------------------------------------

def _tagText(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text.lower() == "unknown" else text


def _leadingInt(value: Any) -> str:
    digits = ""
    for char in _tagText(value):
        if not char.isdigit():
            break
        digits += char
    return str(int(digits)) if digits else ""


def buildSubmitFields(path: str, tags: Dict[str, Any], duration: int, fp: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Per-track submit fields (without the .# index), or None when the file cannot be described."""

    mbid = _tagText(tags.get("_mbid"))
    artist = _tagText(tags.get("artist"))
    title = _tagText(tags.get("title"))

    if not mbid and not (artist and title):
        return None

    fields: Dict[str, str] = {"duration": str(int(duration)), "fingerprint": fp["fingerprint"]}

    if mbid:
        fields["mbid"] = mbid

    for name, value in (
        ("track", title),
        ("artist", artist),
        ("album", _tagText(tags.get("album"))),
        ("albumartist", _tagText(tags.get("album_artist"))),
        ("year", _leadingInt(tags.get("year"))),
        ("trackno", _leadingInt(tags.get("track_number"))),
        ("discno", _leadingInt(tags.get("disc_number"))),
    ):
        if value:
            fields[name] = value

    extension = os.path.splitext(path)[1].lstrip(".").upper()

    if extension:
        fields["fileformat"] = extension

    size = tags.get("file_size")

    if size and duration > 0:
        kbps = int(size * 8 / duration / 1000)
        if kbps > 0:
            fields["bitrate"] = str(kbps)

    return fields


def _postJson(url: str, params: Dict[str, str], compress: bool = True) -> Dict[str, Any]:

    import gzip

    body = urllib.parse.urlencode(params).encode("utf-8")

    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}

    if compress:
        body = gzip.compress(body)
        headers["Content-Encoding"] = "gzip"

    request = urllib.request.Request(url, data=body, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as error:
        # AcoustID reports problems (bad key, bad fingerprint) as JSON with an error message
        try:
            return json.loads(error.read().decode("utf-8", "replace"))
        except Exception:
            raise error


def submit(client_key: str, user_key: str, items: list) -> Dict[str, Any]:
    """Submit one or more tracks (list of buildSubmitFields dicts); returns the parsed JSON response."""

    params: Dict[str, str] = {"client": client_key, "user": user_key, "format": "json", "clientversion": VERSION}

    for index, fields in enumerate(items):
        for name, value in fields.items():
            params[f"{name}.{index}"] = value

    data = _postJson(SUBMIT_URL, params)

    _log(f"submit of {len(items)} track(s): status {data.get('status')}, response {json.dumps(data)[:300]}")

    if data.get("status") != "ok":
        raise RuntimeError((data.get("error") or {}).get("message", "submit error"))

    return data


def submissionStatus(client_key: str, ids: list) -> list:
    """List of (id, status) for earlier submissions ('pending' or 'imported')."""

    query = urllib.parse.urlencode([("client", client_key), ("format", "json")] + [("id", str(i)) for i in ids])

    request = urllib.request.Request(f"{SUBMIT_STATUS_URL}?{query}", headers={"User-Agent": USER_AGENT})

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8", "replace"))

    _log(f"submission_status: {json.dumps(data)[:300]}")

    return [(str(item.get("id")), str(item.get("status"))) for item in data.get("submissions") or []]


class SongSubmitter:
    """Fingerprints one local file and submits it, in a background thread."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._result: Optional[Dict[str, Any]] = None
        self._cancelled = False

    def isBusy(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def cancel(self) -> None:
        self._cancelled = True

    def popResult(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            result, self._result = self._result, None
        return result

    def start(self, client_key: str, user_key: str, file_path: str, track_duration: int, fpcalc_path: str = "", force: bool = False) -> str:

        if self.isBusy():
            return BUSY

        client_key = resolveKey(client_key)
        user_key = (user_key or "").strip()

        if not client_key:
            return NO_KEY

        if not user_key:
            return NO_USER_KEY

        self._cancelled = False

        self._thread = threading.Thread(
            target=self._run,
            args=(client_key, user_key, file_path, track_duration, fpcalc_path, force),
            name="MP3SongSubmit",
            daemon=True,
        )

        self._thread.start()

        return OK

    def _finish(self, status: str, **extra: Any) -> None:
        with self._lock:
            self._result = {"status": status, **extra}

    def _run(self, client_key: str, user_key: str, path: str, duration: int, fpcalc_path: str, force: bool) -> None:

        started = time.monotonic()

        try:

            from .metadata import metadata_reader

            tags = metadata_reader.read(path)

            duration = int(duration or tags.get("duration_seconds") or 0)

            if duration <= 0:
                self._finish(NO_DURATION)
                return

            tag_check = {"_mbid": tags.get("_mbid"), "artist": tags.get("artist"), "title": tags.get("title")}

            if not _tagText(tag_check["_mbid"]) and not (_tagText(tag_check["artist"]) and _tagText(tag_check["title"])):
                _log(f"submit: no usable tags in {os.path.basename(path)}")
                self._finish(NO_TAGS)
                return

            fp, error = fingerprint(path, SUBMIT_SECONDS, fpcalc_path)

            if fp is None:
                self._finish(error)
                return

            fields = buildSubmitFields(path, tags, duration, fp)

            if fields is None:
                self._finish(NO_TAGS)
                return

            label = f"{_tagText(tags.get('artist'))} - {_tagText(tags.get('title'))}"

            unlinked_known = False

            if not force:

                # Already in the database? Then there is nothing to add.
                info: Dict[str, Any] = {}

                match = lookup(client_key, fp["fingerprint"], duration, info)

                unlinked = float(info.get("unlinked_score") or 0) >= EXISTS_SCORE

                unlinked_known = unlinked

                if unlinked:
                    _log("submit: the fingerprint is already known to AcoustID but is NOT linked to a MusicBrainz recording")

                if self._cancelled:
                    return

                if match and match.get("score", 0) >= EXISTS_SCORE:
                    _log(f"submit: already in the database: {match.get('artist')} - {match.get('title')} ({match.get('score')})")
                    self._finish(EXISTS, match=match, label=label, mbid=fields.get("mbid", ""))
                    return

            if self._cancelled:
                return

            _log("submit: MusicBrainz recording ID " + (f"SENT ({fields['mbid']})" if fields.get("mbid") else "not in the tags -- AcoustID can only match by artist/title text"))

            data = submit(client_key, user_key, [fields])

            submissions = data.get("submissions") or []
            ids = [item.get("id") for item in submissions if item.get("id") is not None]
            state = str((submissions[0].get("status") if submissions else "") or "pending")

            # The import is asynchronous: look a couple of times whether it went through.
            for _attempt in range(3):
                if state == "imported" or not ids:
                    break
                time.sleep(3)
                try:
                    statuses = submissionStatus(client_key, ids)
                except Exception as error:
                    _log(f"submission_status failed: {error}")
                    break
                if statuses:
                    state = statuses[0][1]

            self._finish(SUBMITTED, label=label, state=state, mbid=fields.get("mbid", ""), unlinked=bool(unlinked_known))

        except urllib.error.HTTPError as error:
            _log(f"submit HTTP error {error.code}")
            self._finish(NETWORK, detail=f"HTTP {error.code}")
        except (urllib.error.URLError, OSError, ValueError) as error:
            _log(f"submit failed: {error}")
            self._finish(NETWORK, detail=str(error))
        except RuntimeError as error:
            _log(f"AcoustID error: {error}")
            self._finish(FAILED, detail=str(error))
        except Exception as error:
            _log(f"unexpected submit failure: {error}")
            self._finish(FAILED, detail=str(error))
        finally:
            _log(f"submit took {time.monotonic() - started:.1f} s wall; load {_load()}")


song_submitter = SongSubmitter()


def _providerSongId() -> str:
    if song_identifier.isBusy():
        from .localization import _
        return _("Identifying song...")
    if song_submitter.isBusy():
        from .localization import _
        return _("Submitting fingerprint...")
    return ""


try:
    from . import background_tasks as _background_tasks

    _background_tasks.registerProvider(_providerSongId)
except Exception:  # pragma: no cover
    pass

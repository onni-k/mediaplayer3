# -*- coding: utf-8 -*-
"""
Pure Python Chromaprint fingerprint (MediaPlayer3 1.4.004).

A port of the default Chromaprint algorithm (TEST2: 4096-sample frames, hop
1365, 12 chroma bands 28-3520 Hz, 5-tap chroma filter, 16 classifiers) by
Lukas Lalinsky, https://github.com/acoustid/chromaprint, used under the
MIT licence:

    Copyright (C) 2010-2016  Lukas Lalinsky

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions: The above copyright notice and this
    permission notice shall be included in all copies or substantial
    portions of the Software.  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT
    WARRANTY OF ANY KIND.

It needs no third-party modules and no compiled tool.  The input is raw
signed 16-bit little-endian mono PCM at 11025 Hz (the plugin lets
gst-launch-1.0 / ffmpeg decode and resample), so no resampling is done here.

It is run as a separate low-priority process so that it cannot stall the
Enigma2 user interface (GIL):

    python3 chromaprint_py.py -r 11025 -c 1 -l 38 < pcm.raw

which prints DURATION=<s> and FINGERPRINT=<base64> (like fpcalc) on stdout and
one "STATS ..." line (wall/CPU seconds, frames, memory) on stderr.
"""

import array
import base64
import math
import os
import sys
import time
from operator import add, itemgetter, mul, sub

FRAME_SIZE = 4096
HOP = FRAME_SIZE // 3  # 1365: frame overlap is 4096 - 4096/3
MIN_FREQ = 28
MAX_FREQ = 3520
NUM_BANDS = 12

_FILTER_COEFFICIENTS = (0.25, 0.75, 1.0, 0.75, 0.25)

# (filter type, y, height, width), (t0, t1, t2) -- Chromaprint "TEST2"
_CLASSIFIERS = (
    ((0, 4, 3, 15), (1.98215, 2.35817, 2.63523)),
    ((4, 4, 6, 15), (-1.03809, -0.651211, -0.282167)),
    ((1, 0, 4, 16), (-0.298702, 0.119262, 0.558497)),
    ((3, 8, 2, 12), (-0.105439, 0.0153946, 0.135898)),
    ((3, 4, 4, 8), (-0.142891, 0.0258736, 0.200632)),
    ((4, 0, 3, 5), (-0.826319, -0.590612, -0.368214)),
    ((1, 2, 2, 9), (-0.557409, -0.233035, 0.0534525)),
    ((2, 7, 3, 4), (-0.0646826, 0.00620476, 0.0784847)),
    ((2, 6, 2, 16), (-0.192387, -0.029699, 0.215855)),
    ((2, 1, 3, 2), (-0.0397818, -0.00568076, 0.0292026)),
    ((5, 10, 1, 15), (-0.53823, -0.369934, -0.190235)),
    ((3, 6, 2, 10), (-0.124877, 0.0296483, 0.139239)),
    ((2, 1, 1, 14), (-0.101475, 0.0225617, 0.231971)),
    ((3, 5, 6, 4), (-0.0799915, -0.00729616, 0.063262)),
    ((1, 9, 2, 12), (-0.272556, 0.019424, 0.302559)),
    ((3, 4, 2, 14), (-0.164292, -0.0321188, 0.0846339)),
)

_GRAY = (0, 1, 3, 2)

_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


# ---------------------------------------------------------------------------
# FFT
# ---------------------------------------------------------------------------

class _RealFFT:
    """
    Power spectrum of a real signal of length n (n a power of two), via an n/2
    complex FFT.  Written with map()/operator so that the per-element work runs in
    C (about 3x faster than list comprehensions on a receiver CPU).
    """

    def __init__(self, n, first_bin, last_bin):
        self.n = n
        self.m = n // 2
        m = self.m
        self.first = first_bin
        self.last = last_bin  # exclusive

        # Hamming window, scaled like Chromaprint (1 / INT16_MAX)
        self.window = [(0.54 - 0.46 * math.cos(i * 2.0 * math.pi / (n - 1))) / 32767.0 for i in range(n)]

        # bit reversal for the m-point complex FFT
        bits = m.bit_length() - 1
        self.rev = itemgetter(*[int(format(i, "0%db" % bits)[::-1], 2) for i in range(m)])

        # twiddles per stage
        self.stages = []
        size = 2
        while size <= m:
            half = size // 2
            tw = [complex(math.cos(-2 * math.pi * k / size), math.sin(-2 * math.pi * k / size)) for k in range(half)]
            self.stages.append((half, tw))
            size *= 2

        # post-processing for the bins we need:  X[k] = A[k] * Z[k] + B[k] * conj(Z[m-k])
        bins = list(range(first_bin, last_bin))
        wk = [complex(math.cos(-2 * math.pi * k / n), math.sin(-2 * math.pi * k / n)) for k in bins]
        self.a = [0.5 - 0.5j * w for w in wk]
        self.b = [0.5 + 0.5j * w for w in wk]
        self.k1 = itemgetter(*[k % m for k in bins])
        self.k2 = itemgetter(*[(m - k) % m for k in bins])

    def power(self, samples, start):
        """Power of bins first..last-1 of the Hamming-windowed frame samples[start:start+n]."""

        frame = list(map(mul, samples[start:start + self.n], self.window))

        z = self.rev(list(map(complex, frame[0::2], frame[1::2])))
        z = list(z)

        m = self.m
        for half, tw in self.stages:
            size = half * 2
            if half * size <= m:
                # many small blocks: handle butterfly position k of all blocks at once
                for k in range(half):
                    t = tw[k]
                    a = z[k::size]
                    b = [t * v for v in z[k + half::size]] if half > 1 else None
                    if b is None:
                        b = z[k + half::size]  # twiddle is 1
                    z[k::size] = map(add, a, b)
                    z[k + half::size] = map(sub, a, b)
            else:
                for s in range(0, m, size):
                    a = z[s:s + half]
                    b = list(map(mul, tw, z[s + half:s + size]))
                    z[s:s + half] = map(add, a, b)
                    z[s + half:s + size] = map(sub, a, b)

        zc = map(complex.conjugate, self.k2(z))
        x = list(map(add, map(mul, self.a, self.k1(z)), map(mul, self.b, zc)))
        mag = list(map(abs, x))
        return list(map(mul, mag, mag))


class _NumpyFFT:
    """Same interface as _RealFFT, using numpy when the receiver has it (much faster)."""

    def __init__(self, np, n, first_bin, last_bin):
        self.np = np
        self.n = n
        self.first = first_bin
        self.last = last_bin
        self.window = np.array(
            [(0.54 - 0.46 * math.cos(i * 2.0 * math.pi / (n - 1))) / 32767.0 for i in range(n)], dtype=np.float64
        )
        self.data = None
        self.source = None

    def power(self, samples, start):
        np = self.np
        if self.source is not samples:
            self.source = samples
            self.data = np.frombuffer(samples, dtype=np.int16)
        frame = self.data[start:start + self.n].astype(np.float64) * self.window
        spectrum = np.fft.rfft(frame)[self.first:self.last]
        return (spectrum.real * spectrum.real + spectrum.imag * spectrum.imag).tolist()


def _make_fft(first, last, use_numpy=True):
    """Fastest available FFT: numpy if importable, otherwise the pure Python one."""

    if use_numpy:
        try:
            import numpy
            return _NumpyFFT(numpy, FRAME_SIZE, first, last), "numpy " + numpy.__version__
        except Exception:  # not installed / broken: pure Python
            pass
    return _RealFFT(FRAME_SIZE, first, last), "pure python"


# ---------------------------------------------------------------------------
# Chroma, filters, classifiers
# ---------------------------------------------------------------------------

def _prepare_notes(sample_rate):
    first = max(1, int(round(FRAME_SIZE * MIN_FREQ / sample_rate)))
    last = min(FRAME_SIZE // 2, int(round(FRAME_SIZE * MAX_FREQ / sample_rate)))
    base = 440.0 / 16.0
    groups = [[] for _ in range(NUM_BANDS)]
    for i in range(first, last):
        freq = i * sample_rate / FRAME_SIZE
        octave = math.log(freq / base) / math.log(2.0)
        note = int(NUM_BANDS * (octave - math.floor(octave)))
        groups[note].append(i - first)
    return first, last, groups


class _Rolling:
    """Integral image of the last rows (prefix sums over columns and rows)."""

    def __init__(self):
        self.rows = []  # integral image rows

    def add(self, features):
        run = 0.0
        row = []
        for v in features:
            run += v
            row.append(run)
        if self.rows:
            last = self.rows[-1]
            row = [a + b for a, b in zip(row, last)]
        self.rows.append(row)


def _area_integral(rows, r1, c1, r2, c2):
    if r1 == r2 or c1 == c2:
        return 0.0
    if r1 == 0:
        row = rows[r2 - 1]
        return row[c2 - 1] if c1 == 0 else row[c2 - 1] - row[c1 - 1]
    row1 = rows[r1 - 1]
    row2 = rows[r2 - 1]
    if c1 == 0:
        return row2[c2 - 1] - row1[c2 - 1]
    return row2[c2 - 1] - row1[c2 - 1] - row2[c1 - 1] + row1[c1 - 1]


def _apply_filter_integral(rows, x, ftype, y, h, w):
    area = _area_integral
    if ftype == 0:
        a = area(rows, x, y, x + w, y + h)
        b = 0.0
    elif ftype == 1:
        h2 = h // 2
        a = area(rows, x, y + h2, x + w, y + h)
        b = area(rows, x, y, x + w, y + h2)
    elif ftype == 2:
        w2 = w // 2
        a = area(rows, x + w2, y, x + w, y + h)
        b = area(rows, x, y, x + w2, y + h)
    elif ftype == 3:
        w2 = w // 2
        h2 = h // 2
        a = area(rows, x, y + h2, x + w2, y + h) + area(rows, x + w2, y, x + w, y + h2)
        b = area(rows, x, y, x + w2, y + h2) + area(rows, x + w2, y + h2, x + w, y + h)
    elif ftype == 4:
        h3 = h // 3
        a = area(rows, x, y + h3, x + w, y + 2 * h3)
        b = area(rows, x, y, x + w, y + h3) + area(rows, x, y + 2 * h3, x + w, y + h)
    else:
        w3 = w // 3
        a = area(rows, x + w3, y, x + 2 * w3, y + h)
        b = area(rows, x, y, x + w3, y + h) + area(rows, x + 2 * w3, y, x + w, y + h)
    return math.log((1.0 + a) / (1.0 + b))


# ---------------------------------------------------------------------------
# Compression (Chromaprint's fingerprint string)
# ---------------------------------------------------------------------------

def _pack_bits(values, bits):
    """LSB-first bit packing of small integers."""

    out = bytearray()
    acc = 0
    nbits = 0
    mask = (1 << bits) - 1
    for v in values:
        acc |= (v & mask) << nbits
        nbits += bits
        while nbits >= 8:
            out.append(acc & 0xFF)
            acc >>= 8
            nbits -= 8
    if nbits:
        out.append(acc & 0xFF)
    return bytes(out)


def compress(subfingerprints, algorithm=1):
    normal = []
    exceptional = []

    def process(x):
        bit = 1
        last_bit = 0
        while x:
            if x & 1:
                value = bit - last_bit
                if value >= 7:
                    normal.append(7)
                    exceptional.append(value - 7)
                else:
                    normal.append(value)
                last_bit = bit
            x >>= 1
            bit += 1
        normal.append(0)

    size = len(subfingerprints)
    if size:
        process(subfingerprints[0])
        for i in range(1, size):
            process(subfingerprints[i] ^ subfingerprints[i - 1])

    data = bytes([algorithm & 255, (size >> 16) & 255, (size >> 8) & 255, size & 255])
    data += _pack_bits(normal, 3) + _pack_bits(exceptional, 5)
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------

def subfingerprints(samples, sample_rate=11025, progress=None, engine=None):
    """List of 32-bit sub-fingerprints for mono 16-bit `samples` (sequence of ints)."""

    first, last, groups = _prepare_notes(sample_rate)
    fft, name = _make_fft(first, last, use_numpy=os.environ.get("MP3_NO_NUMPY") is None)
    if engine is not None:
        engine.append(name)
    getters = [itemgetter(*idx) for idx in groups]

    count = len(samples)
    frames = 0 if count < FRAME_SIZE else (count - FRAME_SIZE) // HOP + 1

    coeff = _FILTER_COEFFICIENTS
    history = []     # last chroma vectors
    integral = _Rolling()
    result = []
    max_width = 16

    for f in range(frames):

        power = fft.power(samples, f * HOP)

        features = [sum(getter(power)) for getter in getters]

        history.append(features)

        if len(history) >= len(coeff):
            recent = history[-len(coeff):]
            filtered = [sum(recent[j][i] * coeff[j] for j in range(len(coeff))) for i in range(NUM_BANDS)]
            norm = math.sqrt(sum(v * v for v in filtered))
            if norm < 0.01:
                filtered = [0.0] * NUM_BANDS
            else:
                filtered = [v / norm for v in filtered]

            integral.add(filtered)

            rows = integral.rows
            if len(rows) >= max_width:
                offset = len(rows) - max_width
                bits = 0
                for (ftype, y, h, w), (t0, t1, t2) in _CLASSIFIERS:
                    value = _apply_filter_integral(rows, offset, ftype, y, h, w)
                    if value < t1:
                        q = 0 if value < t0 else 1
                    else:
                        q = 2 if value < t2 else 3
                    bits = (bits << 2) | _GRAY[q]
                result.append(bits & 0xFFFFFFFF)

        if len(history) > 8:
            del history[0]

        if progress is not None:
            progress(f + 1, frames)

    return result


def fingerprint(samples, sample_rate=11025, engine=None):
    """(duration seconds, fingerprint string) like fpcalc."""

    duration = int(len(samples) / sample_rate)
    return duration, compress(subfingerprints(samples, sample_rate, engine=engine))


# ---------------------------------------------------------------------------
# Command line (used by the plugin as a separate process)
# ---------------------------------------------------------------------------

def _rss_kb():
    try:
        with open("/proc/self/status") as handle:
            for line in handle:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return -1


def main(argv):

    rate = 11025
    channels = 1
    max_seconds = 120

    i = 0
    while i < len(argv):
        if argv[i] == "-r" and i + 1 < len(argv):
            rate = int(argv[i + 1]); i += 1
        elif argv[i] == "-c" and i + 1 < len(argv):
            channels = int(argv[i + 1]); i += 1
        elif argv[i] == "-l" and i + 1 < len(argv):
            max_seconds = int(argv[i + 1]); i += 1
        elif argv[i] == "-v":
            print("python-chromaprint-port-1")
            return 0
        i += 1

    if channels != 1:
        sys.stderr.write("only mono input is supported\n")
        return 2

    try:
        os.nice(10)  # keep the user interface responsive
    except (OSError, AttributeError):
        pass

    started = time.time()
    cpu_started = time.process_time()

    data = sys.stdin.buffer.read(max_seconds * rate * 2)
    samples = array.array("h")
    samples.frombytes(data[: len(data) - (len(data) % 2)])
    if sys.byteorder == "big":
        samples.byteswap()

    frames = 0 if len(samples) < FRAME_SIZE else (len(samples) - FRAME_SIZE) // HOP + 1
    load_before = os.getloadavg()[0] if hasattr(os, "getloadavg") else -1.0

    engine = []
    duration, text = fingerprint(samples, rate, engine)

    wall = time.time() - started
    cpu = time.process_time() - cpu_started
    load_after = os.getloadavg()[0] if hasattr(os, "getloadavg") else -1.0

    sys.stdout.write("DURATION=%d\nFINGERPRINT=%s\n" % (duration, text))
    sys.stderr.write(
        "STATS wall=%.2fs cpu=%.2fs frames=%d (%.1f ms/frame cpu) audio=%ds peak_rss=%dkB load=%.2f->%.2f python=%s fft=%s\n"
        % (wall, cpu, frames, (cpu / frames * 1000.0) if frames else 0.0, duration, _rss_kb(),
           load_before, load_after, sys.version.split()[0], engine[0] if engine else "?")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# Third-party components

## Chromaprint / fpraw (`bin/fpraw-*` in the released .ipk)

The song identification feature ("Identify song") uses small static
command-line tools, `fpraw-arm`, `fpraw-mipsel` and `fpraw-aarch64`. They
are built from the unmodified [Chromaprint](https://github.com/acoustid/chromaprint)
library (version 1.6.x, audio fingerprinting) plus a tiny front end,
[`tools/fpraw/fpraw.cpp`](tools/fpraw/fpraw.cpp), that reads raw PCM from
standard input and prints the fingerprint. The build recipe is
[`tools/fpraw/build.sh`](tools/fpraw/build.sh).

* Chromaprint: MIT licence, containing parts of FFmpeg under the LGPL 2.1
  &mdash; as a whole Chromaprint is to be considered LGPL 2.1. Copyright
  (C) 2010-2016 Lukas Lalinsky and contributors.
  Source: <https://github.com/acoustid/chromaprint> (see its `LICENSE.md`).
* KISS FFT (the FFT library Chromaprint is built with): BSD-3-Clause,
  Copyright (c) 2003-2010 Mark Borgerding.
* To replace the tools with your own build, run `tools/fpraw/build.sh` and
  copy the results to `src/bin/` (plain, or gzip-compressed as `fpraw-<cpu>.gz`, which the plugin unpacks on first use). The source tree itself contains no prebuilt binaries; they are only in the released .ipk.

The tools are only started by the plugin, as separate processes; the
plugin itself (Python) remains GPL-3.0-or-later.

## AcoustID

Song lookups use the [AcoustID](https://acoustid.org/) web service (free for
non-commercial use). The plugin ships a default application key; you can
enter your own in Settings.

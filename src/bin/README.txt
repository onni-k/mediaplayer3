Optional: prebuilt fingerprint tools (fpraw-arm, fpraw-mipsel, fpraw-aarch64).

Since 1.4.003 "Identify song" works without them: the plugin has a pure Python port of
Chromaprint (chromaprint_py.py) that it runs as a separate low-priority python3 process.
If a working fpraw-<cpu> exists in this folder the plugin uses it instead (faster).
To build them: sh tools/fpraw/build.sh, then copy the fpraw-<cpu> files here.

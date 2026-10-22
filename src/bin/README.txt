Prebuilt song identification tools (fpraw-arm, fpraw-mipsel, fpraw-aarch64) are NOT
kept in the source tree; they are included in the released .ipk package only.
To build them yourself: sh tools/fpraw/build.sh, then copy the fpraw-<cpu> files here
(plain or gzip-compressed as fpraw-<cpu>.gz). Without them "Identify song" reports that
the fingerprint tool is missing; everything else works.

#!/bin/sh
# Builds the static "fpraw" fingerprint tools shipped in src/bin/ (Chromaprint 1.6.x + kissfft).
# Needs: git, cmake, and the cross compilers
#   g++-arm-linux-gnueabihf g++-mipsel-linux-gnu g++-aarch64-linux-gnu
# Usage: sh build.sh   (writes fpraw-arm, fpraw-mipsel, fpraw-aarch64 here; copy them to src/bin/ (plain or as fpraw-<cpu>.gz))
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${WORK:-/tmp/fpraw-build}
mkdir -p "$WORK" && cd "$WORK"
[ -d chromaprint ] || git clone --depth 1 https://github.com/acoustid/chromaprint chromaprint

build() { # name cc cxx flags
    mkdir -p "b_$1" && cd "b_$1"
    cmake ../chromaprint -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DBUILD_TOOLS=OFF \
        -DBUILD_TESTS=OFF -DFFT_LIB=kissfft -DCMAKE_SYSTEM_NAME=Linux \
        -DCMAKE_C_COMPILER="$2" -DCMAKE_CXX_COMPILER="$3" \
        -DCMAKE_C_FLAGS="-Os $4" -DCMAKE_CXX_FLAGS="-Os $4" >/dev/null
    make -j4 >/dev/null
    "$3" -Os $4 -static -I../chromaprint/src -I. "$HERE/fpraw.cpp" "$(find . -name libchromaprint.a)" -o "$HERE/fpraw-$1"
    "${2%gcc}strip" "$HERE/fpraw-$1"
    cd ..
}

build arm arm-linux-gnueabihf-gcc arm-linux-gnueabihf-g++ "-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard"
build mipsel mipsel-linux-gnu-gcc mipsel-linux-gnu-g++ "-march=mips32r2"
build aarch64 aarch64-linux-gnu-gcc aarch64-linux-gnu-g++ ""

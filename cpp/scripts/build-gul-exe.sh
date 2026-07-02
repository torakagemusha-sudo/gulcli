#!/usr/bin/env bash
# Cross-compile a portable Windows gul.exe (x86-64) on Linux using mingw-w64.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${ROOT}/cpp/build-mingw"
cmake -S "${ROOT}/cpp" -B "${BUILD_DIR}" \
  -DCMAKE_SYSTEM_NAME=Windows \
  -DCMAKE_CXX_COMPILER=x86_64-w64-mingw32-g++ \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "${BUILD_DIR}"
cp "${BUILD_DIR}/gul.exe" "${ROOT}/gul.exe"
echo "Wrote ${ROOT}/gul.exe"

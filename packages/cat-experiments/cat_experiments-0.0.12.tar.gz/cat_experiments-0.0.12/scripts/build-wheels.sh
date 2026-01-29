#!/usr/bin/env bash
# Build platform-specific wheels for all supported platforms.
# Usage: ./scripts/build-wheels.sh

set -euo pipefail

cd "$(dirname "$0")/.."

echo "Cleaning dist directory..."
rm -f dist/*.whl

# Format: GOOS:GOARCH:MUSLLINUX:Description
PLATFORMS=(
    "darwin:arm64:0:macOS ARM64"
    "darwin:amd64:0:macOS x86_64"
    "linux:amd64:0:Linux x86_64 (glibc)"
    "linux:arm64:0:Linux ARM64 (glibc)"
    "linux:amd64:1:Linux x86_64 (musl/Alpine)"
    "linux:arm64:1:Linux ARM64 (musl/Alpine)"
    "windows:amd64:0:Windows x86_64"
)

for platform in "${PLATFORMS[@]}"; do
    IFS=':' read -r goos goarch musllinux desc <<< "$platform"
    echo ""
    echo "=== Building $desc ($goos/$goarch) ==="
    GOOS="$goos" GOARCH="$goarch" MUSLLINUX="$musllinux" uv build --wheel
done

echo ""
echo "=== Built wheels ==="
ls -lh dist/*.whl

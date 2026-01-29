#!/bin/bash
# Cross-compile Go CLI for all Node.js platform packages

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLI_DIR="$SCRIPT_DIR/../cli"

# Get version from SDK package.json
VERSION=$(node -p "require('$SCRIPT_DIR/sdk/package.json').version")

echo "Building Go CLI v$VERSION for all platforms..."

cd "$CLI_DIR"

LDFLAGS="-s -w -X main.version=$VERSION"

# Darwin ARM64 (Apple Silicon)
echo "  darwin-arm64..."
GOOS=darwin GOARCH=arm64 CGO_ENABLED=0 go build -ldflags="$LDFLAGS" -o "$SCRIPT_DIR/bin-darwin-arm64/bin/cat-experiments" ./cmd/cat-experiments

# Darwin x64 (Intel Mac)
echo "  darwin-x64..."
GOOS=darwin GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="$LDFLAGS" -o "$SCRIPT_DIR/bin-darwin-x64/bin/cat-experiments" ./cmd/cat-experiments

# Linux ARM64
echo "  linux-arm64..."
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -ldflags="$LDFLAGS" -o "$SCRIPT_DIR/bin-linux-arm64/bin/cat-experiments" ./cmd/cat-experiments

# Linux x64
echo "  linux-x64..."
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="$LDFLAGS" -o "$SCRIPT_DIR/bin-linux-x64/bin/cat-experiments" ./cmd/cat-experiments

# Windows x64
echo "  win32-x64..."
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="$LDFLAGS" -o "$SCRIPT_DIR/bin-win32-x64/bin/cat-experiments.exe" ./cmd/cat-experiments

echo "Done! All binaries built."
ls -lh "$SCRIPT_DIR"/bin-*/bin/cat-experiments*

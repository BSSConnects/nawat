#!/usr/bin/env bash
# Builds the nawat-cli .deb package. Run inside WSL/Linux from the cli/ directory.
set -euo pipefail

SOURCE_DIR=$(cd "$(dirname "$0")" && pwd)
BUILD_DIR=$(mktemp -d /tmp/nawat-cli-build.XXXXXX)
OUTPUT_DIR=$(cd "$SOURCE_DIR/.." && pwd)
trap 'rm -rf "$BUILD_DIR"' EXIT

cp -a "$SOURCE_DIR/." "$BUILD_DIR/"
chmod -R a+rX,u+w,go-w "$BUILD_DIR"
cd "$BUILD_DIR"

if [ "$(id -u)" -eq 0 ]; then
    APT_GET=apt-get
else
    APT_GET="sudo apt-get"
fi

$APT_GET update
$APT_GET install -y build-essential debhelper dh-virtualenv \
    python3-dev python3-venv python3-pip virtualenv devscripts

chmod +x debian/rules
dpkg-buildpackage -us -uc -b

echo "Build complete. .deb package(s) placed in the parent directory:"
cp ../*.deb "$OUTPUT_DIR/"
ls -1 "$OUTPUT_DIR"/*.deb
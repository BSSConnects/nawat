#!/usr/bin/env bash
# Everything CI runs. Run before opening a PR. If CI can fail when this passed, fix this script.
set -euo pipefail
cd "$(dirname "$0")/.."
exec make verify

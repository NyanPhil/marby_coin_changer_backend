#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec "$(pwd)/.venv/bin/python" "$(pwd)/coin_changer_connected.py" --hardware >> "$(pwd)/marby.log" 2>&1

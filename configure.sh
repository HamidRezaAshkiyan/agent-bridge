#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required (Python 3.8+)." >&2
  echo "Install Python 3 via Homebrew (brew install python3) or your OS package manager." >&2
  exit 1
fi

exec python3 "${SCRIPT_DIR}/lib/configure.py" "$@"

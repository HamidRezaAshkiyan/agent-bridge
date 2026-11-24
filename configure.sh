#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer python3 (standard on macOS/Linux). Git Bash and MSYS on Windows usually
# only expose `python`, so fall back to it there.
PYTHON_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "Error: Python 3 is required (Python 3.9+)." >&2
  echo "Install it with 'brew install python3' / your package manager, or on Windows:" >&2
  echo "  winget install --id Python.Python.3.12 -e" >&2
  exit 1
fi

exec "$PYTHON_BIN" "${SCRIPT_DIR}/lib/configure.py" "$@"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_python() {
  for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
      echo "$cand"
      return 0
    fi
  done
  if command -v py >/dev/null 2>&1 && py -3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    echo "py -3"
    return 0
  fi
  return 1
}

PYTHON_CMD="$(find_python || true)"
if [ -z "$PYTHON_CMD" ]; then
  echo "Error: Python 3.8+ is required." >&2
  echo "Install Python 3 via Homebrew (brew install python3), winget (winget install Python.Python.3.12), or your OS package manager." >&2
  exit 1
fi

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
# shellcheck disable=SC2086
exec $PYTHON_CMD "${SCRIPT_DIR}/lib/configure.py" "$@"

#!/usr/bin/env bash
# One-liner bootstrapper for Agent Bridge (macOS / Linux / WSL / Git Bash)
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.sh | bash -s -- install
#
# Windows PowerShell users: use bootstrap.ps1 instead.
set -euo pipefail

REPO_URL="${AGENT_BRIDGE_REPO:-https://github.com/HamidRezaAshkiyan/agent-bridge.git}"
INSTALL_DIR="${AGENT_BRIDGE_HOME:-$HOME/.agent-bridge/repo}"
MODE="${1:-configure}"
shift || true

# `python3` is canonical on macOS/Linux; Git Bash / MSYS only ship `python`.
PYTHON_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

for bin in git; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "Error: '$bin' is required to run Agent Bridge." >&2
    exit 1
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "Error: 'Python 3' is required to run Agent Bridge." >&2
  exit 1
fi

mkdir -p "$(dirname "$INSTALL_DIR")"
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating Agent Bridge in $INSTALL_DIR ..."
  git -C "$INSTALL_DIR" pull --ff-only --quiet || true
else
  echo "Cloning Agent Bridge into $INSTALL_DIR ..."
  git clone --depth 1 --quiet "$REPO_URL" "$INSTALL_DIR"
fi

# chmod is a no-op on filesystems that do not track the executable bit.
chmod +x "$INSTALL_DIR/configure.sh" "$INSTALL_DIR/install-agent.sh" 2>/dev/null || true

if [ "$MODE" = "install" ]; then
  exec "$INSTALL_DIR/install-agent.sh" "$@" </dev/tty
else
  exec "$INSTALL_DIR/configure.sh" "$@" </dev/tty
fi

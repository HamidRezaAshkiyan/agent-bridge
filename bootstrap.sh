#!/usr/bin/env bash
# One-liner bootstrapper for Agent Bridge
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.sh | bash -s -- install
set -euo pipefail

REPO_URL="${AGENT_BRIDGE_REPO:-https://github.com/HamidRezaAshkiyan/agent-bridge.git}"
INSTALL_DIR="${AGENT_BRIDGE_HOME:-$HOME/.agent-bridge/repo}"
MODE="${1:-configure}"
shift || true

if ! command -v git >/dev/null 2>&1; then
  echo "Error: 'git' is required to run Agent Bridge." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1 && ! command -v py >/dev/null 2>&1; then
  echo "Error: Python 3.8+ is required to run Agent Bridge." >&2
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

chmod +x "$INSTALL_DIR/configure.sh" "$INSTALL_DIR/install-agent.sh"

if [ "$MODE" = "install" ]; then
  exec "$INSTALL_DIR/install-agent.sh" "$@" </dev/tty
else
  exec "$INSTALL_DIR/configure.sh" "$@" </dev/tty
fi

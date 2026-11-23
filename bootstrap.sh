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

for bin in git python3; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "Error: '$bin' is required to run Agent Bridge." >&2
    exit 1
  fi
done

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

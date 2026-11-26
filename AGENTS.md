# AGENTS.md — Agent Bridge

## Overview
Zero-dependency, cross-platform interactive toolkit that installs 17 CLI/GUI coding agents and configures 12+ AI provider presets (Metis AI, Metis Global/TapSage, AvalAI, Liara AI, GapGPT, OpenRouter, DeepSeek, Groq, Together AI, Ollama, LM Studio, Custom) across 16 coding tools and desktop apps — including a local Anthropic↔OpenAI HTTP bridge proxy and a stdio MCP server for Claude Desktop.

## Tech Stack & Requirements
- **Core Runtime:** Python 3.8+ (standard library only — zero third-party `pip` or `npm` dependencies)
- **Shell Wrappers:** Bash (`*.sh`), PowerShell 5.1/7+ (`*.ps1`), Windows CMD (`*.cmd`)
- **Showcase Site:** Vanilla HTML/CSS/JS (`docs/`) deployed to GitHub Pages
- **Platforms:** macOS, Linux, Windows, WSL, Git Bash

## Repository Structure
```text
agent-bridge/
├── configure.{sh,ps1,cmd}       # Launchers for lib/configure.py
├── install-agent.{sh,ps1,cmd}   # Launchers for lib/install_agent.py
├── bootstrap.{sh,ps1}           # One-line remote bootstrap installers
├── lib/
│   ├── __init__.py              # Package metadata & __version__
│   ├── configure.py             # CLI & interactive TUI orchestrator (--provider, --agents, --restore, --dry-run)
│   ├── providers.py             # 12 ProviderPreset definitions, ModelSpec, live /v1/models probe
│   ├── configurators.py         # 16 target configurators, BackupManager, safe config merging
│   ├── install_agent.py         # 17-agent installer catalog, OS & package-manager detection
│   ├── desktop_proxy.py         # Local ThreadingHTTPServer (127.0.0.1:4789) with Anthropic↔OpenAI translation
│   ├── mcp_model_bridge.py      # Stdio MCP server (ask_custom_model, list_custom_models, active_provider_info)
│   └── ui.py                    # Cross-platform arrow-key/multi-select ANSI TUI primitives
├── tests/
│   └── test_agent_bridge.py     # unittest suite using isolated temp HOME / APPDATA
└── docs/                        # Static GitHub Pages site + Interactive Config & Command Builder
    ├── index.html
    ├── app.js
    └── styles.css
```

## Architecture & Key Flows
- **Configuration Flow (`lib/configure.py`):** Resolves a `ProviderPreset` into a `ResolvedProvider` (normalizing OpenAI/Anthropic URLs), optionally probes `/v1/models`, creates a timestamped backup session in `~/.agent-bridge/backups/` via `BackupManager`, and invokes selected `AGENT_MAP` configurators in `lib/configurators.py` to merge settings without clobbering existing keys.
- **Installer Flow (`lib/install_agent.py`):** Detects OS and available package managers (`brew`, `winget`, `scoop`, `choco`, `npm`, `pnpm`, `bun`, `uv`, `pipx`, `pip`, `curl`), installs selected `CATALOG` entries, and hands off newly installed targets to `lib/configure.py`.
- **Desktop Bridges:**
  - `lib/desktop_proxy.py` serves `/v1/chat/completions`, `/v1/models`, `/v1/messages`, and `/health` on `127.0.0.1:4789`. For OpenAI-only upstreams (e.g., Liara, Groq, Together, LM Studio), it translates Anthropic `/v1/messages` ↔ OpenAI `/v1/chat/completions` on the fly.
  - `lib/mcp_model_bridge.py` runs as a stdio JSON-RPC MCP server registered in `claude_desktop_config.json`, reading `~/.agent-bridge/proxy.json`.

## Development & Commands
```bash
# Run full test suite (isolated temp directories; never touches real configs or Windows Registry)
python3 -m unittest discover -s tests -v
# Windows:
# py -3 -m unittest discover -s tests -v

# Interactive or non-interactive configuration
./configure.sh --list-providers
./configure.sh --list-agents
./configure.sh --non-interactive --provider avalai --api-key "<key>" --model "gpt-4o" --agents all --dry-run
./configure.sh --restore

# Interactive or non-interactive agent installation
./install-agent.sh --list
./install-agent.sh --agents opencode-cli,claude-code,pi
```

## Configuration & Environment
- **Runtime state dir:** `~/.agent-bridge/` (`proxy.json`, `backups/<timestamp>/`, `start-proxy.{sh,ps1,cmd}`, `cursor-setup.txt`).
- **Env vars read by bridges / CLI:** Provider-specific key env vars (e.g., `METIS_API_KEY`, `AVALAI_API_KEY`, `OPENROUTER_API_KEY`), `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_BASE_URL`, `AGENT_BRIDGE_PROVIDER`, `AGENT_BRIDGE_API_KEY`, `AGENT_BRIDGE_MODEL`, `AGENT_BRIDGE_FORCE_MODEL`, `AGENT_BRIDGE_MCP_CONFIG`, `AGENT_BRIDGE_MODE`.
- **Managed shell blocks:** `shell-env` target writes delimited `# >>> agent-bridge >>>` blocks in `~/.zshrc`/`~/.bashrc` or Windows PowerShell `$PROFILE` + `HKCU\Environment`.

## Conventions & Gotchas
- **Zero external dependencies:** Keep `lib/` strictly Python 3.8+ standard library (`from __future__ import annotations`, `urllib.request`, `http.server`, `json`, `pathlib`, etc.). Do not introduce third-party packages.
- **Anthropic base URLs must NOT end in `/v1`:** Claude Code and Anthropic SDKs append `/v1/messages` automatically; `ProviderPreset.resolved_anthropic_url()` strips trailing `/v1`. Always use `ANTHROPIC_AUTH_TOKEN` (not `ANTHROPIC_API_KEY`) for third-party gateways and strip conflicting `ANTHROPIC_API_KEY`.
- **Cross-platform parity:** Maintain `.sh`, `.ps1`, and `.cmd` entry wrappers and keep Windows `%APPDATA%` paths in sync with macOS/Linux paths in `lib/configurators.py`.
- **VS Code Copilot Agent Mode:** `chatLanguageModels.json` entries require `"toolCalling": true`.
- **Keep `docs/app.js` in sync:** When adding/updating providers or agent targets in `lib/providers.py` or `lib/configurators.py`, update the interactive builder in `docs/` if applicable.

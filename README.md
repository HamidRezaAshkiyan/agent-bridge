# ⚡ Agent Bridge

**One interactive toolkit to install coding agents and configure Metis AI, AvalAI, Liara AI, OpenRouter, or any custom AI provider across every major CLI & GUI coding tool — plus Claude Desktop & ChatGPT Desktop bridges.**

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero%20(Python%203%20%2B%20Bash%20%2F%20PowerShell)-brightgreen.svg)](#requirements)
[![Platforms](https://img.shields.io/badge/platforms-macOS%20%7C%20Linux%20%7C%20Windows-0ea5e9.svg)](#requirements)
[![Live Showcase Website](https://img.shields.io/badge/website-GitHub%20Pages-8b5cf6.svg)](https://hamidrezaashkiyan.github.io/agent-bridge/)

---

## ✨ What's Included

1. **`./configure.sh` / `.\configure.ps1` / `configure.cmd` — Interactive AI Provider Configurator**
   - Arrow-key & multi-select TUI on macOS, Linux, and Windows (with non-interactive CLI flags for automation).
   - Presets for **Metis AI**, **Metis Global (TapSage)**, **AvalAI**, **Liara AI**, **GapGPT**, **OpenRouter**, **DeepSeek**, **Groq**, **Together AI**, **Ollama**, **LM Studio**, and **Custom** endpoints.
   - Configures **16 CLI, GUI, and Desktop targets** in one pass — safely merging into existing config files without clobbering your settings.
   - Built-in **live API connection & model probe** (`/v1/models`) before writing configs.
   - Automatic **timestamped backups** (`~/.agent-bridge/backups/`) with one-command `--restore`.
2. **`./install-agent.sh` / `.\install-agent.ps1` / `install-agent.cmd` — Interactive Coding Agent Installer**
   - Detects your OS (macOS, Linux, Windows, WSL) and package managers (`brew`, `winget`, `scoop`, `choco`, `npm`, `pnpm`, `bun`, `uv`, `pipx`, `pip`, `curl`).
   - Shows live installed status for **17 CLI agents, GUI IDEs, and open-source Desktop Chat GUIs**.
   - Installs your chosen tools and immediately offers to launch the configurator pre-selected with the newly installed agent(s) so you can wire up your API key in seconds.
3. **Claude Desktop & ChatGPT Desktop Custom API Bridges**
   - **`lib/desktop_proxy.py`**: Zero-dependency local HTTP gateway (`http://127.0.0.1:4789`) that forwards OpenAI requests, supports model remapping, and **automatically translates Anthropic `/v1/messages` ↔ OpenAI `/v1/chat/completions`** so even OpenAI-only providers work with Claude Code and Claude Desktop!
   - **`lib/mcp_model_bridge.py`**: Zero-dependency stdio MCP server auto-registered in `claude_desktop_config.json`, giving Claude Desktop native `ask_custom_model` and `list_custom_models` tools.
4. **Interactive Showcase Website (`docs/`)**
   - Includes a live **Interactive Config & Command Builder** — pick a provider and agent to preview the exact generated config file and CLI command.

---

## 🚀 Quick Start

### Option 1: One-Line Run (No Manual Clone Needed)

#### macOS / Linux / WSL / Git Bash
Configure your AI provider across your tools:
```bash
curl -fsSL https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.sh | bash
```

Or launch the **Coding Agent Installer** first (which then offers to configure your API key):
```bash
curl -fsSL https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.sh | bash -s -- install
```

#### Windows (PowerShell)
Configure your AI provider across your tools:
```powershell
irm https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.ps1 | iex
```

Or launch the **Coding Agent Installer** first:
```powershell
$env:AGENT_BRIDGE_MODE="install"; irm https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.ps1 | iex
```

### Option 2: Clone Locally

```bash
git clone https://github.com/HamidRezaAshkiyan/agent-bridge.git
cd agent-bridge

# macOS / Linux / WSL / Git Bash:
./install-agent.sh    # (Optional) install CLI or GUI coding agents
./configure.sh        # configure your AI provider & API key
```

```powershell
git clone https://github.com/HamidRezaAshkiyan/agent-bridge.git
cd agent-bridge

# Windows (PowerShell — or use install-agent.cmd / configure.cmd in CMD):
.\install-agent.ps1   # (Optional) install CLI or GUI coding agents
.\configure.ps1       # configure your AI provider & API key
```

---

## 🌐 Supported AI Providers

| Preset ID | Provider | OpenAI-Compatible Base URL | Anthropic-Compatible Base URL |
| :--- | :--- | :--- | :--- |
| `metis` | **Metis AI** | `https://api.metisai.ir/openai/v1` | `https://api.metisai.ir/anthropic` |
| `metis-global` | **Metis AI (TapSage)** | `https://api.tapsage.com/openai/v1` | `https://api.tapsage.com/anthropic` |
| `avalai` | **AvalAI** | `https://api.avalai.ir/v1` | `https://api.avalai.ir` |
| `liara` | **Liara AI** | `https://ai.liara.ir/api/{workspace_id}/v1` | *(via local bridge proxy)* |
| `gapgpt` | **GapGPT** | `https://api.gapgpt.app/v1` | `https://api.gapgpt.app` |
| `openrouter` | **OpenRouter** | `https://openrouter.ai/api/v1` | `https://openrouter.ai/api` |
| `deepseek` | **DeepSeek** | `https://api.deepseek.com/v1` | `https://api.deepseek.com/anthropic` |
| `groq` | **Groq** | `https://api.groq.com/openai/v1` | *(via local bridge proxy)* |
| `together` | **Together AI** | `https://api.together.xyz/v1` | *(via local bridge proxy)* |
| `ollama` | **Ollama (Local)** | `http://localhost:11434/v1` | `http://localhost:11434` |
| `lmstudio` | **LM Studio (Local)** | `http://localhost:1234/v1` | *(via local bridge proxy)* |
| `custom` | **Custom Provider** | Any custom URL | Optional custom URL or local proxy |

---

## 🛠️ Supported Coding Agents & Desktop Apps (CLI + GUI)

| Target ID | Tool | Type | Mode | Config File(s) Managed |
| :--- | :--- | :--- | :--- | :--- |
| `opencode-cli` | **OpenCode CLI / TUI** | CLI | Native | `~/.config/opencode/opencode.json` |
| `opencode-desktop` | **OpenCode Desktop** | GUI | Native | `~/.config/opencode/opencode.json` + `~/.local/share/opencode/auth.json` |
| `claude-code-cli` | **Claude Code CLI** | CLI | Native | `~/.claude/settings.json` |
| `claude-code-gui` | **Claude Code IDE Extension** | GUI | Native | `~/.claude/settings.json` + VS Code / Cursor `settings.json` |
| `pi` | **Pi Coding Agent** | CLI | Native | `~/.pi/agent/models.json` + `~/.pi/agent/settings.json` |
| `cursor` | **Cursor IDE & Agent CLI** | GUI | Guided + Env | `Cursor/User/settings.json` + `~/.agent-bridge/cursor-setup.txt` |
| `vscode-copilot` | **VS Code GitHub Copilot BYOK** | GUI | Native | `Code/User/chatLanguageModels.json` (and Insiders if present) |
| `codex-cli` | **OpenAI Codex CLI** | CLI | Native | `~/.codex/config.toml` |
| `codex-desktop` | **Codex Desktop** | GUI | Native | `~/.codex/config.toml` + `~/.agent-bridge/proxy.json` |
| `aider` | **Aider** | CLI | Native | `~/.aider.conf.yml` |
| `zed` | **Zed Editor** | GUI | Native | `~/.config/zed/settings.json` (Windows: `%APPDATA%\Zed\settings.json`) |
| `continue` | **Continue (VS Code / JetBrains)** | GUI | Native | `~/.continue/config.yaml` |
| `goose` | **Goose (CLI & Desktop)** | CLI + GUI | Native | `~/.config/goose/config.yaml` (Windows: `%APPDATA%\Block\goose\config\config.yaml`) |
| `claude-desktop` | **Claude Desktop** | Desktop | Proxy + MCP | `developer_settings.json` + `claude_desktop_config.json` + `proxy.json` |
| `chatgpt-desktop` | **ChatGPT Desktop & Open GUIs** | Desktop | Proxy + Guide | `~/.codex/config.toml` + `~/.agent-bridge/proxy.json` |
| `shell-env` | **Shell Environment** | System | Native | Managed `# >>> agent-bridge >>>` block in `~/.zshrc` / `~/.bashrc` or Windows PowerShell `$PROFILE` + `HKCU\Environment` |

> **Windows paths:** VS Code, Cursor, Zed, Goose, and Claude Desktop configs are automatically written under `%APPDATA%` (e.g. `%APPDATA%\Code\User`, `%APPDATA%\Cursor\User`, `%APPDATA%\Claude`), and user-level environment variables are persisted to both PowerShell 5.1/7+ `$PROFILE` files and `HKCU\Environment`.

---

## 🖥️ Using Custom API Providers with Claude Desktop & ChatGPT Desktop

### Claude Desktop (`--agents claude-desktop`)
Agent Bridge sets up **three complementary mechanisms** automatically:
1. **MCP Model Bridge (Works in Every Claude Desktop Build):**
   Registers `agent-bridge-models` (`lib/mcp_model_bridge.py`) in `claude_desktop_config.json`. Restart Claude Desktop and ask Claude to use `ask_custom_model` or `list_custom_models` to query any model on Metis, AvalAI, OpenRouter, Liara, or your custom endpoint directly inside chat.
2. **Developer Mode → Third-Party Inference:**
   Enables `"allowDevTools": true` in `developer_settings.json`. In Claude Desktop, open **Developer → Configure Third-Party Inference...** and enter your Anthropic-compatible Base URL (e.g., `https://api.metisai.ir/anthropic`, `https://api.avalai.ir`, or `http://127.0.0.1:4789` when using our local proxy).
3. **Local Anthropic ↔ OpenAI Bridge Proxy:**
   Run `~/.agent-bridge/start-proxy.sh` (or `%USERPROFILE%\.agent-bridge\start-proxy.cmd` / `start-proxy.ps1` on Windows) to start `lib/desktop_proxy.py` on `http://127.0.0.1:4789`. If your provider is OpenAI-only (e.g., Liara, Groq, Together, LM Studio), it automatically translates Anthropic `/v1/messages` calls into OpenAI `/v1/chat/completions`!

### ChatGPT Desktop (`--agents chatgpt-desktop`)
- Official consumer builds of ChatGPT Desktop hard-pin `chatgpt.com` endpoints.
- Developer / Codex Desktop builds read `~/.codex/config.toml` — Agent Bridge configures `[model_providers.<provider>]` automatically.
- For a full native ChatGPT-style Desktop GUI with custom Base URL + API Key out of the box, run `./install-agent.sh` (or `.\install-agent.ps1` on Windows) to install **Cherry Studio**, **Chatbox**, or **Jan**, and point them to your provider URL or `http://127.0.0.1:4789/v1`.

---

## ⚙️ Non-Interactive & Advanced CLI Usage

### Configure Multiple Agents in One Command
```bash
# macOS / Linux / WSL / Git Bash
./configure.sh --non-interactive \
  --provider avalai \
  --api-key "aa-your-api-key" \
  --model "gpt-4o" \
  --agents "opencode-cli,opencode-desktop,claude-code-cli,pi,vscode-copilot,shell-env"
```

```powershell
# Windows (PowerShell — or use configure.cmd in CMD)
.\configure.ps1 --non-interactive `
  --provider avalai `
  --api-key "aa-your-api-key" `
  --model "gpt-4o" `
  --agents "opencode-cli,opencode-desktop,claude-code-cli,pi,vscode-copilot,shell-env"
```

### Preview Changes Without Touching Any Files (`--dry-run`)
```bash
./configure.sh --non-interactive \
  --provider metis \
  --api-key "tpsg-your-key" \
  --agents all \
  --dry-run
```

### List Providers, Agents, or Restore a Backup
```bash
./configure.sh --list-providers
./configure.sh --list-agents
./configure.sh --restore
```

### Install Specific Agents via CLI
```bash
# Interactive installer
./install-agent.sh

# See installed status of all 17 agents
./install-agent.sh --list

# Install specific agents non-interactively
./install-agent.sh --agents opencode-cli,claude-code,pi
```

---

## 🔧 Troubleshooting Tips

- **Claude Code returns `404` or `401`:**
  - Never append `/v1` to `ANTHROPIC_BASE_URL` (Claude Code appends `/v1/messages` automatically — Agent Bridge strips `/v1` for you).
  - Use `ANTHROPIC_AUTH_TOKEN` (Bearer header) instead of `ANTHROPIC_API_KEY` (`x-api-key`) for third-party gateways. Agent Bridge automatically removes conflicting `ANTHROPIC_API_KEY` entries.
  - If you previously logged into `claude.ai`, run `claude logout` and verify with `/status`.
- **VS Code Copilot custom models don't appear in Agent Mode:**
  - `toolCalling: true` is required in `chatLanguageModels.json` (Agent Bridge sets this automatically). Restart VS Code after updating `chatLanguageModels.json`.
- **Cursor IDE API Key input box won't accept focus:**
  - Toggle the switch ON, click near the text box, and press `Tab` to focus it, then paste your key/URL.
- **Windows PowerShell blocks running `.ps1` scripts (`ExecutionPolicy`):**
  - Either run `configure.cmd` / `install-agent.cmd`, or run PowerShell with `powershell -ExecutionPolicy Bypass -File .\configure.ps1`.

---

## 🧪 Running Tests

```bash
python3 -m unittest discover -s tests -v
# On Windows (if `python3` is not aliased):
# py -3 -m unittest discover -s tests -v
```
Tests run against isolated temporary home and AppData directories and never touch your real configuration files or Windows Registry.

---

## 📋 Requirements

- **macOS, Linux, or Windows** (PowerShell 5.1/7+, CMD, Windows Terminal, WSL, or Git Bash)
- **Python 3.8+** (standard library only — zero `pip` or `npm` dependencies required for Agent Bridge itself)

---

## 📄 License

MIT © [HamidReza Ashkiyan](https://github.com/HamidRezaAshkiyan)

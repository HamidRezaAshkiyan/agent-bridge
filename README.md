# ⚡ Agent Bridge

**One interactive toolkit to install coding agents and configure Metis AI, AvalAI, Liara AI, OpenRouter, or any custom AI provider across every major CLI & GUI coding tool — plus Claude Desktop & ChatGPT Desktop bridges.**

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero%20(Bash%20%2B%20Python%203)-brightgreen.svg)](#requirements)
[![Live Showcase Website](https://img.shields.io/badge/website-GitHub%20Pages-8b5cf6.svg)](https://hamidrezaashkiyan.github.io/agent-bridge/)

---

## ✨ What's Included

1. **`./configure.sh` — Interactive AI Provider Configurator**
   - Arrow-key & multi-select TUI (with non-interactive CLI flags for automation).
   - Presets for **Metis AI**, **Metis Global (TapSage)**, **AvalAI**, **Liara AI**, **GapGPT**, **OpenRouter**, **DeepSeek**, **Groq**, **Together AI**, **Ollama**, **LM Studio**, and **Custom** endpoints.
   - Configures **16 CLI, GUI, and Desktop targets** in one pass — safely merging into existing config files without clobbering your settings.
   - Built-in **live API connection & model probe** (`/v1/models`) before writing configs.
   - Automatic **timestamped backups** (`~/.agent-bridge/backups/`) with one-command `--restore`.
2. **`./install-agent.sh` — Interactive Coding Agent Installer**
   - Detects your OS (macOS, Linux, WSL) and package managers (`brew`, `npm`, `pnpm`, `bun`, `uv`, `pipx`, `curl`).
   - Shows live installed status for **17 CLI agents, GUI IDEs, and open-source Desktop Chat GUIs**.
   - Installs your chosen tools and immediately offers to launch `./configure.sh` pre-selected with the newly installed agent(s) so you can wire up your API key in seconds.
3. **Claude Desktop & ChatGPT Desktop Custom API Bridges**
   - **`lib/desktop_proxy.py`**: Zero-dependency local HTTP gateway (`http://127.0.0.1:4789`) that forwards OpenAI requests, supports model remapping, and **automatically translates Anthropic `/v1/messages` ↔ OpenAI `/v1/chat/completions`** so even OpenAI-only providers work with Claude Code and Claude Desktop!
   - **`lib/mcp_model_bridge.py`**: Zero-dependency stdio MCP server auto-registered in `claude_desktop_config.json`, giving Claude Desktop native `ask_custom_model` and `list_custom_models` tools.
4. **Interactive Showcase Website (`docs/`)**
   - Includes a live **Interactive Config & Command Builder** — pick a provider and agent to preview the exact generated config file and CLI command.

---

## 🚀 Quick Start

### Option 1: One-Line Run (No Manual Clone Needed)

Configure your AI provider across your tools:
```bash
curl -fsSL https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.sh | bash
```

Or launch the **Coding Agent Installer** first (which then offers to configure your API key):
```bash
curl -fsSL https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.sh | bash -s -- install
```

### Option 2: Clone Locally

```bash
git clone https://github.com/HamidRezaAshkiyan/agent-bridge.git
cd agent-bridge

# 1. (Optional) Install your preferred CLI or GUI coding agent(s)
./install-agent.sh

# 2. Configure your AI provider & API key across all selected tools
./configure.sh
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
| `zed` | **Zed Editor** | GUI | Native | `~/.config/zed/settings.json` |
| `continue` | **Continue (VS Code / JetBrains)** | GUI | Native | `~/.continue/config.yaml` |
| `goose` | **Goose (CLI & Desktop)** | CLI + GUI | Native | `~/.config/goose/config.yaml` |
| `claude-desktop` | **Claude Desktop** | Desktop | Proxy + MCP | `developer_settings.json` + `claude_desktop_config.json` + `proxy.json` |
| `chatgpt-desktop` | **ChatGPT Desktop & Open GUIs** | Desktop | Proxy + Guide | `~/.codex/config.toml` + `~/.agent-bridge/proxy.json` |
| `shell-env` | **Shell Environment** | System | Native | Managed `# >>> agent-bridge >>>` block in `~/.zshrc` / `~/.bashrc` |

---

## 🖥️ Using Custom API Providers with Claude Desktop & ChatGPT Desktop

### Claude Desktop (`--agents claude-desktop`)
Agent Bridge sets up **three complementary mechanisms** automatically:
1. **MCP Model Bridge (Works in Every Claude Desktop Build):**
   Registers `agent-bridge-models` (`lib/mcp_model_bridge.py`) in `claude_desktop_config.json`. Restart Claude Desktop and ask Claude to use `ask_custom_model` or `list_custom_models` to query any model on Metis, AvalAI, OpenRouter, Liara, or your custom endpoint directly inside chat.
2. **Developer Mode → Third-Party Inference:**
   Enables `"allowDevTools": true` in `developer_settings.json`. In Claude Desktop, open **Developer → Configure Third-Party Inference...** and enter your Anthropic-compatible Base URL (e.g., `https://api.metisai.ir/anthropic`, `https://api.avalai.ir`, or `http://127.0.0.1:4789` when using our local proxy).
3. **Local Anthropic ↔ OpenAI Bridge Proxy:**
   Run `~/.agent-bridge/start-proxy.sh` to start `lib/desktop_proxy.py` on `http://127.0.0.1:4789`. If your provider is OpenAI-only (e.g., Liara, Groq, Together, LM Studio), it automatically translates Anthropic `/v1/messages` calls into OpenAI `/v1/chat/completions`!

### ChatGPT Desktop (`--agents chatgpt-desktop`)
- Official consumer builds of ChatGPT Desktop hard-pin `chatgpt.com` endpoints.
- Developer / Codex Desktop builds read `~/.codex/config.toml` — Agent Bridge configures `[model_providers.<provider>]` automatically.
- For a full native ChatGPT-style Desktop GUI with custom Base URL + API Key out of the box, run `./install-agent.sh` to install **Cherry Studio**, **Chatbox**, or **Jan**, and point them to your provider URL or `http://127.0.0.1:4789/v1`.

---

## ⚙️ Non-Interactive & Advanced CLI Usage

### Configure Multiple Agents in One Command
```bash
./configure.sh --non-interactive \
  --provider avalai \
  --api-key "aa-your-api-key" \
  --model "gpt-4o" \
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

---

## 🧪 Running Tests

```bash
python3 -m unittest discover -s tests -v
```
Tests run against an isolated temporary `$HOME` directory and never touch your real configuration files.

---

## 📋 Requirements

- **macOS, Linux, or Windows (WSL / Git Bash)**
- **Bash** and **Python 3.8+** (standard library only — zero `pip` or `npm` dependencies required for Agent Bridge itself)

---

## 📄 License

MIT © [HamidReza Ashkiyan](https://github.com/HamidRezaAshkiyan)

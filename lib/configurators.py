"""Safe, idempotent configurators for all major CLI & GUI coding agents and AI desktop apps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Callable
from urllib.parse import urlparse

from lib import platform_support as plat
from lib.providers import ModelSpec, ResolvedProvider


@dataclass
class AgentMeta:
    id: str
    name: str
    category: str  # "cli" | "gui" | "desktop" | "system"
    mode: str      # "native" | "guided" | "proxy+mcp"
    summary: str
    config_hint: str


@dataclass
class ConfigResult:
    agent_id: str
    agent_name: str
    ok: bool
    files_written: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error: str = ""


AGENTS: list[AgentMeta] = [
    AgentMeta("opencode-cli", "OpenCode CLI / TUI", "cli", "native", "Terminal coding agent (opencode.json)", "~/.config/opencode/opencode.json"),
    AgentMeta("opencode-desktop", "OpenCode Desktop (GUI)", "gui", "native", "Desktop app sharing opencode.json + auth.json", "~/.config/opencode/opencode.json"),
    AgentMeta("claude-code-cli", "Claude Code CLI", "cli", "native", "Anthropic terminal agent (~/.claude/settings.json)", "~/.claude/settings.json"),
    AgentMeta("claude-code-gui", "Claude Code IDE Extension (GUI)", "gui", "native", "VS Code & Cursor Claude Code extension settings", "VS Code / Cursor settings.json"),
    AgentMeta("pi", "Pi Coding Agent (CLI)", "cli", "native", "Mario Zechner's Pi agent (models.json + settings.json)", "~/.pi/agent/models.json"),
    AgentMeta("cursor", "Cursor IDE (GUI & Agent CLI)", "gui", "guided", "Terminal env + guided Models > API Keys setup", "Cursor User/settings.json + Keychain"),
    AgentMeta("vscode-copilot", "VS Code GitHub Copilot BYOK (GUI)", "gui", "native", "Native Custom Endpoint (chatLanguageModels.json)", "Code/User/chatLanguageModels.json"),
    AgentMeta("codex-cli", "OpenAI Codex CLI", "cli", "native", "OpenAI terminal coding agent (config.toml)", "~/.codex/config.toml"),
    AgentMeta("codex-desktop", "Codex Desktop (GUI)", "gui", "native", "Codex desktop app + local proxy & env config", "~/.codex/config.toml"),
    AgentMeta("aider", "Aider (CLI)", "cli", "native", "Git-aware AI pair programming CLI (.aider.conf.yml)", "~/.aider.conf.yml"),
    AgentMeta("zed", "Zed Editor (GUI)", "gui", "native", "Zed AI assistant OpenAI-compatible provider", "~/.config/zed/settings.json"),
    AgentMeta("continue", "Continue (VS Code / JetBrains GUI)", "gui", "native", "Open-source IDE assistant (~/.continue/config.yaml)", "~/.continue/config.yaml"),
    AgentMeta("goose", "Goose (CLI & Desktop GUI)", "gui", "native", "Block's open-source AI agent (~/.config/goose/config.yaml)", "~/.config/goose/config.yaml"),
    AgentMeta("claude-desktop", "Claude Desktop (GUI — Proxy & MCP)", "desktop", "proxy+mcp", "Developer Third-Party Inference + local proxy + MCP model bridge", "Claude/claude_desktop_config.json"),
    AgentMeta("chatgpt-desktop", "ChatGPT Desktop & Desktop Proxy (GUI)", "desktop", "proxy+mcp", "Local OpenAI proxy + Codex provider + open desktop GUI guide", "~/.agent-bridge/proxy.json"),
    AgentMeta("shell-env", "Shell Environment (~/.zshrc / ~/.bashrc)", "system", "native", "Managed env exports for all CLI tools & SDKs", "~/.zshrc / ~/.bashrc"),
]

AGENT_MAP: dict[str, AgentMeta] = {a.id: a for a in AGENTS}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def os_name() -> str:
    return plat.os_name()


def vscode_user_dir(insiders: bool = False) -> Path:
    return plat.vscode_user_dir(insiders)


def cursor_user_dir() -> Path:
    return plat.cursor_user_dir()


def claude_desktop_dir() -> Path:
    return plat.claude_desktop_dir()


def detect_shell_rc() -> Path:
    return plat.detect_shell_rc()


class BackupManager:
    """Backs up files before modification and supports clean rollback."""

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.base_dir = plat.bridge_dir() / "backups"
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.session_dir = self.base_dir / self.session_id
        self.manifest: list[dict[str, str]] = []
        self._backed_up: set[str] = set()

    def backup(self, path: Path) -> None:
        if self.dry_run or not path.exists():
            return
        key = str(path.resolve())
        if key in self._backed_up:
            return
        self._backed_up.add(key)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{len(self.manifest):02d}_{path.name}"
        dest = self.session_dir / safe_name
        shutil.copy2(path, dest)
        self.manifest.append({"original": str(path), "backup": str(dest)})
        (self.session_dir / "manifest.json").write_text(
            json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8"
        )

    @staticmethod
    def list_sessions() -> list[Path]:
        base = plat.bridge_dir() / "backups"
        if not base.exists():
            return []
        return sorted([p for p in base.iterdir() if p.is_dir() and (p / "manifest.json").exists()], reverse=True)

    @staticmethod
    def restore_session(session_dir: Path) -> list[str]:
        manifest_path = session_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"No manifest found in {session_dir}")
        entries = json.loads(manifest_path.read_text(encoding="utf-8"))
        restored: list[str] = []
        for entry in entries:
            orig = Path(entry["original"])
            bak = Path(entry["backup"])
            if bak.exists():
                orig.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bak, orig)
                restored.append(str(orig))
        return restored


def _read_json_safe(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return default
    # Strip basic // comments if JSONC
    cleaned = re.sub(r"(?m)^\s*//.*$", "", raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return default


def _write_text(path: Path, content: str, backups: BackupManager) -> None:
    if backups.dry_run:
        return
    backups.backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, data: Any, backups: BackupManager) -> None:
    _write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n", backups)


def _upsert_managed_block(path: Path, marker: str, body: str, backups: BackupManager) -> None:
    start_tag = f"# >>> {marker} >>>"
    end_tag = f"# <<< {marker} <<<"
    block = f"{start_tag}\n{body.rstrip()}\n{end_tag}\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(rf"{re.escape(start_tag)}.*?{re.escape(end_tag)}\n?", re.DOTALL)
    if pattern.search(existing):
        updated = pattern.sub(block, existing)
    else:
        sep = "\n" if existing and not existing.endswith("\n") else ""
        updated = existing + sep + ("\n" if existing else "") + block
    _write_text(path, updated, backups)


def _ensure_models_list(provider: ResolvedProvider) -> list[ModelSpec]:
    models = list(provider.models)
    existing_ids = {m.id for m in models}
    if provider.model and provider.model not in existing_ids:
        models.insert(0, ModelSpec(provider.model, f"{provider.model} ({provider.name})"))
    if provider.anthropic_model and provider.anthropic_model not in {m.id for m in models}:
        models.append(ModelSpec(provider.anthropic_model, f"{provider.anthropic_model} ({provider.name})"))
    return models


def _write_proxy_config(provider: ResolvedProvider, backups: BackupManager) -> list[str]:
    proxy_cfg_path = plat.bridge_dir() / "proxy.json"
    proxy_data = {
        "provider_id": provider.id,
        "provider_name": provider.name,
        "openai_base_url": provider.openai_base_url,
        "anthropic_base_url": provider.anthropic_base_url,
        "api_key": provider.effective_api_key,
        "default_model": provider.model,
        "anthropic_model": provider.anthropic_model,
        "force_model": "",
        "host": "127.0.0.1",
        "port": 4789,
    }
    _write_json(proxy_cfg_path, proxy_data, backups)

    launcher_path = plat.proxy_launcher_path()
    proxy_script = repo_root() / "lib" / "desktop_proxy.py"
    launcher = plat.proxy_launcher_content(sys.executable or "python3", proxy_script, proxy_cfg_path)
    _write_text(launcher_path, launcher, backups)
    if not plat.is_windows() and not backups.dry_run and launcher_path.exists():
        os.chmod(launcher_path, 0o755)
    return [str(proxy_cfg_path), str(launcher_path)]


# ---------------------------------------------------------------------------
# Individual Agent Configurators
# ---------------------------------------------------------------------------


def configure_opencode(provider: ResolvedProvider, backups: BackupManager, desktop: bool = False) -> ConfigResult:
    agent_id = "opencode-desktop" if desktop else "opencode-cli"
    agent_name = AGENT_MAP[agent_id].name
    cfg_path = plat.opencode_config_path()
    data = _read_json_safe(cfg_path, {})
    if not isinstance(data, dict):
        data = {}

    data.setdefault("$schema", "https://opencode.ai/config.json")
    models = _ensure_models_list(provider)
    model_map = {m.id: {"name": m.name} for m in models}

    # OpenCode V2 schema (`providers` + `package` + `settings`)
    providers_block = data.get("providers")
    if not isinstance(providers_block, dict):
        providers_block = {}
    providers_block[provider.id] = {
        "package": "@ai-sdk/openai-compatible",
        "name": provider.name,
        "settings": {
            "baseURL": provider.openai_base_url,
            "apiKey": f"{{env:{provider.env_var}}}" if provider.requires_key else "sk-no-auth-required",
        },
        "models": model_map,
    }
    data["providers"] = providers_block
    data["model"] = f"{provider.id}/{provider.model}"

    _write_json(cfg_path, data, backups)
    files = [str(cfg_path)]

    # Also store credential in OpenCode's auth.json so OpenCode Desktop (GUI) works without shell env
    auth_path = plat.opencode_auth_path()
    auth_data = _read_json_safe(auth_path, {})
    if not isinstance(auth_data, dict):
        auth_data = {}
    auth_data[provider.id] = {"type": "api", "key": provider.effective_api_key}
    _write_json(auth_path, auth_data, backups)
    files.append(str(auth_path))

    notes = [
        f"Default model set to `{provider.id}/{provider.model}`.",
        "OpenCode CLI, TUI, and OpenCode Desktop all share `~/.config/opencode/opencode.json`.",
        "Run `opencode debug config` or `/models` inside OpenCode to verify.",
    ]
    if desktop:
        notes.append("Credentials were also written to `~/.local/share/opencode/auth.json` so OpenCode Desktop GUI picks them up immediately.")
    return ConfigResult(agent_id, agent_name, True, files, notes)


def configure_claude_code(provider: ResolvedProvider, backups: BackupManager, gui: bool = False) -> ConfigResult:
    agent_id = "claude-code-gui" if gui else "claude-code-cli"
    agent_name = AGENT_MAP[agent_id].name
    settings_path = plat.claude_code_settings_path()
    data = _read_json_safe(settings_path, {})
    if not isinstance(data, dict):
        data = {}

    files: list[str] = []
    notes: list[str] = []

    if provider.anthropic_base_url:
        base_url = provider.anthropic_base_url.rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        model_id = provider.anthropic_model or provider.model
    else:
        # Provider is OpenAI-only -> configure local Anthropic-to-OpenAI bridge proxy
        files.extend(_write_proxy_config(provider, backups))
        base_url = "http://127.0.0.1:4789"
        model_id = provider.model
        notes.append(
            f"{provider.name} is OpenAI-only; Agent Bridge configured the local Anthropic↔OpenAI proxy at `{base_url}`."
        )
        notes.append(f"Start the proxy before running Claude Code: `{plat.proxy_start_command()}`")

    env_block = data.get("env")
    if not isinstance(env_block, dict):
        env_block = {}
    env_block["ANTHROPIC_BASE_URL"] = base_url
    env_block["ANTHROPIC_AUTH_TOKEN"] = provider.effective_api_key
    env_block["ANTHROPIC_MODEL"] = model_id
    # Remove conflicting ANTHROPIC_API_KEY so gateways receive Authorization: Bearer cleanly
    env_block.pop("ANTHROPIC_API_KEY", None)
    data["env"] = env_block

    _write_json(settings_path, data, backups)
    files.append(str(settings_path))

    if gui:
        # Also write claudeCode.environmentVariables into VS Code & Cursor settings.json
        ide_targets = [("VS Code", vscode_user_dir() / "settings.json"), ("Cursor", cursor_user_dir() / "settings.json")]
        for ide_name, ide_settings in ide_targets:
            if ide_settings.parent.exists() or ide_name == "VS Code":
                ide_data = _read_json_safe(ide_settings, {})
                if not isinstance(ide_data, dict):
                    ide_data = {}
                ide_data["claudeCode.environmentVariables"] = [
                    {"name": "ANTHROPIC_BASE_URL", "value": base_url},
                    {"name": "ANTHROPIC_AUTH_TOKEN", "value": provider.effective_api_key},
                    {"name": "ANTHROPIC_MODEL", "value": model_id},
                ]
                _write_json(ide_settings, ide_data, backups)
                files.append(str(ide_settings))
        notes.append("Configured `claudeCode.environmentVariables` for VS Code / Cursor Claude Code GUI extensions.")

    notes.append(f"`ANTHROPIC_BASE_URL` set to `{base_url}` (no trailing `/v1` — Claude Code appends `/v1/messages`).")
    notes.append("If you previously logged in with a claude.ai account, run `claude logout` first, then check `/status`.")
    return ConfigResult(agent_id, agent_name, True, files, notes)


def configure_pi(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    pi_dir = plat.pi_agent_dir()
    models_path = pi_dir / "models.json"
    settings_path = pi_dir / "settings.json"

    data = _read_json_safe(models_path, {})
    if not isinstance(data, dict):
        data = {}
    data.setdefault("$schema", "https://pi.dev/schemas/models.schema.json")
    providers_block = data.get("providers")
    if not isinstance(providers_block, dict):
        providers_block = {}

    models = _ensure_models_list(provider)
    providers_block[provider.id] = {
        "name": provider.name,
        "baseUrl": provider.openai_base_url,
        "api": "openai-completions",
        "apiKey": f"${provider.env_var}" if provider.requires_key else "sk-no-auth-required",
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "contextWindow": m.context_window,
                "maxTokens": m.max_tokens,
                "reasoning": m.reasoning,
                "input": ["text", "image"] if m.vision else ["text"],
            }
            for m in models
        ],
    }
    data["providers"] = providers_block
    _write_json(models_path, data, backups)

    settings = _read_json_safe(settings_path, {})
    if not isinstance(settings, dict):
        settings = {}
    settings["defaultProvider"] = provider.id
    settings["defaultModel"] = provider.model
    _write_json(settings_path, settings, backups)

    notes = [
        f"Added `{provider.id}` with {len(models)} model(s) to `~/.pi/agent/models.json`.",
        f"Set default provider/model in `~/.pi/agent/settings.json` to `{provider.id}` / `{provider.model}`.",
        f"Make sure `{provider.env_var}` is exported in your shell (selecting Shell Environment does this automatically).",
        "Pi hot-reloads `models.json` whenever you press `Ctrl+L` or run `/model`.",
    ]
    return ConfigResult("pi", AGENT_MAP["pi"].name, True, [str(models_path), str(settings_path)], notes)


def configure_cursor(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    settings_path = cursor_user_dir() / "settings.json"
    data = _read_json_safe(settings_path, {})
    if not isinstance(data, dict):
        data = {}

    # Inject provider env into Cursor's integrated terminal (for Cursor Agent CLI, Claude Code, etc.)
    env_key = {
        "macos": "terminal.integrated.env.osx",
        "linux": "terminal.integrated.env.linux",
        "windows": "terminal.integrated.env.windows",
    }[os_name()]
    term_env = data.get(env_key)
    if not isinstance(term_env, dict):
        term_env = {}
    term_env["OPENAI_BASE_URL"] = provider.openai_base_url
    term_env["OPENAI_API_KEY"] = provider.effective_api_key
    term_env[provider.env_var] = provider.effective_api_key
    if provider.anthropic_base_url:
        term_env["ANTHROPIC_BASE_URL"] = provider.anthropic_base_url
        term_env["ANTHROPIC_AUTH_TOKEN"] = provider.effective_api_key
    data[env_key] = term_env
    _write_json(settings_path, data, backups)

    guide_path = plat.bridge_dir() / "cursor-setup.txt"
    guide_text = (
        f"Cursor IDE GUI Configuration ({provider.name})\n"
        f"=============================================\n"
        f"Cursor stores BYOK API keys in your OS Keychain, so paste these once in the UI:\n\n"
        f"1. Open Cursor Settings (Cmd+, on macOS / Ctrl+, on Linux & Windows)\n"
        f"2. Go to Models -> API Keys\n"
        f"3. Enable 'OpenAI API Key' and paste your {provider.name} API key\n"
        f"4. Enable 'Override OpenAI Base URL' and enter:\n"
        f"   {provider.openai_base_url}\n"
        f"5. Add/enable model ID: {provider.model}\n\n"
        f"Tip: If Cursor's input box ignores clicks, toggle the switch ON, click near the box, and press Tab.\n"
    )
    _write_text(guide_path, guide_text, backups)

    notes = [
        "Updated Cursor integrated terminal environment variables in `Cursor/User/settings.json`.",
        f"Cursor GUI stores API keys in OS Keychain — open Cursor Settings -> Models -> API Keys and set Override OpenAI Base URL to `{provider.openai_base_url}`.",
        f"Saved step-by-step reference to `{guide_path}`.",
    ]
    return ConfigResult("cursor", AGENT_MAP["cursor"].name, True, [str(settings_path), str(guide_path)], notes)


def configure_vscode_copilot(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    files: list[str] = []
    targets = [vscode_user_dir(insiders=False)]
    insiders_dir = vscode_user_dir(insiders=True)
    if insiders_dir.exists():
        targets.append(insiders_dir)

    models = _ensure_models_list(provider)
    chat_url = provider.openai_base_url.rstrip("/") + "/chat/completions"

    entry = {
        "name": f"{provider.name} (Agent Bridge)",
        "vendor": "customendpoint",
        "apiKey": f"${{env:{provider.env_var}}}" if provider.requires_key else "sk-no-auth-required",
        "apiType": "chat-completions",
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "url": chat_url,
                "toolCalling": True,
                "vision": m.vision,
                "maxInputTokens": m.context_window,
                "maxOutputTokens": m.max_tokens,
            }
            for m in models
        ],
    }

    for user_dir in targets:
        lm_path = user_dir / "chatLanguageModels.json"
        existing = _read_json_safe(lm_path, [])
        if not isinstance(existing, list):
            existing = []
        # Replace previous entry with the same name if present
        existing = [item for item in existing if not (isinstance(item, dict) and item.get("name") == entry["name"])]
        existing.append(entry)
        _write_json(lm_path, existing, backups)
        files.append(str(lm_path))

    notes = [
        f"Added `{entry['name']}` with {len(models)} model(s) (`toolCalling: true`) to `chatLanguageModels.json`.",
        f"Endpoint URL: `{chat_url}`.",
        "Restart VS Code, open Command Palette -> `Chat: Manage Language Models`, and verify your models appear in Copilot Chat & Agent mode.",
    ]
    return ConfigResult("vscode-copilot", AGENT_MAP["vscode-copilot"].name, True, files, notes)


def _upsert_codex_toml(toml_path: Path, provider: ResolvedProvider, backups: BackupManager) -> None:
    provider_key = re.sub(r"[^a-zA-Z0-9_]", "_", provider.id)
    section_header = f"[model_providers.{provider_key}]"
    new_block = (
        f"{section_header}\n"
        f'name = "{provider.name}"\n'
        f'base_url = "{provider.openai_base_url}"\n'
        f'wire_api = "responses"\n'
        f'env_key = "{provider.env_var}"\n'
    )

    existing = toml_path.read_text(encoding="utf-8") if toml_path.exists() else ""
    lines = existing.splitlines()

    # Update or insert top-level model & model_provider
    def set_top_key(text_lines: list[str], key: str, value: str) -> list[str]:
        pat = re.compile(rf"^\s*{re.escape(key)}\s*=")
        for idx, line in enumerate(text_lines):
            if line.strip().startswith("["):
                # Reached first table without finding top-level key
                text_lines.insert(idx, f'{key} = "{value}"')
                return text_lines
            if pat.match(line):
                text_lines[idx] = f'{key} = "{value}"'
                return text_lines
        text_lines.insert(0, f'{key} = "{value}"')
        return text_lines

    lines = set_top_key(lines, "model", provider.model)
    lines = set_top_key(lines, "model_provider", provider_key)
    updated = "\n".join(lines).rstrip() + "\n"

    # Replace existing [model_providers.<provider_key>] section if present
    sec_pat = re.compile(
        rf"(?ms)^{re.escape(section_header)}\n.*?(?=^\[|\Z)"
    )
    if sec_pat.search(updated):
        updated = sec_pat.sub(new_block + "\n", updated)
    else:
        updated = updated + "\n" + new_block

    _write_text(toml_path, updated, backups)


def configure_codex(provider: ResolvedProvider, backups: BackupManager, desktop: bool = False) -> ConfigResult:
    agent_id = "codex-desktop" if desktop else "codex-cli"
    agent_name = AGENT_MAP[agent_id].name
    toml_path = plat.codex_config_path()
    _upsert_codex_toml(toml_path, provider, backups)
    files = [str(toml_path)]
    notes = [
        f"Configured `[model_providers.{re.sub(r'[^a-zA-Z0-9_]', '_', provider.id)}]` in `~/.codex/config.toml`.",
        f"Make sure `{provider.env_var}` is exported in your shell environment.",
    ]
    if desktop:
        files.extend(_write_proxy_config(provider, backups))
        notes.append("Desktop GUI apps inherit env vars from the session that launched them — start Codex Desktop from a terminal with the key exported, or set it as a user environment variable (`setx`).")
    return ConfigResult(agent_id, agent_name, True, files, notes)


def configure_aider(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    conf_path = plat.aider_config_path()
    body = (
        f"openai-api-base: {provider.openai_base_url}\n"
        f"openai-api-key: {provider.effective_api_key}\n"
        f"model: openai/{provider.model}\n"
    )
    _upsert_managed_block(conf_path, "agent-bridge-aider", body, backups)
    notes = [
        f"Configured Aider to use `openai/{provider.model}` via `{provider.openai_base_url}`.",
        "Run `aider` in any git repository to start coding.",
    ]
    return ConfigResult("aider", AGENT_MAP["aider"].name, True, [str(conf_path)], notes)


def configure_zed(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    settings_path = plat.zed_settings_path()
    data = _read_json_safe(settings_path, {})
    if not isinstance(data, dict):
        data = {}

    lm = data.get("language_models")
    if not isinstance(lm, dict):
        lm = {}
    oa_compat = lm.get("openai_compatible")
    if not isinstance(oa_compat, dict):
        oa_compat = {}

    models = _ensure_models_list(provider)
    oa_compat[provider.name] = {
        "api_url": provider.openai_base_url,
        "available_models": [
            {
                "name": m.id,
                "display_name": m.name,
                "max_tokens": m.context_window,
                "max_output_tokens": m.max_tokens,
            }
            for m in models
        ],
    }
    lm["openai_compatible"] = oa_compat
    data["language_models"] = lm
    _write_json(settings_path, data, backups)

    notes = [
        f"Added `{provider.name}` under `language_models.openai_compatible` in `~/.config/zed/settings.json`.",
        "Open Zed Agent Panel -> Settings and enter your API key once (or export `OPENAI_API_KEY`).",
    ]
    return ConfigResult("zed", AGENT_MAP["zed"].name, True, [str(settings_path)], notes)


def configure_continue(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    cfg_path = plat.continue_config_path()
    models = _ensure_models_list(provider)
    lines = [
        "name: Agent Bridge Config",
        "version: 1.0.0",
        "schema: v1",
        "models:",
    ]
    for m in models[:4]:
        lines.extend(
            [
                f"  - name: {m.name}",
                "    provider: openai",
                f"    model: {m.id}",
                f"    apiBase: {provider.openai_base_url}",
                f"    apiKey: {provider.effective_api_key}",
                "    roles:",
                "      - chat",
                "      - edit",
                "      - apply",
            ]
        )
    _write_text(cfg_path, "\n".join(lines) + "\n", backups)
    notes = [
        f"Wrote Continue config with {min(len(models), 4)} model(s) to `~/.continue/config.yaml`.",
        "Works in both VS Code and JetBrains Continue extensions.",
    ]
    return ConfigResult("continue", AGENT_MAP["continue"].name, True, [str(cfg_path)], notes)


def configure_goose(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    cfg_path = plat.goose_config_path()
    parsed = urlparse(provider.openai_base_url)
    host = f"{parsed.scheme}://{parsed.netloc}"
    base_path = (parsed.path.rstrip("/") + "/chat/completions").lstrip("/")
    body = (
        "GOOSE_PROVIDER: openai\n"
        f"GOOSE_MODEL: {provider.model}\n"
        f"OPENAI_HOST: {host}\n"
        f"OPENAI_BASE_PATH: {base_path}\n"
    )
    _upsert_managed_block(cfg_path, "agent-bridge-goose", body, backups)
    notes = [
        f"Configured Goose CLI & Desktop (`OPENAI_HOST: {host}`, `OPENAI_BASE_PATH: {base_path}`).",
        "Make sure `OPENAI_API_KEY` is exported in your shell environment.",
    ]
    return ConfigResult("goose", AGENT_MAP["goose"].name, True, [str(cfg_path)], notes)


def configure_claude_desktop(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    cdir = claude_desktop_dir()
    files: list[str] = []
    files.extend(_write_proxy_config(provider, backups))

    # 1. Unlock Developer Mode (Third-Party Inference menu)
    dev_path = cdir / "developer_settings.json"
    dev_data = _read_json_safe(dev_path, {})
    if not isinstance(dev_data, dict):
        dev_data = {}
    dev_data["allowDevTools"] = True
    _write_json(dev_path, dev_data, backups)
    files.append(str(dev_path))

    # 2. Register zero-dependency MCP custom-model bridge in claude_desktop_config.json
    mcp_path = cdir / "claude_desktop_config.json"
    mcp_data = _read_json_safe(mcp_path, {})
    if not isinstance(mcp_data, dict):
        mcp_data = {}
    servers = mcp_data.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
    mcp_script = str(repo_root() / "lib" / "mcp_model_bridge.py")
    proxy_cfg = str(plat.bridge_dir() / "proxy.json")
    servers["agent-bridge-models"] = {
        "command": sys.executable or "python3",
        "args": [mcp_script],
        "env": {
            "AGENT_BRIDGE_MCP_CONFIG": proxy_cfg,
        },
    }
    mcp_data["mcpServers"] = servers
    _write_json(mcp_path, mcp_data, backups)
    files.append(str(mcp_path))

    inference_url = provider.anthropic_base_url or "http://127.0.0.1:4789"
    notes = [
        "1) MCP Model Bridge registered in `claude_desktop_config.json` (`ask_custom_model`, `list_custom_models`). Restart Claude Desktop to query your custom provider directly in any chat!",
        f"2) Developer Mode enabled (`developer_settings.json`). In Claude Desktop go to Developer -> Configure Third-Party Inference and set Base URL to `{inference_url}`.",
        f"3) If using an OpenAI-only provider or model remapping, run `{plat.proxy_start_command()}` to start the local Anthropic↔OpenAI bridge on `http://127.0.0.1:4789`.",
    ]
    return ConfigResult("claude-desktop", AGENT_MAP["claude-desktop"].name, True, files, notes)


def configure_chatgpt_desktop(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    files = _write_proxy_config(provider, backups)
    toml_path = plat.codex_config_path()
    _upsert_codex_toml(toml_path, provider, backups)
    files.append(str(toml_path))

    guide_path = plat.bridge_dir() / "chatgpt-desktop-guide.txt"
    guide = (
        f"ChatGPT Desktop & Custom OpenAI Desktop Setup ({provider.name})\n"
        f"================================================================\n"
        f"Provider Base URL : {provider.openai_base_url}\n"
        f"Default Model     : {provider.model}\n"
        f"Local Bridge Proxy: http://127.0.0.1:4789/v1  (run {plat.proxy_start_command()})\n\n"
        f"Important Note on Consumer ChatGPT Desktop:\n"
        f"- Official consumer ChatGPT Desktop hard-pins chatgpt.com endpoints.\n"
        f"- Developer / Codex Desktop builds read `~/.codex/config.toml` (already configured!).\n"
        f"- For a full native ChatGPT-style Desktop GUI with custom Base URL + API Key, install\n"
        f"  Cherry Studio, Chatbox, or Jan via the agent installer and point it to:\n"
        f"    Base URL: {provider.openai_base_url}\n"
        f"    Model   : {provider.model}\n"
    )
    _write_text(guide_path, guide, backups)
    files.append(str(guide_path))

    notes = [
        "Configured `~/.codex/config.toml` for ChatGPT/Codex developer desktop builds.",
        f"Generated local OpenAI proxy launcher (`{plat.proxy_launcher_path()}`) on `http://127.0.0.1:4789/v1`.",
        "Note: Standard consumer ChatGPT Desktop pins `chatgpt.com`. For a 100% native custom-API Desktop GUI, install Cherry Studio, Chatbox, or Jan via the agent installer.",
    ]
    return ConfigResult("chatgpt-desktop", AGENT_MAP["chatgpt-desktop"].name, True, files, notes)


def configure_shell_env(provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    rc_path = detect_shell_rc()
    if plat.shell_env_style() == "powershell":
        lines = [
            f'$env:AGENT_BRIDGE_PROVIDER = "{provider.id}"',
            f'$env:{provider.env_var} = "{provider.effective_api_key}"',
            f'$env:OPENAI_BASE_URL = "{provider.openai_base_url}"',
            f'$env:OPENAI_API_KEY = "{provider.effective_api_key}"',
        ]
        if provider.anthropic_base_url:
            lines.append(f'$env:ANTHROPIC_BASE_URL = "{provider.anthropic_base_url}"')
            lines.append(f'$env:ANTHROPIC_AUTH_TOKEN = "{provider.effective_api_key}"')
        else:
            # Local proxy handles Anthropic<->OpenAI translation; point Claude tools at it.
            lines.append('$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:4789"')
            lines.append(f'$env:ANTHROPIC_AUTH_TOKEN = "{provider.effective_api_key}"')
        lines.append("Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue")
    else:
        lines = [
            f'export AGENT_BRIDGE_PROVIDER="{provider.id}"',
            f'export {provider.env_var}="{provider.effective_api_key}"',
            f'export OPENAI_BASE_URL="{provider.openai_base_url}"',
            f'export OPENAI_API_KEY="{provider.effective_api_key}"',
        ]
        if provider.anthropic_base_url:
            lines.append(f'export ANTHROPIC_BASE_URL="{provider.anthropic_base_url}"')
            lines.append(f'export ANTHROPIC_AUTH_TOKEN="{provider.effective_api_key}"')
        lines.append("unset ANTHROPIC_API_KEY")
    _upsert_managed_block(rc_path, "agent-bridge", "\n".join(lines), backups)
    notes = [
        f"Updated managed `# >>> agent-bridge >>>` block in `{rc_path}`.",
        plat.source_hint(rc_path),
    ]
    return ConfigResult("shell-env", AGENT_MAP["shell-env"].name, True, [str(rc_path)], notes)


CONFIGURATOR_DISPATCH: dict[str, Callable[[ResolvedProvider, BackupManager], ConfigResult]] = {
    "opencode-cli": lambda p, b: configure_opencode(p, b, desktop=False),
    "opencode-desktop": lambda p, b: configure_opencode(p, b, desktop=True),
    "claude-code-cli": lambda p, b: configure_claude_code(p, b, gui=False),
    "claude-code-gui": lambda p, b: configure_claude_code(p, b, gui=True),
    "pi": configure_pi,
    "cursor": configure_cursor,
    "vscode-copilot": configure_vscode_copilot,
    "codex-cli": lambda p, b: configure_codex(p, b, desktop=False),
    "codex-desktop": lambda p, b: configure_codex(p, b, desktop=True),
    "aider": configure_aider,
    "zed": configure_zed,
    "continue": configure_continue,
    "goose": configure_goose,
    "claude-desktop": configure_claude_desktop,
    "chatgpt-desktop": configure_chatgpt_desktop,
    "shell-env": configure_shell_env,
}


def run_configurator(agent_id: str, provider: ResolvedProvider, backups: BackupManager) -> ConfigResult:
    fn = CONFIGURATOR_DISPATCH.get(agent_id)
    if not fn:
        return ConfigResult(agent_id, agent_id, False, error=f"Unknown agent: {agent_id}")
    try:
        return fn(provider, backups)
    except Exception as exc:
        meta = AGENT_MAP.get(agent_id)
        return ConfigResult(agent_id, meta.name if meta else agent_id, False, error=str(exc))

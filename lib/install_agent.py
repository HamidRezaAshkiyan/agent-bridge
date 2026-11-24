#!/usr/bin/env python3
"""Interactive coding agent & AI desktop app installer with automatic provider setup handoff."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib import __version__, platform_support as plat, ui


@dataclass
class InstallableAgent:
    id: str
    name: str
    category: str       # "cli" | "gui" | "chat-gui"
    summary: str
    config_agent_id: str  # Maps to lib/configurators.py agent ID (or "")
    binary_check: str = ""
    macos_app: str = ""
    windows_app: str = ""
    npm_pkg: str = ""
    brew_formula: str = ""
    brew_cask: str = ""
    uv_tool: str = ""
    pip_pkg: str = ""
    curl_cmd: str = ""
    winget_id: str = ""
    download_url: str = ""


CATALOG: list[InstallableAgent] = [
    # --- CLI Coding Agents ---
    InstallableAgent(
        id="claude-code",
        name="Claude Code (CLI)",
        category="cli",
        summary="Anthropic's official agentic coding CLI",
        config_agent_id="claude-code-cli",
        binary_check="claude",
        npm_pkg="@anthropic-ai/claude-code",
        curl_cmd="curl -fsSL https://claude.ai/install.sh | bash",
        winget_id="Anthropic.ClaudeCode",
        download_url="https://docs.anthropic.com/en/docs/claude-code",
    ),
    InstallableAgent(
        id="opencode-cli",
        name="OpenCode (CLI / TUI)",
        category="cli",
        summary="Open-source terminal coding agent with multi-provider support",
        config_agent_id="opencode-cli",
        binary_check="opencode",
        brew_formula="opencode",
        npm_pkg="opencode-ai",
        curl_cmd="curl -fsSL https://opencode.ai/install | bash",
        winget_id="Anomaly.OpenCode",
        download_url="https://opencode.ai",
    ),
    InstallableAgent(
        id="pi",
        name="Pi Coding Agent (CLI)",
        category="cli",
        summary="Minimal, extensible coding agent by Mario Zechner",
        config_agent_id="pi",
        binary_check="pi",
        npm_pkg="@mariozechner/pi-coding-agent",
        download_url="https://pi.dev",
    ),
    InstallableAgent(
        id="codex-cli",
        name="OpenAI Codex (CLI)",
        category="cli",
        summary="OpenAI's lightweight terminal coding agent",
        config_agent_id="codex-cli",
        binary_check="codex",
        npm_pkg="@openai/codex",
        brew_formula="codex",
        winget_id="OpenAI.Codex",
        download_url="https://github.com/openai/codex",
    ),
    InstallableAgent(
        id="aider",
        name="Aider (CLI)",
        category="cli",
        summary="Git-integrated AI pair programmer in your terminal",
        config_agent_id="aider",
        binary_check="aider",
        uv_tool="aider-chat",
        pip_pkg="aider-chat",
        download_url="https://aider.chat",
    ),
    InstallableAgent(
        id="gemini-cli",
        name="Gemini CLI",
        category="cli",
        summary="Google's open-source terminal AI agent",
        config_agent_id="shell-env",
        binary_check="gemini",
        npm_pkg="@google/gemini-cli",
        brew_formula="gemini-cli",
        download_url="https://github.com/google-gemini/gemini-cli",
    ),
    InstallableAgent(
        id="goose-cli",
        name="Goose (CLI)",
        category="cli",
        summary="Block's extensible open-source developer agent",
        config_agent_id="goose",
        binary_check="goose",
        brew_formula="block-goose-cli",
        curl_cmd="curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash",
        winget_id="AgenticAIFoundation.gooseCLI",
        download_url="https://block.github.io/goose",
    ),
    # --- GUI IDEs & Desktop Coding Apps ---
    InstallableAgent(
        id="opencode-desktop",
        name="OpenCode Desktop (GUI)",
        category="gui",
        summary="Native desktop GUI for OpenCode",
        config_agent_id="opencode-desktop",
        macos_app="/Applications/OpenCode.app",
        windows_app="%LOCALAPPDATA%\\Programs\\opencode\\opencode.exe",
        brew_cask="opencode-desktop",
        winget_id="Anomaly.OpenCode.Desktop",
        download_url="https://opencode.ai/download",
    ),
    InstallableAgent(
        id="cursor",
        name="Cursor IDE (GUI)",
        category="gui",
        summary="AI-first code editor built on VS Code",
        config_agent_id="cursor",
        binary_check="cursor",
        macos_app="/Applications/Cursor.app",
        windows_app="%LOCALAPPDATA%\\Programs\\cursor\\Cursor.exe",
        brew_cask="cursor",
        winget_id="Anysphere.Cursor",
        download_url="https://cursor.com/downloads",
    ),
    InstallableAgent(
        id="vscode",
        name="Visual Studio Code (GUI)",
        category="gui",
        summary="VS Code with GitHub Copilot BYOK, Cline & Continue",
        config_agent_id="vscode-copilot",
        binary_check="code",
        macos_app="/Applications/Visual Studio Code.app",
        windows_app="%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe",
        brew_cask="visual-studio-code",
        winget_id="Microsoft.VisualStudioCode",
        download_url="https://code.visualstudio.com/download",
    ),
    InstallableAgent(
        id="zed",
        name="Zed Editor (GUI)",
        category="gui",
        summary="High-performance Rust editor with native AI agent panel",
        config_agent_id="zed",
        binary_check="zed",
        macos_app="/Applications/Zed.app",
        windows_app="%LOCALAPPDATA%\\Programs\\Zed\\zed.exe",
        brew_cask="zed",
        curl_cmd="curl -f https://zed.dev/install.sh | sh",
        winget_id="ZedIndustries.Zed",
        download_url="https://zed.dev/download",
    ),
    InstallableAgent(
        id="windsurf",
        name="Windsurf IDE (GUI)",
        category="gui",
        summary="Agentic IDE by Codeium",
        config_agent_id="shell-env",
        macos_app="/Applications/Windsurf.app",
        windows_app="%LOCALAPPDATA%\\Programs\\Windsurf\\Windsurf.exe",
        brew_cask="windsurf",
        winget_id="Codeium.Windsurf",
        download_url="https://codeium.com/windsurf/download",
    ),
    InstallableAgent(
        id="claude-desktop",
        name="Claude Desktop (GUI)",
        category="gui",
        summary="Anthropic desktop app (+ Agent Bridge MCP & Third-Party Inference)",
        config_agent_id="claude-desktop",
        macos_app="/Applications/Claude.app",
        windows_app="%LOCALAPPDATA%\\AnthropicClaude\\claude.exe",
        brew_cask="claude",
        winget_id="Anthropic.Claude",
        download_url="https://claude.ai/download",
    ),
    InstallableAgent(
        id="chatgpt-desktop",
        name="ChatGPT Desktop (GUI)",
        category="gui",
        summary="OpenAI desktop app",
        config_agent_id="chatgpt-desktop",
        macos_app="/Applications/ChatGPT.app",
        windows_app="%LOCALAPPDATA%\\Programs\\ChatGPT\\ChatGPT.exe",
        brew_cask="chatgpt",
        winget_id="OpenAI.ChatGPT",
        download_url="https://openai.com/chatgpt/desktop",
    ),
    # --- Native Custom-API Open-Source Desktop Chat GUIs ---
    InstallableAgent(
        id="cherry-studio",
        name="Cherry Studio (Open-Source Chat GUI)",
        category="chat-gui",
        summary="Beautiful desktop AI client with 100% native custom Base URL & API key",
        config_agent_id="chatgpt-desktop",
        macos_app="/Applications/Cherry Studio.app",
        windows_app="%LOCALAPPDATA%\\Programs\\Cherry Studio\\Cherry Studio.exe",
        brew_cask="cherry-studio",
        winget_id="kangfenmao.CherryStudio",
        download_url="https://cherry-ai.com/download",
    ),
    InstallableAgent(
        id="chatbox",
        name="Chatbox (Open-Source Chat GUI)",
        category="chat-gui",
        summary="Cross-platform desktop GUI for Metis, AvalAI, OpenAI & Claude APIs",
        config_agent_id="chatgpt-desktop",
        macos_app="/Applications/chatbox.app",
        windows_app="%LOCALAPPDATA%\\Programs\\Chatbox\\Chatbox.exe",
        brew_cask="chatbox",
        winget_id="Bin-Huang.Chatbox",
        download_url="https://chatboxai.app",
    ),
    InstallableAgent(
        id="jan",
        name="Jan (Open-Source Local + API Chat GUI)",
        category="chat-gui",
        summary="Offline-first ChatGPT alternative supporting custom remote APIs",
        config_agent_id="chatgpt-desktop",
        macos_app="/Applications/Jan.app",
        windows_app="%LOCALAPPDATA%\\Programs\\Jan\\Jan.exe",
        brew_cask="jan",
        winget_id="Jan.Jan",
        download_url="https://jan.ai",
    ),
]

CATALOG_MAP = {a.id: a for a in CATALOG}


def expand_windows_path(raw: str) -> Path | None:
    """Expand a ``%VAR%``-style Windows app path into an absolute path."""
    if not raw:
        return None
    expanded = os.path.expandvars(raw)
    return Path(expanded)


def app_installed(agent: InstallableAgent) -> bool:
    """Check the OS-native application location for this agent."""
    if plat.is_macos() and agent.macos_app:
        return Path(agent.macos_app).exists()
    if plat.is_windows() and agent.windows_app:
        candidate = expand_windows_path(agent.windows_app)
        return bool(candidate and candidate.exists())
    return False


def detect_env() -> dict[str, bool | str]:
    return {
        "os": plat.os_name(),
        "brew": shutil.which("brew") is not None,
        "npm": shutil.which("npm") is not None,
        "pnpm": shutil.which("pnpm") is not None,
        "bun": shutil.which("bun") is not None,
        "uv": shutil.which("uv") is not None,
        "pipx": shutil.which("pipx") is not None,
        "pip3": shutil.which("pip3") is not None,
        "curl": shutil.which("curl") is not None,
        "winget": shutil.which("winget") is not None,
        "scoop": shutil.which("scoop") is not None,
        "choco": shutil.which("choco") is not None,
    }


def is_installed(agent: InstallableAgent) -> bool:
    if agent.binary_check and shutil.which(agent.binary_check):
        return True
    return app_installed(agent)


def choose_install_command(agent: InstallableAgent, env: dict[str, bool | str]) -> tuple[str, str]:
    """Return (method_label, shell_command) for the best available package manager."""
    os_id = env["os"]

    if os_id == "macos" and env["brew"]:
        if agent.brew_cask:
            return ("Homebrew Cask", f"brew install --cask {agent.brew_cask}")
        if agent.brew_formula:
            return ("Homebrew", f"brew install {agent.brew_formula}")

    if os_id == "windows":
        # winget is present on Windows 10 1809+ / Windows 11 by default and handles
        # both CLIs and desktop apps, so it is preferred over npm for GUI targets.
        if agent.winget_id and env["winget"]:
            return ("winget", f"winget install --id {agent.winget_id} -e --accept-source-agreements --accept-package-agreements")
        if agent.npm_pkg and env["npm"]:
            return ("npm", f"npm install -g {agent.npm_pkg}")
        if agent.pip_pkg and env["pipx"]:
            return ("pipx", f"pipx install {agent.pip_pkg}")
        if agent.pip_pkg and env["pip3"]:
            return ("pip3", f"pip3 install --user {agent.pip_pkg}")
        if agent.uv_tool and env["uv"]:
            return ("uv", f"uv tool install {agent.uv_tool}")
        return ("Manual Download", "")

    if agent.npm_pkg:
        if env["npm"]:
            return ("npm", f"npm install -g {agent.npm_pkg}")
        if env["pnpm"]:
            return ("pnpm", f"pnpm add -g {agent.npm_pkg}")
        if env["bun"]:
            return ("bun", f"bun add -g {agent.npm_pkg}")
    if agent.uv_tool and env["uv"]:
        return ("uv", f"uv tool install {agent.uv_tool}")
    if agent.pip_pkg and env["pipx"]:
        return ("pipx", f"pipx install {agent.pip_pkg}")
    if agent.pip_pkg and env["pip3"]:
        return ("pip3", f"pip3 install --user {agent.pip_pkg}")
    if agent.curl_cmd and env["curl"]:
        return ("Official Installer", agent.curl_cmd)
    if agent.brew_formula and env["brew"]:
        return ("Homebrew", f"brew install {agent.brew_formula}")
    return ("Manual Download", "")


def build_parser() -> argparse.ArgumentParser:
    prog = "install-agent.ps1" if plat.is_windows() else "install-agent.sh"
    p = argparse.ArgumentParser(
        prog=prog,
        description="Install your preferred CLI or GUI coding agent and configure it with your custom AI provider.",
    )
    p.add_argument("--agents", help="Comma-separated agent IDs to install (skip interactive menu)")
    p.add_argument("--list", action="store_true", help="List available agents with install status and exit")
    p.add_argument("--dry-run", action="store_true", help="Show install commands without executing them")
    p.add_argument("--no-configure", action="store_true", help="Skip offering to configure the provider after installation")
    p.add_argument("--version", action="version", version=f"agent-bridge {__version__}")
    return p


def cmd_list(env: dict[str, bool | str]) -> int:
    ui.section("Available Coding Agents & Desktop Apps")
    for ag in CATALOG:
        installed = is_installed(ag)
        status = f"{ui.C.GREEN}✓ Installed{ui.C.RESET}" if installed else f"{ui.C.GRAY}○ Not installed{ui.C.RESET}"
        method, cmd = choose_install_command(ag, env)
        print(f"  {ui.C.CYAN}{ag.id:<18}{ui.C.RESET} {status:<24} {ui.C.BOLD}{ag.name}{ui.C.RESET}")
        print(f"                     {ui.C.DIM}{ag.summary}{ui.C.RESET}")
        if cmd:
            print(f"                     {ui.C.GRAY}via {method}: {cmd}{ui.C.RESET}")
        elif ag.download_url:
            print(f"                     {ui.C.GRAY}Download: {ag.download_url}{ui.C.RESET}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    env = detect_env()

    if args.list:
        return cmd_list(env)

    ui.print_banner(
        f"Agent Bridge v{__version__} — Coding Agent Installer",
        "Install CLI & GUI coding agents, then wire them up to your custom API key",
    )

    tools_present = [k for k in ("brew", "winget", "scoop", "choco", "npm", "pnpm", "bun", "uv", "pipx", "curl") if env.get(k)]
    ui.info(f"Detected OS: {ui.C.BOLD}{env['os']}{ui.C.RESET} • Package managers: {', '.join(tools_present) or 'none'}")

    try:
        if args.agents:
            selected_ids = [a.strip() for a in args.agents.split(",") if a.strip()]
            bad = [a for a in selected_ids if a not in CATALOG_MAP]
            if bad:
                raise SystemExit(f"Unknown agent ID(s): {', '.join(bad)}. Run --list to view options.")
        else:
            items: list[tuple[str, str, str]] = []
            for ag in CATALOG:
                tag = "✓ installed" if is_installed(ag) else ag.category.upper()
                items.append((ag.id, f"{ag.name} ({tag})", ag.summary))
            selected_ids = ui.select_many(
                "Select coding agent(s) or desktop app(s) to install:",
                items,
                preselected=[],
            )

        plan: list[tuple[InstallableAgent, str, str]] = []
        ui.section("Installation Plan")
        for aid in selected_ids:
            ag = CATALOG_MAP[aid]
            method, cmd = choose_install_command(ag, env)
            plan.append((ag, method, cmd))
            if cmd:
                print(f"  {ui.C.CYAN}•{ui.C.RESET} {ui.C.BOLD}{ag.name}{ui.C.RESET} via {method}")
                print(f"    {ui.C.DIM}$ {cmd}{ui.C.RESET}")
            else:
                ui.warn(f"{ag.name}: no supported package manager found — download at {ag.download_url}")

        if args.dry_run:
            ui.warn("DRY RUN MODE — no commands were executed.")
            return 0

        if not args.agents and not ui.confirm("Proceed with installation?", default=True):
            ui.info("Cancelled.")
            return 0

        installed_config_targets: list[str] = []
        ui.section("Installing")
        for ag, method, cmd in plan:
            if not cmd:
                ui.info(f"Open {ag.download_url} to install {ag.name}.")
                continue
            ui.info(f"Installing {ui.C.BOLD}{ag.name}{ui.C.RESET} ({method})...")
            proc = subprocess.run(cmd, shell=True)
            if proc.returncode == 0:
                ui.success(f"{ag.name} installed successfully!")
                if ag.config_agent_id and ag.config_agent_id not in installed_config_targets:
                    installed_config_targets.append(ag.config_agent_id)
            else:
                ui.error(f"Failed to install {ag.name} (exit code {proc.returncode}).")
                if ag.download_url:
                    ui.info(f"Fallback manual download: {ag.download_url}")

        if not args.no_configure and installed_config_targets:
            print()
            ui.section("Configure with Your Custom AI Provider")
            if ui.confirm(
                f"Configure {', '.join(installed_config_targets)} with your custom API key & provider now?",
                default=True,
            ):
                if "shell-env" not in installed_config_targets:
                    installed_config_targets.append("shell-env")
                cfg_script = REPO_ROOT / "lib" / "configure.py"
                # Launch configure in-process successor; execv works on POSIX and Windows,
                # but subprocess keeps the return code explicit and works everywhere.
                proc = subprocess.run(
                    [sys.executable, str(cfg_script), "--agents", ",".join(installed_config_targets)]
                )
                return proc.returncode

        return 0

    except KeyboardInterrupt:
        print()
        ui.warn("Aborted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

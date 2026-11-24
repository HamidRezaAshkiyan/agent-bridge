"""Cross-platform primitives: OS detection, profile/config paths, console setup and launchers.

Everything platform-specific lives here so the configurators stay declarative and the
same code path works on macOS, Linux and Windows.

Path resolution rules that matter on Windows:

* Tools that follow the XDG layout (OpenCode, Pi, Codex, Aider, Continue) still use
  dot-directories under the user profile on Windows, so the POSIX path is correct there.
* Tools that use the native Windows layout (Zed, Goose) live under ``%APPDATA%``.
* Editor/desktop-app configs (VS Code, Cursor, Claude Desktop) live under ``%APPDATA%``
  and already have their own helpers.

``AGENT_BRIDGE_USER_HOME`` overrides the profile root. It exists so the test suite (and
sandboxed installs) can redirect writes without touching the real user profile.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


# ---------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------

def os_name() -> str:
    """Return ``"macos"``, ``"windows"`` or ``"linux"``."""
    sys_name = sys.platform
    if sys_name == "darwin":
        return "macos"
    if sys_name.startswith("win"):
        return "windows"
    return "linux"


def is_windows() -> bool:
    return os_name() == "windows"


def is_macos() -> bool:
    return os_name() == "macos"


def is_linux() -> bool:
    return os_name() == "linux"


# ---------------------------------------------------------------------------
# Profile & directory resolution
# ---------------------------------------------------------------------------

def home_dir() -> Path:
    """Profile root every configurator writes into.

    Honours ``AGENT_BRIDGE_USER_HOME`` so tests never leak into the real profile.
    """
    override = os.environ.get("AGENT_BRIDGE_USER_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home()


def appdata_dir() -> Path:
    """Roaming application data (``%APPDATA%`` on Windows, ``~/.config`` elsewhere)."""
    if is_windows():
        raw = os.environ.get("APPDATA", "").strip()
        return Path(raw) if raw else home_dir() / "AppData" / "Roaming"
    return home_dir() / ".config"


def localappdata_dir() -> Path:
    """Local application data (``%LOCALAPPDATA%`` on Windows, ``~/.local/share`` elsewhere)."""
    if is_windows():
        raw = os.environ.get("LOCALAPPDATA", "").strip()
        return Path(raw) if raw else home_dir() / "AppData" / "Local"
    return home_dir() / ".local" / "share"


def documents_dir() -> Path:
    if is_windows():
        return home_dir() / "Documents"
    return home_dir() / "Documents"


def bridge_dir() -> Path:
    """Agent Bridge's own state directory (backups, proxy config, guides)."""
    return home_dir() / ".agent-bridge"


# ---------------------------------------------------------------------------
# Per-tool config paths
# ---------------------------------------------------------------------------

def opencode_config_path() -> Path:
    # XDG-style layout on every OS, including Windows.
    return home_dir() / ".config" / "opencode" / "opencode.json"


def opencode_auth_path() -> Path:
    return home_dir() / ".local" / "share" / "opencode" / "auth.json"


def claude_code_settings_path() -> Path:
    return home_dir() / ".claude" / "settings.json"


def pi_agent_dir() -> Path:
    return home_dir() / ".pi" / "agent"


def codex_config_path() -> Path:
    return home_dir() / ".codex" / "config.toml"


def aider_config_path() -> Path:
    return home_dir() / ".aider.conf.yml"


def continue_config_path() -> Path:
    return home_dir() / ".continue" / "config.yaml"


def zed_settings_path() -> Path:
    # Zed stores its config under the native app-data dir on Windows.
    if is_windows():
        return appdata_dir() / "Zed" / "settings.json"
    return home_dir() / ".config" / "zed" / "settings.json"


def goose_config_path() -> Path:
    # Goose uses the native app-data dir on Windows, XDG config on macOS/Linux.
    if is_windows():
        return appdata_dir() / "Block" / "goose" / "config" / "config.yaml"
    return home_dir() / ".config" / "goose" / "config.yaml"


def vscode_user_dir(insiders: bool = False) -> Path:
    folder = "Code - Insiders" if insiders else "Code"
    if is_macos():
        return home_dir() / "Library" / "Application Support" / folder / "User"
    if is_windows():
        return appdata_dir() / folder / "User"
    return home_dir() / ".config" / folder / "User"


def cursor_user_dir() -> Path:
    if is_macos():
        return home_dir() / "Library" / "Application Support" / "Cursor" / "User"
    if is_windows():
        return appdata_dir() / "Cursor" / "User"
    return home_dir() / ".config" / "Cursor" / "User"


def claude_desktop_dir() -> Path:
    if is_macos():
        return home_dir() / "Library" / "Application Support" / "Claude"
    if is_windows():
        return appdata_dir() / "Claude"
    return home_dir() / ".config" / "Claude"


# ---------------------------------------------------------------------------
# Shell integration
# ---------------------------------------------------------------------------

def powershell_profile_path() -> Path:
    """Best-guess path of the PowerShell profile that Windows users actually load.

    PowerShell 7+ uses ``Documents/PowerShell``; Windows PowerShell 5.1 uses
    ``Documents/WindowsPowerShell``. Prefer whichever already exists.
    """
    modern = documents_dir() / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    legacy = documents_dir() / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
    if modern.exists():
        return modern
    if legacy.exists():
        return legacy
    return modern if shutil.which("pwsh") else legacy


def detect_shell_rc() -> Path:
    """Shell startup file that ``shell-env`` should manage."""
    if is_windows():
        return powershell_profile_path()
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell or (is_macos() and not (home_dir() / ".bashrc").exists()):
        return home_dir() / ".zshrc"
    return home_dir() / ".bashrc"


def shell_env_style() -> str:
    """``"posix"`` (export/unset) or ``"powershell"`` ($env: assignments)."""
    return "powershell" if is_windows() else "posix"


def source_hint(path: Path) -> str:
    """How the user activates the managed shell block in a new session."""
    if is_windows():
        return f'Run `. "{path}"` (or open a new PowerShell window) to activate.'
    return f"Run `source {path}` (or open a new terminal) to activate."


# ---------------------------------------------------------------------------
# Launchers (proxy start scripts, etc.)
# ---------------------------------------------------------------------------

def proxy_launcher_path() -> Path:
    """Start-proxy script, batch/PowerShell on Windows and shell everywhere else."""
    name = "start-proxy.ps1" if is_windows() else "start-proxy.sh"
    return bridge_dir() / name


def proxy_launcher_content(python_exe: str, proxy_script: Path, proxy_config: Path) -> str:
    """Render the platform-appropriate proxy launcher."""
    if is_windows():
        return (
            "# Agent Bridge - local proxy launcher (PowerShell)\n"
            "$ErrorActionPreference = 'Stop'\n"
            f'& "{python_exe}" "{proxy_script}" --config "{proxy_config}" @args\n'
            "exit $LASTEXITCODE\n"
        )
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'exec "{python_exe}" "{proxy_script}" --config "{proxy_config}" "$@"\n'
    )


def proxy_start_command() -> str:
    """Human-facing command that starts the local proxy."""
    path = proxy_launcher_path()
    if is_windows():
        return f'powershell -ExecutionPolicy Bypass -File "{path}"'
    return str(path)


# ---------------------------------------------------------------------------
# Console setup
# ---------------------------------------------------------------------------

def configure_stdio() -> None:
    """Make stdout/stderr UTF-8 safe and enable ANSI colours on Windows.

    Windows consoles default to a legacy code page which cannot encode the box
    drawing characters and emoji this project prints. Without this every banner
    raises ``UnicodeEncodeError`` on a default ``cmd.exe``/PowerShell session.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if is_windows():
        _enable_windows_vt()


def _enable_windows_vt() -> None:
    """Enable virtual-terminal processing so ANSI escape codes render in cmd.exe."""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        enable_vt = 0x0004
        for handle_id in (-11, -12):  # STDOUT, STDERR
            handle = kernel32.GetStdHandle(handle_id)
            if handle in (0, -1):
                continue
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                continue
            kernel32.SetConsoleMode(handle, mode.value | enable_vt)
    except Exception:
        # Not a console (piped output, IDE terminal) or no ctypes: ANSI stays as-is.
        pass


def ansi_supported() -> bool:
    """Whether ANSI escapes are likely to render in the current terminal."""
    if os.environ.get("NO_COLOR") is not None:
        return False
    if not sys.stdout.isatty():
        return False
    if is_windows():
        # Windows Terminal, VS Code, Cursor and modern conhost all support ANSI.
        if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
            return True
        term = os.environ.get("TERM", "")
        return "xterm" in term or "cygwin" in term or "msys" in term
    return True


# ---------------------------------------------------------------------------
# Python discovery (used by launchers and messages)
# ---------------------------------------------------------------------------

def python_command_hint() -> str:
    """The command a Windows user should use to run the Python entry points."""
    return "py -3" if is_windows() else "python3"


def cli_entry_command(script_name: str, args: str = "") -> str:
    """How to invoke a repo entry point on this OS."""
    base = f"python lib\\{script_name}" if is_windows() else f"./{script_name.replace('.py', '.sh')}"
    return f"{base} {args}".strip()

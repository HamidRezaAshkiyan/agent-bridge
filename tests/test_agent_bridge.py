"""Comprehensive test suite for Agent Bridge (runs in an isolated temporary profile)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib import platform_support as plat
from lib.configurators import AGENTS, BackupManager, run_configurator
from lib.desktop_proxy import (
    anthropic_to_openai_request,
    make_handler,
    openai_to_anthropic_response,
)
from lib.providers import PROVIDERS, ResolvedProvider
from http.server import ThreadingHTTPServer


# Environment variables that redirect profile/config resolution on each OS.
# Path.home() ignores HOME on Windows, which is why the override below targets
# AGENT_BRIDGE_USER_HOME (honoured by lib.platform_support) rather than HOME.
PROFILE_ENV_VARS = ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "AGENT_BRIDGE_USER_HOME")


def isolated_env(home: Path) -> dict[str, str]:
    """Environment that confines every config write to ``home``."""
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["AGENT_BRIDGE_USER_HOME"] = str(home)
    env["APPDATA"] = str(home / "AppData" / "Roaming")
    env["LOCALAPPDATA"] = str(home / "AppData" / "Local")
    (home / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True)
    (home / "AppData" / "Local").mkdir(parents=True, exist_ok=True)
    return env


def apply_env(env: dict[str, str]) -> dict[str, str | None]:
    """Apply ``env`` to this process and return the previous values for restore."""
    previous: dict[str, str | None] = {}
    for key in PROFILE_ENV_VARS:
        previous[key] = os.environ.get(key)
        if key in env:
            os.environ[key] = env[key]
        else:
            os.environ.pop(key, None)
    return previous


def restore_env(previous: dict[str, str | None]) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


class TestAgentBridge(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.home = Path(self._tmpdir.name)
        self._previous_env = apply_env(isolated_env(self.home))

    def tearDown(self) -> None:
        restore_env(self._previous_env)
        self._tmpdir.cleanup()

    def _make_provider(self, pid: str = "metis") -> ResolvedProvider:
        p = PROVIDERS[pid]
        return ResolvedProvider(
            id=p.id,
            name=p.name,
            openai_base_url=p.resolved_openai_url("ws-123"),
            anthropic_base_url=p.resolved_anthropic_url("ws-123"),
            api_key="sk-test-1234567890",
            env_var=p.env_var,
            model=p.default_model,
            anthropic_model=p.anthropic_model,
            models=list(p.models),
            requires_key=p.requires_key,
        )

    def test_all_configurators_succeed_and_preserve_existing_keys(self) -> None:
        # Seed pre-existing settings to verify non-destructive merging
        claude_settings = self.home / ".claude" / "settings.json"
        claude_settings.parent.mkdir(parents=True, exist_ok=True)
        claude_settings.write_text(
            json.dumps({"customFlag": True, "env": {"ANTHROPIC_API_KEY": "old-key", "KEEP_ME": "yes"}}),
            encoding="utf-8",
        )

        provider = self._make_provider("avalai")
        backups = BackupManager(dry_run=False)

        for agent in AGENTS:
            res = run_configurator(agent.id, provider, backups)
            self.assertTrue(res.ok, f"Configurator {agent.id} failed: {res.error}")
            self.assertTrue(res.files_written, f"Configurator {agent.id} wrote no files")
            for fpath in res.files_written:
                self.assertTrue(Path(fpath).exists(), f"Missing output file {fpath} for {agent.id}")

        # Verify Claude Code preserved unrelated keys and removed ANTHROPIC_API_KEY
        c_data = json.loads(claude_settings.read_text(encoding="utf-8"))
        self.assertTrue(c_data["customFlag"])
        self.assertEqual(c_data["env"]["KEEP_ME"], "yes")
        self.assertNotIn("ANTHROPIC_API_KEY", c_data["env"])
        self.assertEqual(c_data["env"]["ANTHROPIC_BASE_URL"], "https://api.avalai.ir")
        self.assertFalse(c_data["env"]["ANTHROPIC_BASE_URL"].endswith("/v1"))
        self.assertEqual(c_data["env"]["ANTHROPIC_AUTH_TOKEN"], "sk-test-1234567890")

        # Verify OpenCode JSON schema
        oc_data = json.loads((self.home / ".config" / "opencode" / "opencode.json").read_text(encoding="utf-8"))
        self.assertIn("avalai", oc_data["providers"])
        self.assertEqual(oc_data["providers"]["avalai"]["settings"]["baseURL"], "https://api.avalai.ir/v1")

        # Verify Pi models.json
        pi_data = json.loads((self.home / ".pi" / "agent" / "models.json").read_text(encoding="utf-8"))
        self.assertIn("avalai", pi_data["providers"])
        self.assertEqual(pi_data["providers"]["avalai"]["api"], "openai-completions")
        self.assertGreaterEqual(len(pi_data["providers"]["avalai"]["models"]), 1)

        # Verify Codex config.toml
        codex_toml = (self.home / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[model_providers.avalai]", codex_toml)
        self.assertIn('base_url = "https://api.avalai.ir/v1"', codex_toml)

        # Verify backup & restore
        sessions = BackupManager.list_sessions()
        self.assertGreaterEqual(len(sessions), 1)
        restored = BackupManager.restore_session(sessions[0])
        self.assertIn(str(claude_settings), restored)
        restored_data = json.loads(claude_settings.read_text(encoding="utf-8"))
        self.assertEqual(restored_data["env"]["ANTHROPIC_API_KEY"], "old-key")

    def test_openai_only_provider_uses_local_proxy_for_claude_code(self) -> None:
        provider = self._make_provider("liara")
        self.assertEqual(provider.anthropic_base_url, "")
        backups = BackupManager(dry_run=False)
        res = run_configurator("claude-code-cli", provider, backups)
        self.assertTrue(res.ok)
        c_data = json.loads((self.home / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(c_data["env"]["ANTHROPIC_BASE_URL"], "http://127.0.0.1:4789")
        self.assertTrue((self.home / ".agent-bridge" / "proxy.json").exists())
        self.assertTrue(plat.proxy_launcher_path().exists())

    def _entry_command(self, script_name: str, args: list[str]) -> list[str]:
        """Build the command that runs a repo entry point on this OS.

        The .sh/.ps1 wrappers are thin launchers whose only job is to locate Python and
        exec the module, so the module is invoked directly here. Wrapper existence and
        syntax are asserted separately in ``test_windows_entry_points_exist``.
        """
        modules = {
            "configure.sh": "configure.py",
            "install-agent.sh": "install_agent.py",
        }
        module = REPO_ROOT / "lib" / modules[script_name]
        return [sys.executable, str(module), *args]

    def test_non_interactive_cli_and_dry_run(self) -> None:
        proc = subprocess.run(
            self._entry_command(
                "configure.sh",
                [
                    "--non-interactive",
                    "--provider",
                    "metis",
                    "--agents",
                    "opencode-cli,claude-code-cli,pi,vscode-copilot,shell-env",
                    "--api-key",
                    "sk-metis-demo",
                    "--dry-run",
                ],
            ),
            env=isolated_env(self.home),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # Dry run must not write files
        self.assertFalse((self.home / ".claude" / "settings.json").exists())

    def test_install_agent_list_and_dry_run(self) -> None:
        proc = subprocess.run(
            self._entry_command("install-agent.sh", ["--agents", "opencode-cli,pi", "--dry-run"]),
            env=isolated_env(self.home),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("DRY RUN MODE", proc.stdout)

    def test_desktop_proxy_health_and_translation(self) -> None:
        oa_req = anthropic_to_openai_request(
            {
                "model": "claude-sonnet-4-6",
                "system": "Be helpful",
                "messages": [{"role": "user", "content": [{"type": "text", "text": "Hi"}]}],
                "max_tokens": 512,
            },
            fallback_model="gpt-4o",
            force_model="gpt-4.1",
        )
        self.assertEqual(oa_req["model"], "gpt-4.1")
        self.assertEqual(oa_req["messages"][0]["role"], "system")
        self.assertEqual(oa_req["messages"][1]["content"], "Hi")

        anth = openai_to_anthropic_response(
            {
                "id": "chatcmpl-1",
                "model": "gpt-4.1",
                "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
            requested_model="gpt-4.1",
        )
        self.assertEqual(anth["content"][0]["text"], "Hello!")
        self.assertEqual(anth["stop_reason"], "end_turn")

        cfg = {
            "provider_name": "Metis AI",
            "openai_base_url": "https://api.metisai.ir/openai/v1",
            "anthropic_base_url": "https://api.metisai.ir/anthropic",
            "default_model": "gpt-4o",
            "force_model": "",
        }
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cfg))
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            time.sleep(0.05)
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(data["status"], "ok")
                self.assertEqual(data["provider"], "Metis AI")
        finally:
            server.shutdown()
            server.server_close()

    def test_mcp_model_bridge_handshake_and_tools(self) -> None:
        proc = subprocess.Popen(
            [sys.executable, str(REPO_ROOT / "lib" / "mcp_model_bridge.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stdin and proc.stdout
        msgs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "active_provider_info", "arguments": {}}},
        ]
        for m in msgs:
            proc.stdin.write(json.dumps(m) + "\n")
        proc.stdin.close()
        out_lines = [line.strip() for line in proc.stdout.readlines() if line.strip()]
        proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()
        proc.wait(timeout=5)
        self.assertEqual(len(out_lines), 3)
        init_res = json.loads(out_lines[0])
        self.assertEqual(init_res["result"]["serverInfo"]["name"], "agent-bridge-models")
        tools_res = json.loads(out_lines[1])
        tool_names = [t["name"] for t in tools_res["result"]["tools"]]
        self.assertIn("ask_custom_model", tool_names)
        self.assertIn("list_custom_models", tool_names)


class TestWindowsSupport(unittest.TestCase):
    """Platform behaviours that only matter on Windows.

    The path assertions are pure functions of ``platform_support`` so they also run
    (and stay honest) on macOS/Linux CI, where they simply assert the POSIX shape.
    """

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.home = Path(self._tmpdir.name)
        self._previous_env = apply_env(isolated_env(self.home))

    def tearDown(self) -> None:
        restore_env(self._previous_env)
        self._tmpdir.cleanup()

    def test_profile_override_redirects_all_paths(self) -> None:
        """AGENT_BRIDGE_USER_HOME must confine every write into the sandbox."""
        self.assertEqual(plat.home_dir(), self.home)
        for path in (
            plat.bridge_dir(),
            plat.opencode_config_path(),
            plat.claude_code_settings_path(),
            plat.codex_config_path(),
            plat.aider_config_path(),
            plat.continue_config_path(),
            plat.pi_agent_dir(),
        ):
            self.assertTrue(
                str(path).startswith(str(self.home)),
                f"{path} escaped the sandbox {self.home}",
            )

    def test_proxy_launcher_matches_platform(self) -> None:
        launcher = plat.proxy_launcher_path()
        if plat.is_windows():
            self.assertEqual(launcher.name, "start-proxy.ps1")
        else:
            self.assertEqual(launcher.name, "start-proxy.sh")

        content = plat.proxy_launcher_content(
            "python.exe" if plat.is_windows() else "python3",
            Path("proxy.py"),
            Path("proxy.json"),
        )
        if plat.is_windows():
            self.assertIn("$ErrorActionPreference", content)
            self.assertIn("--config", content)
        else:
            self.assertTrue(content.startswith("#!/usr/bin/env bash"))

    def test_shell_env_uses_native_syntax(self) -> None:
        provider = ResolvedProvider(
            id="metis",
            name="Metis AI",
            openai_base_url="https://api.metisai.ir/openai/v1",
            anthropic_base_url="https://api.metisai.ir/anthropic",
            api_key="sk-x",
            env_var="METIS_API_KEY",
            model="gpt-4o",
            anthropic_model="claude-sonnet-4-6",
            models=[],
        )
        res = run_configurator("shell-env", provider, BackupManager())
        self.assertTrue(res.ok, res.error)
        text = Path(res.files_written[0]).read_text(encoding="utf-8")
        self.assertIn("# >>> agent-bridge >>>", text)
        self.assertIn("# <<< agent-bridge <<<", text)
        self.assertIn("METIS_API_KEY", text)
        if plat.is_windows():
            self.assertIn("$env:METIS_API_KEY", text)
            self.assertNotIn("export ", text)
            self.assertTrue(res.files_written[0].endswith(".ps1"))
        else:
            self.assertIn("export METIS_API_KEY", text)
            self.assertNotIn("$env:", text)

    def test_windows_style_paths_are_appdata_based(self) -> None:
        """On Windows the editor/desktop-app configs live under %APPDATA%."""
        if not plat.is_windows():
            self.skipTest("Windows-only path layout")
        appdata = Path(os.environ["APPDATA"])
        self.assertTrue(str(plat.cursor_user_dir()).startswith(str(appdata)))
        self.assertTrue(str(plat.vscode_user_dir()).startswith(str(appdata)))
        self.assertTrue(str(plat.claude_desktop_dir()).startswith(str(appdata)))
        self.assertTrue(str(plat.zed_settings_path()).startswith(str(appdata)))
        self.assertTrue(str(plat.goose_config_path()).startswith(str(appdata)))
        # CLI tools keep their XDG-style dot-directories even on Windows.
        self.assertTrue(str(plat.codex_config_path()).startswith(str(self.home)))
        self.assertEqual(plat.opencode_config_path().parts[-2:], ("opencode", "opencode.json"))

    def test_console_setup_does_not_raise(self) -> None:
        # Idempotent and safe when stdout is redirected (as it is under the test runner).
        plat.configure_stdio()
        plat.configure_stdio()

    def test_windows_entry_points_exist(self) -> None:
        """The Windows launchers ship alongside the POSIX ones."""
        for name in ("bootstrap.sh", "configure.sh", "install-agent.sh"):
            self.assertTrue((REPO_ROOT / name).is_file(), f"missing {name}")

        for name in (
            "bootstrap.ps1",
            "configure.ps1",
            "install-agent.ps1",
            "configure.cmd",
            "install-agent.cmd",
            Path("scripts") / "python-detect.ps1",
        ):
            self.assertTrue((REPO_ROOT / name).is_file(), f"missing {name}")

        # The PowerShell wrappers must delegate to the matching Python module.
        for ps1, module in (
            ("configure.ps1", "configure.py"),
            ("install-agent.ps1", "install_agent.py"),
        ):
            body = (REPO_ROOT / ps1).read_text(encoding="utf-8")
            self.assertIn(module, body)
            self.assertIn("Get-AgentBridgePython", body)

    def test_install_catalog_covers_windows_targets(self) -> None:
        from lib.install_agent import CATALOG, choose_install_command

        windows_env = {
            "os": "windows",
            "winget": True,
            "npm": True,
            "pnpm": False,
            "bun": False,
            "uv": False,
            "pipx": False,
            "pip3": False,
            "curl": True,
            "brew": False,
            "scoop": False,
            "choco": False,
        }
        for agent in CATALOG:
            if agent.category in ("gui", "chat-gui"):
                self.assertTrue(
                    agent.windows_app,
                    f"{agent.id} has no windows_app path",
                )
            method, cmd = choose_install_command(agent, windows_env)
            self.assertNotIn("brew", cmd, f"{agent.id} chose Homebrew on Windows")
            self.assertNotIn("| bash", cmd, f"{agent.id} chose a POSIX-only installer on Windows")
            if agent.winget_id:
                self.assertEqual(method, "winget", f"{agent.id} ignored its winget_id")

    def test_windows_prefers_winget_then_falls_back(self) -> None:
        """With winget absent, Windows installs must still find a working method."""
        from lib.install_agent import CATALOG, choose_install_command

        no_winget = {
            "os": "windows",
            "winget": False,
            "npm": True,
            "pnpm": False,
            "bun": False,
            "uv": False,
            "pipx": False,
            "pip3": False,
            "curl": False,
            "brew": False,
            "scoop": False,
            "choco": False,
        }
        for agent in CATALOG:
            method, cmd = choose_install_command(agent, no_winget)
            self.assertNotIn("brew", cmd)
            self.assertNotIn("| bash", cmd)
            # CLIs should still be installable via npm; GUIs may fall back to manual.
            if agent.category == "cli" and agent.npm_pkg:
                self.assertEqual(method, "npm", f"{agent.id} lost its npm fallback")


if __name__ == "__main__":
    unittest.main()

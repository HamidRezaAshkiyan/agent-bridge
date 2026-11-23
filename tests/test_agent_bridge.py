"""Comprehensive test suite for Agent Bridge (runs in an isolated temporary HOME)."""

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

from lib.configurators import AGENTS, BackupManager, run_configurator
from lib.desktop_proxy import (
    anthropic_to_openai_request,
    make_handler,
    openai_to_anthropic_response,
)
from lib.providers import PROVIDERS, ResolvedProvider
from http.server import ThreadingHTTPServer


class TestAgentBridge(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_home = os.environ.get("HOME")
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["HOME"] = self._tmpdir.name
        self.home = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        if self._orig_home is not None:
            os.environ["HOME"] = self._orig_home
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
        self.assertTrue((self.home / ".agent-bridge" / "start-proxy.sh").exists())

    def test_non_interactive_cli_and_dry_run(self) -> None:
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        proc = subprocess.run(
            [
                str(REPO_ROOT / "configure.sh"),
                "--non-interactive",
                "--provider",
                "metis",
                "--agents",
                "opencode-cli,claude-code-cli,pi,vscode-copilot,shell-env",
                "--api-key",
                "sk-metis-demo",
                "--dry-run",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # Dry run must not write files
        self.assertFalse((self.home / ".claude" / "settings.json").exists())

    def test_install_agent_list_and_dry_run(self) -> None:
        proc = subprocess.run(
            [str(REPO_ROOT / "install-agent.sh"), "--agents", "opencode-cli,pi", "--dry-run"],
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


if __name__ == "__main__":
    unittest.main()

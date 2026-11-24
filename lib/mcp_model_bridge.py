#!/usr/bin/env python3
"""Zero-dependency stdio MCP server exposing your custom AI provider inside Claude Desktop.

Registered automatically into claude_desktop_config.json by Agent Bridge.
Tools exposed:
  - ask_custom_model: Query any model on Metis, AvalAI, OpenRouter, Liara, or custom OpenAI-compatible API.
  - list_custom_models: List models currently offered by your configured provider.
  - active_provider_info: Inspect active provider name, base URL, and default model.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
from typing import Any

CONFIG_PATH = Path(os.environ.get("AGENT_BRIDGE_MCP_CONFIG", Path.home() / ".agent-bridge" / "proxy.json"))


def load_cfg() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "provider_name": os.environ.get("AGENT_BRIDGE_PROVIDER", "custom"),
        "openai_base_url": os.environ.get("OPENAI_BASE_URL", ""),
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "default_model": os.environ.get("AGENT_BRIDGE_MODEL", "gpt-4o"),
    }


def call_chat_completion(prompt: str, model: str = "", system: str = "", temperature: float = 0.7) -> str:
    cfg = load_cfg()
    base_url = cfg.get("openai_base_url", "").rstrip("/")
    api_key = cfg.get("api_key", "")
    chosen_model = model or cfg.get("default_model", "gpt-4o")
    if not base_url:
        return "Error: No custom provider configured. Run Agent Bridge (./configure.sh or .\\configure.ps1) to set one up."

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps(
        {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
        }
    ).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "agent-bridge-mcp/1.0",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(f"{base_url}/chat/completions", data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            choices = data.get("choices") or []
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return json.dumps(data)
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")[:500]
        return f"Provider HTTP {exc.code} error: {err}"
    except Exception as exc:
        return f"Request error: {exc}"


def list_models() -> str:
    cfg = load_cfg()
    base_url = cfg.get("openai_base_url", "").rstrip("/")
    api_key = cfg.get("api_key", "")
    if not base_url:
        return "No custom provider configured."
    headers = {"Accept": "application/json", "User-Agent": "agent-bridge-mcp/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(f"{base_url}/models", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            ids = [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and m.get("id")]
            if not ids:
                return "Provider responded, but returned no model list."
            return f"Available models on {cfg.get('provider_name')} ({len(ids)} total):\n" + "\n".join(
                f"- {m}" for m in ids[:60]
            )
    except Exception as exc:
        return f"Could not fetch models from {base_url}/models: {exc}"


TOOLS = [
    {
        "name": "ask_custom_model",
        "description": "Send a prompt to your configured custom AI provider (Metis, AvalAI, OpenRouter, Liara, or custom OpenAI-compatible API).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The prompt to send to the custom model."},
                "model": {"type": "string", "description": "Optional model ID override (uses configured default if omitted)."},
                "system": {"type": "string", "description": "Optional system instruction."},
                "temperature": {"type": "number", "description": "Sampling temperature (default 0.7)."},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "list_custom_models",
        "description": "List available model IDs from your configured custom AI provider.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "active_provider_info",
        "description": "Show the active custom AI provider name, base URL, and default model.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def send_response(msg: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle_request(req: dict[str, Any]) -> None:
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        send_response(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "agent-bridge-models", "version": "1.0.0"},
                },
            }
        )
    elif method == "notifications/initialized":
        return
    elif method == "tools/list":
        send_response({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        if name == "ask_custom_model":
            text = call_chat_completion(
                prompt=str(args.get("prompt", "")),
                model=str(args.get("model", "")),
                system=str(args.get("system", "")),
                temperature=float(args.get("temperature", 0.7)),
            )
        elif name == "list_custom_models":
            text = list_models()
        elif name == "active_provider_info":
            cfg = load_cfg()
            text = json.dumps(
                {
                    "provider": cfg.get("provider_name"),
                    "openai_base_url": cfg.get("openai_base_url"),
                    "anthropic_base_url": cfg.get("anthropic_base_url"),
                    "default_model": cfg.get("default_model"),
                },
                indent=2,
            )
        else:
            send_response(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {name}"},
                }
            )
            return
        send_response(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        )
    elif req_id is not None:
        send_response(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        )


def main() -> int:
    if os.name == "nt":
        for _stream in (sys.stdin, sys.stdout, sys.stderr):
            if hasattr(_stream, "reconfigure"):
                try:
                    _stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        handle_request(req)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

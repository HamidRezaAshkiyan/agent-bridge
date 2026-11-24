#!/usr/bin/env python3
"""Zero-dependency local HTTP bridge proxy for Claude Desktop, ChatGPT Desktop, and CLI agents.

Features:
- Exposes OpenAI-compatible endpoints (/v1/chat/completions, /v1/models) forwarded to your custom provider.
- Exposes Anthropic Messages API (/v1/messages):
  * If upstream has an Anthropic base URL, forwards directly with Bearer / x-api-key auth.
  * Otherwise, translates Anthropic /v1/messages <-> OpenAI /v1/chat/completions on the fly!
- Optional model remapping (map any requested model name to your chosen custom model).
- /health endpoint for diagnostics.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib import platform_support as plat

plat.configure_stdio()

DEFAULT_CONFIG_PATH = plat.bridge_dir() / "proxy.json"


def load_proxy_config(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "provider_name": os.environ.get("AGENT_BRIDGE_PROVIDER", "custom"),
        "openai_base_url": os.environ.get("OPENAI_BASE_URL", "https://api.avalai.ir/v1"),
        "anthropic_base_url": os.environ.get("ANTHROPIC_BASE_URL", ""),
        "api_key": os.environ.get("AGENT_BRIDGE_API_KEY") or os.environ.get("OPENAI_API_KEY", ""),
        "default_model": os.environ.get("AGENT_BRIDGE_MODEL", "gpt-4o"),
        "force_model": os.environ.get("AGENT_BRIDGE_FORCE_MODEL", ""),
        "host": "127.0.0.1",
        "port": 4789,
    }


def anthropic_to_openai_request(payload: dict[str, Any], fallback_model: str, force_model: str) -> dict[str, Any]:
    """Translate an Anthropic /v1/messages request body into OpenAI /v1/chat/completions format."""
    messages: list[dict[str, Any]] = []
    system_prompt = payload.get("system")
    if isinstance(system_prompt, str) and system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    elif isinstance(system_prompt, list):
        text_parts = [b.get("text", "") for b in system_prompt if isinstance(b, dict) and b.get("type") == "text"]
        if text_parts:
            messages.append({"role": "system", "content": "\n".join(text_parts)})

    for msg in payload.get("messages", []):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            text_chunks: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_chunks.append(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        text_chunks.append(str(block.get("content", "")))
            messages.append({"role": role, "content": "\n".join(text_chunks)})

    model = force_model or payload.get("model") or fallback_model
    out: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": payload.get("max_tokens", 4096),
        "stream": False,
    }
    if "temperature" in payload:
        out["temperature"] = payload["temperature"]
    return out


def openai_to_anthropic_response(data: dict[str, Any], requested_model: str) -> dict[str, Any]:
    """Translate an OpenAI chat completion response into Anthropic Messages API shape."""
    choices = data.get("choices") or []
    text = ""
    stop_reason = "end_turn"
    if choices:
        choice = choices[0]
        msg = choice.get("message") or {}
        text = msg.get("content") or ""
        finish = choice.get("finish_reason")
        if finish == "length":
            stop_reason = "max_tokens"
    usage = data.get("usage") or {}
    return {
        "id": data.get("id", f"msg_{int(time.time())}"),
        "type": "message",
        "role": "assistant",
        "model": data.get("model", requested_model),
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


def make_handler(cfg: dict[str, Any]) -> type[BaseHTTPRequestHandler]:
    class BridgeProxyHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write(f"[agent-bridge-proxy] {self.address_string()} - {fmt % args}\n")

        def _send_json(self, code: int, body: Any) -> None:
            raw = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(raw)

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length", "0") or "0")
            return self.rfile.read(length) if length > 0 else b""

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:
            if self.path in ("/health", "/"):
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "service": "agent-bridge-proxy",
                        "provider": cfg.get("provider_name", "custom"),
                        "openai_base_url": cfg.get("openai_base_url", ""),
                        "anthropic_base_url": cfg.get("anthropic_base_url", ""),
                        "default_model": cfg.get("default_model", ""),
                        "force_model": cfg.get("force_model", ""),
                    },
                )
                return

            if self.path.startswith("/v1/models"):
                upstream = cfg.get("openai_base_url", "").rstrip("/") + "/models"
                self._forward_raw("GET", upstream, b"", use_anthropic=False)
                return

            self._send_json(404, {"error": f"Unknown route: {self.path}"})

        def do_POST(self) -> None:
            raw_body = self._read_body()
            if self.path.startswith("/v1/messages"):
                anthropic_base = cfg.get("anthropic_base_url", "").rstrip("/")
                if anthropic_base:
                    # Forward directly to native Anthropic-compatible endpoint
                    try:
                        payload = json.loads(raw_body.decode("utf-8"))
                        if cfg.get("force_model"):
                            payload["model"] = cfg["force_model"]
                        raw_body = json.dumps(payload).encode("utf-8")
                    except Exception:
                        pass
                    upstream = anthropic_base + "/v1/messages"
                    self._forward_raw("POST", upstream, raw_body, use_anthropic=True)
                    return

                # Translate Anthropic -> OpenAI chat completions
                try:
                    payload = json.loads(raw_body.decode("utf-8"))
                except json.JSONDecodeError:
                    self._send_json(400, {"error": "Invalid JSON body"})
                    return
                oa_req = anthropic_to_openai_request(
                    payload,
                    fallback_model=cfg.get("default_model", "gpt-4o"),
                    force_model=cfg.get("force_model", ""),
                )
                upstream = cfg.get("openai_base_url", "").rstrip("/") + "/chat/completions"
                status, resp_bytes = self._upstream_call(
                    "POST", upstream, json.dumps(oa_req).encode("utf-8"), use_anthropic=False
                )
                if status != 200:
                    self._send_json(status, {"error": resp_bytes.decode("utf-8", errors="replace")})
                    return
                try:
                    oa_data = json.loads(resp_bytes.decode("utf-8"))
                    anth_resp = openai_to_anthropic_response(oa_data, oa_req["model"])
                    self._send_json(200, anth_resp)
                except Exception as exc:
                    self._send_json(502, {"error": f"Failed to translate upstream response: {exc}"})
                return

            if self.path.startswith("/v1/"):
                # OpenAI-compatible passthrough (/v1/chat/completions, /v1/responses, etc.)
                try:
                    payload = json.loads(raw_body.decode("utf-8"))
                    if cfg.get("force_model") and isinstance(payload, dict):
                        payload["model"] = cfg["force_model"]
                    raw_body = json.dumps(payload).encode("utf-8")
                except Exception:
                    pass
                subpath = self.path[len("/v1") :]
                upstream = cfg.get("openai_base_url", "").rstrip("/") + subpath
                self._forward_raw("POST", upstream, raw_body, use_anthropic=False)
                return

            self._send_json(404, {"error": f"Unknown route: {self.path}"})

        def _upstream_call(
            self, method: str, url: str, body: bytes, use_anthropic: bool
        ) -> tuple[int, bytes]:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "agent-bridge-proxy/1.0",
            }
            api_key = cfg.get("api_key", "")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                if use_anthropic:
                    headers["x-api-key"] = api_key
                    headers["anthropic-version"] = self.headers.get("anthropic-version", "2023-06-01")
            req = urllib.request.Request(url, data=body if method == "POST" else None, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    return resp.status, resp.read()
            except urllib.error.HTTPError as exc:
                return exc.code, exc.read()
            except Exception as exc:
                return 502, json.dumps({"error": str(exc)}).encode("utf-8")

        def _forward_raw(self, method: str, url: str, body: bytes, use_anthropic: bool) -> None:
            status, resp_bytes = self._upstream_call(method, url, body, use_anthropic)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp_bytes)

    return BridgeProxyHandler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Bridge local AI gateway proxy")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to proxy.json")
    parser.add_argument("--host", default="", help="Bind host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=0, help="Bind port (default 4789)")
    args = parser.parse_args(argv)

    cfg = load_proxy_config(args.config)
    host = args.host or cfg.get("host", "127.0.0.1")
    port = args.port or int(cfg.get("port", 4789))

    server = ThreadingHTTPServer((host, port), make_handler(cfg))
    print(f"⚡ Agent Bridge Proxy running on http://{host}:{port}")
    print(f"   Provider        : {cfg.get('provider_name')}")
    print(f"   OpenAI Upstream : {cfg.get('openai_base_url')}")
    print(f"   Anthropic Mode  : {'native forward' if cfg.get('anthropic_base_url') else 'auto-translate -> OpenAI'}")
    print(f"   Default Model   : {cfg.get('default_model')}")
    if cfg.get("force_model"):
        print(f"   Model Override  : {cfg.get('force_model')}")
    print("   Press Ctrl+C to stop.\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Agent Bridge Proxy...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

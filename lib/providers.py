"""Built-in AI provider presets and live connectivity testing."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import time
import urllib.error
import urllib.request
from typing import Any


@dataclass
class ModelSpec:
    id: str
    name: str
    context_window: int = 128000
    max_tokens: int = 8192
    vision: bool = True
    reasoning: bool = False


@dataclass
class ProviderPreset:
    id: str
    name: str
    tagline: str
    website: str
    openai_base_url: str
    anthropic_base_url: str
    env_var: str
    default_model: str
    anthropic_model: str
    requires_key: bool = True
    needs_workspace_id: bool = False
    models: list[ModelSpec] = field(default_factory=list)
    notes: str = ""

    def resolved_openai_url(self, workspace_id: str = "") -> str:
        url = self.openai_base_url
        if "{workspace_id}" in url:
            url = url.replace("{workspace_id}", workspace_id or "YOUR_WORKSPACE_ID")
        return url.rstrip("/")

    def resolved_anthropic_url(self, workspace_id: str = "") -> str:
        url = self.anthropic_base_url
        if not url:
            return ""
        if "{workspace_id}" in url:
            url = url.replace("{workspace_id}", workspace_id or "YOUR_WORKSPACE_ID")
        # Claude Code & native Anthropic SDKs append /v1/messages automatically
        url = url.rstrip("/")
        if url.endswith("/v1"):
            url = url[:-3]
        return url


@dataclass
class ResolvedProvider:
    id: str
    name: str
    openai_base_url: str
    anthropic_base_url: str
    api_key: str
    env_var: str
    model: str
    anthropic_model: str
    models: list[ModelSpec]
    requires_key: bool = True

    @property
    def effective_api_key(self) -> str:
        return self.api_key or ("sk-no-auth-required" if not self.requires_key else "")


PROVIDERS: dict[str, ProviderPreset] = {
    "metis": ProviderPreset(
        id="metis",
        name="Metis AI",
        tagline="Iranian & global multi-model gateway (OpenAI + Anthropic + Gemini)",
        website="https://metisai.ir",
        openai_base_url="https://api.metisai.ir/openai/v1",
        anthropic_base_url="https://api.metisai.ir/anthropic",
        env_var="METIS_API_KEY",
        default_model="gpt-4o",
        anthropic_model="claude-sonnet-4-6",
        notes="For servers outside Iran that cannot reach .ir domains, use the 'metis-global' (tapsage.com) preset.",
        models=[
            ModelSpec("gpt-4o", "GPT-4o (Metis)", 128000, 16384, True, False),
            ModelSpec("gpt-4.1", "GPT-4.1 (Metis)", 1000000, 32768, True, False),
            ModelSpec("claude-sonnet-4-6", "Claude Sonnet 4.6 (Metis)", 200000, 16384, True, True),
            ModelSpec("claude-3-7-sonnet-latest", "Claude 3.7 Sonnet (Metis)", 200000, 16384, True, True),
            ModelSpec("gemini-2.5-pro", "Gemini 2.5 Pro (Metis)", 1000000, 65536, True, True),
            ModelSpec("deepseek-r1", "DeepSeek R1 (Metis)", 128000, 8192, False, True),
        ],
    ),
    "metis-global": ProviderPreset(
        id="metis-global",
        name="Metis AI (Global / TapSage)",
        tagline="Metis AI international gateway via api.tapsage.com",
        website="https://metisai.ir",
        openai_base_url="https://api.tapsage.com/openai/v1",
        anthropic_base_url="https://api.tapsage.com/anthropic",
        env_var="METIS_API_KEY",
        default_model="gpt-4o",
        anthropic_model="claude-sonnet-4-6",
        notes="Same Metis API key, routed via international tapsage.com domain.",
        models=[
            ModelSpec("gpt-4o", "GPT-4o (Metis Global)", 128000, 16384, True, False),
            ModelSpec("gpt-4.1", "GPT-4.1 (Metis Global)", 1000000, 32768, True, False),
            ModelSpec("claude-sonnet-4-6", "Claude Sonnet 4.6 (Metis Global)", 200000, 16384, True, True),
            ModelSpec("gemini-2.5-pro", "Gemini 2.5 Pro (Metis Global)", 1000000, 65536, True, True),
        ],
    ),
    "avalai": ProviderPreset(
        id="avalai",
        name="AvalAI",
        tagline="Unified OpenAI & Anthropic compatible API gateway (api.avalai.ir)",
        website="https://avalai.ir",
        openai_base_url="https://api.avalai.ir/v1",
        anthropic_base_url="https://api.avalai.ir",
        env_var="AVALAI_API_KEY",
        default_model="gpt-4o",
        anthropic_model="claude-sonnet-4-6",
        notes="Supports native OpenAI (/v1) and Anthropic Messages (/v1/messages) endpoints with one API key.",
        models=[
            ModelSpec("gpt-4o", "GPT-4o (AvalAI)", 128000, 16384, True, False),
            ModelSpec("gpt-4.1", "GPT-4.1 (AvalAI)", 1000000, 32768, True, False),
            ModelSpec("claude-sonnet-4-6", "Claude Sonnet 4.6 (AvalAI)", 200000, 16384, True, True),
            ModelSpec("claude-opus-4-6", "Claude Opus 4.6 (AvalAI)", 200000, 16384, True, True),
            ModelSpec("gemini-2.5-pro", "Gemini 2.5 Pro (AvalAI)", 1000000, 65536, True, True),
            ModelSpec("deepseek-chat", "DeepSeek V3 (AvalAI)", 128000, 8192, False, False),
        ],
    ),
    "liara": ProviderPreset(
        id="liara",
        name="Liara AI",
        tagline="Liara Cloud AI gateway (workspace-scoped OpenAI-compatible API)",
        website="https://liara.ir",
        openai_base_url="https://ai.liara.ir/api/{workspace_id}/v1",
        anthropic_base_url="",
        env_var="LIARA_API_KEY",
        default_model="openai/gpt-4o-mini",
        anthropic_model="anthropic/claude-sonnet-4-6",
        needs_workspace_id=True,
        notes="Requires your Liara AI workspace ID from console.liara.ir.",
        models=[
            ModelSpec("openai/gpt-4o", "GPT-4o (Liara)", 128000, 16384, True, False),
            ModelSpec("openai/gpt-4o-mini", "GPT-4o Mini (Liara)", 128000, 16384, True, False),
            ModelSpec("anthropic/claude-sonnet-4-6", "Claude Sonnet 4.6 (Liara)", 200000, 16384, True, True),
            ModelSpec("google/gemini-2.5-pro", "Gemini 2.5 Pro (Liara)", 1000000, 65536, True, True),
        ],
    ),
    "gapgpt": ProviderPreset(
        id="gapgpt",
        name="GapGPT",
        tagline="OpenAI-compatible multi-model API gateway (api.gapgpt.app)",
        website="https://gapgpt.app",
        openai_base_url="https://api.gapgpt.app/v1",
        anthropic_base_url="https://api.gapgpt.app",
        env_var="GAPGPT_API_KEY",
        default_model="gpt-4o",
        anthropic_model="claude-sonnet-4-6",
        models=[
            ModelSpec("gpt-4o", "GPT-4o (GapGPT)", 128000, 16384, True, False),
            ModelSpec("claude-sonnet-4-6", "Claude Sonnet 4.6 (GapGPT)", 200000, 16384, True, True),
            ModelSpec("deepseek-chat", "DeepSeek Chat (GapGPT)", 128000, 8192, False, False),
        ],
    ),
    "openrouter": ProviderPreset(
        id="openrouter",
        name="OpenRouter",
        tagline="Global unified API for 300+ models (openrouter.ai)",
        website="https://openrouter.ai",
        openai_base_url="https://openrouter.ai/api/v1",
        anthropic_base_url="https://openrouter.ai/api",
        env_var="OPENROUTER_API_KEY",
        default_model="anthropic/claude-sonnet-4-6",
        anthropic_model="anthropic/claude-sonnet-4-6",
        models=[
            ModelSpec("anthropic/claude-sonnet-4-6", "Claude Sonnet 4.6 (OpenRouter)", 200000, 16384, True, True),
            ModelSpec("openai/gpt-4.1", "GPT-4.1 (OpenRouter)", 1000000, 32768, True, False),
            ModelSpec("google/gemini-2.5-pro", "Gemini 2.5 Pro (OpenRouter)", 1000000, 65536, True, True),
            ModelSpec("deepseek/deepseek-r1", "DeepSeek R1 (OpenRouter)", 128000, 8192, False, True),
        ],
    ),
    "deepseek": ProviderPreset(
        id="deepseek",
        name="DeepSeek",
        tagline="Official DeepSeek API (OpenAI & Anthropic compatible)",
        website="https://platform.deepseek.com",
        openai_base_url="https://api.deepseek.com/v1",
        anthropic_base_url="https://api.deepseek.com/anthropic",
        env_var="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        anthropic_model="deepseek-chat",
        models=[
            ModelSpec("deepseek-chat", "DeepSeek V3", 128000, 8192, False, False),
            ModelSpec("deepseek-reasoner", "DeepSeek R1 Reasoner", 128000, 8192, False, True),
        ],
    ),
    "groq": ProviderPreset(
        id="groq",
        name="Groq",
        tagline="Ultra-fast LPU inference (OpenAI-compatible)",
        website="https://console.groq.com",
        openai_base_url="https://api.groq.com/openai/v1",
        anthropic_base_url="",
        env_var="GROQ_API_KEY",
        default_model="llama-3.3-70b-versatile",
        anthropic_model="llama-3.3-70b-versatile",
        models=[
            ModelSpec("llama-3.3-70b-versatile", "Llama 3.3 70B (Groq)", 128000, 32768, False, False),
            ModelSpec("qwen-qwq-32b", "Qwen QwQ 32B (Groq)", 128000, 16384, False, True),
        ],
    ),
    "together": ProviderPreset(
        id="together",
        name="Together AI",
        tagline="Fast open-source model hosting (api.together.xyz)",
        website="https://together.ai",
        openai_base_url="https://api.together.xyz/v1",
        anthropic_base_url="",
        env_var="TOGETHER_API_KEY",
        default_model="Qwen/Qwen2.5-Coder-32B-Instruct",
        anthropic_model="Qwen/Qwen2.5-Coder-32B-Instruct",
        models=[
            ModelSpec("Qwen/Qwen2.5-Coder-32B-Instruct", "Qwen 2.5 Coder 32B", 32768, 8192, False, False),
            ModelSpec("deepseek-ai/DeepSeek-V3", "DeepSeek V3 (Together)", 128000, 8192, False, False),
        ],
    ),
    "ollama": ProviderPreset(
        id="ollama",
        name="Ollama (Local)",
        tagline="Run local models on localhost:11434 (no API key needed)",
        website="https://ollama.com",
        openai_base_url="http://localhost:11434/v1",
        anthropic_base_url="http://localhost:11434",
        env_var="OLLAMA_API_KEY",
        default_model="qwen2.5-coder:14b",
        anthropic_model="qwen2.5-coder:14b",
        requires_key=False,
        models=[
            ModelSpec("qwen2.5-coder:14b", "Qwen 2.5 Coder 14B (Local)", 32768, 8192, False, False),
            ModelSpec("qwen2.5-coder:7b", "Qwen 2.5 Coder 7B (Local)", 32768, 8192, False, False),
            ModelSpec("deepseek-r1:14b", "DeepSeek R1 14B (Local)", 32768, 8192, False, True),
        ],
    ),
    "lmstudio": ProviderPreset(
        id="lmstudio",
        name="LM Studio (Local)",
        tagline="Local OpenAI-compatible server on localhost:1234",
        website="https://lmstudio.ai",
        openai_base_url="http://localhost:1234/v1",
        anthropic_base_url="",
        env_var="LMSTUDIO_API_KEY",
        default_model="local-model",
        anthropic_model="local-model",
        requires_key=False,
        models=[
            ModelSpec("local-model", "LM Studio Active Model", 32768, 8192, False, False),
        ],
    ),
    "custom": ProviderPreset(
        id="custom",
        name="Custom Provider",
        tagline="Any OpenAI-compatible or Anthropic-compatible API endpoint",
        website="",
        openai_base_url="https://api.example.com/v1",
        anthropic_base_url="",
        env_var="CUSTOM_AI_API_KEY",
        default_model="gpt-4o",
        anthropic_model="claude-sonnet-4-6",
        models=[],
    ),
}


def test_provider_connection(
    base_url: str,
    api_key: str,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Probe `<base_url>/models` to validate connectivity and API key."""
    url = base_url.rstrip("/") + "/models"
    headers = {
        "Accept": "application/json",
        "User-Agent": "agent-bridge/1.0",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            body = resp.read().decode("utf-8", errors="replace")
            models: list[str] = []
            try:
                data = json.loads(body)
                if isinstance(data, dict) and isinstance(data.get("data"), list):
                    models = [str(m.get("id")) for m in data["data"] if isinstance(m, dict) and m.get("id")]
            except json.JSONDecodeError:
                pass
            return {
                "ok": True,
                "status": resp.status,
                "latency_ms": elapsed_ms,
                "models": models,
                "url": url,
            }
    except urllib.error.HTTPError as exc:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return {
            "ok": False,
            "status": exc.code,
            "latency_ms": elapsed_ms,
            "error": f"HTTP {exc.code} {exc.reason}",
            "detail": detail,
            "url": url,
        }
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return {
            "ok": False,
            "status": 0,
            "latency_ms": elapsed_ms,
            "error": str(exc),
            "url": url,
        }

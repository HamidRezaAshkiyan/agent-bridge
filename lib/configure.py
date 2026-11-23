#!/usr/bin/env python3
"""Interactive & CLI orchestrator for Agent Bridge configuration."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

# Ensure repo root is importable when invoked directly
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib import __version__, ui
from lib.configurators import AGENTS, AGENT_MAP, BackupManager, run_configurator
from lib.providers import PROVIDERS, ModelSpec, ResolvedProvider, test_provider_connection


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="configure.sh",
        description="Configure Metis AI, AvalAI, OpenRouter, Liara, or custom AI providers across CLI & GUI coding agents.",
    )
    p.add_argument("--provider", choices=list(PROVIDERS.keys()), help="Provider preset ID")
    p.add_argument("--agents", help="Comma-separated agent IDs (e.g. opencode-cli,claude-code-cli,pi,vscode-copilot) or 'all'")
    p.add_argument("--api-key", default="", help="API key (or set via provider env var)")
    p.add_argument("--base-url", default="", help="Override OpenAI-compatible base URL")
    p.add_argument("--anthropic-url", default="", help="Override Anthropic-compatible base URL (without /v1)")
    p.add_argument("--workspace-id", default="", help="Workspace ID (for Liara AI)")
    p.add_argument("--model", default="", help="Default model ID")
    p.add_argument("--anthropic-model", default="", help="Anthropic model ID (for Claude Code / Desktop)")
    p.add_argument("--test", action="store_true", help="Test API connection before writing configs")
    p.add_argument("--skip-test", action="store_true", help="Skip interactive connection test prompt")
    p.add_argument("--dry-run", action="store_true", help="Preview actions without modifying any files")
    p.add_argument("--non-interactive", action="store_true", help="Run without interactive prompts (requires --provider and --agents)")
    p.add_argument("--list-providers", action="store_true", help="List built-in provider presets and exit")
    p.add_argument("--list-agents", action="store_true", help="List supported CLI & GUI agents and exit")
    p.add_argument("--restore", action="store_true", help="Restore config files from a previous Agent Bridge backup")
    p.add_argument("--version", action="version", version=f"agent-bridge {__version__}")
    return p


def cmd_list_providers() -> int:
    ui.section("Supported AI Providers")
    for pid, pr in PROVIDERS.items():
        anth = pr.anthropic_base_url or "(via local bridge proxy)"
        print(f"  {ui.C.CYAN}{pid:<14}{ui.C.RESET} {ui.C.BOLD}{pr.name}{ui.C.RESET}")
        print(f"                 OpenAI   : {pr.openai_base_url}")
        print(f"                 Anthropic: {anth}")
    return 0


def cmd_list_agents() -> int:
    ui.section("Supported Coding Agents & Desktop Apps")
    for ag in AGENTS:
        badge = f"[{ag.category.upper()}]"
        print(f"  {ui.C.CYAN}{ag.id:<18}{ui.C.RESET} {ui.C.GRAY}{badge:<10}{ui.C.RESET} {ui.C.BOLD}{ag.name}{ui.C.RESET}")
        print(f"                     {ui.C.DIM}{ag.summary} ({ag.config_hint}){ui.C.RESET}")
    return 0


def cmd_restore() -> int:
    sessions = BackupManager.list_sessions()
    if not sessions:
        ui.warn("No backups found in ~/.agent-bridge/backups.")
        return 0
    items = [(str(s), s.name, f"Backup directory: {s}") for s in sessions[:15]]
    chosen = ui.select_one("Select a backup session to restore:", items)
    if not ui.confirm(f"Restore files from backup {Path(chosen).name}?", default=True):
        ui.info("Cancelled.")
        return 0
    restored = BackupManager.restore_session(Path(chosen))
    for r in restored:
        ui.success(f"Restored {r}")
    return 0


def resolve_provider_interactive(args: argparse.Namespace) -> ResolvedProvider:
    ui.step(1, 4, "Choose your AI Provider")
    if args.provider:
        pid = args.provider
        ui.info(f"Using provider preset: {ui.C.BOLD}{PROVIDERS[pid].name}{ui.C.RESET}")
    else:
        items = [
            (k, p.name, p.tagline)
            for k, p in PROVIDERS.items()
        ]
        pid = ui.select_one("Select an AI provider:", items, default_index=0)

    preset = PROVIDERS[pid]
    if preset.notes:
        ui.info(preset.notes)

    ui.step(2, 4, f"Configure {preset.name} Credentials & Model")

    workspace_id = args.workspace_id
    if preset.needs_workspace_id and not workspace_id:
        workspace_id = ui.prompt_text("Liara AI Workspace ID", required=True)

    if pid == "custom":
        custom_name = ui.prompt_text("Custom Provider Name", default="My Custom AI", required=True)
        openai_url = args.base_url or ui.prompt_text("OpenAI-compatible Base URL (e.g. https://api.example.com/v1)", required=True)
        anth_url = args.anthropic_url or ui.prompt_text("Anthropic-compatible Base URL (optional, without /v1)", default="")
        env_var = ui.prompt_text("Environment variable name for API key", default="CUSTOM_AI_API_KEY", required=True)
    else:
        custom_name = preset.name
        openai_url = args.base_url or preset.resolved_openai_url(workspace_id)
        anth_url = args.anthropic_url or preset.resolved_anthropic_url(workspace_id)
        env_var = preset.env_var
        ui.info(f"OpenAI Base URL   : {ui.C.CYAN}{openai_url}{ui.C.RESET}")
        if anth_url:
            ui.info(f"Anthropic Base URL: {ui.C.CYAN}{anth_url}{ui.C.RESET}")
        else:
            ui.info(f"Anthropic Base URL: {ui.C.GRAY}(OpenAI-only — local bridge proxy will be used for Claude tools){ui.C.RESET}")

    existing_env_key = os.environ.get(env_var, "")
    api_key = args.api_key
    if not api_key:
        if preset.requires_key:
            api_key = ui.prompt_secret(f"{custom_name} API Key", default=existing_env_key, allow_empty=False)
        else:
            ui.info(f"{custom_name} runs locally and does not require an API key.")
            api_key = "sk-no-auth-required"

    # Model selection
    default_model = args.model or preset.default_model
    if not args.model and preset.models:
        model_items = [(m.id, m.id, m.name) for m in preset.models]
        model_items.append(("__custom__", "Enter custom model ID...", "Type any model supported by your provider"))
        picked = ui.select_one("Select default model:", model_items, default_index=0)
        if picked == "__custom__":
            default_model = ui.prompt_text("Model ID", default=preset.default_model, required=True)
        else:
            default_model = picked
    elif not args.model:
        default_model = ui.prompt_text("Default Model ID", default=preset.default_model, required=True)

    anth_model = args.anthropic_model or preset.anthropic_model or default_model
    models = list(preset.models)
    if not any(m.id == default_model for m in models):
        models.insert(0, ModelSpec(default_model, f"{default_model} ({custom_name})"))

    resolved = ResolvedProvider(
        id=pid,
        name=custom_name,
        openai_base_url=openai_url.rstrip("/"),
        anthropic_base_url=anth_url.rstrip("/"),
        api_key=api_key,
        env_var=env_var,
        model=default_model,
        anthropic_model=anth_model,
        models=models,
        requires_key=preset.requires_key,
    )

    # Optional connectivity test
    do_test = args.test or (not args.skip_test and ui.confirm("Test API connection now?", default=True))
    if do_test:
        ui.info(f"Probing {resolved.openai_base_url}/models ...")
        res = test_provider_connection(resolved.openai_base_url, resolved.effective_api_key)
        if res["ok"]:
            count = len(res.get("models") or [])
            ui.success(f"Connected! HTTP {res['status']} in {res['latency_ms']}ms ({count} models reported).")
            if res.get("models"):
                sample = ", ".join(res["models"][:6])
                ui.info(f"Sample models: {sample}")
        else:
            ui.warn(f"Connection check failed: {res.get('error')} ({res.get('latency_ms')}ms)")
            if res.get("detail"):
                ui.info(f"Response: {res['detail'][:140]}")
            if not ui.confirm("Continue writing configuration anyway?", default=True):
                raise KeyboardInterrupt

    return resolved


def resolve_provider_noninteractive(args: argparse.Namespace) -> ResolvedProvider:
    if not args.provider:
        raise SystemExit("Error: --provider is required in --non-interactive mode.")
    preset = PROVIDERS[args.provider]
    openai_url = (args.base_url or preset.resolved_openai_url(args.workspace_id)).rstrip("/")
    anth_url = (args.anthropic_url or preset.resolved_anthropic_url(args.workspace_id)).rstrip("/")
    if anth_url.endswith("/v1"):
        anth_url = anth_url[:-3]
    api_key = args.api_key or os.environ.get(preset.env_var, "") or ("sk-no-auth-required" if not preset.requires_key else "")
    if preset.requires_key and not api_key:
        raise SystemExit(f"Error: provide --api-key or set {preset.env_var} in environment.")
    model = args.model or preset.default_model
    anth_model = args.anthropic_model or preset.anthropic_model or model
    models = list(preset.models)
    if not any(m.id == model for m in models):
        models.insert(0, ModelSpec(model, f"{model} ({preset.name})"))
    return ResolvedProvider(
        id=preset.id,
        name=preset.name,
        openai_base_url=openai_url,
        anthropic_base_url=anth_url,
        api_key=api_key,
        env_var=preset.env_var,
        model=model,
        anthropic_model=anth_model,
        models=models,
        requires_key=preset.requires_key,
    )


def select_agents(args: argparse.Namespace) -> list[str]:
    if args.agents:
        if args.agents.strip().lower() == "all":
            return [a.id for a in AGENTS]
        requested = [a.strip() for a in args.agents.split(",") if a.strip()]
        invalid = [a for a in requested if a not in AGENT_MAP]
        if invalid:
            raise SystemExit(f"Unknown agent ID(s): {', '.join(invalid)}. Run --list-agents to see valid IDs.")
        return requested

    if args.non_interactive:
        raise SystemExit("Error: --agents is required in --non-interactive mode.")

    ui.step(3, 4, "Select Coding Agents & Desktop Apps to Configure")
    items = [
        (a.id, f"{a.name} [{a.category.upper()}]", a.summary)
        for a in AGENTS
    ]
    preselected = ["opencode-cli", "claude-code-cli", "pi", "vscode-copilot", "shell-env"]
    return ui.select_many("Choose all tools you want to configure:", items, preselected=preselected)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_providers:
        return cmd_list_providers()
    if args.list_agents:
        return cmd_list_agents()
    if args.restore:
        return cmd_restore()

    ui.print_banner(
        f"Agent Bridge v{__version__} — AI Provider Configurator",
        "Configure Metis, AvalAI & custom APIs across CLI + GUI coding agents",
    )

    try:
        if args.non_interactive:
            provider = resolve_provider_noninteractive(args)
            if args.test:
                res = test_provider_connection(provider.openai_base_url, provider.effective_api_key)
                if res["ok"]:
                    ui.success(f"Connection test OK ({res['latency_ms']}ms)")
                else:
                    ui.warn(f"Connection test failed: {res.get('error')}")
        else:
            provider = resolve_provider_interactive(args)

        agent_ids = select_agents(args)

        ui.step(4, 4, "Review & Apply Configuration")
        print(f"  Provider      : {ui.C.BOLD}{provider.name}{ui.C.RESET} ({provider.id})")
        print(f"  OpenAI URL    : {ui.C.CYAN}{provider.openai_base_url}{ui.C.RESET}")
        if provider.anthropic_base_url:
            print(f"  Anthropic URL : {ui.C.CYAN}{provider.anthropic_base_url}{ui.C.RESET}")
        print(f"  API Key       : {ui.mask_secret(provider.effective_api_key)}")
        print(f"  Default Model : {ui.C.BOLD}{provider.model}{ui.C.RESET}")
        print(f"  Targets ({len(agent_ids)})  : {', '.join(agent_ids)}")
        if args.dry_run:
            ui.warn("DRY RUN MODE — no files will be modified.")

        if not args.non_interactive and not ui.confirm("Apply configuration to the selected tools?", default=True):
            ui.info("Cancelled. No files were changed.")
            return 0

        backups = BackupManager(dry_run=args.dry_run)
        ui.section("Applying Configurations")
        ok_count = 0
        for aid in agent_ids:
            result = run_configurator(aid, provider, backups)
            if result.ok:
                ok_count += 1
                ui.success(f"{ui.C.BOLD}{result.agent_name}{ui.C.RESET}")
                for fpath in result.files_written:
                    tag = "(dry-run)" if args.dry_run else ""
                    print(f"     {ui.C.DIM}↳ {fpath} {tag}{ui.C.RESET}")
                for note in result.notes:
                    print(f"     {ui.C.GRAY}• {note}{ui.C.RESET}")
            else:
                ui.error(f"{result.agent_name}: {result.error}")

        print()
        ui.section("Done")
        ui.success(f"Configured {ok_count}/{len(agent_ids)} target(s) for {provider.name}.")
        if not args.dry_run and backups.manifest:
            ui.info(f"Backups saved to: {backups.session_dir} (restore anytime with `./configure.sh --restore`).")
        return 0 if ok_count == len(agent_ids) else 1

    except KeyboardInterrupt:
        print()
        ui.warn("Aborted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

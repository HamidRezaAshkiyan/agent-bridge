const PROVIDERS = [
  {
    id: 'metis',
    name: 'Metis AI',
    tagline: 'Iranian & global multi-model gateway (OpenAI + Anthropic + Gemini)',
    openaiUrl: 'https://api.metisai.ir/openai/v1',
    anthropicUrl: 'https://api.metisai.ir/anthropic',
    envVar: 'METIS_API_KEY',
    defaultModel: 'gpt-4o',
    anthropicModel: 'claude-sonnet-4-6',
  },
  {
    id: 'metis-global',
    name: 'Metis AI (TapSage)',
    tagline: 'International mirror for servers outside Iran',
    openaiUrl: 'https://api.tapsage.com/openai/v1',
    anthropicUrl: 'https://api.tapsage.com/anthropic',
    envVar: 'METIS_API_KEY',
    defaultModel: 'gpt-4o',
    anthropicModel: 'claude-sonnet-4-6',
  },
  {
    id: 'avalai',
    name: 'AvalAI',
    tagline: 'Unified OpenAI & Anthropic compatible API gateway',
    openaiUrl: 'https://api.avalai.ir/v1',
    anthropicUrl: 'https://api.avalai.ir',
    envVar: 'AVALAI_API_KEY',
    defaultModel: 'gpt-4o',
    anthropicModel: 'claude-sonnet-4-6',
  },
  {
    id: 'liara',
    name: 'Liara AI',
    tagline: 'Workspace-scoped OpenAI-compatible gateway on Liara Cloud',
    openaiUrl: 'https://ai.liara.ir/api/{workspace_id}/v1',
    anthropicUrl: '',
    envVar: 'LIARA_API_KEY',
    defaultModel: 'openai/gpt-4o-mini',
    anthropicModel: 'anthropic/claude-sonnet-4-6',
    needsWorkspace: true,
  },
  {
    id: 'gapgpt',
    name: 'GapGPT',
    tagline: 'OpenAI & Anthropic compatible multi-model gateway',
    openaiUrl: 'https://api.gapgpt.app/v1',
    anthropicUrl: 'https://api.gapgpt.app',
    envVar: 'GAPGPT_API_KEY',
    defaultModel: 'gpt-4o',
    anthropicModel: 'claude-sonnet-4-6',
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    tagline: 'Global unified router for 300+ frontier & open models',
    openaiUrl: 'https://openrouter.ai/api/v1',
    anthropicUrl: 'https://openrouter.ai/api',
    envVar: 'OPENROUTER_API_KEY',
    defaultModel: 'anthropic/claude-sonnet-4-6',
    anthropicModel: 'anthropic/claude-sonnet-4-6',
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    tagline: 'Official DeepSeek V3 & R1 API (OpenAI + Anthropic)',
    openaiUrl: 'https://api.deepseek.com/v1',
    anthropicUrl: 'https://api.deepseek.com/anthropic',
    envVar: 'DEEPSEEK_API_KEY',
    defaultModel: 'deepseek-chat',
    anthropicModel: 'deepseek-chat',
  },
  {
    id: 'groq',
    name: 'Groq',
    tagline: 'Ultra-low latency LPU inference (OpenAI-compatible)',
    openaiUrl: 'https://api.groq.com/openai/v1',
    anthropicUrl: '',
    envVar: 'GROQ_API_KEY',
    defaultModel: 'llama-3.3-70b-versatile',
    anthropicModel: 'llama-3.3-70b-versatile',
  },
  {
    id: 'together',
    name: 'Together AI',
    tagline: 'Fast open-source model hosting',
    openaiUrl: 'https://api.together.xyz/v1',
    anthropicUrl: '',
    envVar: 'TOGETHER_API_KEY',
    defaultModel: 'Qwen/Qwen2.5-Coder-32B-Instruct',
    anthropicModel: 'Qwen/Qwen2.5-Coder-32B-Instruct',
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    tagline: 'Private local models on localhost:11434 (no key required)',
    openaiUrl: 'http://localhost:11434/v1',
    anthropicUrl: 'http://localhost:11434',
    envVar: 'OLLAMA_API_KEY',
    defaultModel: 'qwen2.5-coder:14b',
    anthropicModel: 'qwen2.5-coder:14b',
    local: true,
  },
  {
    id: 'lmstudio',
    name: 'LM Studio (Local)',
    tagline: 'Local OpenAI-compatible server on localhost:1234',
    openaiUrl: 'http://localhost:1234/v1',
    anthropicUrl: '',
    envVar: 'LMSTUDIO_API_KEY',
    defaultModel: 'local-model',
    anthropicModel: 'local-model',
    local: true,
  },
  {
    id: 'custom',
    name: 'Custom Provider',
    tagline: 'Any self-hosted or third-party OpenAI/Anthropic gateway',
    openaiUrl: 'https://api.example.com/v1',
    anthropicUrl: '',
    envVar: 'CUSTOM_AI_API_KEY',
    defaultModel: 'gpt-4o',
    anthropicModel: 'claude-sonnet-4-6',
    isCustom: true,
  },
];

const AGENTS = [
  { id: 'opencode-cli', name: 'OpenCode CLI / TUI', category: 'cli', mode: 'Native', path: '~/.config/opencode/opencode.json', desc: 'Open-source terminal agent using V2 providers schema.' },
  { id: 'opencode-desktop', name: 'OpenCode Desktop (GUI)', category: 'gui', mode: 'Native', path: '~/.config/opencode/opencode.json + auth.json', desc: 'Desktop app sharing opencode.json with GUI credential store.' },
  { id: 'claude-code-cli', name: 'Claude Code CLI', category: 'cli', mode: 'Native', path: '~/.claude/settings.json', desc: 'Sets ANTHROPIC_BASE_URL (auto-strips /v1) & ANTHROPIC_AUTH_TOKEN.' },
  { id: 'claude-code-gui', name: 'Claude Code IDE Extension', category: 'gui', mode: 'Native', path: 'VS Code & Cursor settings.json', desc: 'Writes claudeCode.environmentVariables for GUI IDE extensions.' },
  { id: 'pi', name: 'Pi Coding Agent (CLI)', category: 'cli', mode: 'Native', path: '~/.pi/agent/models.json', desc: 'Full models.json provider block + default provider in settings.json.' },
  { id: 'cursor', name: 'Cursor IDE (GUI & CLI)', category: 'gui', mode: 'Guided + Env', path: 'Cursor/User/settings.json + Keychain', desc: 'Terminal env vars + step-by-step Keychain BYOK guide.' },
  { id: 'vscode-copilot', name: 'VS Code Copilot BYOK (GUI)', category: 'gui', mode: 'Native', path: 'Code/User/chatLanguageModels.json', desc: 'Native Custom Endpoint with toolCalling: true for Agent mode.' },
  { id: 'codex-cli', name: 'OpenAI Codex CLI', category: 'cli', mode: 'Native', path: '~/.codex/config.toml', desc: 'Defines [model_providers.<id>] with responses wire_api.' },
  { id: 'codex-desktop', name: 'Codex Desktop (GUI)', category: 'gui', mode: 'Native', path: '~/.codex/config.toml + proxy.json', desc: 'Shares Codex TOML config plus desktop proxy & env helper.' },
  { id: 'aider', name: 'Aider (CLI)', category: 'cli', mode: 'Native', path: '~/.aider.conf.yml', desc: 'Managed block with openai-api-base, key, and model.' },
  { id: 'zed', name: 'Zed Editor (GUI)', category: 'gui', mode: 'Native', path: '~/.config/zed/settings.json', desc: 'Adds provider under language_models.openai_compatible.' },
  { id: 'continue', name: 'Continue (VS Code / JetBrains)', category: 'gui', mode: 'Native', path: '~/.continue/config.yaml', desc: 'Generates v1 schema config.yaml with chat/edit/apply roles.' },
  { id: 'goose', name: 'Goose (CLI & Desktop)', category: 'gui', mode: 'Native', path: '~/.config/goose/config.yaml', desc: 'Configures OPENAI_HOST and OPENAI_BASE_PATH cleanly.' },
  { id: 'claude-desktop', name: 'Claude Desktop (GUI)', category: 'desktop', mode: 'Proxy + MCP', path: 'Claude/claude_desktop_config.json', desc: 'Enables Developer Third-Party Inference + MCP custom-model bridge.' },
  { id: 'chatgpt-desktop', name: 'ChatGPT Desktop & Open GUIs', category: 'desktop', mode: 'Proxy + Guide', path: '~/.agent-bridge/proxy.json', desc: 'Local OpenAI proxy + Codex config + Cherry Studio/Chatbox guide.' },
  { id: 'shell-env', name: 'Shell Environment', category: 'system', mode: 'Native', path: '~/.zshrc / ~/.bashrc / PowerShell $PROFILE', desc: 'Idempotent # >>> agent-bridge >>> block (+ Windows User Env) for all SDKs & CLIs.' },
];

function getResolvedUrls(p) {
  let openai = p.openaiUrl;
  if (p.needsWorkspace) {
    const ws = document.getElementById('inp-workspace').value.trim() || 'YOUR_WORKSPACE_ID';
    openai = openai.replace('{workspace_id}', ws);
  }
  if (p.isCustom) {
    openai = document.getElementById('inp-custom-url').value.trim() || 'https://api.example.com/v1';
  }
  openai = openai.replace(/\/+$/, '');
  const anth = p.anthropicUrl ? p.anthropicUrl.replace(/\/+$/, '') : '';
  return { openai, anth };
}

function generateConfigPreview(p, a, model) {
  const { openai, anth } = getResolvedUrls(p);
  const keyExpr = p.local ? 'sk-no-auth-required' : `{env:${p.envVar}}`;
  const keyPlaceholder = p.local ? 'sk-no-auth-required' : `YOUR_${p.envVar}`;

  switch (a.id) {
    case 'opencode-cli':
    case 'opencode-desktop':
      return JSON.stringify({
        $schema: 'https://opencode.ai/config.json',
        model: `${p.id}/${model}`,
        providers: {
          [p.id]: {
            package: '@ai-sdk/openai-compatible',
            name: p.name,
            settings: { baseURL: openai, apiKey: keyExpr },
            models: { [model]: { name: `${model} (${p.name})` } },
          },
        },
      }, null, 2);

    case 'claude-code-cli':
    case 'claude-code-gui':
      return JSON.stringify({
        env: {
          ANTHROPIC_BASE_URL: anth || 'http://127.0.0.1:4789',
          ANTHROPIC_AUTH_TOKEN: keyPlaceholder,
          ANTHROPIC_MODEL: anth ? p.anthropicModel : model,
        },
      }, null, 2);

    case 'pi':
      return JSON.stringify({
        $schema: 'https://pi.dev/schemas/models.schema.json',
        providers: {
          [p.id]: {
            name: p.name,
            baseUrl: openai,
            api: 'openai-completions',
            apiKey: p.local ? 'sk-no-auth-required' : `$${p.envVar}`,
            models: [{ id: model, name: `${model} (${p.name})`, contextWindow: 128000, maxTokens: 16384 }],
          },
        },
      }, null, 2);

    case 'vscode-copilot':
      return JSON.stringify([
        {
          name: `${p.name} (Agent Bridge)`,
          vendor: 'customendpoint',
          apiKey: p.local ? 'sk-no-auth-required' : `\${env:${p.envVar}}`,
          apiType: 'chat-completions',
          models: [
            {
              id: model,
              name: `${model} (${p.name})`,
              url: `${openai}/chat/completions`,
              toolCalling: true,
              vision: true,
              maxInputTokens: 128000,
              maxOutputTokens: 16384,
            },
          ],
        },
      ], null, 2);

    case 'codex-cli':
    case 'codex-desktop': {
      const pk = p.id.replace(/[^a-zA-Z0-9_]/g, '_');
      return `model = "${model}"\nmodel_provider = "${pk}"\n\n[model_providers.${pk}]\nname = "${p.name}"\nbase_url = "${openai}"\nwire_api = "responses"\nenv_key = "${p.envVar}"`;
    }

    case 'aider':
      return `# >>> agent-bridge-aider >>>\nopenai-api-base: ${openai}\nopenai-api-key: ${keyPlaceholder}\nmodel: openai/${model}\n# <<< agent-bridge-aider <<<`;

    case 'zed':
      return JSON.stringify({
        language_models: {
          openai_compatible: {
            [p.name]: {
              api_url: openai,
              available_models: [{ name: model, display_name: `${model} (${p.name})`, max_tokens: 128000 }],
            },
          },
        },
      }, null, 2);

    case 'continue':
      return `name: Agent Bridge Config\nversion: 1.0.0\nschema: v1\nmodels:\n  - name: ${model} (${p.name})\n    provider: openai\n    model: ${model}\n    apiBase: ${openai}\n    apiKey: ${keyPlaceholder}\n    roles: [chat, edit, apply]`;

    case 'goose': {
      let host = 'https://api.example.com';
      let basePath = 'v1/chat/completions';
      try {
        const u = new URL(openai);
        host = `${u.protocol}//${u.host}`;
        basePath = `${u.pathname.replace(/\/+$/, '')}/chat/completions`.replace(/^\/+/, '');
      } catch (_) {}
      return `GOOSE_PROVIDER: openai\nGOOSE_MODEL: ${model}\nOPENAI_HOST: ${host}\nOPENAI_BASE_PATH: ${basePath}`;
    }

    case 'claude-desktop':
      return JSON.stringify({
        mcpServers: {
          'agent-bridge-models': {
            command: 'python3',
            args: ['/path/to/agent-bridge/lib/mcp_model_bridge.py'],
            env: { AGENT_BRIDGE_MCP_CONFIG: '~/.agent-bridge/proxy.json' },
          },
        },
        _thirdPartyInferenceURL: anth || 'http://127.0.0.1:4789',
      }, null, 2);

    case 'chatgpt-desktop':
      return JSON.stringify({
        provider_name: p.name,
        openai_base_url: openai,
        default_model: model,
        local_proxy_url: 'http://127.0.0.1:4789/v1',
        start_command: '~/.agent-bridge/start-proxy.sh',
      }, null, 2);

    case 'cursor':
      return `// Cursor Settings -> Models -> API Keys (stored in OS Keychain)\nOverride OpenAI Base URL : ${openai}\nOpenAI API Key           : ${keyPlaceholder}\nModel ID                 : ${model}\n\n// Plus terminal.integrated.env updated in Cursor/User/settings.json`;

    default:
      return `# >>> agent-bridge >>>\nexport AGENT_BRIDGE_PROVIDER="${p.id}"\nexport ${p.envVar}="${keyPlaceholder}"\nexport OPENAI_BASE_URL="${openai}"\nexport OPENAI_API_KEY="${keyPlaceholder}"${anth ? `\nexport ANTHROPIC_BASE_URL="${anth}"\nexport ANTHROPIC_AUTH_TOKEN="${keyPlaceholder}"` : ''}\n# <<< agent-bridge <<<`;
  }
}

function updateBuilder() {
  const pid = document.getElementById('sel-provider').value;
  const aid = document.getElementById('sel-agent').value;
  const p = PROVIDERS.find((x) => x.id === pid) || PROVIDERS[0];
  const a = AGENTS.find((x) => x.id === aid) || AGENTS[0];

  document.getElementById('workspace-field').hidden = !p.needsWorkspace;
  document.getElementById('custom-url-field').hidden = !p.isCustom;

  const modelInput = document.getElementById('inp-model');
  const model = modelInput.value.trim() || p.defaultModel;

  document.getElementById('out-path').textContent = a.path;
  const modeEl = document.getElementById('out-mode');
  modeEl.textContent = a.mode;
  modeEl.className = 'badge ' + (a.mode === 'Native' ? 'badge-green' : a.mode.includes('Proxy') ? 'badge-purple' : 'badge-yellow');

  const { openai } = getResolvedUrls(p);
  let cmd = `./configure.sh --non-interactive --provider ${p.id} --agents ${a.id} --model "${model}"`;
  if (!p.local) cmd += ` --api-key "YOUR_API_KEY"`;
  if (p.needsWorkspace) cmd += ` --workspace-id "${document.getElementById('inp-workspace').value.trim() || 'YOUR_WORKSPACE_ID'}"`;
  if (p.isCustom) cmd += ` --base-url "${openai}"`;

  document.getElementById('out-cmd').textContent = cmd;
  document.getElementById('out-file-title').textContent = `Preview: ${a.path}`;
  document.getElementById('out-config').textContent = generateConfigPreview(p, a, model);
}

function renderProviders() {
  const grid = document.getElementById('providers-grid');
  grid.innerHTML = '';
  PROVIDERS.forEach((p) => {
    const card = document.createElement('article');
    card.className = 'card provider-card';
    card.innerHTML = `
      <div class="provider-top">
        <h3>${p.name}</h3>
        <span class="badge ${p.anthropicUrl ? 'badge-green' : 'badge-cyan'}">${p.anthropicUrl ? 'OpenAI + Anthropic' : 'OpenAI + Proxy'}</span>
      </div>
      <p>${p.tagline}</p>
      <div class="provider-urls">
        <span title="${p.openaiUrl}">OpenAI: ${p.openaiUrl}</span>
        <span>Anthropic: ${p.anthropicUrl || 'Auto-translated via local proxy'}</span>
      </div>
    `;
    card.addEventListener('click', () => {
      document.getElementById('sel-provider').value = p.id;
      document.getElementById('inp-model').value = p.defaultModel;
      updateBuilder();
      document.getElementById('builder').scrollIntoView({ behavior: 'smooth' });
    });
    grid.appendChild(card);
  });
}

function renderAgents(filter = 'all') {
  const grid = document.getElementById('agents-grid');
  grid.innerHTML = '';
  AGENTS.filter((a) => filter === 'all' || a.category === filter).forEach((a) => {
    const badgeClass = a.mode === 'Native' ? 'badge-green' : a.mode.includes('Proxy') ? 'badge-purple' : 'badge-yellow';
    const card = document.createElement('article');
    card.className = 'card';
    card.innerHTML = `
      <div class="agent-card-top">
        <h3>${a.name}</h3>
        <span class="badge ${badgeClass}">${a.mode}</span>
      </div>
      <p>${a.desc}</p>
      <div class="agent-path">${a.path}</div>
    `;
    grid.appendChild(card);
  });
}

function init() {
  // Populate dropdowns
  const selP = document.getElementById('sel-provider');
  PROVIDERS.forEach((p) => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = p.name;
    selP.appendChild(opt);
  });

  const selA = document.getElementById('sel-agent');
  AGENTS.forEach((a) => {
    const opt = document.createElement('option');
    opt.value = a.id;
    opt.textContent = a.name;
    selA.appendChild(opt);
  });

  document.getElementById('inp-model').value = PROVIDERS[0].defaultModel;

  selP.addEventListener('change', () => {
    const p = PROVIDERS.find((x) => x.id === selP.value);
    if (p) document.getElementById('inp-model').value = p.defaultModel;
    updateBuilder();
  });
  selA.addEventListener('change', updateBuilder);
  document.getElementById('inp-model').addEventListener('input', updateBuilder);
  document.getElementById('inp-workspace').addEventListener('input', updateBuilder);
  document.getElementById('inp-custom-url').addEventListener('input', updateBuilder);

  // Quickstart tabs
  document.querySelectorAll('.qs-tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.qs-tab').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('hero-cmd').textContent = btn.dataset.cmd;
    });
  });

  // Agent filter buttons
  document.querySelectorAll('.filter-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      renderAgents(btn.dataset.filter);
    });
  });

  // Copy buttons
  document.querySelectorAll('.copy-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const target = document.getElementById(btn.dataset.copyTarget);
      if (!target) return;
      try {
        await navigator.clipboard.writeText(target.textContent);
        const orig = btn.textContent;
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = orig;
          btn.classList.remove('copied');
        }, 1600);
      } catch (_) {}
    });
  });

  renderProviders();
  renderAgents('all');
  updateBuilder();
}

document.addEventListener('DOMContentLoaded', init);

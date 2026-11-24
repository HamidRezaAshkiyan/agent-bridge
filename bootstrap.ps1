# One-liner PowerShell bootstrapper for Agent Bridge (Windows)
# Usage:
#   irm https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.ps1 | iex
#   $env:AGENT_BRIDGE_MODE="install"; irm https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.ps1 | iex
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.ps1))) install

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Mode = "",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassThruArgs = @()
)

$ErrorActionPreference = "Stop"

$RepoUrl = if ($env:AGENT_BRIDGE_REPO) { $env:AGENT_BRIDGE_REPO } else { "https://github.com/HamidRezaAshkiyan/agent-bridge.git" }
$InstallDir = if ($env:AGENT_BRIDGE_HOME) { $env:AGENT_BRIDGE_HOME } else { Join-Path $HOME ".agent-bridge\repo" }

if (-not $Mode) {
    $Mode = if ($env:AGENT_BRIDGE_MODE) { $env:AGENT_BRIDGE_MODE } else { "configure" }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Error: 'git' is required to run Agent Bridge. Install Git for Windows: winget install Git.Git"
    exit 1
}

function Find-Python {
    foreach ($candidate in @("python", "python3", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        # Skip the Windows Store app execution alias stub
        if ($cmd.Source -like "*\WindowsApps\python*.exe") {
            try {
                $ver = & $cmd.Source --version 2>&1
                if ($LASTEXITCODE -ne 0 -or $ver -notmatch "Python 3\.") { continue }
            } catch { continue }
        }
        try {
            if ($candidate -eq "py") {
                $ver = & py -3 --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3\.") { return @("py", "-3") }
            } else {
                $ver = & $cmd.Source --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3\.") { return @($cmd.Source) }
            }
        } catch { continue }
    }
    return $null
}

$pyCmd = Find-Python
if (-not $pyCmd) {
    Write-Error "Error: Python 3.8+ is required. Install it via: winget install Python.Python.3.12"
    exit 1
}

$parentDir = Split-Path -Parent $InstallDir
if (-not (Test-Path $parentDir)) {
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
}

if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Host "Updating Agent Bridge in $InstallDir ..."
    try {
        & git -C $InstallDir pull --ff-only --quiet
    } catch {
        # Continue with existing local copy if offline or diverged
    }
} else {
    Write-Host "Cloning Agent Bridge into $InstallDir ..."
    & git clone --depth 1 --quiet $RepoUrl $InstallDir
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

if ($Mode -eq "install") {
    $script = Join-Path $InstallDir "install-agent.ps1"
} else {
    $script = Join-Path $InstallDir "configure.ps1"
}

& $script @PassThruArgs
exit $LASTEXITCODE

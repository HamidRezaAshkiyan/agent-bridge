# Agent Bridge - Windows one-liner bootstrapper (PowerShell).
#
# Usage:
#   irm https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.ps1 | iex
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/HamidRezaAshkiyan/agent-bridge/main/bootstrap.ps1))) install
#
# The "irm | iex" form cannot receive arguments, so to install coding agents
# (instead of configuring a provider) use the second form above, or pass
# -Mode install after cloning the repo.

[CmdletBinding()]
param(
    [ValidateSet('configure', 'install')]
    [string] $Mode = 'configure',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Args
)

$ErrorActionPreference = 'Stop'

$repoUrl = if ($env:AGENT_BRIDGE_REPO) { $env:AGENT_BRIDGE_REPO } else { 'https://github.com/HamidRezaAshkiyan/agent-bridge.git' }
$installDir = if ($env:AGENT_BRIDGE_HOME) { $env:AGENT_BRIDGE_HOME } else { Join-Path $env:USERPROFILE '.agent-bridge\repo' }

function Test-Command {
    param([string] $Name)
    return [bool] (Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-Command git)) {
    Write-Host "Error: 'git' is required to run Agent Bridge." -ForegroundColor Red
    Write-Host "Install it with:  winget install --id Git.Git -e" -ForegroundColor Yellow
    exit 1
}

$pythonOk = $false
foreach ($candidate in @('py', 'python3', 'python')) {
    if (Test-Command $candidate) { $pythonOk = $true; break }
}
if (-not $pythonOk) {
    Write-Host "Error: 'Python 3' is required to run Agent Bridge." -ForegroundColor Red
    Write-Host "Install it with:  winget install --id Python.Python.3.12 -e" -ForegroundColor Yellow
    exit 1
}

$gitDir = Join-Path $installDir '.git'
if (Test-Path $gitDir) {
    Write-Host "Updating Agent Bridge in $installDir ..." -ForegroundColor Cyan
    git -C $installDir pull --ff-only --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Could not fast-forward; keeping the existing checkout." -ForegroundColor Yellow
    }
}
else {
    Write-Host "Cloning Agent Bridge into $installDir ..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path (Split-Path -Parent $installDir) -Force | Out-Null
    git clone --depth 1 --quiet $repoUrl $installDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: git clone failed." -ForegroundColor Red
        exit 1
    }
}

$entry = if ($Mode -eq 'install') { 'install-agent.ps1' } else { 'configure.ps1' }
$entryPath = Join-Path $installDir $entry

. (Join-Path $installDir 'scripts\args.ps1')
$forwarded = ConvertFrom-AgentBridgeArgs -Arguments $Args -ListFlags @('--agents')

Write-Host ""
Write-Host ("Launching " + $entry) -ForegroundColor Green
& $entryPath @forwarded
exit $LASTEXITCODE

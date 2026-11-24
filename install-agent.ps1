<#
.SYNOPSIS
    Agent Bridge - interactive coding agent installer (Windows entry point).

.DESCRIPTION
    Windows counterpart of ./install-agent.sh. Locates a Python 3 interpreter and runs
    lib/install_agent.py with whatever arguments you pass through.

.EXAMPLE
    ./install-agent.ps1

.EXAMPLE
    ./install-agent.ps1 --list
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Args
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

. (Join-Path $scriptDir 'scripts\python-detect.ps1')
. (Join-Path $scriptDir 'scripts\args.ps1')

$python = Get-AgentBridgePython
if (-not $python) {
    Write-Host "Error: Python 3.9+ is required to run Agent Bridge." -ForegroundColor Red
    Write-Host "Install it with:  winget install --id Python.Python.3.12 -e" -ForegroundColor Yellow
    Write-Host "or download from: https://www.python.org/downloads/windows/" -ForegroundColor Yellow
    exit 1
}

$arguments = ConvertFrom-AgentBridgeArgs -Arguments $Args -ListFlags @('--agents')

& $python (Join-Path $scriptDir 'lib\install_agent.py') @arguments
exit $LASTEXITCODE

<#
.SYNOPSIS
    Agent Bridge - interactive AI provider configurator (Windows entry point).

.DESCRIPTION
    Windows counterpart of ./configure.sh. Locates a Python 3 interpreter and runs
    lib/configure.py with whatever arguments you pass through.

.EXAMPLE
    ./configure.ps1

.EXAMPLE
    ./configure.ps1 --provider metis --agents all --non-interactive
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

& $python (Join-Path $scriptDir 'lib\configure.py') @arguments
exit $LASTEXITCODE

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
    Write-Host ""
    Write-Host "Diagnostics:" -ForegroundColor Yellow
    foreach ($candidate in @('py', 'python3', 'python')) {
        $found = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($found) {
            Write-Host ("  found '{0}' at {1}" -f $candidate, $found.Source)
            $ver = Invoke-PythonProbe -Exe $candidate -Prefix @() -Code 'import sys; print(sys.version)'
            if ($ver) { Write-Host ("    version: {0}" -f "$ver".Trim()) }
            else { Write-Host "    could not execute it (blocked, or not a real interpreter)" }
        }
        else {
            Write-Host ("  '{0}' not on PATH" -f $candidate)
        }
    }
    Write-Host "  Tip: set AGENT_BRIDGE_PYTHON to a python.exe path to skip detection."
    exit 1
}

# Wrap in @() : a single-element return collapses to a plain string, and splatting a
# string enumerates its characters ("- - l i s t ...") instead of passing one argument.
$forwardArgs = @(ConvertFrom-AgentBridgeArgs -Arguments $Args -ListFlags @('--agents'))

& $python (Join-Path $scriptDir 'lib\configure.py') @forwardArgs
exit $LASTEXITCODE

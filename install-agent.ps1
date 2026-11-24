#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $ScriptDir "lib\install_agent.py"

function Resolve-Python {
    foreach ($candidate in @("python", "python3", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        try {
            if ($candidate -eq "py") {
                $ver = & py -3 --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3\.") {
                    return @{ Exe = "py"; Prefix = @("-3") }
                }
            } else {
                $ver = & $cmd.Source --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3\.") {
                    return @{ Exe = $cmd.Source; Prefix = @() }
                }
            }
        } catch { continue }
    }
    return $null
}

$py = Resolve-Python
if (-not $py) {
    Write-Error "Error: Python 3.8+ is required. Install Python via 'winget install Python.Python.3.12' or https://www.python.org/downloads/"
    exit 1
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

& $py.Exe @($py.Prefix) $Target @args
exit $LASTEXITCODE

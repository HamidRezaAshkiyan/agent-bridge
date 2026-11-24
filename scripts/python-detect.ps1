# Agent Bridge - shared Python 3 discovery for the PowerShell entry points.
# Dot-source this file, then call Get-AgentBridgePython.

function Invoke-PythonProbe {
    <#
    .SYNOPSIS
        Runs a Python candidate and returns its stdout, or $null on any failure.

    .DESCRIPTION
        Native command failures (missing shim, Store alias stub, blocked exec) must
        never abort the caller, so errors are suppressed locally instead of relying
        on the caller's $ErrorActionPreference.
    #>
    param(
        [Parameter(Mandatory)][string] $Exe,
        [string[]] $Prefix = @(),
        [string] $Code
    )

    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $arguments = @()
        $arguments += $Prefix
        $arguments += @('-c', $Code)
        $output = & $Exe @arguments 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        return $output
    }
    catch {
        return $null
    }
    finally {
        $ErrorActionPreference = $previous
    }
}

function Get-AgentBridgePython {
    <#
    .SYNOPSIS
        Returns the path to a usable Python 3 interpreter, or $null.

    .DESCRIPTION
        Tries, in order:
          1. AGENT_BRIDGE_PYTHON (explicit override)
          2. the 'py' launcher with -3 (standard Python for Windows install)
          3. python3 on PATH (scoop / MSYS / Store builds)
          4. python on PATH, if it reports version 3

        Candidates that fail to launch are skipped, so a broken 'py' alias (a common
        Windows Store stub) falls through to the next option instead of aborting.
    #>
    [CmdletBinding()]
    param(
        [int] $MinimumMinor = 9
    )

    $candidates = @()

    if ($env:AGENT_BRIDGE_PYTHON) {
        $candidates += , @($env:AGENT_BRIDGE_PYTHON, @())
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $candidates += , @('py', @('-3'))
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $candidates += , @('python3', @())
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $candidates += , @('python', @())
    }

    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        $prefix = $candidate[1]

        $version = Invoke-PythonProbe -Exe $exe -Prefix $prefix -Code 'import sys; print("%d.%d" % sys.version_info[:2])'
        if (-not $version) { continue }

        $parts = "$version".Trim().Split('.')
        if ($parts.Count -lt 2) { continue }

        $major = 0
        $minor = 0
        if (-not [int]::TryParse($parts[0], [ref] $major)) { continue }
        if (-not [int]::TryParse($parts[1], [ref] $minor)) { continue }
        if ($major -ne 3 -or $minor -lt $MinimumMinor) { continue }

        # Resolve to a concrete executable path so later calls skip the launcher.
        $exePath = Invoke-PythonProbe -Exe $exe -Prefix $prefix -Code 'import sys; print(sys.executable)'
        if ($exePath) { return "$exePath".Trim() }
        return $exe
    }

    return $null
}

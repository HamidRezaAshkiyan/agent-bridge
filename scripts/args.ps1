# Agent Bridge - shared argument normalisation for the PowerShell entry points.
# Dot-source this file, then call ConvertFrom-AgentBridgeArgs.
#
# Why this exists:
#   PowerShell treats an unquoted comma as an array separator, so the very natural
#   invocation
#
#       ./configure.ps1 --agents opencode-cli,pi
#
#   reaches the script as @('--agents', 'opencode-cli', 'pi') - the comma is gone and
#   argparse sees two positional tokens. Requiring quotes would be a papercut, so the
#   list-valued flags are re-joined here before the arguments reach Python.

function ConvertFrom-AgentBridgeArgs {
    <#
    .SYNOPSIS
        Re-joins comma-separated list arguments that PowerShell split on parse.

    .DESCRIPTION
        For each flag in -ListFlags, every consecutive token that is not itself a
        recognised flag is glued back together with commas and passed as one value.
        Tokens that start with '-' are treated as the next flag.

    .EXAMPLE
        ConvertFrom-AgentBridgeArgs -Arguments @('--agents','opencode-cli','pi','--dry-run')
        # -> @('--agents','opencode-cli,pi','--dry-run')
    #>
    param(
        [string[]] $Arguments = @(),
        [string[]] $ListFlags = @('--agents')
    )

    if (-not $Arguments -or $Arguments.Count -eq 0) { return @() }

    $normalised = New-Object System.Collections.Generic.List[string]
    $index = 0

    while ($index -lt $Arguments.Count) {
        $token = $Arguments[$index]

        if ($ListFlags -notcontains $token) {
            $normalised.Add($token)
            $index++
            continue
        }

        # Collect the flag's value plus any tokens PowerShell split off after it.
        $normalised.Add($token)
        $index++

        $values = New-Object System.Collections.Generic.List[string]
        while ($index -lt $Arguments.Count) {
            $candidate = $Arguments[$index]
            if ($candidate -like '-*') { break }
            $values.Add($candidate)
            $index++
        }

        if ($values.Count -gt 0) {
            $normalised.Add(($values -join ','))
        }
    }

    # Callers must wrap the result in @(): a single-element array collapses to a string
    # on output, and splatting a string enumerates its characters.
    return $normalised.ToArray()
}

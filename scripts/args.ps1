# Agent Bridge - shared argument normalisation for the PowerShell entry points.
# Dot-source this file, then call ConvertFrom-AgentBridgeArgs.
#
# Why this exists:
#   PowerShell treats an unquoted comma as an array separator, so the very natural
#   invocation
#
#       ./configure.ps1 --agents opencode-cli,pi
#
#   does not arrive as the string "opencode-cli,pi". Depending on how the script is
#   launched the value becomes either an array of tokens or a single space-joined
#   token ("opencode-cli pi") - in both cases the comma is lost and argparse sees
#   garbage. Requiring quotes would be a papercut, so the value of list-valued flags
#   is re-normalised here into a comma-separated string before reaching Python.
#
#   Agent IDs and provider IDs never contain whitespace, so splitting on both commas
#   and whitespace is unambiguous for the flags this applies to.

function ConvertFrom-AgentBridgeArgs {
    <#
    .SYNOPSIS
        Normalises list-valued flags that PowerShell split or space-joined.

    .DESCRIPTION
        For each flag in -ListFlags, every consecutive token that is not itself a
        recognised flag is collected, split on commas/whitespace, and re-joined with
        commas as a single value. Tokens starting with '-' begin the next flag.

    .EXAMPLE
        ConvertFrom-AgentBridgeArgs -Arguments @('--agents','opencode-cli','pi','--dry-run')
        # -> @('--agents','opencode-cli,pi','--dry-run')

    .EXAMPLE
        # The form PowerShell produces when the comma-array is stringified:
        ConvertFrom-AgentBridgeArgs -Arguments @('--agents','opencode-cli pi','--dry-run')
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

        $items = New-Object System.Collections.Generic.List[string]
        while ($index -lt $Arguments.Count) {
            $candidate = $Arguments[$index]
            if ($candidate -like '-*') { break }
            foreach ($piece in ($candidate -split '[,\s]+')) {
                if ($piece) { $items.Add($piece) }
            }
            $index++
        }

        if ($items.Count -gt 0) {
            $normalised.Add(($items -join ','))
        }
    }

    # Callers must wrap the result in @(): a single-element array collapses to a string
    # on output, and splatting a string enumerates its characters.
    return $normalised.ToArray()
}

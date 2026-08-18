<#
.SYNOPSIS
    Wiz Health Assessment & Skills installer for Windows PowerShell.

.DESCRIPTION
    Locates a suitable Python interpreter and delegates to install.py, which
    does the real work. Windows users need no bash, WSL, or Git Bash.

.EXAMPLE
    .\install.ps1
    Interactive install.

.EXAMPLE
    .\install.ps1 -Yes -Target claude
    Unattended install into Claude Code.

.NOTES
    If Windows blocks the script, either run it once as:
        powershell -ExecutionPolicy Bypass -File .\install.ps1
    or allow local scripts for your user:
        Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#>

[CmdletBinding()]
param(
    [string]$Target,
    [switch]$Yes,
    [switch]$SkipCredentials,
    [switch]$SkipDeps
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

# Candidate interpreters, best first. The py launcher is the most reliable on
# Windows; bare "python"/"python3" may be a Microsoft Store stub that is on
# PATH but cannot execute, so each candidate is version-probed before use.
$candidates = @(
    @{ Exe = 'py';      Prefix = @('-3') },
    @{ Exe = 'python';  Prefix = @() },
    @{ Exe = 'python3'; Prefix = @() }
)

$python = $null
foreach ($candidate in $candidates) {
    if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) { continue }
    $probe = @($candidate.Prefix) + @('-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)')

    # Windows PowerShell 5.1 wraps a native command's stderr in an ErrorRecord,
    # which would be terminating under the script's 'Stop' preference and make a
    # perfectly good interpreter look unusable. Relax the preference for the
    # probe and judge the candidate purely by its exit code.
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $candidate.Exe @probe 2>&1 | Out-Null
        $exitCode = $LASTEXITCODE
    } catch {
        $exitCode = 1
    } finally {
        $ErrorActionPreference = $previousPreference
    }

    if ($exitCode -eq 0) { $python = $candidate; break }
}

if ($null -eq $python) {
    Write-Host '[!] Python 3.8+ is required but was not found on PATH.'
    Write-Host '    Looked for: py -3, python, python3'
    Write-Host '    Install it from https://www.python.org/downloads/ (tick'
    Write-Host '    "Add python.exe to PATH" in the installer) and re-run this script.'
    exit 1
}

$forwarded = @('install.py')
if ($Target)          { $forwarded += @('--target', $Target) }
if ($Yes)             { $forwarded += '--yes' }
if ($SkipCredentials) { $forwarded += '--skip-credentials' }
if ($SkipDeps)        { $forwarded += '--skip-deps' }

$arguments = @($python.Prefix) + $forwarded
& $python.Exe @arguments
exit $LASTEXITCODE

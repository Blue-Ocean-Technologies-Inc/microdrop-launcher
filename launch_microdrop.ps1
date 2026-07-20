# Slim launcher: env setup + arg forwarding only. Git operations, pixi
# self-update, and launch configuration live in microdrop_setup.py.
# Location-independent: -InstallDir points at the pixi-microdrop checkout and
# defaults to this script's own folder (so a direct run from the repo root
# still works); microdrop_setup passes it explicitly when it lives elsewhere.
param (
    # pixi-microdrop checkout root (the folder containing microdrop-py/).
    [string]$InstallDir = $PSScriptRoot,

    # Back-compat with the old .bat wrappers; equivalent to "--device <x>".
    [ValidateSet("dropbot", "opendrop", "mock")]
    [string]$Device,

    [Parameter(ValueFromRemainingArguments)]
    $MicrodropArgs
)

$Host.UI.RawUI.WindowTitle = "Microdrop (Beta)"

$parentPath = Join-Path -Path $InstallDir -ChildPath "microdrop-py"

Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "      Pixi Microdrop Launcher           " -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Cyan

if (-not (Get-Command "pixi" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: 'pixi' command not found. Is it installed and in your PATH?" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -Path $parentPath)) {
    Write-Host "Error: microdrop-py not found at $parentPath" -ForegroundColor Red
    exit 1
}

Set-Location -Path $parentPath

$runArgs = @()
if ($Device) { $runArgs += @("--device", $Device) }
if ($MicrodropArgs) { $runArgs += $MicrodropArgs }

Write-Host "Starting Microdrop..." -ForegroundColor Magenta
& pixi run microdrop_launch @runArgs

Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "Done." -ForegroundColor Gray

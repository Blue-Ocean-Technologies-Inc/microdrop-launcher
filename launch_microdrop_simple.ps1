# Simple launcher: runs the Microdrop source's own entry point,
# `pixi run microdrop --device <device>`, which always loads the current
# release's full plugin set. Git operations and pixi self-update live in
# microdrop_setup.py; launch_microdrop.ps1 is the fine-grained counterpart.
# Location-independent: -InstallDir points at the pixi-microdrop checkout and
# defaults to this script's own folder (so a direct run from the repo root
# still works); microdrop_setup passes it explicitly when it lives elsewhere.
param (
    # pixi-microdrop checkout root (the folder containing microdrop-py/).
    [string]$InstallDir = $PSScriptRoot,

    [ValidateSet("dropbot", "portable", "opendrop", "mock")]
    [string]$Device = "dropbot"
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

Write-Host "Starting Microdrop..." -ForegroundColor Magenta
& pixi run microdrop --device $Device

Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "Done." -ForegroundColor Gray

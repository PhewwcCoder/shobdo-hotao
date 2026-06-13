# Folder-based PyInstaller build (preferred over single-file) -> dist\ShobdoHotao\
# Phase 3 will flesh out model/font/ffmpeg bundling and code-signing hooks.
$ErrorActionPreference = "Stop"
$venvPy = Join-Path (Resolve-Path ".venv") "Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    throw "No .venv found. Run scripts\setup_windows.ps1 first."
}

& $venvPy -m PyInstaller `
    --noconfirm `
    --name ShobdoHotao `
    --windowed `
    --add-data "models;models" `
    --add-data "src/shobdohotao/ui/theme/assets;shobdohotao/ui/theme/assets" `
    src/shobdohotao/__main__.py

Write-Host "Build output: dist\ShobdoHotao\"

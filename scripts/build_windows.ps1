# Folder-based PyInstaller build (preferred over single-file) -> dist\ShobdoHotao\
#
# Collects DeepFilterNet (df) data/binaries and the theme assets. PyInstaller's
# built-in hooks handle torch/torchaudio. A custom icon is embedded if
# assets\app.ico exists. Run scripts\setup_windows.ps1 first to create .venv.
$ErrorActionPreference = "Stop"
$venvPy = Join-Path (Resolve-Path ".venv") "Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    throw "No .venv found. Run scripts\setup_windows.ps1 first."
}

$pyArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--name", "ShobdoHotao",
    "--windowed",
    # DeepFilterNet ships its runtime pieces as package data + a native lib.
    "--collect-all", "df",
    # Bundled UI artwork (backgrounds, etc.).
    "--add-data", "src/shobdohotao/ui/theme/assets;shobdohotao/ui/theme/assets",
    # Pre-fetched model weights, when present (otherwise fetched on first run).
    "--add-data", "models;models"
)
if (Test-Path "assets\app.ico") {
    $pyArgs += @("--icon", "assets\app.ico")
}
$pyArgs += "src/shobdohotao/__main__.py"

& $venvPy @pyArgs

Write-Host "Build output: dist\ShobdoHotao\"

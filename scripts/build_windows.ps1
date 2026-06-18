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
    # Find the package under src/ and bundle ALL its submodules (the app uses
    # lazy/function-level imports that static analysis can otherwise miss).
    "--paths", "src",
    "--collect-submodules", "shobdohotao",
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
# Entry is the package-aware launcher (main.py), NOT __main__.py directly:
# running __main__.py as a script breaks its relative imports.
$pyArgs += "main.py"

& $venvPy @pyArgs

Write-Host "Build output: dist\ShobdoHotao\"

# Launches ShobdoHotao from the local virtual environment.
$ErrorActionPreference = "Stop"
$venvPy = Join-Path (Resolve-Path ".venv") "Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    throw "No .venv found. Run scripts\setup_windows.ps1 first."
}
& $venvPy -m shobdohotao

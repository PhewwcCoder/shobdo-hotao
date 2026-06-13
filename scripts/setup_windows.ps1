# Sets up a reproducible Python 3.11 dev environment on Windows.
# Installs CPU PyTorch FIRST (so DeepFilterNet does not pull a CUDA build),
# then the app + dev dependencies. Run from the repository root.

$ErrorActionPreference = "Stop"

# Prefer the 3.11 launcher; fall back to whatever 'python' is if absent.
$py = "py"
$pyArgs = @("-3.11")
try { & $py $pyArgs --version } catch { $py = "python"; $pyArgs = @() }

Write-Host "Creating virtual environment (.venv)..."
& $py $pyArgs -m venv .venv

$venvPy = Join-Path (Resolve-Path ".venv") "Scripts\python.exe"

Write-Host "Upgrading pip..."
& $venvPy -m pip install --upgrade pip

Write-Host "Installing CPU PyTorch first (pinned for DeepFilterNet 0.5.6)..."
# DeepFilterNet 0.5.6 imports torchaudio.backend.common, removed in torchaudio
# >= 2.2. Pin the last compatible CPU pair.
& $venvPy -m pip install "torch==2.0.1" "torchaudio==2.0.2" `
    --index-url https://download.pytorch.org/whl/cpu

Write-Host "Installing soundfile (torchaudio I/O backend on Windows)..."
& $venvPy -m pip install soundfile

Write-Host "Installing app + dev dependencies..."
& $venvPy -m pip install -e ".[dev]"

Write-Host "Done. Activate with: .\.venv\Scripts\Activate.ps1"

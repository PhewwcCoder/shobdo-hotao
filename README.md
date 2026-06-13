# শব্দ-হটাও · ShobdoHotao

**আপনার রেকর্ডিং থেকে আওয়াজ দূর করুন — সম্পূর্ণ অফলাইনে।**
Remove background noise from your recordings — fully offline.

Select a noisy recording, choose a strength, click **Clean Audio / আওয়াজ দূর করুন**,
compare, and export. No account. No upload. No limit.

Works on **audio files** (MP3/WAV/M4A/FLAC/…) and on the **audio track of videos**
(MP4/MOV/MKV/AVI/WebM): the video is copied losslessly and only its noisy audio
is cleaned and remuxed back. See [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md).

---

## Privacy first

- Audio **never leaves your computer**. No login, API key, cloud, telemetry, ads, or quota.
- Core processing works **without internet** after installation.
- App source is **MIT**; third-party licenses are preserved in
  [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Status

Early scaffold (Phase 1). The architecture, pure-Python core, i18n catalogs
(Bangla + English), and a placeholder Aero UI shell are in place with a passing
test suite. The DeepFilterNet3 backend and Qt UI require the full dependency set
(see below). See [`docs/AUDIT.md`](docs/AUDIT.md) for the current state and
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for layer boundaries.

## Requirements

- Windows 10/11 x64 (default target), CPU-only.
- Python **3.11** (64-bit) for development.

> **PyTorch pin:** DeepFilterNet 0.5.6 requires `torch==2.0.1` + `torchaudio==2.0.2`
> (newer torchaudio removed `torchaudio.backend.common`, which DeepFilterNet
> imports). `setup_windows.ps1` installs these CPU builds for you.

## Setup (development)

```powershell
# from the repo root
./scripts/setup_windows.ps1     # creates .venv, installs CPU PyTorch + deps
./scripts/run_windows.ps1       # launches the app
```

## Run tests

The pure-Python core has no heavy dependencies and tests run anywhere:

```bash
python -m pytest          # or: PYTHONPATH=src python -m pytest
ruff check .
```

## Build (Windows release ZIP)

```powershell
./scripts/build_windows.ps1     # folder-based PyInstaller build
```

## License

MIT — see [`LICENSE`](LICENSE).

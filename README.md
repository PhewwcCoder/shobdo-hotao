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

Working desktop app (audio + video) with a managed local library. Cleaned files
are saved under your **Documents** folder:

```
Documents/ShobdoHotao/
├── Cleaned Files/{Audio,Video}/   # your results
├── Database/  Logs/  Temp/
```

During processing a dedicated **Processing view** shows a live pipeline stepper,
a reactive signal visualizer, and a real engine log (genuine FFmpeg progress for
video; honest elapsed/stage for AI denoising — no fake percentages). After
processing you **name the file** (live Windows-safe validation), then a
**completion screen** offers Play/Open, Show in Folder, and Clean Another. A
**Cleaned Files** button opens your library. Everything stays offline.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for layer boundaries,
[`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) for behaviour, and
[`docs/ROADMAP.md`](docs/ROADMAP.md) for what's next (in-app library screen,
storage settings, installer).

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

# Architecture

Strict layer boundaries. Arrows show allowed dependencies; nothing points back up.

```
__main__ ─▶ ui/ ─▶ workers/ ─▶ services/pipeline ───────▶ ffmpeg_service
              │       │      ─▶ services/video_processing ─▶ media/ ─▶ ffmpeg_runner
              │       │                │                     │         ├▶ probe
              │       │                │                     │         ├▶ video_extractor
              │       │                └▶ denoise_backend    │         └▶ video_muxer
              ▼       └▶ processing_worker / video_worker
          i18n/ , config , ui/theme          domain  (imported by everyone, imports nothing app-specific)
```

## Two processing paths

| | Audio | Video |
|--|-------|-------|
| Orchestrator | `services/pipeline.Pipeline` | `services/video_processing_service.VideoProcessingService` |
| Worker | `workers/processing_worker` | `workers/video_worker` |
| Media ops | `services/ffmpeg_service`, `services/media_probe` | `media/` (probe, video_extractor, video_muxer, ffmpeg_runner) |
| Stages | validate → convert → enhance → export | inspect → extract → enhance → mux |

Both reuse the **same** `services/denoise_backend` (DeepFilterNet3, lazily
initialised once per process) and the same collision-safe naming
(`domain.derive_cleaned_path`).

## The media/ subpackage (video)

- **`ffmpeg_runner.FfmpegRunner`** — `Popen`-based, **cancellable**: `cancel()`
  terminates (then kills) the active FFmpeg process so the UI Cancel button can
  stop a long encode. (The short audio convert path keeps the simpler blocking
  `ffmpeg_service.run_ffmpeg`.)
- **`probe.probe_video`** — full ffprobe inspection → `VideoMetadata`
  (container, video codec, duration, every audio stream, subtitle streams).
- **`video_extractor`** / **`video_muxer`** — pure command builders. The muxer
  is container-aware: `-c:v copy` always, AAC for mp4/mov/mkv/avi, Opus for
  webm, subtitles + metadata preserved where the container allows.

## Rules enforced by the scaffold

- **`domain.py` is pure.** No Qt, FFmpeg, torch, or DeepFilterNet imports. It
  holds enums and frozen data contracts and is fully unit-tested.
- **`ui/` is presentation only.** It never constructs an FFmpeg command or
  touches DeepFilterNet. It depends on `services.pipeline` (and read-only
  `media_probe`) — not on `ffmpeg_service`/`denoise_backend` directly.
- **All FFmpeg lives in `services/ffmpeg_service.py`**; all ML lives in
  `services/denoise_backend.py`.
- **`services/pipeline.py` owns the job lifecycle:** validate → temp dir →
  convert to 48 kHz PCM WAV → enhance → export → verify output → clean temp in
  *all* outcomes (success, error, cancel).
- **`workers/` only adapts** the synchronous pipeline to Qt signals.
- **Subprocess calls use argument arrays.** Never `shell=True`, never execute
  user text.
- **Lazy heavy imports.** Qt, torch, DeepFilterNet, and imageio-ffmpeg are
  imported inside functions/classes so the package imports cleanly on machines
  without them — which is what lets the core be tested in CI.

## Dependency injection for testability

`Pipeline` takes its outside-world collaborators as constructor arguments
(`backend`, `ffmpeg_exe`, `probe_fn`, `run_fn`, `free_bytes_fn`, `exists_fn`).
Tests pass fakes to exercise the full lifecycle — including guaranteed temp
cleanup and collision-safe naming — without real FFmpeg, a real model, or real
audio. See [`tests/test_pipeline.py`](../tests/test_pipeline.py).

## i18n

Dict-based catalogs in `i18n/` (`en.py`, `bn.py`) with identical key sets.
Chosen over Qt `.ts`/`.qm` to avoid a compile step in the offline build and to
keep diffs reviewable. A parity test fails the build if Bangla is missing or has
extra keys.

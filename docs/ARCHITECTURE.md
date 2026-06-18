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

## storage/ and platform/ (Stage 1 — local library)

Filesystem and OS-integration logic live outside the Qt widgets so they are
fully unit-tested:

- **`storage/app_paths.AppPaths`** — resolves the library layout under the
  user's Documents (`Documents/ShobdoHotao/{Cleaned Files/{Audio,Video},
  Database, Logs, Temp}`) via `QStandardPaths` with a headless fallback. Accepts
  an explicit `root` so tests use a temp dir.
- **`storage/filename_validator`** — Windows-safe name rules (illegal chars,
  reserved device names, trailing dot/space, length) + collision-safe
  `name_2/_3` naming. Allows Unicode/Bengali.
- **`storage/storage_service.StorageService`** — moves a completed *staged*
  output into the right library folder; `discard()` cleans up on cancel.
- **`platform/file_actions`** — `open_file` / `reveal_in_file_manager` /
  `open_directory` with per-OS, unit-tested command builders (Windows
  `explorer /select`).

### Save flow (no silent saves)

Processing writes into a per-job **staging dir** under `Temp/` (not the
library). When the job finishes the window shows the **Save Cleaned File**
dialog (`ui/dialogs/save_dialog`); on save, `StorageService` moves the file into
the library with a collision-safe name; on cancel the staged file is discarded
(no orphans). The **Completion view** then offers Play/Open · Show in Folder ·
Clean Another · Go to Cleaned Files. The pipeline/services are unchanged — only
the `output_dir` they're given (a staging dir) and the post-step differ.

## UI shell + rich processing events (polish stage)

The window is a **shell**: an `AppHeader` (title · Home · Cleaned Files ·
language pill) over a `QStackedWidget` of three views in `ui/views/` —
`home_view` (drop-zone ↔ `MediaCard`), `processing_view`, `completion_view`.

Real, honest progress flows end-to-end:

```
service  --ProcessingObserver-->  worker (Qt signals)  -->  ProcessingPresenter  -->  ProcessingView
   |  on_stage / on_progress / on_activity / on_media_info        (stage_changed, progress_changed,
   |                                                               activity, media_info, finished…)
```

- **`domain.ProcessingStage` / `ActivityCode`** — fine-grained stages and
  structured log events (UI formats them via `ui/activity_format`, so technical
  messages stay translatable and free of temp paths).
- **`services/events.ProcessingObserver`** — optional sink the services emit to
  (additive; the old `progress(JobState,…)` callback is unchanged). The backend
  reports the **LOADING_MODEL → DENOISING** split via an `on_stage` callback (no
  algorithm change). `FfmpegRunner` parses `-progress pipe:1` for **genuine**
  numeric progress on the video extract/mux stages.
- **`ui/stepper_model`** — pure state model for the `PipelineStepper`
  (Pending/Active/Completed/Failed/Cancelled); unit-tested without a display.
- **`ui/controllers/processing_presenter`** — turns worker signals into view
  updates and owns the elapsed-time timer (UI thread; the worker thread is busy
  inside the blocking job).
- **`ui/widgets/signal_visualizer`** — QPainter-only reactive orb (idle breathing
  → processing rings/bars → done/failed/cancelled), 60 fps cap, pauses when
  hidden, static under reduce-motion.

### Genuine vs. indeterminate progress
Genuine numeric: video **Extracting audio** + **Rebuilding video** (FFmpeg
`out_time_us ÷ duration`). Indeterminate (by necessity): **Removing noise**
(DeepFilterNet `enhance()` is one opaque call — chunking would change output
quality), plus Preparing/Inspecting/Loading model/Saving. These show elapsed
time + "Stage X of N", never a fabricated percentage.

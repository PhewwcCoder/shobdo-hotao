# Roadmap

Staged delivery of the "user-friendly Windows app" work. Each stage runs the
full test suite + Ruff and is manually launch-verified before the next begins.

## ✅ Stage 1 — Managed storage, naming, completion (done)
- `storage/app_paths` (Documents-based library), auto-created dirs.
- Windows-safe filename validation + collision-safe naming.
- `storage/storage_service` (stage → name → move into library; discard on cancel).
- `platform/file_actions` (open / reveal-in-Explorer / open-dir).
- Save Cleaned File dialog (live validation) + completion panel
  (Play/Open · Show in Folder · Clean Another).
- Cleaned Files button (opens library folder — in-app screen comes in Stage 2).
- Home polish: selected-filename label, dynamic **Clean Audio / Clean Video
  Audio**, dark-theme contrast fix for the Bengali title.

## ✅ UI/UX polish stage (done)
- Shell: `AppHeader` + `QStackedWidget` (Home / Processing / Completion).
- Home: Aero drop-zone ↔ `MediaCard` (real probed details), dynamic
  Clean Audio / Clean Video Audio, drag-and-drop.
- Processing view: pipeline stepper · QPainter signal visualizer · engine log,
  driven by **real** backend events (`ProcessingObserver` → worker signals →
  presenter). Genuine FFmpeg progress for video extract/mux; honest
  indeterminate + elapsed for denoising. One Cancel action.
- Completion view (Play/Open · Show in Folder · Clean Another · Cleaned Files).
- Dark Frutiger-Aero theme with button states; reduce-motion respected.
- 20 new headless Qt tests + pure stepper/activity tests.

## ⏳ Stage 2 — Library screen + metadata DB
- SQLite (`storage/library_database`, `library_repository`) — metadata only.
- In-app Cleaned Files screen: list, search, filter (All/Audio/Video), sort,
  open, rename, delete (remove-from-library vs delete-from-disk), details.
- Startup reconciliation of DB rows against files on disk (mark missing).

## ⏳ Stage 3 — Storage settings + reconciliation
- Settings: show/open/change/restore library location; optional move-existing.
- Friendlier error surfaces; richer reconciliation.

## ⏳ Stage 4 — PyInstaller one-folder build
- Windowed (no console) `ShobdoHotao.exe`, icon, Qt plugins, FFmpeg, model
  weights; resource-path helper; user-writable logs/data.

## ⏳ Stage 5 — Inno Setup installer
- Program Files install, Start-menu/desktop shortcuts, uninstall that preserves
  the user's Cleaned Files, release docs.

## Original product phases (pre-existing)
- Phase 1 hardening, Phase 2 queue/waveform, Phase 3 release engineering,
  Phase 4 v1.0 benchmarking & docs.

# AUDIT — শব্দ-হটাও (ShobdoHotao)

_Date: 2026-06-13 · Phase: 0 → 1 (initial scaffold)_

## 1. Starting state

Per §8 of the master command, the audit begins by inspecting the repository and
running existing checks.

- The project directory (`c:\Users\Aryan\.vscode\shobdo-hotao`) was **completely
  empty** — no source, tests, docs, `CLAUDE.md`, `README.md`, or the
  `docs/PRODUCT_SPEC.md` / `docs/ARCHITECTURE.md` / `docs/ROADMAP.md` referenced
  in §8. This is the "repository is bare" case, so the first slice is to
  **scaffold the architecture in §4** with stub services, a runnable Aero window,
  and passing placeholder tests — done in this session.
- There were therefore no existing checks to run before scaffolding.

## 2. Findings

Severity scale: **High** (blocks correctness/safety or a non-negotiable rule),
**Medium** (should fix before the phase is "done"), **Low** (hygiene / future).

| # | Severity | Finding | Evidence | Action |
|---|----------|---------|----------|--------|
| A-1 | **High** | The detected git repository root is the user's **home folder** (`C:/Users/Aryan/.git`), so `git status` from the project lists hundreds of unrelated personal files; any commit here would have staged the entire home directory. | `git rev-parse --show-toplevel` → `C:/Users/Aryan`; `git status` listed `NTUSER.DAT`, `Downloads/`, etc. | **Mitigated:** ran `git init` inside the project to give it its own repo boundary, plus a `.gitignore`. **Recommend** the user review/remove the stray `C:/Users/Aryan/.git` if unintended (left untouched — outside project scope). |
| A-2 | **Medium** | Dev machine has **Python 3.12.3**, not the required 3.11; `py -3.11` is absent. DeepFilterNet 0.5.6 supports Python ≤ 3.11, so the ML backend cannot be installed/run here. | `python --version` → 3.12.3; `py -3.11 --version` → no runtime. | Install Python 3.11 (64-bit) before Phase 1 backend work; `setup_windows.ps1` targets `py -3.11`. Pin 3.11 for reproducible builds. |
| A-3 | **Medium** | **PySide6 not installed**; UI cannot launch on this machine. | `import PySide6` → ModuleNotFoundError. | Scaffold uses **lazy Qt imports** so the package imports and the core is fully testable without Qt. Install via `setup_windows.ps1` to run the UI. |
| A-4 | **Low** | `ruff` was not installed. | `ruff --version` → not found. | Installed during audit; added ruff config to `pyproject.toml`. Repo is now lint-clean. |
| A-5 | **Low** | `__main__.main()` catches `ImportError` around the `create_app` *import*, but the actual `QApplication` import happens lazily *inside* `create_app`, so a missing-PySide6 failure at runtime would not hit the friendly message. | `src/shobdohotao/__main__.py`, `ui/main_window.py:create_app`. | Acceptable for scaffold (target machine has Qt). Harden in Phase 1 by wrapping the `create_app()` call. |
| A-6 | **Low** | ffprobe is not guaranteed to ship with `imageio-ffmpeg`; metadata probing may degrade. | `ffmpeg_service.get_ffprobe_exe` falls back to a sibling binary then PATH. | Probe degrades to size-only metadata rather than failing a job. Phase 3 should confirm an ffprobe binary is bundled. |

## 3. What was built (first slice — scaffold)

Architecture per §4 with strict layer boundaries (see
[`ARCHITECTURE.md`](ARCHITECTURE.md)):

- **`domain.py`** — pure enums + frozen contracts (`Strength`, `OutputFormat`,
  `JobState`, `ErrorCode`, `AudioMetadata`, `DenoiseRequest`, `JobResult`,
  `ProcessingError`) and `derive_output_path` (collision-safe `_cleaned` naming,
  never equals input). No Qt/FFmpeg/torch.
- **`services/`** — `ffmpeg_service` (argument-array command builders, no shell),
  `media_probe` (ffprobe JSON → metadata), `denoise_backend` (DeepFilterNet3,
  lazy + process-wide reuse), `pipeline` (full lifecycle with **guaranteed temp
  cleanup** in all outcomes, low-disk preflight, DI for testability),
  `logging_service` (rotating local logs).
- **`workers/processing_worker.py`** — QObject adapter, signals only,
  cooperative cancel.
- **`ui/`** — `main_window` (presentation only, worker-thread jobs, double-start
  guard, fully translated), `sound_orb` (custom-painted Aero orb with reduce-
  motion support), `theme/tokens` (centralised Aero design tokens + QSS).
- **`i18n/`** — dict-based EN/BN catalogs with a parity test; runtime language
  toggle persisted via `QSettings`.
- **`config.py`** — QSettings-backed settings with an in-memory fallback so it is
  testable headless.
- **Tests (23, all passing)** — domain contracts, i18n parity + every error code
  translated, FFmpeg/ffprobe command construction, and the full pipeline
  lifecycle (happy path, enhance failure, cancel, missing input, low disk,
  collision) using fakes.
- Project files: `pyproject.toml`, `README.md`, `LICENSE` (MIT),
  `THIRD_PARTY_NOTICES.md`, `.gitignore`, Windows scripts.

## 4. Checks run this session

| Check | Command | Result |
|-------|---------|--------|
| Unit tests | `PYTHONPATH=src python -m pytest -q` | **23 passed** |
| Lint | `python -m ruff check .` | **All checks passed** |
| Import (no Qt/torch) | import all 16 modules | **All OK** |

## 5. Non-negotiable rules — scaffold compliance

- ✅ No network/cloud/telemetry on any path; logs are local-only.
- ✅ Subprocess via argument arrays only; never `shell=True`, never user text.
- ✅ Outputs use `_cleaned` suffix, collision-safe, never overwrite input.
- ✅ Temp dir removed on success **and** failure **and** cancel (tested).
- ✅ Errors are structured `ErrorCode`s mapped to plain translated text; raw
  exceptions go to logs only.
- ✅ Full bilingual catalog (EN/BN) with parity test; runtime toggle.
- ✅ "Reduce motion" / "reduce transparency" honoured in the theme + orb.
- ✅ No "all noise removed / studio quality" claims; disclaimer string present.
- ⏳ Verified end-to-end audio processing requires Python 3.11 + the ML stack
  (A-2/A-3) — **not yet exercised on real audio**.

## 6. Next smallest slice (Phase 1)

Harden the entry point (A-5) and add an **integration test that asserts exact
FFmpeg argument arrays** the pipeline constructs (convert + export) using a
recording fake — closing the loop on §10 "argument lists only". Then stand up
the Python 3.11 venv and run one real file end-to-end (acceptance scenario #1:
noisy 44.1 kHz MP3 → Balanced → MP3) to validate the DeepFilterNet integration.

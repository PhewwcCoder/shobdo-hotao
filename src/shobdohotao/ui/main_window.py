"""Application shell: header + stacked Home/Processing/Completion views.

Presentation only (no FFmpeg/DeepFilterNet here). Jobs run on a worker thread;
a :class:`ProcessingPresenter` drives the processing view from real events; the
shell owns file selection, the staging→name→save→completion flow, and view
switching. Qt is imported lazily so the package still imports without PySide6.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from ..config import Settings
from ..domain import (
    SUPPORTED_VIDEO_CONTAINERS,
    DenoiseRequest,
    MediaInfo,
    MediaType,
    ProcessingError,
    VideoDenoiseRequest,
)
from ..i18n import Language, Translator
from ..platform import file_actions
from ..services.pipeline import Pipeline
from ..services.video_processing_service import VideoProcessingService
from ..storage.app_paths import AppPaths
from ..storage.storage_service import StorageService


def create_app() -> tuple[Any, Any]:
    """Create the QApplication and MainWindow. Returns (app, window)."""
    from PySide6.QtWidgets import QApplication  # type: ignore

    app = QApplication.instance() or QApplication([])
    window = _build_main_window_class()()
    return app, window


def _build_main_window_class() -> Any:
    from PySide6.QtWidgets import (  # type: ignore
        QFileDialog,
        QInputDialog,
        QMainWindow,
        QMessageBox,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    from .controllers.processing_presenter import ProcessingPresenter
    from .theme.tokens import build_stylesheet
    from .views.completion_view import CompletionView
    from .views.home_view import HomeView
    from .views.processing_view import ProcessingView
    from .widgets.app_header import AppHeader
    from .workers_glue import run_worker_on_thread

    open_filter = (
        "Media (*.mp3 *.wav *.m4a *.flac *.ogg *.aac "
        "*.mp4 *.mov *.mkv *.avi *.webm);;All files (*)"
    )

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self._settings = Settings()
            self._t = Translator(self._settings.language())
            self._pipeline = Pipeline()
            self._paths = AppPaths()
            self._storage = StorageService(self._paths)
            try:
                self._paths.create_required_dirs()
            except OSError:
                pass

            self._input_path: Path | None = None
            self._media_info: MediaInfo | None = None
            self._video_meta: Any = None
            self._active_media_type = MediaType.AUDIO
            self._active_staging: Path | None = None
            self._active_duration: float | None = None
            self._thread: Any = None
            self._worker: Any = None
            self._probe_thread: Any = None
            self._probe_worker: Any = None
            self._pending_path: Path | None = None

            self.setWindowTitle(self._t.tr("app.title"))
            self.setMinimumSize(900, 620)
            self.setStyleSheet(
                build_stylesheet(
                    reduce_transparency=self._settings.reduce_transparency()
                )
            )
            self._build_ui()

        # --- construction ----------------------------------------------
        def _build_ui(self) -> None:
            # Qt classes + view classes come from the enclosing closure scope.
            central = QWidget()
            root = QVBoxLayout(central)

            self._header = AppHeader(self._t)
            self._header.home_requested.connect(self._go_home)
            self._header.library_requested.connect(self._open_library)
            self._header.language_toggled.connect(self._toggle_language)
            root.addWidget(self._header)

            self._stack = QStackedWidget()
            self._home = HomeView(self._t)
            self._processing = ProcessingView(self._t)
            self._completion = CompletionView(self._t)
            for v in (self._home, self._processing, self._completion):
                self._stack.addWidget(v)
            root.addWidget(self._stack, 1)
            self.setCentralWidget(central)

            reduce_motion = self._settings.reduce_motion()
            self._home.set_reduce_motion(reduce_motion)
            self._processing.set_reduce_motion(reduce_motion)

            # Home signals.
            self._home.open_requested.connect(self._choose_file)
            self._home.replace_requested.connect(self._choose_file)
            self._home.clean_requested.connect(self._start_job)
            self._home.library_requested.connect(self._open_library)  # reuse
            self._home.file_dropped.connect(lambda p: self._select_file(Path(p)))
            # Reflect the persisted strength and save changes back to settings.
            self._home.set_strength(self._settings.strength())
            self._home.strength_changed.connect(self._settings.set_strength)

            # Processing + presenter.
            self._processing.cancel_requested.connect(self._cancel_job)
            self._presenter = ProcessingPresenter(
                self._processing, self._t,
                on_finished=self._on_finished,
                on_failed=self._on_failed,
                on_cancelled=self._on_cancelled,
            )

            # Completion signals.
            self._completion.open_requested.connect(self._completion_open)
            self._completion.show_in_folder_requested.connect(self._completion_reveal)
            self._completion.clean_another_requested.connect(self._clean_another)
            self._completion.library_requested.connect(self._open_library)

            self._go_home()

        # --- navigation ------------------------------------------------
        def _go_home(self) -> None:
            """Header Home: return to the empty landing (ignored mid-job)."""
            if self._thread is not None:
                return  # don't navigate away while a job is running
            self._input_path = None
            self._media_info = None
            self._home.show_empty()
            self._stack.setCurrentWidget(self._home)

        def _open_library(self) -> None:
            # Stage 2 will replace this with an in-app library screen.
            self._paths.cleaned_files_dir().mkdir(parents=True, exist_ok=True)
            self._guard(lambda: file_actions.open_directory(
                self._paths.cleaned_files_dir()))

        def _toggle_language(self) -> None:
            new = Language.BN if self._t.language is Language.EN else Language.EN
            self._t.set_language(new)
            self._settings.set_language(new)
            self.setWindowTitle(self._t.tr("app.title"))
            self._header.retranslate(self._t)
            self._home.retranslate(self._t)
            self._processing.retranslate(self._t)
            self._completion.retranslate(self._t)
            self._presenter.set_translator(self._t)

        # --- file selection --------------------------------------------
        def _choose_file(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, self._t.tr("action.open"), "", open_filter
            )
            if path:
                self._select_file(Path(path))

        def _is_video(self, path: Path) -> bool:
            return path.suffix.lstrip(".").lower() in SUPPORTED_VIDEO_CONTAINERS

        def _select_file(self, path: Path) -> None:
            # Probe off the UI thread so the home screen can animate its
            # cleaning-spinner instead of freezing while ffprobe runs.
            if self._probe_thread is not None:
                return  # a probe is already in flight
            from ..workers.probe_worker import make_probe_worker

            self._pending_path = path
            self._stack.setCurrentWidget(self._home)
            self._home.show_loading()
            worker = make_probe_worker(path, self._is_video(path))
            worker.done.connect(self._on_probe_done)
            worker.failed.connect(self._on_probe_failed)
            worker.done.connect(self._teardown_probe_thread)
            worker.failed.connect(self._teardown_probe_thread)
            self._probe_worker = worker
            self._probe_thread = run_worker_on_thread(worker)

        def _on_probe_done(self, info: MediaInfo, video_meta: Any) -> None:
            self._home.hide_loading()
            self._video_meta = video_meta
            self._input_path = self._pending_path
            self._media_info = info
            self._active_media_type = info.media_type
            self._active_duration = info.duration_seconds or None
            self._home.show_selected(info)
            self._stack.setCurrentWidget(self._home)

        def _on_probe_failed(self, exc: ProcessingError) -> None:
            self._home.hide_loading()
            self._error_box(self._t.tr(f"error.{exc.code.value}"))

        def _teardown_probe_thread(self, *_args: Any) -> None:
            if self._probe_thread is not None:
                self._probe_thread.quit()
                self._probe_thread.wait()
            self._probe_thread = None
            self._probe_worker = None

        # --- job start -------------------------------------------------
        def _staging_dir(self) -> Path:
            staging = self._paths.temp_dir() / f"job_{uuid.uuid4().hex[:8]}"
            staging.mkdir(parents=True, exist_ok=True)
            return staging

        def _start_job(self) -> None:
            if self._input_path is None or self._thread is not None:
                return
            if self._active_media_type is MediaType.VIDEO:
                self._start_video_job(self._input_path)
            else:
                self._start_audio_job(self._input_path)

        def _begin_processing(self, worker: Any) -> None:
            self._worker = worker
            self._processing.configure(self._active_media_type,
                                       self._input_path.name)
            self._stack.setCurrentWidget(self._processing)
            self._presenter.attach(worker)
            worker.finished.connect(self._teardown_thread)
            worker.failed.connect(self._teardown_thread)
            worker.canceled.connect(self._teardown_thread)
            self._presenter.start_timer()
            self._thread = run_worker_on_thread(worker)

        def _start_audio_job(self, input_path: Path) -> None:
            from ..workers.processing_worker import make_worker

            staging = self._staging_dir()
            self._active_staging = staging
            request = DenoiseRequest(
                input_path=input_path,
                output_dir=staging,
                output_format=self._settings.output_format(),
                strength=self._settings.strength(),
            )
            self._begin_processing(make_worker(request, self._pipeline))

        def _start_video_job(self, input_path: Path) -> None:
            from ..workers.video_worker import make_video_worker

            chosen = self._choose_audio_stream(self._video_meta)
            if chosen is False:
                return  # user cancelled the picker
            staging = self._staging_dir()
            self._active_staging = staging
            request = VideoDenoiseRequest(
                input_path=input_path,
                output_dir=staging,
                strength=self._settings.strength(),
                audio_stream_index=chosen,
            )
            service = VideoProcessingService()
            self._begin_processing(make_video_worker(request, service))

        def _choose_audio_stream(self, meta: Any) -> Any:
            if meta is None or len(meta.audio_streams) <= 1:
                return None
            labels = [s.label() for s in meta.audio_streams]
            choice, ok = QInputDialog.getItem(
                self, self._t.tr("video.choose_audio.title"),
                self._t.tr("video.choose_audio.prompt"), labels, 0, False,
            )
            if not ok:
                return False
            return meta.audio_streams[labels.index(choice)].index

        def _cancel_job(self) -> None:
            if self._worker is not None:
                self._worker.cancel()

        # --- terminal outcomes (from presenter) ------------------------
        def _on_finished(self, result: Any) -> None:
            staged: Path = result.output_path
            original = result.request.input_path.name
            duration = self._active_duration
            md = getattr(result, "input_metadata", None)
            if duration is None and md is not None:
                duration = md.duration_seconds or None
            self._save_and_complete(staged, original, duration)

        def _on_failed(self, error: ProcessingError) -> None:
            self._cleanup_staging()
            self._show_error_recovery(error)

        def _on_cancelled(self) -> None:
            self._cleanup_staging()
            self._back_to_selected()

        # --- save + completion -----------------------------------------
        def _save_and_complete(self, staged: Path, original: str,
                               duration: float | None) -> None:
            from .dialogs.save_dialog import prompt_save_name

            suggested = self._storage.suggested_stem(original)
            destination = str(self._paths.library_for(self._active_media_type))
            extension = staged.suffix.lstrip(".")
            while True:
                stem = prompt_save_name(
                    self, self._t, suggested_stem=suggested, extension=extension,
                    destination_dir=destination,
                )
                if stem is None:
                    if self._confirm_discard():
                        self._storage.discard(staged)
                        self._cleanup_staging()
                        self._back_to_selected()
                        return
                    continue
                try:
                    final = self._storage.save_cleaned(
                        staged, stem, self._active_media_type
                    )
                except ProcessingError as exc:
                    self._error_box(self._t.tr(f"error.{exc.code.value}"))
                    continue
                self._cleanup_staging()
                self._completion.set_result(final, self._active_media_type, duration)
                self._completion_path = final
                self._stack.setCurrentWidget(self._completion)
                return

        def _completion_open(self) -> None:
            if getattr(self, "_completion_path", None):
                self._guard(lambda: file_actions.open_file(self._completion_path))

        def _completion_reveal(self) -> None:
            if getattr(self, "_completion_path", None):
                self._guard(
                    lambda: file_actions.reveal_in_file_manager(self._completion_path)
                )

        def _clean_another(self) -> None:
            self._go_home()  # reset to the empty landing

        def _back_to_selected(self) -> None:
            if self._media_info is not None:
                self._home.show_selected(self._media_info)
            else:
                self._home.show_empty()
            self._stack.setCurrentWidget(self._home)

        # --- error recovery --------------------------------------------
        def _show_error_recovery(self, error: ProcessingError) -> None:
            box = QMessageBox(self)
            box.setWindowTitle(self._t.tr("app.title"))
            box.setText(self._t.tr(f"error.{error.code.value}"))
            retry = box.addButton(self._t.tr("action.try_again"),
                                  QMessageBox.ButtonRole.AcceptRole)
            another = box.addButton(self._t.tr("action.choose_another"),
                                    QMessageBox.ButtonRole.ActionRole)
            box.addButton(self._t.tr("action.view_log_folder"),
                          QMessageBox.ButtonRole.HelpRole)
            box.exec()
            clicked = box.clickedButton()
            if clicked is retry:
                self._back_to_selected()
                self._start_job()
            elif clicked is another:
                self._clean_another()
            else:
                from ..services.logging_service import log_dir

                log_dir().mkdir(parents=True, exist_ok=True)
                self._guard(lambda: file_actions.open_directory(log_dir()))
                self._back_to_selected()

        def _confirm_discard(self) -> bool:
            box = QMessageBox(self)
            box.setWindowTitle(self._t.tr("save.discard.title"))
            box.setText(self._t.tr("save.discard.body"))
            discard = box.addButton(self._t.tr("save.discard.discard"),
                                    QMessageBox.ButtonRole.DestructiveRole)
            box.addButton(self._t.tr("save.discard.keep"),
                          QMessageBox.ButtonRole.RejectRole)
            box.exec()
            return box.clickedButton() is discard

        # --- helpers ---------------------------------------------------
        def _cleanup_staging(self) -> None:
            if self._active_staging is not None:
                import shutil

                shutil.rmtree(self._active_staging, ignore_errors=True)
                self._active_staging = None

        def _teardown_thread(self, *_args: Any) -> None:
            if self._thread is not None:
                self._thread.quit()
                self._thread.wait()
            self._thread = None
            self._worker = None

        def _error_box(self, message: str) -> None:
            QMessageBox.warning(self, self._t.tr("app.title"), message)

        def _guard(self, action) -> None:
            try:
                action()
            except ProcessingError as exc:
                self._error_box(self._t.tr(f"error.{exc.code.value}"))

    return MainWindow

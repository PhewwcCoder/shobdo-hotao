"""Main application window — presentation only (rule §4).

This module imports Qt lazily so importing the package on a headless machine
does not require PySide6. The window:
- never builds an FFmpeg command or touches DeepFilterNet;
- runs every job on a worker thread (never the main thread);
- disables controls that could start a second job while one runs;
- pulls every label from the i18n catalog (no hardcoded English).

This is the MVP shell: it wires the Aero theme, the language toggle, the sound
orb, and the Clean/Cancel flow. Deeper UX (queue, waveform) is Phase 2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import Settings
from ..domain import (
    SUPPORTED_VIDEO_CONTAINERS,
    DenoiseRequest,
    JobState,
    ProcessingError,
    VideoDenoiseRequest,
)
from ..i18n import Language, Translator
from ..services.pipeline import Pipeline
from ..services.video_processing_service import VideoProcessingService
from .theme.tokens import build_stylesheet
from .widgets.sound_orb import OrbState, make_orb
from .workers_glue import start_job, start_video_job  # thin helpers, see below


def create_app() -> tuple[Any, Any]:
    """Create the QApplication and MainWindow. Returns (app, window)."""
    from PySide6.QtWidgets import QApplication  # type: ignore

    app = QApplication.instance() or QApplication([])
    window = _build_main_window_class()()
    return app, window


def _build_main_window_class() -> Any:
    from PySide6.QtCore import Qt, QThread  # type: ignore
    from PySide6.QtWidgets import (  # type: ignore
        QFileDialog,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self._settings = Settings()
            self._t = Translator(self._settings.language())
            self._pipeline = Pipeline()
            self._input_path: Path | None = None
            self._thread: QThread | None = None
            self._worker: Any = None

            self.setStyleSheet(
                build_stylesheet(
                    reduce_transparency=self._settings.reduce_transparency()
                )
            )
            self._build_ui()
            self._retranslate()

        # --- UI construction -------------------------------------------
        def _build_ui(self) -> None:
            # Qt widget classes come from the enclosing closure scope.
            central = QWidget()
            root = QVBoxLayout(central)

            self._title = QLabel()
            self._title.setObjectName("Title")
            root.addWidget(self._title)

            self._orb = make_orb()
            self._orb.set_reduce_motion(self._settings.reduce_motion())
            root.addWidget(self._orb, alignment=Qt.AlignmentFlag.AlignHCenter)

            self._status = QLabel()
            self._status.setObjectName("Muted")
            root.addWidget(self._status, alignment=Qt.AlignmentFlag.AlignHCenter)

            controls = QHBoxLayout()
            self._open_btn = QPushButton()
            self._open_btn.clicked.connect(self._on_open)
            self._clean_btn = QPushButton()
            self._clean_btn.clicked.connect(self._on_clean)
            self._clean_btn.setEnabled(False)
            self._cancel_btn = QPushButton()
            self._cancel_btn.clicked.connect(self._on_cancel)
            self._cancel_btn.setEnabled(False)
            self._lang_btn = QPushButton()
            self._lang_btn.clicked.connect(self._on_toggle_language)
            for b in (self._open_btn, self._clean_btn, self._cancel_btn,
                      self._lang_btn):
                controls.addWidget(b)
            root.addLayout(controls)

            self.setCentralWidget(central)

        # --- i18n -------------------------------------------------------
        def _retranslate(self) -> None:
            t = self._t.tr
            self.setWindowTitle(t("app.title"))
            self._title.setText(t("app.title.native"))
            self._open_btn.setText(t("action.open"))
            self._clean_btn.setText(t("action.clean"))
            self._cancel_btn.setText(t("action.cancel"))
            self._lang_btn.setText("বাংলা | EN")
            self._status.setText(t("status.idle"))
            for b in (self._open_btn, self._clean_btn, self._cancel_btn):
                b.setAccessibleName(b.text())

        def _on_toggle_language(self) -> None:
            new = Language.BN if self._t.language is Language.EN else Language.EN
            self._t.set_language(new)
            self._settings.set_language(new)
            self._retranslate()

        # --- actions ----------------------------------------------------
        def _on_open(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, self._t.tr("action.open"), "",
                "Media (*.mp3 *.wav *.m4a *.flac *.ogg *.aac "
                "*.mp4 *.mov *.mkv *.avi *.webm);;All files (*)",
            )
            if path:
                self._input_path = Path(path)
                self._clean_btn.setEnabled(True)

        def _is_video(self, path: Path) -> bool:
            return path.suffix.lstrip(".").lower() in SUPPORTED_VIDEO_CONTAINERS

        def _on_clean(self) -> None:
            if self._input_path is None or self._thread is not None:
                return  # double-start guard
            if self._is_video(self._input_path):
                self._start_video_job(self._input_path)
            else:
                self._start_audio_job(self._input_path)

        def _start_audio_job(self, input_path: Path) -> None:
            request = DenoiseRequest(
                input_path=input_path,
                output_dir=self._settings.output_dir(),
                output_format=self._settings.output_format(),
                strength=self._settings.strength(),
            )
            self._set_busy(True)
            self._orb.set_state(OrbState.PROCESSING)
            self._thread, self._worker = start_job(
                request, self._pipeline,
                on_progress=self._on_progress,
                on_finished=self._on_finished,
                on_failed=self._on_failed,
                on_cancelled=self._on_cancelled,
            )

        def _start_video_job(self, input_path: Path) -> None:
            # Probe on the main thread (fast) to offer a stream picker when the
            # video has more than one audio track (functional requirement §3).
            from ..media.probe import probe_video

            try:
                meta = probe_video(input_path)
            except ProcessingError as exc:
                self._on_failed(exc)
                return

            chosen = self._choose_audio_stream(meta)
            if chosen is False:  # user cancelled the picker
                return

            request = VideoDenoiseRequest(
                input_path=input_path,
                output_dir=self._settings.output_dir(),
                strength=self._settings.strength(),
                audio_stream_index=chosen,
            )
            service = VideoProcessingService()
            self._set_busy(True)
            self._orb.set_state(OrbState.PROCESSING)
            self._thread, self._worker = start_video_job(
                request, service,
                on_progress=self._on_progress,
                on_finished=self._on_finished,
                on_failed=self._on_failed,
                on_cancelled=self._on_cancelled,
            )

        def _choose_audio_stream(self, meta: Any) -> Any:
            """Return a stream index, None (auto/first), or False (cancelled)."""
            if len(meta.audio_streams) <= 1:
                return None
            labels = [s.label() for s in meta.audio_streams]
            choice, ok = QInputDialog.getItem(
                self,
                self._t.tr("video.choose_audio.title"),
                self._t.tr("video.choose_audio.prompt"),
                labels,
                0,
                False,
            )
            if not ok:
                return False
            return meta.audio_streams[labels.index(choice)].index

        def _on_cancel(self) -> None:
            if self._worker is not None:
                self._worker.cancel()

        # --- worker callbacks ------------------------------------------
        def _on_progress(self, state: JobState, _fraction: float) -> None:
            key = {
                JobState.VALIDATING: "status.validating",
                JobState.CONVERTING: "status.converting",
                JobState.ENHANCING: "status.enhancing",
                JobState.EXPORTING: "status.exporting",
                JobState.INSPECTING: "status.inspecting",
                JobState.EXTRACTING: "status.extracting",
                JobState.MUXING: "status.muxing",
            }.get(state)
            if key:
                self._status.setText(self._t.tr(key))

        def _on_finished(self, _result: Any) -> None:
            self._orb.set_state(OrbState.DONE)
            self._status.setText(self._t.tr("status.done"))
            self._teardown_thread()
            self._set_busy(False)

        def _on_failed(self, error: ProcessingError) -> None:
            self._status.setText(self._t.tr(f"error.{error.code.value}"))
            self._orb.set_state(OrbState.IDLE)
            self._teardown_thread()
            self._set_busy(False)

        def _on_cancelled(self) -> None:
            self._status.setText(self._t.tr("status.cancelled"))
            self._orb.set_state(OrbState.IDLE)
            self._teardown_thread()
            self._set_busy(False)

        # --- thread lifecycle ------------------------------------------
        def _set_busy(self, busy: bool) -> None:
            self._open_btn.setEnabled(not busy)
            self._clean_btn.setEnabled(not busy and self._input_path is not None)
            self._lang_btn.setEnabled(not busy)
            self._cancel_btn.setEnabled(busy)

        def _teardown_thread(self) -> None:
            if self._thread is not None:
                self._thread.quit()
                self._thread.wait()
            self._thread = None
            self._worker = None

    return MainWindow

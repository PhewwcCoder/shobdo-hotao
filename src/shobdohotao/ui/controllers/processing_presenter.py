"""Mediates between worker signals and the processing view.

Translates raw events (ProcessingStage / ActivityCode / progress) into view
updates, owns the elapsed-time timer (on the UI thread — the worker thread is
busy inside the blocking job), and forwards terminal outcomes to shell-provided
callbacks. Holds no FFmpeg/model logic.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QTimer

from ...domain import ActivityCode, MediaInfo, ProcessingStage
from ...i18n import Translator
from ..activity_format import format_activity
from ..views.processing_view import ProcessingView


class ProcessingPresenter(QObject):
    def __init__(
        self,
        view: ProcessingView,
        translator: Translator,
        *,
        on_finished: Callable[[Any], None],
        on_failed: Callable[[Any], None],
        on_cancelled: Callable[[], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._view = view
        self._t = translator
        self._on_finished = on_finished
        self._on_failed = on_failed
        self._on_cancelled = on_cancelled
        self._start_monotonic = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick_elapsed)

    def set_translator(self, translator: Translator) -> None:
        self._t = translator

    def attach(self, worker: Any) -> None:
        worker.stage_changed.connect(self._on_stage)
        worker.progress_changed.connect(self._on_progress)
        worker.activity.connect(self._on_activity)
        worker.media_info.connect(self._on_media_info)
        worker.finished.connect(self._handle_finished)
        worker.failed.connect(self._handle_failed)
        worker.canceled.connect(self._handle_cancelled)

    def start_timer(self) -> None:
        self._start_monotonic = time.monotonic()
        self._view.set_elapsed(0)
        self._timer.start()

    def stop_timer(self) -> None:
        self._timer.stop()

    # --- event handlers ---------------------------------------------
    def _tick_elapsed(self) -> None:
        self._view.set_elapsed(int(time.monotonic() - self._start_monotonic))

    def _on_stage(self, stage: ProcessingStage) -> None:
        self._view.set_stage(stage)

    def _on_progress(self, current: int, total: int) -> None:
        self._view.set_stage_progress(current, total)

    def _on_activity(self, code: ActivityCode, params: dict) -> None:
        ts = time.strftime("%H:%M:%S")
        self._view.append_activity(ts, format_activity(self._t, code, params))

    def _on_media_info(self, info: MediaInfo) -> None:
        # Real media details are already shown on the home card + logged via the
        # INPUT_IDENTIFIED activity; nothing extra needed here.
        pass

    def _handle_finished(self, result: Any) -> None:
        self.stop_timer()
        self._view.mark_completed()
        self._on_finished(result)

    def _handle_failed(self, error: Any) -> None:
        self.stop_timer()
        self._view.mark_failed()
        self._on_failed(error)

    def _handle_cancelled(self) -> None:
        self.stop_timer()
        self._view.mark_cancelled()
        self._on_cancelled()

"""Qt adapter: runs the synchronous pipeline on a worker thread.

This module imports Qt lazily at call sites where possible, but the QObject
subclass needs PySide6 at class-definition time. To keep the package importable
without Qt, the class is built inside ``_build_worker_class`` and only realised
when ``make_worker`` is first called.

The worker emits signals only; it never touches widgets. Cancellation is
cooperative via a thread-safe flag checked between pipeline stages.
"""

from __future__ import annotations

import threading
from typing import Any

from ..domain import DenoiseRequest, JobResult, ProcessingError
from ..services.logging_service import get_logger
from ..services.pipeline import Pipeline

_WORKER_CLASS: Any = None


def _build_worker_class() -> Any:
    from PySide6.QtCore import QObject, Signal, Slot  # type: ignore

    class ProcessingWorker(QObject):
        progress = Signal(object, float)   # (JobState, fraction)
        stage_changed = Signal(object)     # ProcessingStage
        progress_changed = Signal(int, int)  # (current, total) — real, video FFmpeg
        activity = Signal(object, object)  # (ActivityCode, params dict)
        media_info = Signal(object)        # MediaInfo
        finished = Signal(object)          # JobResult
        failed = Signal(object)            # ProcessingError
        canceled = Signal()

        def __init__(self, request: DenoiseRequest, pipeline: Pipeline) -> None:
            super().__init__()
            self._request = request
            self._pipeline = pipeline
            self._cancel = threading.Event()

        def cancel(self) -> None:
            self._cancel.set()

        # ProcessingObserver interface (called on the worker thread; signals are
        # delivered to the UI thread via queued connections).
        def on_stage(self, stage: object) -> None:
            self.stage_changed.emit(stage)

        def on_progress(self, current: int, total: int) -> None:
            self.progress_changed.emit(current, total)

        def on_activity(self, code: object, **params: object) -> None:
            self.activity.emit(code, dict(params))

        def on_media_info(self, info: object) -> None:
            self.media_info.emit(info)

        @Slot()
        def run(self) -> None:
            try:
                result: JobResult = self._pipeline.run(
                    self._request,
                    progress=lambda state, frac: self.progress.emit(state, frac),
                    cancelled=self._cancel.is_set,
                    observer=self,
                )
                self.finished.emit(result)
            except ProcessingError as exc:
                if exc.code.value == "cancelled":
                    self.canceled.emit()
                else:
                    # Log the real cause; the UI only shows a friendly message.
                    get_logger().error("audio worker failed: %s", exc)
                    self.failed.emit(exc)
            except Exception as exc:  # noqa: BLE001 - convert to structured error
                from ..domain import ErrorCode

                get_logger().exception("unexpected audio worker error")
                self.failed.emit(ProcessingError(ErrorCode.UNKNOWN, repr(exc)))

    return ProcessingWorker


def make_worker(request: DenoiseRequest, pipeline: Pipeline) -> Any:
    """Create a ProcessingWorker (requires PySide6)."""
    global _WORKER_CLASS
    if _WORKER_CLASS is None:
        _WORKER_CLASS = _build_worker_class()
    return _WORKER_CLASS(request, pipeline)

"""Qt adapter: runs the video processing service on a worker thread.

Mirrors :mod:`shobdohotao.workers.processing_worker`. Cancellation is wired to
the service's :class:`FfmpegRunner` so a Cancel click terminates the running
FFmpeg subprocess (functional requirement §16). Qt is imported lazily so the
package imports without PySide6.
"""

from __future__ import annotations

from typing import Any

from ..domain import ErrorCode, ProcessingError, VideoDenoiseRequest, VideoJobResult
from ..services.logging_service import get_logger
from ..services.video_processing_service import VideoProcessingService

_WORKER_CLASS: Any = None


def _build_worker_class() -> Any:
    from PySide6.QtCore import QObject, Signal, Slot  # type: ignore

    class VideoWorker(QObject):
        progress = Signal(object, float)   # (JobState, fraction)
        finished = Signal(object)          # VideoJobResult
        failed = Signal(object)            # ProcessingError
        canceled = Signal()

        def __init__(
            self, request: VideoDenoiseRequest, service: VideoProcessingService
        ) -> None:
            super().__init__()
            self._request = request
            self._service = service
            self._log = get_logger()

        def cancel(self) -> None:
            # Terminates any running FFmpeg and flags the service to stop.
            self._service.cancel()

        @Slot()
        def run(self) -> None:
            try:
                result: VideoJobResult = self._service.run(
                    self._request,
                    progress=lambda state, frac: self.progress.emit(state, frac),
                )
                self.finished.emit(result)
            except ProcessingError as exc:
                if exc.code is ErrorCode.CANCELLED:
                    self.canceled.emit()
                else:
                    self._log.error("video worker failed: %s", exc)
                    self.failed.emit(exc)
            except Exception as exc:  # noqa: BLE001 - convert to structured error
                self._log.exception("unexpected video worker error")
                self.failed.emit(ProcessingError(ErrorCode.UNKNOWN, repr(exc)))

    return VideoWorker


def make_video_worker(
    request: VideoDenoiseRequest, service: VideoProcessingService
) -> Any:
    """Create a VideoWorker (requires PySide6)."""
    global _WORKER_CLASS
    if _WORKER_CLASS is None:
        _WORKER_CLASS = _build_worker_class()
    return _WORKER_CLASS(request, service)

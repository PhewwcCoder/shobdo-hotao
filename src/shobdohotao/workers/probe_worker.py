"""Qt adapter: probe a media file off the UI thread.

Probing shells out to ffprobe, which can take a moment (especially for video).
Running it on the UI thread freezes the window; this worker moves it onto a
QThread so the home screen can show its cleaning-spinner animation meanwhile.
Mirrors the lazy-class pattern of ``processing_worker`` so the package imports
without PySide6.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..domain import ErrorCode, MediaInfo, ProcessingError
from ..services.logging_service import get_logger

_WORKER_CLASS: Any = None


def _build_worker_class() -> Any:
    from PySide6.QtCore import QObject, Signal, Slot  # type: ignore

    class ProbeWorker(QObject):
        # (MediaInfo, video_meta | None)
        done = Signal(object, object)
        failed = Signal(object)  # ProcessingError

        def __init__(self, path: Path, is_video: bool) -> None:
            super().__init__()
            self._path = path
            self._is_video = is_video

        @Slot()
        def run(self) -> None:
            try:
                if self._is_video:
                    from ..media.probe import probe_video

                    meta = probe_video(self._path)
                    self.done.emit(MediaInfo.from_video(meta), meta)
                else:
                    from ..services import media_probe

                    meta = media_probe.probe(self._path)
                    self.done.emit(MediaInfo.from_audio(meta), None)
            except ProcessingError as exc:
                get_logger().error("probe failed: %s", exc)
                self.failed.emit(exc)
            except Exception as exc:  # noqa: BLE001 - convert to structured error
                get_logger().exception("unexpected probe error")
                self.failed.emit(ProcessingError(ErrorCode.UNKNOWN, repr(exc)))

    return ProbeWorker


def make_probe_worker(path: Path, is_video: bool) -> Any:
    """Create a ProbeWorker (requires PySide6)."""
    global _WORKER_CLASS
    if _WORKER_CLASS is None:
        _WORKER_CLASS = _build_worker_class()
    return _WORKER_CLASS(path, is_video)

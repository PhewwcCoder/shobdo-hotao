"""Thin glue: move a ProcessingWorker onto a QThread and wire its signals.

Kept separate from ``main_window`` so the window body stays focused on layout
and so this Qt-threading boilerplate can be reviewed in isolation. Qt is
imported lazily.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..domain import DenoiseRequest, VideoDenoiseRequest
from ..services.pipeline import Pipeline
from ..services.video_processing_service import VideoProcessingService
from ..workers.processing_worker import make_worker
from ..workers.video_worker import make_video_worker


def start_job(
    request: DenoiseRequest,
    pipeline: Pipeline,
    *,
    on_progress: Callable[..., None],
    on_finished: Callable[..., None],
    on_failed: Callable[..., None],
    on_cancelled: Callable[..., None],
) -> tuple[Any, Any]:
    """Start the job on a worker thread. Returns (thread, worker).

    The caller is responsible for tearing down the thread once a terminal
    signal fires.
    """
    from PySide6.QtCore import QThread  # type: ignore

    thread = QThread()
    worker = make_worker(request, pipeline)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.progress.connect(on_progress)
    worker.finished.connect(on_finished)
    worker.failed.connect(on_failed)
    worker.canceled.connect(on_cancelled)
    thread.start()
    return thread, worker


def start_video_job(
    request: VideoDenoiseRequest,
    service: VideoProcessingService,
    *,
    on_progress: Callable[..., None],
    on_finished: Callable[..., None],
    on_failed: Callable[..., None],
    on_cancelled: Callable[..., None],
) -> tuple[Any, Any]:
    """Start a video denoise job on a worker thread. Returns (thread, worker)."""
    from PySide6.QtCore import QThread  # type: ignore

    thread = QThread()
    worker = make_video_worker(request, service)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.progress.connect(on_progress)
    worker.finished.connect(on_finished)
    worker.failed.connect(on_failed)
    worker.canceled.connect(on_cancelled)
    thread.start()
    return thread, worker

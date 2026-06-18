"""Thin glue: move a worker QObject onto a QThread and start it.

Signal wiring (presenter + teardown) is done by the shell so this stays a
single-responsibility helper. Qt is imported lazily.
"""

from __future__ import annotations

from typing import Any


def run_worker_on_thread(worker: Any) -> Any:
    """Move ``worker`` to a fresh QThread, start it, and return the thread.

    ``thread.started`` triggers ``worker.run``. The caller connects the worker's
    terminal signals (finished/failed/canceled) and is responsible for quitting
    the thread afterwards.
    """
    from PySide6.QtCore import QThread  # type: ignore

    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    thread.start()
    return thread

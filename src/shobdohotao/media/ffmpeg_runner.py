"""Cancellable FFmpeg/ffprobe subprocess runner.

Unlike ``services.ffmpeg_service.run_ffmpeg`` (a simple blocking ``subprocess.
run`` used by the short audio-conversion path), video encode/remux can take a
long time, so this runner uses ``Popen`` and can **safely terminate** the
FFmpeg process when the user cancels (functional requirement §16).

Rules honoured:
- Argument arrays only; never ``shell=True``; never user text as a command.
- Cancellation terminates the child, escalating to kill after a short grace.
- On non-zero exit we raise a translatable :class:`ProcessingError`
  (``CANCELLED`` if we asked it to stop, else ``FFMPEG_FAILED``).
"""

from __future__ import annotations

import subprocess
import threading

from ..domain import ErrorCode, ProcessingError


class FfmpegRunner:
    """Runs one FFmpeg command at a time with cooperative cancellation.

    A single runner instance is reused across the stages of one job so a
    Cancel click can terminate whichever FFmpeg invocation is currently
    running.
    """

    def __init__(self, *, kill_grace_seconds: float = 5.0) -> None:
        self._lock = threading.Lock()
        self._proc: subprocess.Popen[bytes] | None = None
        self._cancelled = False
        self._kill_grace = kill_grace_seconds

    def cancel(self) -> None:
        """Request cancellation and terminate any running FFmpeg process."""
        with self._lock:
            self._cancelled = True
            proc = self._proc
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=self._kill_grace)
            except subprocess.TimeoutExpired:
                proc.kill()

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def run(self, cmd: list[str], *, timeout: float | None = None) -> None:
        """Execute an FFmpeg argument array, raising on failure/cancel."""
        with self._lock:
            if self._cancelled:
                raise ProcessingError(ErrorCode.CANCELLED, "cancelled before start")
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except FileNotFoundError as exc:
                raise ProcessingError(
                    ErrorCode.FFMPEG_FAILED, f"binary missing: {exc}"
                ) from exc
            proc = self._proc

        try:
            _stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            proc.communicate()
            raise ProcessingError(ErrorCode.FFMPEG_FAILED, f"timeout: {exc}") from exc
        finally:
            with self._lock:
                self._proc = None

        if self.cancelled:
            raise ProcessingError(ErrorCode.CANCELLED, "user cancelled")
        if proc.returncode != 0:
            text = (stderr or b"").decode("utf-8", "replace").strip()
            tail = " | ".join(text.splitlines()[-5:])
            raise ProcessingError(ErrorCode.FFMPEG_FAILED, tail)

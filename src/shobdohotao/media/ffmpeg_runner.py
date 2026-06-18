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
from collections.abc import Callable

from ..domain import ErrorCode, ProcessingError

# Called with (processed_seconds, total_seconds) during an FFmpeg run when a
# total duration is known. total_seconds may be 0 -> treat as indeterminate.
ProgressCallback = Callable[[int, int], None]


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

    def run(
        self,
        cmd: list[str],
        *,
        timeout: float | None = None,
        total_seconds: float | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        """Execute an FFmpeg argument array, raising on failure/cancel.

        When ``on_progress`` and a positive ``total_seconds`` are given, the
        runner injects ``-progress pipe:1`` and reports processed seconds /
        total seconds as FFmpeg works (genuine progress for encode/remux).
        """
        track = bool(on_progress and total_seconds and total_seconds > 0)
        if track:
            # Insert progress flags right after the executable.
            cmd = [cmd[0], "-progress", "pipe:1", "-nostats", *cmd[1:]]

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
            if track:
                stderr = self._run_with_progress(
                    proc, int(total_seconds), on_progress  # type: ignore[arg-type]
                )
            else:
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

    @staticmethod
    def _run_with_progress(
        proc: subprocess.Popen[bytes],
        total_seconds: int,
        on_progress: ProgressCallback,
    ) -> bytes:
        """Stream stdout for `-progress` lines; drain stderr concurrently."""
        stderr_chunks: list[bytes] = []

        def _drain() -> None:
            if proc.stderr is not None:
                stderr_chunks.append(proc.stderr.read())

        drainer = threading.Thread(target=_drain, daemon=True)
        drainer.start()

        if proc.stdout is not None:
            for raw in proc.stdout:
                line = raw.decode("utf-8", "replace").strip()
                if line.startswith("out_time_us=") or line.startswith("out_time_ms="):
                    value = line.split("=", 1)[1]
                    try:
                        micros = int(value)
                    except ValueError:
                        continue  # "N/A" early in the run
                    current = micros // 1_000_000
                    on_progress(min(current, total_seconds), total_seconds)
        proc.wait()
        drainer.join(timeout=2.0)
        return b"".join(stderr_chunks)

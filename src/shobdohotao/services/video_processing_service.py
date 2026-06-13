"""Video job orchestration with guaranteed cleanup.

Lifecycle for one video job:
    inspect -> validate (audio? duration? disk?) -> temp dir -> extract audio
    -> enhance -> mux cleaned audio with original video -> verify -> clean temp
    in *all* outcomes (success, error, cancel).

Like :class:`shobdohotao.services.pipeline.Pipeline`, all outside-world
collaborators are injected so the orchestration is testable with fakes and no
real FFmpeg / model / video.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

from ..domain import (
    DEFAULT_MAX_VIDEO_SECONDS,
    SUPPORTED_VIDEO_CONTAINERS,
    ErrorCode,
    JobState,
    ProcessingError,
    VideoDenoiseRequest,
    VideoJobResult,
    VideoMetadata,
    derive_cleaned_path,
)
from ..media import probe as video_probe
from ..media import video_extractor, video_muxer
from ..media.ffmpeg_runner import FfmpegRunner
from . import ffmpeg_service
from .denoise_backend import DenoiseBackend, get_backend
from .logging_service import get_logger

ProgressFn = Callable[[JobState, float], None]

_MIN_FREE_HEADROOM = 50 * 1024 * 1024  # 50 MB beyond input size


def _noop_progress(_state: JobState, _fraction: float) -> None:
    pass


def _free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


class VideoProcessingService:
    """Runs one video denoise job with guaranteed temp cleanup and cancel."""

    def __init__(
        self,
        *,
        backend: DenoiseBackend | None = None,
        ffmpeg_exe: str | None = None,
        runner: FfmpegRunner | None = None,
        probe_fn: Callable[[Path], VideoMetadata] | None = None,
        free_bytes_fn: Callable[[Path], int] = _free_bytes,
        exists_fn: Callable[[Path], bool] = Path.exists,
        max_duration_seconds: float = DEFAULT_MAX_VIDEO_SECONDS,
    ) -> None:
        self._backend = backend if backend is not None else get_backend()
        self._ffmpeg_exe = ffmpeg_exe
        self._runner = runner if runner is not None else FfmpegRunner()
        self._probe_fn = probe_fn or video_probe.probe_video
        self._free_bytes_fn = free_bytes_fn
        self._exists_fn = exists_fn
        self._max_duration = max_duration_seconds
        self._log = get_logger()

    @property
    def runner(self) -> FfmpegRunner:
        """Exposed so a worker can wire the Cancel button to it."""
        return self._runner

    def cancel(self) -> None:
        self._runner.cancel()

    def _ffmpeg(self) -> str:
        if self._ffmpeg_exe is None:
            self._ffmpeg_exe = ffmpeg_service.get_ffmpeg_exe()
        return self._ffmpeg_exe

    def run(
        self,
        request: VideoDenoiseRequest,
        *,
        progress: ProgressFn = _noop_progress,
    ) -> VideoJobResult:
        temp_dir: Path | None = None
        try:
            container = request.container()
            if container not in SUPPORTED_VIDEO_CONTAINERS:
                raise ProcessingError(ErrorCode.UNSUPPORTED_CONTAINER, container)

            # 1. Inspect.
            progress(JobState.INSPECTING, 0.0)
            if not self._exists_fn(request.input_path):
                raise ProcessingError(ErrorCode.FILE_NOT_FOUND, str(request.input_path))
            meta = self._probe_fn(request.input_path)

            # 2. Validate: audio present, duration, disk.
            if not meta.has_audio:
                raise ProcessingError(ErrorCode.NO_AUDIO_STREAM, str(request.input_path))
            if meta.duration_seconds > self._max_duration:
                raise ProcessingError(
                    ErrorCode.VIDEO_TOO_LONG,
                    f"{meta.duration_seconds:.0f}s > {self._max_duration:.0f}s",
                )
            stream_index = self._select_stream(request, meta)

            request.output_dir.mkdir(parents=True, exist_ok=True)
            # Output is roughly input size; budget 1.5x input + headroom.
            needed = int(meta.size_bytes * 1.5) + _MIN_FREE_HEADROOM
            if self._free_bytes_fn(request.output_dir) < needed:
                raise ProcessingError(ErrorCode.LOW_DISK_SPACE, f"need ~{needed} bytes")

            # 3. Temp workspace.
            temp_dir = Path(tempfile.mkdtemp(prefix="shobdohotao_vid_"))
            wav_in = temp_dir / "audio_48k.wav"
            wav_out = temp_dir / "audio_48k_cleaned.wav"

            # 4. Extract chosen audio stream.
            progress(JobState.EXTRACTING, 0.15)
            self._runner.run(
                video_extractor.build_extract_audio_cmd(
                    self._ffmpeg(), request.input_path, wav_in,
                    stream_index=stream_index,
                )
            )

            # 5. Enhance via the shared DeepFilterNet backend.
            progress(JobState.ENHANCING, 0.4)
            self._backend.enhance(wav_in, wav_out, request.strength)
            if not wav_out.exists():
                raise ProcessingError(ErrorCode.ENHANCE_FAILED, "no enhanced wav")

            # 6. Mux cleaned audio with original video.
            progress(JobState.MUXING, 0.75)
            output_path = derive_cleaned_path(
                request.input_path, request.output_dir, container,
                exists=self._exists_fn,
            )
            self._runner.run(
                video_muxer.build_mux_cmd(
                    self._ffmpeg(), request.input_path, wav_out, output_path,
                    container=container,
                    keep_subtitles=bool(meta.subtitle_streams),
                )
            )

            # 7. Verify.
            if not self._exists_fn(output_path):
                raise ProcessingError(ErrorCode.OUTPUT_NOT_WRITTEN, str(output_path))

            progress(JobState.DONE, 1.0)
            return VideoJobResult(
                request=request,
                output_path=output_path,
                metadata=meta,
                cleaned_stream_index=stream_index if stream_index is not None else 0,
            )
        except ProcessingError as exc:
            # Cancellation is expected; everything else is logged with detail.
            if exc.code is not ErrorCode.CANCELLED:
                self._log.error("video job failed: %s", exc)
            raise
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _select_stream(
        request: VideoDenoiseRequest, meta: VideoMetadata
    ) -> int | None:
        """Resolve the audio stream index to clean.

        Returns ``None`` to mean "first audio stream" (FFmpeg ``0:a:0``). If the
        user picked a specific index, validate it exists.
        """
        if request.audio_stream_index is None:
            return None
        valid = {s.index for s in meta.audio_streams}
        if request.audio_stream_index not in valid:
            raise ProcessingError(
                ErrorCode.NO_AUDIO_STREAM,
                f"stream {request.audio_stream_index} not in {sorted(valid)}",
            )
        return request.audio_stream_index

"""Job orchestration with guaranteed cleanup.

Lifecycle for one job (rule §4):
    validate -> temp dir -> convert to 48 kHz PCM WAV -> enhance -> export
    -> verify output exists -> clean temp in *all* outcomes.

Everything the pipeline touches the outside world through is injected
(``ffmpeg_exe`` resolver, ``backend``, ``probe`` fn, ``run`` fn, a low-disk
check, and a ``cancelled`` callback). That keeps the orchestration logic pure
enough to test with fakes and no real FFmpeg / model / filesystem audio.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

from ..domain import (
    ActivityCode,
    AudioMetadata,
    DenoiseRequest,
    ErrorCode,
    JobResult,
    JobState,
    MediaInfo,
    ProcessingError,
    ProcessingStage,
    derive_output_path,
)
from . import ffmpeg_service, media_probe
from .denoise_backend import DenoiseBackend, get_backend
from .events import NullObserver, ProcessingObserver

# Reported progress is coarse and stage-based; exact percentages are not
# meaningful for a single opaque enhancement pass.
ProgressFn = Callable[[JobState, float], None]
CancelledFn = Callable[[], bool]

# Require at least this much free space (bytes) beyond the input size before
# starting, as a preflight against half-written outputs.
_MIN_FREE_HEADROOM = 50 * 1024 * 1024  # 50 MB


def _noop_progress(_state: JobState, _fraction: float) -> None:
    pass


def _not_cancelled() -> bool:
    return False


def _free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def _make_enhance_stage_cb(obs: ProcessingObserver) -> Callable[[ProcessingStage], None]:
    """Forward the backend's LOADING_MODEL/DENOISING split to the observer.

    Shared by the audio and video orchestrators so they report the model-load →
    denoise transition identically.
    """

    def _cb(stage: ProcessingStage) -> None:
        obs.on_stage(stage)
        if stage is ProcessingStage.DENOISING:
            obs.on_activity(ActivityCode.MODEL_READY)
            obs.on_activity(ActivityCode.DENOISE_STARTED)
            # Narrate the enhancement pass so the user sees how the noise is
            # actually removed (the pass itself is a single blocking call).
            obs.on_activity(ActivityCode.ANALYZING)
            obs.on_activity(ActivityCode.PROFILING_NOISE)
            obs.on_activity(ActivityCode.SEPARATING)
            obs.on_activity(ActivityCode.APPLYING_MASK)

    return _cb


class Pipeline:
    """Runs one denoise job at a time with guaranteed temp cleanup."""

    def __init__(
        self,
        *,
        backend: DenoiseBackend | None = None,
        ffmpeg_exe: str | None = None,
        probe_fn: Callable[[Path], AudioMetadata] | None = None,
        run_fn: Callable[[list[str]], None] | None = None,
        free_bytes_fn: Callable[[Path], int] = _free_bytes,
        exists_fn: Callable[[Path], bool] = Path.exists,
    ) -> None:
        self._backend = backend if backend is not None else get_backend()
        self._ffmpeg_exe = ffmpeg_exe
        self._probe_fn = probe_fn or media_probe.probe
        self._run_fn = run_fn or ffmpeg_service.run_ffmpeg
        self._free_bytes_fn = free_bytes_fn
        self._exists_fn = exists_fn

    def _ffmpeg(self) -> str:
        if self._ffmpeg_exe is None:
            self._ffmpeg_exe = ffmpeg_service.get_ffmpeg_exe()
        return self._ffmpeg_exe

    def run(
        self,
        request: DenoiseRequest,
        *,
        progress: ProgressFn = _noop_progress,
        cancelled: CancelledFn = _not_cancelled,
        observer: ProcessingObserver | None = None,
    ) -> JobResult:
        """Execute the job. Always cleans temp, even on error/cancel.

        ``observer`` (optional) receives rich stage/activity/media events for the
        processing UI; the coarse ``progress`` callback is still emitted for
        back-compat.
        """
        obs = observer or NullObserver()
        temp_dir: Path | None = None
        try:
            # 1. Validate input.
            progress(JobState.VALIDATING, 0.0)
            obs.on_stage(ProcessingStage.PREPARING)
            if not self._exists_fn(request.input_path):
                raise ProcessingError(ErrorCode.FILE_NOT_FOUND, str(request.input_path))
            metadata = self._probe_fn(request.input_path)
            obs.on_media_info(MediaInfo.from_audio(metadata))
            obs.on_activity(
                ActivityCode.INPUT_IDENTIFIED,
                kind=(metadata.path.suffix.lstrip(".").upper() or "audio"),
            )
            if metadata.sample_rate:
                obs.on_activity(
                    ActivityCode.AUDIO_STREAM,
                    codec=metadata.codec or "audio",
                    sample_rate=metadata.sample_rate,
                    channels=metadata.channels,
                )
            self._check_cancelled(cancelled)

            # Preflight: ensure output folder exists and has headroom.
            request.output_dir.mkdir(parents=True, exist_ok=True)
            needed = metadata.size_bytes + _MIN_FREE_HEADROOM
            if self._free_bytes_fn(request.output_dir) < needed:
                raise ProcessingError(
                    ErrorCode.LOW_DISK_SPACE,
                    f"need ~{needed} bytes free",
                )

            # 2. Temp workspace.
            temp_dir = Path(tempfile.mkdtemp(prefix="shobdohotao_"))
            wav_in = temp_dir / "input_48k.wav"
            wav_out = temp_dir / "enhanced_48k.wav"

            # 3. Convert to 48 kHz PCM WAV.
            progress(JobState.CONVERTING, 0.1)
            obs.on_stage(ProcessingStage.CONVERTING)
            obs.on_activity(ActivityCode.CONVERTING)
            self._run_fn(
                ffmpeg_service.build_convert_to_wav_cmd(
                    self._ffmpeg(), request.input_path, wav_in
                )
            )
            self._check_cancelled(cancelled)

            # 4. Enhance (the backend splits LOADING_MODEL -> DENOISING). Chunked
            # internally so memory stays bounded on long files; reports real
            # progress and is cancellable between chunks.
            progress(JobState.ENHANCING, 0.4)
            self._backend.enhance(
                wav_in, wav_out, request.strength,
                on_stage=_make_enhance_stage_cb(obs),
                on_progress=obs.on_progress,
                cancelled=cancelled,
            )
            if not wav_out.exists():
                raise ProcessingError(ErrorCode.ENHANCE_FAILED, "no enhanced wav")
            obs.on_activity(ActivityCode.RECONSTRUCTING)
            self._check_cancelled(cancelled)

            # 5. Export to chosen format with a collision-safe name.
            progress(JobState.EXPORTING, 0.8)
            obs.on_stage(ProcessingStage.ENCODING)
            obs.on_activity(ActivityCode.ENCODING)
            output_path = derive_output_path(
                request.input_path,
                request.output_dir,
                request.output_format,
                exists=self._exists_fn,
            )
            self._run_fn(
                ffmpeg_service.build_export_cmd(
                    self._ffmpeg(), wav_out, output_path, request.output_format
                )
            )

            # 6. Verify output landed.
            obs.on_activity(ActivityCode.VERIFYING)
            if not self._exists_fn(output_path):
                raise ProcessingError(ErrorCode.OUTPUT_NOT_WRITTEN, str(output_path))

            obs.on_activity(ActivityCode.DONE)
            progress(JobState.DONE, 1.0)
            warnings: list[str] = []
            if metadata.is_silentish:
                warnings.append("input duration unknown or zero")
            return JobResult(
                request=request,
                output_path=output_path,
                input_metadata=metadata,
                warnings=tuple(warnings),
            )
        finally:
            # 7. Clean temp in ALL outcomes (success, error, cancel).
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _check_cancelled(cancelled: CancelledFn) -> None:
        if cancelled():
            raise ProcessingError(ErrorCode.CANCELLED, "user cancelled")

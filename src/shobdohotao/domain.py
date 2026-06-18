"""Domain contracts for শব্দ-হটাও (ShobdoHotao).

This module is the pure core of the application. It MUST NOT import Qt,
FFmpeg, torch, or DeepFilterNet. Everything here is plain Python + stdlib so
it can be imported and tested on any machine, including CI runners that lack
the heavy ML/UI dependencies.

All data contracts are immutable (frozen dataclasses) so they can be passed
safely between the pipeline, the worker thread, and the UI without aliasing
bugs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Strength(Enum):
    """Denoise strength presets shown to the user.

    Bangla labels: মৃদু / সুষম / কড়া. The label text itself lives in the i18n
    catalog; this enum only carries the stable identifier plus the backend
    tuning that maps to DeepFilterNet's attenuation limit (dB). A higher
    attenuation limit removes more noise but risks artefacts on speech.
    """

    GENTLE = "gentle"
    BALANCED = "balanced"
    STRONG = "strong"

    @property
    def attenuation_limit_db(self) -> float:
        """Max noise attenuation in dB applied by the backend.

        ``None``-like behaviour (no limit) is intentionally avoided: we always
        cap attenuation so a preset can never silence quiet speech entirely.
        """
        return {
            Strength.GENTLE: 12.0,
            Strength.BALANCED: 24.0,
            Strength.STRONG: 100.0,
        }[self]


class OutputFormat(Enum):
    """Supported export formats. Values double as file extensions."""

    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"

    @property
    def extension(self) -> str:
        return self.value


class MediaType(Enum):
    """Whether a cleaned output is audio or video.

    Used to route saved outputs into the right library folder
    (Cleaned Files/Audio vs Cleaned Files/Video).
    """

    AUDIO = "audio"
    VIDEO = "video"


class JobState(Enum):
    """Lifecycle states for a single denoise job."""

    PENDING = "pending"
    VALIDATING = "validating"
    CONVERTING = "converting"
    ENHANCING = "enhancing"
    EXPORTING = "exporting"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"
    # Video-specific stages (audio jobs reuse VALIDATING/CONVERTING/EXPORTING).
    INSPECTING = "inspecting"
    EXTRACTING = "extracting"
    MUXING = "muxing"


class ErrorCode(Enum):
    """Stable, translatable error identifiers.

    The UI maps each code to a plain-language message in the active language.
    The full original exception is only ever written to the local log, never
    shown raw to the student.
    """

    UNKNOWN = "unknown"
    FILE_NOT_FOUND = "file_not_found"
    UNSUPPORTED_FORMAT = "unsupported_format"
    UNSUPPORTED_CONTAINER = "unsupported_container"
    CORRUPT_MEDIA = "corrupt_media"
    NO_AUDIO_STREAM = "no_audio_stream"
    FFMPEG_FAILED = "ffmpeg_failed"
    BACKEND_INIT_FAILED = "backend_init_failed"
    ENHANCE_FAILED = "enhance_failed"
    OUTPUT_NOT_WRITTEN = "output_not_written"
    LOW_DISK_SPACE = "low_disk_space"
    VIDEO_TOO_LONG = "video_too_long"
    CANCELLED = "cancelled"
    # Library / storage (Stage 1)
    INVALID_FILENAME = "invalid_filename"
    OUTPUT_FOLDER_FAILED = "output_folder_failed"
    SAVE_FAILED = "save_failed"
    FILE_LOCKED = "file_locked"
    CANNOT_OPEN = "cannot_open"
    FILE_MISSING = "file_missing"


class ProcessingStage(Enum):
    """Fine-grained, user-facing pipeline stages for the processing view.

    Richer than :class:`JobState`: splits the opaque "enhancing" job state into
    LOADING_MODEL + DENOISING and names each step the way the UI presents it. The
    string value is also the i18n key suffix (``stage.<value>``).
    """

    PREPARING = "preparing"
    INSPECTING = "inspecting"
    EXTRACTING_AUDIO = "extracting_audio"
    CONVERTING = "converting"
    LOADING_MODEL = "loading_model"
    DENOISING = "denoising"
    ENCODING = "encoding"
    MUXING_VIDEO = "muxing_video"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Ordered stepper sequences shown in the processing view (terminal
# COMPLETED/FAILED/CANCELLED states are not steps).
AUDIO_STAGE_SEQUENCE = (
    ProcessingStage.PREPARING,
    ProcessingStage.CONVERTING,
    ProcessingStage.LOADING_MODEL,
    ProcessingStage.DENOISING,
    ProcessingStage.ENCODING,
    ProcessingStage.FINALIZING,
)
VIDEO_STAGE_SEQUENCE = (
    ProcessingStage.INSPECTING,
    ProcessingStage.EXTRACTING_AUDIO,
    ProcessingStage.LOADING_MODEL,
    ProcessingStage.DENOISING,
    ProcessingStage.MUXING_VIDEO,
    ProcessingStage.FINALIZING,
)


def stage_sequence_for(media_type: MediaType) -> tuple[ProcessingStage, ...]:
    return (
        VIDEO_STAGE_SEQUENCE
        if media_type is MediaType.VIDEO
        else AUDIO_STAGE_SEQUENCE
    )


# Map the coarse JobState (emitted by services) to a ProcessingStage.
# LOADING_MODEL/DENOISING are split by the backend, not derivable from JobState
# alone, so ENHANCING maps to DENOISING here as the default.
_JOBSTATE_TO_STAGE = {
    JobState.VALIDATING: ProcessingStage.PREPARING,
    JobState.INSPECTING: ProcessingStage.INSPECTING,
    JobState.CONVERTING: ProcessingStage.CONVERTING,
    JobState.EXTRACTING: ProcessingStage.EXTRACTING_AUDIO,
    JobState.ENHANCING: ProcessingStage.DENOISING,
    JobState.EXPORTING: ProcessingStage.ENCODING,
    JobState.MUXING: ProcessingStage.MUXING_VIDEO,
    JobState.DONE: ProcessingStage.COMPLETED,
    JobState.FAILED: ProcessingStage.FAILED,
    JobState.CANCELLED: ProcessingStage.CANCELLED,
}


def stage_for_jobstate(state: JobState) -> ProcessingStage | None:
    return _JOBSTATE_TO_STAGE.get(state)


class ActivityCode(Enum):
    """Structured engine-log events. The UI maps each to an i18n template and
    fills parameters, so the processing layer never emits pre-formatted prose
    (keeps activity messages translatable). Value is the i18n key suffix
    (``activity.<value>``).
    """

    INPUT_IDENTIFIED = "input_identified"
    AUDIO_STREAM = "audio_stream"
    EXTRACTING = "extracting"
    CONVERTING = "converting"
    MODEL_READY = "model_ready"
    DENOISE_STARTED = "denoise_started"
    # Narration of the DeepFilterNet3 enhancement pass — purely descriptive log
    # detail so the user can see *how* the noise is being removed.
    ANALYZING = "analyzing"
    PROFILING_NOISE = "profiling_noise"
    SEPARATING = "separating"
    APPLYING_MASK = "applying_mask"
    RECONSTRUCTING = "reconstructing"
    VERIFYING = "verifying"
    FFMPEG_PROGRESS = "ffmpeg_progress"
    REBUILDING_VIDEO = "rebuilding_video"
    ENCODING = "encoding"
    SAVING = "saving"
    DONE = "done"


# Sample rate DeepFilterNet3 operates at internally. The pipeline converts every
# input to this rate as 16-bit PCM WAV before enhancement.
PROCESSING_SAMPLE_RATE = 48_000


@dataclass(frozen=True)
class AudioMetadata:
    """Probed metadata for a media file (from ffprobe)."""

    path: Path
    duration_seconds: float
    sample_rate: int
    channels: int
    size_bytes: int
    codec: str = ""

    @property
    def is_silentish(self) -> bool:
        return self.duration_seconds <= 0.0


@dataclass(frozen=True)
class DenoiseRequest:
    """One unit of work: clean ``input_path`` and write a cleaned export."""

    input_path: Path
    output_dir: Path
    output_format: OutputFormat
    strength: Strength = Strength.BALANCED

    def __post_init__(self) -> None:
        # Frozen dataclass: validate without mutating.
        if not isinstance(self.input_path, Path):
            raise TypeError("input_path must be a pathlib.Path")
        if not isinstance(self.output_dir, Path):
            raise TypeError("output_dir must be a pathlib.Path")


@dataclass(frozen=True)
class ProcessingError(Exception):
    """Structured, translatable error raised across layer boundaries.

    ``code`` selects the user-facing translated message; ``detail`` is for the
    log only. We deliberately do not put English prose in here that the UI
    would show directly — the UI owns presentation and language.
    """

    code: ErrorCode
    detail: str = ""

    def __str__(self) -> str:  # for logs
        return f"{self.code.value}: {self.detail}" if self.detail else self.code.value


@dataclass(frozen=True)
class JobResult:
    """Outcome of a completed job."""

    request: DenoiseRequest
    output_path: Path
    input_metadata: AudioMetadata | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)


def derive_cleaned_path(
    input_path: Path,
    output_dir: Path,
    extension: str,
    *,
    exists: callable[[Path], bool] | None = None,
) -> Path:
    """Compute a deterministic, collision-safe ``_cleaned`` output path.

    ``extension`` is the bare extension without a leading dot (e.g. ``"mp3"``
    or ``"mp4"``). Filenames are kept ASCII-safe via the input stem; the caller
    is responsible for sanitising non-ASCII stems if required. ``exists`` is
    injected so this is pure and unit-testable without the filesystem; it
    defaults to ``Path.exists``.

    Never returns a path equal to ``input_path`` (rule §2.6: never overwrite
    the input). On collision, appends ``_2``, ``_3``, ... before the suffix
    (e.g. ``lecture_cleaned.mp4`` → ``lecture_cleaned_2.mp4``).
    """
    if exists is None:
        exists = Path.exists

    stem = input_path.stem
    suffix = f".{extension.lstrip('.')}"
    candidate = output_dir / f"{stem}_cleaned{suffix}"

    index = 2
    while exists(candidate) or candidate.resolve() == input_path.resolve():
        candidate = output_dir / f"{stem}_cleaned_{index}{suffix}"
        index += 1
    return candidate


def derive_output_path(
    input_path: Path,
    output_dir: Path,
    output_format: OutputFormat,
    *,
    exists: callable[[Path], bool] | None = None,
) -> Path:
    """Audio convenience wrapper over :func:`derive_cleaned_path`."""
    return derive_cleaned_path(
        input_path, output_dir, output_format.extension, exists=exists
    )


# ---------------------------------------------------------------------------
# Video contracts
# ---------------------------------------------------------------------------

# Containers we accept on input (lower-case, no dot). Output defaults to the
# same container so the video stream can be copied without re-encoding.
SUPPORTED_VIDEO_CONTAINERS = frozenset({"mp4", "mov", "mkv", "avi", "webm"})

# Conservative default cap for a single job (rule: define a supported max
# length). Five hours of audio enhancement is already very long on CPU.
DEFAULT_MAX_VIDEO_SECONDS = 5 * 60 * 60


@dataclass(frozen=True)
class AudioStreamInfo:
    """One audio stream inside a media container."""

    index: int          # ffmpeg stream index within the file
    codec: str
    channels: int
    sample_rate: int
    language: str = ""
    title: str = ""

    def label(self) -> str:
        """Human-ish label for a stream picker (language-neutral)."""
        parts = [f"#{self.index}", self.codec or "audio"]
        if self.channels:
            parts.append(f"{self.channels}ch")
        if self.language:
            parts.append(self.language)
        if self.title:
            parts.append(self.title)
        return " · ".join(parts)


@dataclass(frozen=True)
class SubtitleStreamInfo:
    index: int
    codec: str
    language: str = ""


@dataclass(frozen=True)
class VideoMetadata:
    """Probed metadata for a video file (from ffprobe)."""

    path: Path
    container: str
    video_codec: str
    duration_seconds: float
    size_bytes: int
    width: int = 0
    height: int = 0
    frame_rate: float = 0.0
    audio_streams: tuple[AudioStreamInfo, ...] = field(default_factory=tuple)
    subtitle_streams: tuple[SubtitleStreamInfo, ...] = field(default_factory=tuple)

    @property
    def has_audio(self) -> bool:
        return len(self.audio_streams) > 0


@dataclass(frozen=True)
class VideoDenoiseRequest:
    """Clean the audio of a video and remux into a cleaned video file.

    ``audio_stream_index`` selects which audio stream to clean; ``None`` means
    use the first audio stream. ``output_container`` defaults to the input's
    container so the video stream can be copied losslessly.
    """

    input_path: Path
    output_dir: Path
    strength: Strength = Strength.BALANCED
    audio_stream_index: int | None = None
    output_container: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.input_path, Path):
            raise TypeError("input_path must be a pathlib.Path")
        if not isinstance(self.output_dir, Path):
            raise TypeError("output_dir must be a pathlib.Path")

    def container(self) -> str:
        """Effective output container (lower-case, no dot)."""
        if self.output_container:
            return self.output_container.lstrip(".").lower()
        return self.input_path.suffix.lstrip(".").lower()


@dataclass(frozen=True)
class VideoJobResult:
    """Outcome of a completed video job."""

    request: VideoDenoiseRequest
    output_path: Path
    metadata: VideoMetadata | None = None
    cleaned_stream_index: int = 0
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MediaInfo:
    """A unified, view-facing description of a selected input file.

    Built from the probed audio/video metadata so the home-screen media card and
    the processing header can show real details without depending on the
    probe-specific shapes.
    """

    path: Path
    media_type: MediaType
    container: str = ""
    size_bytes: int = 0
    duration_seconds: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    width: int = 0
    height: int = 0
    audio_codec: str = ""
    video_codec: str = ""

    @classmethod
    def from_audio(cls, meta: AudioMetadata) -> MediaInfo:
        return cls(
            path=meta.path,
            media_type=MediaType.AUDIO,
            container=meta.path.suffix.lstrip(".").lower(),
            size_bytes=meta.size_bytes,
            duration_seconds=meta.duration_seconds,
            sample_rate=meta.sample_rate,
            channels=meta.channels,
            audio_codec=meta.codec,
        )

    @classmethod
    def from_video(cls, meta: VideoMetadata) -> MediaInfo:
        first_audio = meta.audio_streams[0] if meta.audio_streams else None
        return cls(
            path=meta.path,
            media_type=MediaType.VIDEO,
            container=meta.container,
            size_bytes=meta.size_bytes,
            duration_seconds=meta.duration_seconds,
            sample_rate=first_audio.sample_rate if first_audio else 0,
            channels=first_audio.channels if first_audio else 0,
            width=meta.width,
            height=meta.height,
            audio_codec=first_audio.codec if first_audio else "",
            video_codec=meta.video_codec,
        )


@dataclass(frozen=True)
class ProcessingResult:
    """View-facing result of a finished job, ready for the save/completion step.

    Decouples the UI from the audio/video result shapes. ``staged_path`` is the
    completed-but-unsaved output in the staging dir.
    """

    staged_path: Path
    media_type: MediaType
    original_name: str
    duration_seconds: float | None = None

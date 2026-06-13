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

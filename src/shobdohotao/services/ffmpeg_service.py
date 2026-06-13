"""All FFmpeg interaction. The UI never builds commands; only this module does.

Commands are built as argument *arrays* (never shell strings, never
``shell=True``, never user text executed). The command-building functions are
pure so they can be unit-tested without invoking FFmpeg.

The FFmpeg/FFprobe binaries are resolved via ``imageio-ffmpeg`` so a packaged
release ships its own binary and needs no system FFmpeg.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..domain import PROCESSING_SAMPLE_RATE, ErrorCode, OutputFormat, ProcessingError


def get_ffmpeg_exe() -> str:
    """Path to the bundled FFmpeg binary (via imageio-ffmpeg)."""
    from imageio_ffmpeg import get_ffmpeg_exe as _exe  # lazy import

    return _exe()


def get_ffprobe_exe() -> str:
    """Path to ffprobe.

    imageio-ffmpeg ships ffmpeg but not always ffprobe. We fall back to a
    sibling ``ffprobe`` next to the ffmpeg binary, then to PATH. Probing is not
    on the critical processing path, so a missing ffprobe degrades to "unknown"
    metadata rather than failing a job.
    """
    ffmpeg = Path(get_ffmpeg_exe())
    sibling = ffmpeg.with_name("ffprobe" + ffmpeg.suffix)
    if sibling.exists():
        return str(sibling)
    return "ffprobe"


def build_convert_to_wav_cmd(
    ffmpeg_exe: str, src: Path, dst: Path, *, sample_rate: int = PROCESSING_SAMPLE_RATE
) -> list[str]:
    """Command to convert any input to mono/stereo 16-bit PCM WAV at 48 kHz.

    DeepFilterNet3 operates at 48 kHz. We preserve channel count here and let
    the backend collapse to mono internally if needed; keeping stereo lets us
    re-expand on export when the source was stereo.
    """
    return [
        ffmpeg_exe,
        "-hide_banner",
        "-nostdin",
        "-y",
        "-i", str(src),
        "-vn",                       # drop any video stream
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        str(dst),
    ]


def build_export_cmd(
    ffmpeg_exe: str,
    src: Path,
    dst: Path,
    output_format: OutputFormat,
    *,
    mp3_bitrate: str = "192k",
) -> list[str]:
    """Command to export the enhanced WAV to the user's chosen format."""
    cmd = [ffmpeg_exe, "-hide_banner", "-nostdin", "-y", "-i", str(src), "-vn"]
    if output_format is OutputFormat.MP3:
        cmd += ["-acodec", "libmp3lame", "-b:a", mp3_bitrate]
    elif output_format is OutputFormat.FLAC:
        cmd += ["-acodec", "flac"]
    elif output_format is OutputFormat.WAV:
        cmd += ["-acodec", "pcm_s16le"]
    else:  # pragma: no cover - exhaustive enum
        raise ProcessingError(ErrorCode.UNSUPPORTED_FORMAT, str(output_format))
    cmd.append(str(dst))
    return cmd


def run_ffmpeg(cmd: list[str], *, timeout: float | None = None) -> None:
    """Execute an FFmpeg argument array. Raises ``ProcessingError`` on failure.

    The full stderr is attached to the error ``detail`` for the log only.
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ProcessingError(ErrorCode.FFMPEG_FAILED, f"binary missing: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProcessingError(ErrorCode.FFMPEG_FAILED, f"timeout: {exc}") from exc

    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()[-5:]
        raise ProcessingError(ErrorCode.FFMPEG_FAILED, " | ".join(tail))

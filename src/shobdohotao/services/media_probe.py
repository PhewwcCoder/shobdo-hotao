"""ffprobe-based metadata extraction (duration / channels / rate / size).

Probing is best-effort: if ffprobe is missing or the file is odd, we still
return whatever we can (file size from the OS) so the UI can show partial info
rather than failing. Hard validation (corrupt / no audio) happens here too and
raises a translatable ``ProcessingError``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..domain import AudioMetadata, ErrorCode, ProcessingError
from . import ffmpeg_service


def build_probe_cmd(ffprobe_exe: str, src: Path) -> list[str]:
    """Pure command builder (unit-testable)."""
    return [
        ffprobe_exe,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-select_streams", "a",
        str(src),
    ]


def _parse_probe_json(raw: str, src: Path, size_bytes: int) -> AudioMetadata:
    data = json.loads(raw)
    streams = data.get("streams", [])
    if not streams:
        raise ProcessingError(ErrorCode.NO_AUDIO_STREAM, str(src))
    audio = streams[0]
    fmt = data.get("format", {})
    duration = float(fmt.get("duration") or audio.get("duration") or 0.0)
    return AudioMetadata(
        path=src,
        duration_seconds=duration,
        sample_rate=int(audio.get("sample_rate") or 0),
        channels=int(audio.get("channels") or 0),
        size_bytes=size_bytes,
        codec=str(audio.get("codec_name") or ""),
    )


def probe(src: Path, *, ffprobe_exe: str | None = None) -> AudioMetadata:
    """Probe ``src`` for audio metadata. Raises on missing file / no audio."""
    if not src.exists():
        raise ProcessingError(ErrorCode.FILE_NOT_FOUND, str(src))

    size_bytes = src.stat().st_size
    exe = ffprobe_exe or ffmpeg_service.get_ffprobe_exe()

    try:
        proc = subprocess.run(
            build_probe_cmd(exe, src),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        # ffprobe unavailable: degrade to size-only metadata.
        return AudioMetadata(src, 0.0, 0, 0, size_bytes)

    if proc.returncode != 0 or not proc.stdout.strip():
        raise ProcessingError(ErrorCode.CORRUPT_MEDIA, (proc.stderr or "").strip())

    try:
        return _parse_probe_json(proc.stdout, src, size_bytes)
    except (ValueError, KeyError) as exc:
        raise ProcessingError(ErrorCode.CORRUPT_MEDIA, str(exc)) from exc

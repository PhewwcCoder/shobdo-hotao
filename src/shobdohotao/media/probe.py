"""Full ffprobe-based media inspection for video files.

Returns a :class:`VideoMetadata` covering container, video codec, duration,
every audio stream, and subtitle streams (functional requirement §2). The
command builder and JSON parser are pure so they unit-test without ffprobe.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ..domain import (
    AudioStreamInfo,
    ErrorCode,
    ProcessingError,
    SubtitleStreamInfo,
    VideoMetadata,
)
from ..services import ffmpeg_service


def build_probe_cmd(ffprobe_exe: str, src: Path) -> list[str]:
    """Pure command builder: probe all streams + format as JSON."""
    return [
        ffprobe_exe,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(src),
    ]


def _parse_frame_rate(value: str) -> float:
    """Parse ffprobe ``r_frame_rate`` like ``30000/1001`` into fps."""
    if not value or value == "0/0":
        return 0.0
    if "/" in value:
        num, _, den = value.partition("/")
        try:
            d = float(den)
            return float(num) / d if d else 0.0
        except ValueError:
            return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_probe_json(raw: str, src: Path, size_bytes: int) -> VideoMetadata:
    """Parse ffprobe JSON into :class:`VideoMetadata` (pure)."""
    data = json.loads(raw)
    fmt = data.get("format", {})
    streams = data.get("streams", [])

    video_codec = ""
    width = height = 0
    frame_rate = 0.0
    audio: list[AudioStreamInfo] = []
    subs: list[SubtitleStreamInfo] = []

    for s in streams:
        kind = s.get("codec_type")
        if kind == "video":
            if not video_codec:  # first/primary video stream
                video_codec = str(s.get("codec_name") or "")
                width = int(s.get("width") or 0)
                height = int(s.get("height") or 0)
                frame_rate = _parse_frame_rate(str(s.get("r_frame_rate") or ""))
        elif kind == "audio":
            tags = s.get("tags", {}) or {}
            audio.append(
                AudioStreamInfo(
                    index=int(s.get("index", len(audio))),
                    codec=str(s.get("codec_name") or ""),
                    channels=int(s.get("channels") or 0),
                    sample_rate=int(s.get("sample_rate") or 0),
                    language=str(tags.get("language") or ""),
                    title=str(tags.get("title") or ""),
                )
            )
        elif kind == "subtitle":
            tags = s.get("tags", {}) or {}
            subs.append(
                SubtitleStreamInfo(
                    index=int(s.get("index", 0)),
                    codec=str(s.get("codec_name") or ""),
                    language=str(tags.get("language") or ""),
                )
            )

    container = (
        str(fmt.get("format_name") or "").split(",")[0]
        or src.suffix.lstrip(".").lower()
    )
    duration = float(fmt.get("duration") or 0.0)

    return VideoMetadata(
        path=src,
        container=container,
        video_codec=video_codec,
        duration_seconds=duration,
        size_bytes=size_bytes,
        width=width,
        height=height,
        frame_rate=frame_rate,
        audio_streams=tuple(audio),
        subtitle_streams=tuple(subs),
    )


# --- ffmpeg -i fallback (when ffprobe is not bundled/available) -----------

_CHANNEL_WORDS = {
    "mono": 1,
    "stereo": 2,
    "2.1": 3,
    "quad": 4,
    "4.0": 4,
    "5.0": 5,
    "5.1": 6,
    "6.1": 7,
    "7.1": 8,
}


def _channels_from_layout(text: str) -> int:
    text = text.strip().lower()
    if text in _CHANNEL_WORDS:
        return _CHANNEL_WORDS[text]
    m = re.match(r"(\d+)\s*channels", text)
    return int(m.group(1)) if m else 0


def parse_ffmpeg_info(text: str, src: Path, size_bytes: int) -> VideoMetadata:
    """Parse ``ffmpeg -i`` stderr into :class:`VideoMetadata` (pure).

    Used only when ffprobe is unavailable; the bundled FFmpeg can still report
    stream info on stderr (it errors with "At least one output file…" but the
    inspection text is printed first).
    """
    if "Input #" not in text:
        raise ProcessingError(ErrorCode.CORRUPT_MEDIA, "ffmpeg could not read input")

    duration = 0.0
    dm = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if dm:
        h, m, s = int(dm.group(1)), int(dm.group(2)), float(dm.group(3))
        duration = h * 3600 + m * 60 + s

    container = src.suffix.lstrip(".").lower()
    cm = re.search(r"Input #0,\s*([^,]+)", text)
    if cm:
        container = cm.group(1).strip().split(",")[0]

    video_codec = ""
    width = height = 0
    frame_rate = 0.0
    audio: list[AudioStreamInfo] = []
    subs: list[SubtitleStreamInfo] = []

    stream_re = re.compile(
        r"Stream #0:(\d+)(?:\[[^\]]*\])?(?:\(([^)]+)\))?:\s*"
        r"(Video|Audio|Subtitle):\s*(.*)"
    )
    for line in text.splitlines():
        sm = stream_re.search(line)
        if not sm:
            continue
        index = int(sm.group(1))
        language = (sm.group(2) or "").strip()
        if language == "und":
            language = ""
        kind = sm.group(3)
        rest = sm.group(4)
        codec = rest.split(maxsplit=1)[0].strip(" ,") if rest else ""

        if kind == "Video" and not video_codec:
            video_codec = codec
            res = re.search(r"(\d{2,5})x(\d{2,5})", rest)
            if res:
                width, height = int(res.group(1)), int(res.group(2))
            fps = re.search(r"([\d.]+)\s*fps", rest)
            if fps:
                frame_rate = float(fps.group(1))
        elif kind == "Audio":
            sr = re.search(r"(\d+)\s*Hz", rest)
            channels = 0
            for part in rest.split(","):
                c = _channels_from_layout(part)
                if c:
                    channels = c
                    break
            audio.append(
                AudioStreamInfo(
                    index=index,
                    codec=codec,
                    channels=channels,
                    sample_rate=int(sr.group(1)) if sr else 0,
                    language=language,
                )
            )
        elif kind == "Subtitle":
            subs.append(SubtitleStreamInfo(index=index, codec=codec, language=language))

    return VideoMetadata(
        path=src,
        container=container,
        video_codec=video_codec,
        duration_seconds=duration,
        size_bytes=size_bytes,
        width=width,
        height=height,
        frame_rate=frame_rate,
        audio_streams=tuple(audio),
        subtitle_streams=tuple(subs),
    )


def _probe_via_ffmpeg(src: Path, size_bytes: int) -> VideoMetadata:
    ffmpeg_exe = ffmpeg_service.get_ffmpeg_exe()
    proc = subprocess.run(
        [ffmpeg_exe, "-hide_banner", "-nostdin", "-i", str(src)],
        capture_output=True,
        text=True,
        check=False,
    )
    # ffmpeg prints stream info to stderr then exits non-zero (no output file).
    return parse_ffmpeg_info(proc.stderr or "", src, size_bytes)


def probe_video(src: Path, *, ffprobe_exe: str | None = None) -> VideoMetadata:
    """Probe ``src``. Raises on missing file or corrupt/unreadable media.

    Prefers ffprobe; transparently falls back to ``ffmpeg -i`` parsing when
    ffprobe is not available (imageio-ffmpeg ships ffmpeg but not ffprobe), so
    video inspection works offline with only the bundled FFmpeg.
    """
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
        # No ffprobe binary — use the ffmpeg fallback.
        return _probe_via_ffmpeg(src, size_bytes)

    if proc.returncode != 0 or not proc.stdout.strip():
        raise ProcessingError(ErrorCode.CORRUPT_MEDIA, (proc.stderr or "").strip())

    try:
        return parse_probe_json(proc.stdout, src, size_bytes)
    except (ValueError, KeyError) as exc:
        raise ProcessingError(ErrorCode.CORRUPT_MEDIA, str(exc)) from exc

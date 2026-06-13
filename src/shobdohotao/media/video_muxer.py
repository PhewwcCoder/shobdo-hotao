"""Remux the cleaned audio back with the original video (pure builder).

Design goals (functional requirements §6–§10):
- Copy the original video stream with ``-c:v copy`` (no quality loss); since the
  default output container matches the input, copy is always compatible.
- Encode the cleaned audio with a codec appropriate to the container:
  AAC for mp4/mov/mkv/avi, libopus for webm (webm forbids AAC).
- Preserve subtitle streams and global metadata where the container allows.
- Map exactly one (the cleaned) audio stream into the output.
"""

from __future__ import annotations

from pathlib import Path

# Audio encoder chosen per output container.
_AUDIO_CODEC_BY_CONTAINER = {
    "mp4": "aac",
    "mov": "aac",
    "mkv": "aac",
    "avi": "aac",
    "webm": "libopus",
}

# Containers we will try to copy subtitle streams into. webm/avi have poor or
# no subtitle support via copy, so we skip subtitles there.
_SUBTITLE_FRIENDLY = {"mp4", "mov", "mkv"}


def audio_codec_for(container: str) -> str:
    """Audio encoder for a given output container (defaults to AAC)."""
    return _AUDIO_CODEC_BY_CONTAINER.get(container.lower(), "aac")


def build_mux_cmd(
    ffmpeg_exe: str,
    video_src: Path,
    cleaned_wav: Path,
    dst: Path,
    *,
    container: str,
    audio_bitrate: str = "192k",
    keep_subtitles: bool = True,
) -> list[str]:
    """Build the FFmpeg command to remux ``cleaned_wav`` into ``video_src``.

    Input 0 is the original video; input 1 is the cleaned WAV. We take video
    from input 0, the single audio from input 1, and (optionally) subtitles
    from input 0.
    """
    container = container.lower()
    codec = audio_codec_for(container)

    cmd = [
        ffmpeg_exe,
        "-hide_banner",
        "-nostdin",
        "-y",
        "-i", str(video_src),     # 0: original video
        "-i", str(cleaned_wav),   # 1: cleaned audio
        "-map", "0:v:0",          # original video stream
        "-map", "1:a:0",          # cleaned audio stream
    ]

    include_subs = keep_subtitles and container in _SUBTITLE_FRIENDLY
    if include_subs:
        cmd += ["-map", "0:s?"]   # subtitles if present (optional)

    cmd += [
        "-c:v", "copy",           # no video re-encode -> no quality loss
        "-c:a", codec,
        "-b:a", audio_bitrate,
    ]
    if include_subs:
        cmd += ["-c:s", "copy"]

    # Preserve global + per-stream metadata where possible.
    cmd += ["-map_metadata", "0"]

    # Faststart helps mp4/mov play before fully downloaded; harmless locally.
    if container in {"mp4", "mov"}:
        cmd += ["-movflags", "+faststart"]

    cmd.append(str(dst))
    return cmd

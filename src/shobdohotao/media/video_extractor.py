"""Extract one audio stream from a video as a 48 kHz PCM WAV (pure builder).

The extracted WAV feeds the existing DeepFilterNet pipeline. We pick a single
audio stream (the user's choice, or the first) and decode it to mono/stereo
16-bit PCM at 48 kHz — the rate the model operates at.
"""

from __future__ import annotations

from pathlib import Path

from ..domain import PROCESSING_SAMPLE_RATE


def build_extract_audio_cmd(
    ffmpeg_exe: str,
    src: Path,
    dst_wav: Path,
    *,
    stream_index: int | None = None,
    sample_rate: int = PROCESSING_SAMPLE_RATE,
) -> list[str]:
    """Build the FFmpeg command to extract one audio stream to WAV.

    ``stream_index`` is the absolute ffprobe stream index. We map it with
    ``-map 0:<index>`` when given; otherwise ``-map 0:a:0`` (first audio
    stream). ``-vn`` drops video so only audio is written.
    """
    if stream_index is not None:
        mapping = ["-map", f"0:{stream_index}"]
    else:
        mapping = ["-map", "0:a:0"]
    return [
        ffmpeg_exe,
        "-hide_banner",
        "-nostdin",
        "-y",
        "-i", str(src),
        *mapping,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        str(dst_wav),
    ]

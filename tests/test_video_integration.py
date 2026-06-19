"""Integration test: generate a short real video, then run the full video
service (real FFmpeg extract + mux) with a copy-backend standing in for
DeepFilterNet (so the test needs no torch).

Skips automatically if the bundled FFmpeg cannot be located or fails to
generate the fixture (e.g. a minimal FFmpeg build without libx264/aac).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from shobdohotao.domain import (
    JobState,
    Strength,
    VideoDenoiseRequest,
    VideoMetadata,
)
from shobdohotao.media.ffmpeg_runner import FfmpegRunner
from shobdohotao.services import ffmpeg_service
from shobdohotao.services.video_processing_service import VideoProcessingService


def _ffmpeg_exe() -> str:
    return ffmpeg_service.get_ffmpeg_exe()


def _make_test_video(path: Path, ffmpeg: str) -> bool:
    """Create a ~1s 160x120 video with a 440 Hz tone. Returns success."""
    cmd = [
        ffmpeg, "-hide_banner", "-nostdin", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=1:size=160x120:rate=15",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=60, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and path.exists() and path.stat().st_size > 0


class CopyBackend:
    """Stand-in for DeepFilterNet: copies input WAV to output WAV."""

    def enhance(self, wav_in: Path, wav_out: Path, strength: Strength,
                on_stage=None, on_progress=None, cancelled=None) -> None:
        shutil.copyfile(wav_in, wav_out)


@pytest.fixture()
def ffmpeg() -> str:
    try:
        return _ffmpeg_exe()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"FFmpeg unavailable: {exc}")


def test_full_video_processing_with_real_ffmpeg(ffmpeg: str, tmp_path: Path) -> None:
    src = tmp_path / "sample.mp4"
    if not _make_test_video(src, ffmpeg):
        pytest.skip("could not generate test video (FFmpeg build lacks x264/aac)")

    # Inject metadata (avoids depending on a bundled ffprobe); the rest of the
    # pipeline — extract + mux — runs against real FFmpeg.
    meta = VideoMetadata(
        path=src, container="mp4", video_codec="h264",
        duration_seconds=1.0, size_bytes=src.stat().st_size,
        width=160, height=120, frame_rate=15.0,
        audio_streams=(),  # filled below
    )
    from shobdohotao.domain import AudioStreamInfo

    meta = VideoMetadata(
        **{**meta.__dict__,
           "audio_streams": (AudioStreamInfo(1, "aac", 1, 44100),)}
    )

    out_dir = tmp_path / "out"
    request = VideoDenoiseRequest(input_path=src, output_dir=out_dir)
    states: list[JobState] = []
    service = VideoProcessingService(
        backend=CopyBackend(),
        ffmpeg_exe=ffmpeg,
        runner=FfmpegRunner(),
        probe_fn=lambda p: meta,
    )
    result = service.run(request, progress=lambda s, f: states.append(s))

    assert result.output_path.exists()
    assert result.output_path.stat().st_size > 0
    assert result.output_path.name == "sample_cleaned.mp4"
    assert states[-1] is JobState.DONE
    # Original is untouched.
    assert src.exists()

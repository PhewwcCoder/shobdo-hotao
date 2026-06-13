"""Video processing service lifecycle tests using fakes.

Verifies: stage order, guaranteed temp cleanup on success/error/cancel,
no-audio / unsupported-container / too-long / low-disk handling, multi-stream
selection, and collision-safe output naming. No real FFmpeg / model / video.
"""

from __future__ import annotations

import glob
import shutil
import tempfile
from pathlib import Path

import pytest

from shobdohotao.domain import (
    AudioStreamInfo,
    ErrorCode,
    JobState,
    ProcessingError,
    Strength,
    VideoDenoiseRequest,
    VideoMetadata,
)
from shobdohotao.media.ffmpeg_runner import FfmpegRunner
from shobdohotao.services.video_processing_service import VideoProcessingService


class FakeBackend:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def enhance(self, wav_in: Path, wav_out: Path, strength: Strength) -> None:
        if self.fail:
            raise ProcessingError(ErrorCode.ENHANCE_FAILED, "fake")
        shutil.copyfile(wav_in, wav_out)


class FakeRunner:
    """Duck-typed FfmpegRunner: writes each command's destination file."""

    def __init__(self, *, cancel_on_call: int | None = None) -> None:
        self.calls: list[list[str]] = []
        self._cancel_on = cancel_on_call

    def run(self, cmd: list[str], *, timeout: float | None = None) -> None:
        self.calls.append(cmd)
        if self._cancel_on is not None and len(self.calls) >= self._cancel_on:
            raise ProcessingError(ErrorCode.CANCELLED, "user cancelled")
        Path(cmd[-1]).write_bytes(b"FAKEMEDIA")

    def cancel(self) -> None:
        self._cancel_on = 1


def _meta(path: Path, *, streams: int = 1, duration: float = 30.0) -> VideoMetadata:
    audio = tuple(
        AudioStreamInfo(index=i + 1, codec="aac", channels=2, sample_rate=48000)
        for i in range(streams)
    )
    return VideoMetadata(
        path=path, container="mp4", video_codec="h264",
        duration_seconds=duration, size_bytes=1024, width=1280, height=720,
        frame_rate=30.0, audio_streams=audio,
    )


def _temp_dirs() -> set[str]:
    return set(glob.glob(str(Path(tempfile.gettempdir()) / "shobdohotao_vid_*")))


def _request(tmp_path: Path, **kw) -> VideoDenoiseRequest:
    inp = tmp_path / "lecture.mp4"
    inp.write_bytes(b"video")
    return VideoDenoiseRequest(
        input_path=inp, output_dir=tmp_path / "out", **kw
    )


def _service(runner, *, backend=None, meta_fn=None, free=10**12, max_dur=10**9):
    return VideoProcessingService(
        backend=backend or FakeBackend(),
        ffmpeg_exe="ffmpeg",
        runner=runner,
        probe_fn=meta_fn or _meta,
        free_bytes_fn=lambda p: free,
        max_duration_seconds=max_dur,
    )


def test_happy_path_extract_enhance_mux_and_cleanup(tmp_path: Path) -> None:
    before = _temp_dirs()
    runner = FakeRunner()
    states: list[JobState] = []
    svc = _service(runner)
    result = svc.run(_request(tmp_path), progress=lambda s, f: states.append(s))

    assert result.output_path.name == "lecture_cleaned.mp4"
    assert result.output_path.exists()
    # Two ffmpeg calls: extract + mux.
    assert len(runner.calls) == 2
    assert states[0] is JobState.INSPECTING
    assert JobState.EXTRACTING in states and JobState.MUXING in states
    assert states[-1] is JobState.DONE
    assert _temp_dirs() == before  # temp cleaned


def test_no_audio_raises_and_cleans(tmp_path: Path) -> None:
    before = _temp_dirs()
    runner = FakeRunner()
    svc = _service(runner, meta_fn=lambda p: _meta(p, streams=0))
    with pytest.raises(ProcessingError) as exc:
        svc.run(_request(tmp_path))
    assert exc.value.code is ErrorCode.NO_AUDIO_STREAM
    assert runner.calls == []  # never reached extraction
    assert _temp_dirs() == before


def test_unsupported_container(tmp_path: Path) -> None:
    inp = tmp_path / "clip.flv"
    inp.write_bytes(b"x")
    req = VideoDenoiseRequest(input_path=inp, output_dir=tmp_path / "out")
    with pytest.raises(ProcessingError) as exc:
        _service(FakeRunner()).run(req)
    assert exc.value.code is ErrorCode.UNSUPPORTED_CONTAINER


def test_video_too_long(tmp_path: Path) -> None:
    svc = _service(FakeRunner(), meta_fn=lambda p: _meta(p, duration=99999),
                   max_dur=60)
    with pytest.raises(ProcessingError) as exc:
        svc.run(_request(tmp_path))
    assert exc.value.code is ErrorCode.VIDEO_TOO_LONG


def test_low_disk_space(tmp_path: Path) -> None:
    svc = _service(FakeRunner(), free=1)
    with pytest.raises(ProcessingError) as exc:
        svc.run(_request(tmp_path))
    assert exc.value.code is ErrorCode.LOW_DISK_SPACE


def test_enhance_failure_cleans_temp(tmp_path: Path) -> None:
    before = _temp_dirs()
    svc = _service(FakeRunner(), backend=FakeBackend(fail=True))
    with pytest.raises(ProcessingError) as exc:
        svc.run(_request(tmp_path))
    assert exc.value.code is ErrorCode.ENHANCE_FAILED
    assert _temp_dirs() == before


def test_cancel_during_mux_cleans_temp(tmp_path: Path) -> None:
    before = _temp_dirs()
    runner = FakeRunner(cancel_on_call=2)  # extract ok, cancel at mux
    svc = _service(runner)
    with pytest.raises(ProcessingError) as exc:
        svc.run(_request(tmp_path))
    assert exc.value.code is ErrorCode.CANCELLED
    assert _temp_dirs() == before


def test_multi_stream_selection_valid(tmp_path: Path) -> None:
    runner = FakeRunner()
    svc = _service(runner, meta_fn=lambda p: _meta(p, streams=3))
    result = svc.run(_request(tmp_path, audio_stream_index=2))
    assert result.cleaned_stream_index == 2
    # Extraction command should map the chosen absolute stream index.
    assert "0:2" in runner.calls[0]


def test_multi_stream_selection_invalid_index(tmp_path: Path) -> None:
    svc = _service(FakeRunner(), meta_fn=lambda p: _meta(p, streams=2))
    with pytest.raises(ProcessingError) as exc:
        svc.run(_request(tmp_path, audio_stream_index=99))
    assert exc.value.code is ErrorCode.NO_AUDIO_STREAM


def test_output_collision_uses_underscore_2(tmp_path: Path) -> None:
    req = _request(tmp_path)
    req.output_dir.mkdir(parents=True, exist_ok=True)
    (req.output_dir / "lecture_cleaned.mp4").write_bytes(b"existing")
    result = _service(FakeRunner()).run(req)
    assert result.output_path.name == "lecture_cleaned_2.mp4"


# --- FfmpegRunner cancellation (no real subprocess needed) ---------------

def test_runner_run_after_cancel_raises_without_launching() -> None:
    runner = FfmpegRunner()
    runner.cancel()
    assert runner.cancelled is True
    with pytest.raises(ProcessingError) as exc:
        runner.run(["ffmpeg", "-version"])  # should not launch
    assert exc.value.code is ErrorCode.CANCELLED

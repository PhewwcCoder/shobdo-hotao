"""Pipeline lifecycle tests using fakes (no FFmpeg, no torch, no real audio).

Verifies the hard rules from §4/§10:
- temp dir cleaned in ALL outcomes (success, error, cancel);
- stages run in order;
- collision-safe output naming;
- low-disk preflight.
"""

from __future__ import annotations

import glob
import tempfile
from pathlib import Path

import pytest

from shobdohotao.domain import (
    AudioMetadata,
    DenoiseRequest,
    ErrorCode,
    JobState,
    OutputFormat,
    ProcessingError,
    Strength,
)
from shobdohotao.services.pipeline import Pipeline


class FakeBackend:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def enhance(self, wav_in: Path, wav_out: Path, strength: Strength,
                on_stage=None) -> None:
        self.calls += 1
        if on_stage is not None:
            from shobdohotao.domain import ProcessingStage
            on_stage(ProcessingStage.LOADING_MODEL)
            on_stage(ProcessingStage.DENOISING)
        if self.fail:
            raise ProcessingError(ErrorCode.ENHANCE_FAILED, "fake fail")
        wav_out.write_bytes(b"RIFFfake")  # produce a real enhanced wav


def _meta(path: Path) -> AudioMetadata:
    return AudioMetadata(path, 10.0, 44100, 2, 1024, "mp3")


def _fake_run_factory(record: list[list[str]]):
    def run(cmd: list[str]) -> None:
        record.append(cmd)
        # Emulate FFmpeg writing its destination (last arg).
        Path(cmd[-1]).write_bytes(b"data")
    return run


def _temp_dirs() -> list[str]:
    return glob.glob(str(Path(tempfile.gettempdir()) / "shobdohotao_*"))


def _make_request(tmp_path: Path) -> DenoiseRequest:
    inp = tmp_path / "noisy.mp3"
    inp.write_bytes(b"x")
    return DenoiseRequest(
        input_path=inp,
        output_dir=tmp_path / "out",
        output_format=OutputFormat.MP3,
        strength=Strength.BALANCED,
    )


def test_happy_path_produces_output_and_cleans_temp(tmp_path: Path) -> None:
    before = set(_temp_dirs())
    record: list[list[str]] = []
    states: list[JobState] = []
    pipeline = Pipeline(
        backend=FakeBackend(),
        ffmpeg_exe="ffmpeg",
        probe_fn=_meta,
        run_fn=_fake_run_factory(record),
        free_bytes_fn=lambda p: 10**12,
    )
    result = pipeline.run(
        _make_request(tmp_path),
        progress=lambda s, f: states.append(s),
    )
    assert result.output_path.exists()
    assert result.output_path.name == "noisy_cleaned.mp3"
    # Two ffmpeg calls: convert + export.
    assert len(record) == 2
    # Stage order observed.
    assert states[0] is JobState.VALIDATING
    assert JobState.ENHANCING in states
    assert states[-1] is JobState.DONE
    # No leftover temp dirs.
    assert set(_temp_dirs()) == before


def test_enhance_failure_cleans_temp_and_raises(tmp_path: Path) -> None:
    before = set(_temp_dirs())
    pipeline = Pipeline(
        backend=FakeBackend(fail=True),
        ffmpeg_exe="ffmpeg",
        probe_fn=_meta,
        run_fn=_fake_run_factory([]),
        free_bytes_fn=lambda p: 10**12,
    )
    with pytest.raises(ProcessingError) as exc:
        pipeline.run(_make_request(tmp_path))
    assert exc.value.code is ErrorCode.ENHANCE_FAILED
    assert set(_temp_dirs()) == before  # cleaned despite failure


def test_cancel_cleans_temp_and_raises_cancelled(tmp_path: Path) -> None:
    before = set(_temp_dirs())
    pipeline = Pipeline(
        backend=FakeBackend(),
        ffmpeg_exe="ffmpeg",
        probe_fn=_meta,
        run_fn=_fake_run_factory([]),
        free_bytes_fn=lambda p: 10**12,
    )
    with pytest.raises(ProcessingError) as exc:
        pipeline.run(_make_request(tmp_path), cancelled=lambda: True)
    assert exc.value.code is ErrorCode.CANCELLED
    assert set(_temp_dirs()) == before


def test_missing_input_raises_file_not_found(tmp_path: Path) -> None:
    req = DenoiseRequest(
        input_path=tmp_path / "ghost.mp3",
        output_dir=tmp_path / "out",
        output_format=OutputFormat.WAV,
    )
    pipeline = Pipeline(
        backend=FakeBackend(),
        ffmpeg_exe="ffmpeg",
        probe_fn=_meta,
        run_fn=_fake_run_factory([]),
        free_bytes_fn=lambda p: 10**12,
    )
    with pytest.raises(ProcessingError) as exc:
        pipeline.run(req)
    assert exc.value.code is ErrorCode.FILE_NOT_FOUND


def test_low_disk_space_preflight(tmp_path: Path) -> None:
    pipeline = Pipeline(
        backend=FakeBackend(),
        ffmpeg_exe="ffmpeg",
        probe_fn=_meta,
        run_fn=_fake_run_factory([]),
        free_bytes_fn=lambda p: 1,  # basically no space
    )
    with pytest.raises(ProcessingError) as exc:
        pipeline.run(_make_request(tmp_path))
    assert exc.value.code is ErrorCode.LOW_DISK_SPACE


def test_output_name_collision_is_resolved(tmp_path: Path) -> None:
    req = _make_request(tmp_path)
    req.output_dir.mkdir(parents=True, exist_ok=True)
    (req.output_dir / "noisy_cleaned.mp3").write_bytes(b"existing")
    pipeline = Pipeline(
        backend=FakeBackend(),
        ffmpeg_exe="ffmpeg",
        probe_fn=_meta,
        run_fn=_fake_run_factory([]),
        free_bytes_fn=lambda p: 10**12,
    )
    result = pipeline.run(req)
    assert result.output_path.name == "noisy_cleaned_2.mp3"

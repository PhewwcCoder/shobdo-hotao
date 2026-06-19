"""Backend model-reuse / post-filter / chunked-streaming logic.

Uses a fake DeepFilterNet ``init_fn`` (no real model) and a passthrough enhance
function, plus real (tiny) WAV files via soundfile, so we can assert: when the
model is (re)loaded, that long audio is processed in bounded chunks, progress is
reported, and cancellation is honoured between chunks — all without the ML stack.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("soundfile")
pytest.importorskip("torch")

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402

from shobdohotao.domain import (  # noqa: E402
    ErrorCode,
    ProcessingError,
    ProcessingStage,
    Strength,
)
from shobdohotao.services.denoise_backend import (  # noqa: E402
    _CHUNK_SECONDS,
    DeepFilterNetBackend,
)

_SR = 48_000


class _FakeState:
    def sr(self) -> int:
        return _SR


def _passthrough(model, df_state, audio, atten_lim_db=None):
    """Stand-in for df.enhance: returns the input tensor unchanged."""
    return audio


def _make_backend():
    calls: list[bool] = []

    def fake_init(post_filter: bool):
        calls.append(post_filter)
        return ("model", _FakeState(), _passthrough)

    return DeepFilterNetBackend(init_fn=fake_init), calls


def _write_wav(path: Path, seconds: float, channels: int = 1) -> None:
    n = int(seconds * _SR)
    data = (np.random.rand(n, channels).astype("float32") * 0.2 - 0.1)
    sf.write(str(path), data, _SR, subtype="PCM_16")


def test_model_loaded_once_for_repeated_balanced(tmp_path: Path) -> None:
    backend, calls = _make_backend()
    src = tmp_path / "in.wav"
    _write_wav(src, 0.5)
    backend.enhance(src, tmp_path / "o1.wav", Strength.BALANCED)
    backend.enhance(src, tmp_path / "o2.wav", Strength.GENTLE)
    assert calls == [False]  # both keep post-filter off -> single load


def test_strong_reloads_with_post_filter_then_reuses(tmp_path: Path) -> None:
    backend, calls = _make_backend()
    src = tmp_path / "in.wav"
    _write_wav(src, 0.3)
    backend.enhance(src, tmp_path / "o1.wav", Strength.BALANCED)  # pf off
    backend.enhance(src, tmp_path / "o2.wav", Strength.STRONG)    # pf on -> reload
    backend.enhance(src, tmp_path / "o3.wav", Strength.STRONG)    # reuse
    assert calls == [False, True]


def test_stage_callback_sequences_loading_then_denoising(tmp_path: Path) -> None:
    backend, _calls = _make_backend()
    src = tmp_path / "in.wav"
    _write_wav(src, 0.2)
    seen: list[ProcessingStage] = []
    backend.enhance(src, tmp_path / "o.wav", Strength.BALANCED, on_stage=seen.append)
    assert seen == [ProcessingStage.LOADING_MODEL, ProcessingStage.DENOISING]


def test_output_matches_input_length_and_channels(tmp_path: Path) -> None:
    backend, _calls = _make_backend()
    src = tmp_path / "in.wav"
    _write_wav(src, 1.5, channels=2)  # stereo, passthrough
    out = tmp_path / "o.wav"
    backend.enhance(src, out, Strength.BALANCED)
    assert out.exists()
    info_in, info_out = sf.info(str(src)), sf.info(str(out))
    assert info_out.channels == 2
    assert info_out.samplerate == _SR
    assert abs(info_out.frames - info_in.frames) <= 1  # length preserved


def test_long_audio_is_processed_in_multiple_chunks(tmp_path: Path) -> None:
    # Spy enhance: count how many times it's invoked (= number of chunks).
    chunks: list[int] = []

    def spy_init(post_filter: bool):
        def spy(model, df_state, audio, atten_lim_db=None):
            chunks.append(audio.shape[-1])
            return audio
        return ("model", _FakeState(), spy)

    backend = DeepFilterNetBackend(init_fn=spy_init)
    src = tmp_path / "in.wav"
    _write_wav(src, _CHUNK_SECONDS * 2.5)  # 2.5 chunks
    backend.enhance(src, tmp_path / "o.wav", Strength.BALANCED)
    assert len(chunks) == 3  # bounded passes, not one giant tensor
    assert max(chunks) <= _CHUNK_SECONDS * _SR  # each pass is one chunk at most


def test_progress_reported_and_reaches_total(tmp_path: Path) -> None:
    backend, _calls = _make_backend()
    src = tmp_path / "in.wav"
    _write_wav(src, _CHUNK_SECONDS * 2.0)
    seen: list[tuple[int, int]] = []
    backend.enhance(src, tmp_path / "o.wav", Strength.BALANCED,
                    on_progress=lambda cur, tot: seen.append((cur, tot)))
    assert seen, "expected progress callbacks"
    assert all(0 <= cur <= tot for cur, tot in seen)
    assert seen[-1][0] == seen[-1][1]  # finishes at 100%


def test_cancellation_stops_between_chunks(tmp_path: Path) -> None:
    backend, _calls = _make_backend()
    src = tmp_path / "in.wav"
    _write_wav(src, _CHUNK_SECONDS * 3.0)
    with pytest.raises(ProcessingError) as ei:
        backend.enhance(src, tmp_path / "o.wav", Strength.BALANCED,
                        cancelled=lambda: True)  # cancel immediately
    assert ei.value.code is ErrorCode.CANCELLED


def test_init_failure_becomes_backend_init_error(tmp_path: Path) -> None:
    def boom(post_filter: bool):
        raise RuntimeError("no model files")

    backend = DeepFilterNetBackend(init_fn=boom)
    src = tmp_path / "in.wav"
    _write_wav(src, 0.1)
    with pytest.raises(ProcessingError) as ei:
        backend.enhance(src, tmp_path / "o.wav", Strength.BALANCED)
    assert ei.value.code is ErrorCode.BACKEND_INIT_FAILED

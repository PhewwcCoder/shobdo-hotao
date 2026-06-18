"""Backend model-reuse / post-filter logic (no real DeepFilterNet load).

The DeepFilterNet init is injected as a fake so we can assert *when* the model
is (re)loaded: once normally, again only when the post-filter state changes
(STRONG turns it on; GENTLE/BALANCED leave it off).
"""

from __future__ import annotations

from pathlib import Path

from shobdohotao.domain import ErrorCode, ProcessingError, Strength
from shobdohotao.services.denoise_backend import DeepFilterNetBackend


class _FakeState:
    def sr(self) -> int:
        return 48_000


class _FakeIO:
    def __init__(self) -> None:
        self.saved: list[str] = []

    def load_audio(self, path: str, sr: int):
        return ("audio", sr)

    def save_audio(self, path: str, enhanced, sr: int) -> None:
        self.saved.append(path)


def _make_backend():
    calls: list[bool] = []
    io = _FakeIO()

    def fake_init(post_filter: bool):
        calls.append(post_filter)
        return ("model", _FakeState(), lambda *a, **k: "enhanced", io)

    return DeepFilterNetBackend(init_fn=fake_init), calls, io


def test_model_loaded_once_for_repeated_balanced(tmp_path: Path) -> None:
    backend, calls, io = _make_backend()
    out = tmp_path / "o.wav"
    backend.enhance(tmp_path / "a.wav", out, Strength.BALANCED)
    backend.enhance(tmp_path / "b.wav", out, Strength.GENTLE)
    # Both keep post-filter OFF -> a single load, reused.
    assert calls == [False]
    assert len(io.saved) == 2


def test_strong_reloads_with_post_filter_then_reuses(tmp_path: Path) -> None:
    backend, calls, io = _make_backend()
    out = tmp_path / "o.wav"
    backend.enhance(tmp_path / "a.wav", out, Strength.BALANCED)  # pf off
    backend.enhance(tmp_path / "b.wav", out, Strength.STRONG)    # pf on -> reload
    backend.enhance(tmp_path / "c.wav", out, Strength.STRONG)    # reuse
    assert calls == [False, True]


def test_stage_callback_sequences_loading_then_denoising(tmp_path: Path) -> None:
    backend, _calls, _io = _make_backend()
    seen = []
    backend.enhance(tmp_path / "a.wav", tmp_path / "o.wav", Strength.BALANCED,
                    on_stage=seen.append)
    from shobdohotao.domain import ProcessingStage

    assert seen == [ProcessingStage.LOADING_MODEL, ProcessingStage.DENOISING]


def test_init_failure_becomes_backend_init_error(tmp_path: Path) -> None:
    def boom(post_filter: bool):
        raise RuntimeError("no model files")

    backend = DeepFilterNetBackend(init_fn=boom)
    try:
        backend.enhance(tmp_path / "a.wav", tmp_path / "o.wav", Strength.BALANCED)
    except ProcessingError as exc:
        assert exc.code is ErrorCode.BACKEND_INIT_FAILED
    else:  # pragma: no cover
        raise AssertionError("expected ProcessingError")

"""Speech enhancement backend — DeepFilterNet3 only.

The model is initialised lazily and reused for the whole process lifetime
(rule §10: "DeepFilterNet initialized once per process and reused"). Heavy
imports (torch, df) happen inside ``_ensure_loaded`` so this module imports
cleanly on machines without the ML stack (CI, dev sandboxes).

The backend protocol is small and injectable so the pipeline can be tested
with a fake backend.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from ..domain import ErrorCode, ProcessingError, ProcessingStage, Strength

# Called with LOADING_MODEL just before the (possibly first-time) model load and
# DENOISING once the model is ready and enhancement is about to start.
StageCallback = Callable[[ProcessingStage], None]


class DenoiseBackend(Protocol):
    """Minimal contract the pipeline depends on."""

    def enhance(
        self,
        wav_in: Path,
        wav_out: Path,
        strength: Strength,
        on_stage: StageCallback | None = None,
    ) -> None:
        """Read 48 kHz PCM WAV ``wav_in``, write enhanced WAV ``wav_out``."""
        ...


def _default_init(post_filter: bool):
    """Load DeepFilterNet3. ``post_filter`` enables the model's extra
    noise-reduction post-filter (used by the STRONG preset). Heavy ML imports
    stay inside so this module imports cleanly without the stack installed."""
    from df import io as df_io  # type: ignore
    from df.enhance import enhance, init_df  # type: ignore

    model, df_state, _ = init_df(post_filter=post_filter)
    return model, df_state, enhance, df_io


class DeepFilterNetBackend:
    """Lazy, process-wide DeepFilterNet3 backend.

    Thread-safe lazy init guards against two jobs racing the first load, even
    though the MVP runs one job at a time. The model is reused across jobs; it is
    only reloaded when the requested post-filter state changes (STRONG turns the
    post-filter on, GENTLE/BALANCED leave it off), so the common case never pays
    the load cost twice. ``init_fn`` is injectable for tests.
    """

    def __init__(self, init_fn=_default_init) -> None:
        self._lock = threading.Lock()
        self._init_fn = init_fn
        self._model = None
        self._df_state = None
        self._enhance_fn = None
        self._io = None  # df.io module (load/save audio)
        self._loaded_pf: bool | None = None  # post-filter state of loaded model

    def _ensure_loaded(self, post_filter: bool) -> None:
        if self._model is not None and self._loaded_pf == post_filter:
            return
        with self._lock:
            if self._model is not None and self._loaded_pf == post_filter:
                return
            try:
                model, df_state, enhance_fn, io = self._init_fn(post_filter)
            except Exception as exc:  # noqa: BLE001
                raise ProcessingError(
                    ErrorCode.BACKEND_INIT_FAILED, repr(exc)
                ) from exc
            self._model = model
            self._df_state = df_state
            self._enhance_fn = enhance_fn
            self._io = io
            self._loaded_pf = post_filter

    def enhance(
        self,
        wav_in: Path,
        wav_out: Path,
        strength: Strength,
        on_stage: StageCallback | None = None,
    ) -> None:
        # STRONG adds DeepFilterNet's post-filter for extra residual-noise
        # removal; GENTLE/BALANCED keep the default (preserves prior behaviour).
        want_post_filter = strength is Strength.STRONG
        if on_stage is not None:
            on_stage(ProcessingStage.LOADING_MODEL)
        self._ensure_loaded(want_post_filter)
        if on_stage is not None:
            on_stage(ProcessingStage.DENOISING)
        assert self._enhance_fn is not None and self._io is not None
        try:
            audio, _ = self._io.load_audio(str(wav_in), sr=self._df_state.sr())
            enhanced = self._enhance_fn(
                self._model,
                self._df_state,
                audio,
                atten_lim_db=strength.attenuation_limit_db,
            )
            self._io.save_audio(str(wav_out), enhanced, sr=self._df_state.sr())
        except ProcessingError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProcessingError(ErrorCode.ENHANCE_FAILED, repr(exc)) from exc


# Process-wide singleton accessor.
_INSTANCE: DeepFilterNetBackend | None = None


def get_backend() -> DeepFilterNetBackend:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = DeepFilterNetBackend()
    return _INSTANCE

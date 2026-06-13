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
from pathlib import Path
from typing import Protocol

from ..domain import ErrorCode, ProcessingError, Strength


class DenoiseBackend(Protocol):
    """Minimal contract the pipeline depends on."""

    def enhance(self, wav_in: Path, wav_out: Path, strength: Strength) -> None:
        """Read 48 kHz PCM WAV ``wav_in``, write enhanced WAV ``wav_out``."""
        ...


class DeepFilterNetBackend:
    """Lazy, process-wide DeepFilterNet3 backend.

    Thread-safe lazy init guards against two jobs racing the first load, even
    though the MVP runs one job at a time.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._model = None
        self._df_state = None
        self._enhance_fn = None
        self._io = None  # df.io module (load/save audio)

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            try:
                from df import io as df_io  # type: ignore
                from df.enhance import enhance, init_df  # type: ignore

                model, df_state, _ = init_df()
                self._model = model
                self._df_state = df_state
                self._enhance_fn = enhance
                self._io = df_io
            except Exception as exc:  # noqa: BLE001
                raise ProcessingError(
                    ErrorCode.BACKEND_INIT_FAILED, repr(exc)
                ) from exc

    def enhance(self, wav_in: Path, wav_out: Path, strength: Strength) -> None:
        self._ensure_loaded()
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

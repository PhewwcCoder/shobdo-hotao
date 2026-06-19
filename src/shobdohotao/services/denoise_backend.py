"""Speech enhancement backend — DeepFilterNet3 only.

The model is initialised lazily and reused for the whole process lifetime
(rule §10: "DeepFilterNet initialized once per process and reused"). Heavy
imports (torch, df, soundfile) happen inside methods so this module imports
cleanly on machines without the ML stack (CI, dev sandboxes).

Long files are processed in fixed-length chunks (see ``_CHUNK_SECONDS``) so peak
memory stays bounded: DeepFilterNet's ``enhance`` builds a full STFT of whatever
tensor it is given, so feeding it a whole 2-hour recording at once allocates
gigabytes and thrashes/crashes the machine. Chunked + ``torch.no_grad`` keeps
RAM flat regardless of input length, reports real progress, and is cancellable
between chunks.

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
# Reports denoise progress as (seconds_done, seconds_total).
ProgressCallback = Callable[[int, int], None]
# Returns True if the user asked to cancel (checked between chunks).
CancelledCallback = Callable[[], bool]

# Seconds of audio enhanced per pass. Small enough that one chunk's STFT +
# model activations stay in the tens-to-low-hundreds of MB even for stereo.
_CHUNK_SECONDS = 30


class DenoiseBackend(Protocol):
    """Minimal contract the pipeline depends on."""

    def enhance(
        self,
        wav_in: Path,
        wav_out: Path,
        strength: Strength,
        on_stage: StageCallback | None = None,
        on_progress: ProgressCallback | None = None,
        cancelled: CancelledCallback | None = None,
    ) -> None:
        """Read 48 kHz PCM WAV ``wav_in``, write enhanced WAV ``wav_out``."""
        ...


def _default_init(post_filter: bool):
    """Load DeepFilterNet3. ``post_filter`` enables the model's extra
    noise-reduction post-filter (used by the STRONG preset). Heavy ML imports
    stay inside so this module imports cleanly without the stack installed."""
    from df.enhance import enhance, init_df  # type: ignore

    model, df_state, _ = init_df(post_filter=post_filter)
    return model, df_state, enhance


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
        self._loaded_pf: bool | None = None  # post-filter state of loaded model

    def _ensure_loaded(self, post_filter: bool) -> None:
        if self._model is not None and self._loaded_pf == post_filter:
            return
        with self._lock:
            if self._model is not None and self._loaded_pf == post_filter:
                return
            try:
                model, df_state, enhance_fn = self._init_fn(post_filter)
            except Exception as exc:  # noqa: BLE001
                raise ProcessingError(
                    ErrorCode.BACKEND_INIT_FAILED, repr(exc)
                ) from exc
            self._model = model
            self._df_state = df_state
            self._enhance_fn = enhance_fn
            self._loaded_pf = post_filter

    def enhance(
        self,
        wav_in: Path,
        wav_out: Path,
        strength: Strength,
        on_stage: StageCallback | None = None,
        on_progress: ProgressCallback | None = None,
        cancelled: CancelledCallback | None = None,
    ) -> None:
        # STRONG adds DeepFilterNet's post-filter for extra residual-noise
        # removal; GENTLE/BALANCED keep the default (preserves prior behaviour).
        want_post_filter = strength is Strength.STRONG
        if on_stage is not None:
            on_stage(ProcessingStage.LOADING_MODEL)
        self._ensure_loaded(want_post_filter)
        if on_stage is not None:
            on_stage(ProcessingStage.DENOISING)
        assert self._enhance_fn is not None and self._df_state is not None

        import numpy as np  # type: ignore
        import soundfile as sf  # type: ignore
        import torch  # type: ignore

        atten = strength.attenuation_limit_db
        try:
            with sf.SoundFile(str(wav_in)) as fin:
                sr = int(fin.samplerate)
                channels = int(fin.channels)
                total_frames = len(fin)
                total_sec = max(1, total_frames // sr)
                chunk_frames = _CHUNK_SECONDS * sr
                done_frames = 0
                with sf.SoundFile(
                    str(wav_out), mode="w", samplerate=sr,
                    channels=channels, subtype="PCM_16",
                ) as fout:
                    while True:
                        if cancelled is not None and cancelled():
                            raise ProcessingError(ErrorCode.CANCELLED, "user cancelled")
                        block = fin.read(frames=chunk_frames, dtype="float32",
                                         always_2d=True)  # [frames, channels]
                        if block.shape[0] == 0:
                            break
                        # df.enhance wants [channels, samples]; it batches over
                        # channels. no_grad avoids retaining the autograd graph
                        # (huge for long audio).
                        audio = torch.from_numpy(np.ascontiguousarray(block.T))
                        with torch.no_grad():
                            enhanced = self._enhance_fn(
                                self._model, self._df_state, audio,
                                atten_lim_db=atten,
                            )
                        out = enhanced.detach().cpu().numpy() \
                            if hasattr(enhanced, "detach") else np.asarray(enhanced)
                        fout.write(out.T)  # back to [frames, channels]
                        done_frames += block.shape[0]
                        if on_progress is not None:
                            on_progress(min(done_frames // sr, total_sec), total_sec)
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

"""Observer protocol for rich processing events (pure, no Qt).

Services optionally accept a :class:`ProcessingObserver`. When provided they
report fine-grained stages, real numeric progress (where available), structured
activity events, and probed media info. The Qt worker supplies an observer that
re-emits these as signals; tests supply :class:`RecordingObserver`.

This is additive: the existing ``progress(JobState, fraction)`` callback on the
services is unchanged, so prior behaviour and tests are preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..domain import ActivityCode, MediaInfo, ProcessingStage


@runtime_checkable
class ProcessingObserver(Protocol):
    def on_stage(self, stage: ProcessingStage) -> None: ...

    def on_progress(self, current: int, total: int) -> None:
        """Numeric progress for the *current* stage. ``total <= 0`` means
        indeterminate (the UI shows an indeterminate animation)."""
        ...

    def on_activity(self, code: ActivityCode, **params: object) -> None: ...

    def on_media_info(self, info: MediaInfo) -> None: ...


class NullObserver:
    """No-op observer used when a caller does not care about rich events."""

    def on_stage(self, stage: ProcessingStage) -> None:
        pass

    def on_progress(self, current: int, total: int) -> None:
        pass

    def on_activity(self, code: ActivityCode, **params: object) -> None:
        pass

    def on_media_info(self, info: MediaInfo) -> None:
        pass


@dataclass
class RecordingObserver:
    """Captures every event for assertions in tests."""

    stages: list[ProcessingStage] = field(default_factory=list)
    progress: list[tuple[int, int]] = field(default_factory=list)
    activities: list[tuple[ActivityCode, dict]] = field(default_factory=list)
    media: list[MediaInfo] = field(default_factory=list)

    def on_stage(self, stage: ProcessingStage) -> None:
        self.stages.append(stage)

    def on_progress(self, current: int, total: int) -> None:
        self.progress.append((current, total))

    def on_activity(self, code: ActivityCode, **params: object) -> None:
        self.activities.append((code, dict(params)))

    def on_media_info(self, info: MediaInfo) -> None:
        self.media.append(info)

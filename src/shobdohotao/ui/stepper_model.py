"""Pure state model for the pipeline stepper (no Qt).

The widget renders from this model; keeping the transition logic here means the
stage→status mapping is unit-tested without a display (spec: test state, not
frames).
"""

from __future__ import annotations

from enum import Enum

from ..domain import ProcessingStage


class StepStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepperModel:
    def __init__(self, sequence: tuple[ProcessingStage, ...]) -> None:
        self._sequence = tuple(sequence)
        self._status: dict[ProcessingStage, StepStatus] = {
            s: StepStatus.PENDING for s in self._sequence
        }

    @property
    def sequence(self) -> tuple[ProcessingStage, ...]:
        return self._sequence

    def statuses(self) -> list[tuple[ProcessingStage, StepStatus]]:
        return [(s, self._status[s]) for s in self._sequence]

    def status_of(self, stage: ProcessingStage) -> StepStatus:
        return self._status[stage]

    def active_index(self) -> int | None:
        for i, s in enumerate(self._sequence):
            if self._status[s] is StepStatus.ACTIVE:
                return i
        return None

    def set_active(self, stage: ProcessingStage) -> None:
        """Mark ``stage`` active; everything before it completed, after pending.

        Stages not in this sequence (e.g. LOADING_MODEL on a path that skips it)
        are ignored gracefully.
        """
        if stage not in self._status:
            return
        idx = self._sequence.index(stage)
        for i, s in enumerate(self._sequence):
            if i < idx:
                self._status[s] = StepStatus.COMPLETED
            elif i == idx:
                self._status[s] = StepStatus.ACTIVE
            else:
                self._status[s] = StepStatus.PENDING

    def complete_all(self) -> None:
        for s in self._sequence:
            self._status[s] = StepStatus.COMPLETED

    def set_failed(self) -> None:
        """Mark the active step failed (others keep their state)."""
        idx = self.active_index()
        if idx is None:
            # Nothing active yet — fail the first pending step.
            for i, s in enumerate(self._sequence):
                if self._status[s] is StepStatus.PENDING:
                    idx = i
                    break
        if idx is not None:
            self._status[self._sequence[idx]] = StepStatus.FAILED

    def set_cancelled(self) -> None:
        """Mark the active step cancelled; pending steps stay pending."""
        idx = self.active_index()
        if idx is not None:
            self._status[self._sequence[idx]] = StepStatus.CANCELLED

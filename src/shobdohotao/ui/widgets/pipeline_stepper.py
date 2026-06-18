"""Vertical pipeline stepper widget driven by the pure StepperModel.

Each step shows a status glyph + translated stage name. Visual state is read
from :class:`~shobdohotao.ui.stepper_model.StepperModel`; the transition logic
is unit-tested separately (state, not frames).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ...domain import MediaType, ProcessingStage, stage_sequence_for
from ...i18n import Translator
from ..stepper_model import StepperModel, StepStatus

_GLYPH = {
    StepStatus.PENDING: "○",
    StepStatus.ACTIVE: "◉",
    StepStatus.COMPLETED: "✓",
    StepStatus.FAILED: "✕",
    StepStatus.CANCELLED: "–",
}
_COLOR = {
    StepStatus.PENDING: "#6B7B8A",
    StepStatus.ACTIVE: "#38bdf8",
    StepStatus.COMPLETED: "#4ade80",
    StepStatus.FAILED: "#f87171",
    StepStatus.CANCELLED: "#94a3b8",
}


class PipelineStepper(QWidget):
    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = translator
        self._model = StepperModel(stage_sequence_for(MediaType.AUDIO))
        self._rows: dict[ProcessingStage, QLabel] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(10)
        self._rebuild()

    # --- configuration ----------------------------------------------
    def configure(self, media_type: MediaType) -> None:
        """Set the stage sequence for the media type and reset to pending."""
        self._model = StepperModel(stage_sequence_for(media_type))
        self._rebuild()

    def set_active(self, stage: ProcessingStage) -> None:
        self._model.set_active(stage)
        self._refresh()

    def complete_all(self) -> None:
        self._model.complete_all()
        self._refresh()

    def set_failed(self) -> None:
        self._model.set_failed()
        self._refresh()

    def set_cancelled(self) -> None:
        self._model.set_cancelled()
        self._refresh()

    # --- rendering --------------------------------------------------
    def _rebuild(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._rows = {}
        for stage in self._model.sequence:
            row = QLabel()
            row.setTextFormat(Qt.TextFormat.PlainText)
            self._rows[stage] = row
            self._layout.addWidget(row)
        self._layout.addStretch(1)
        self._refresh()

    def _refresh(self) -> None:
        for stage, label in self._rows.items():
            status = self._model.status_of(stage)
            name = self._t.tr(f"stage.{stage.value}")
            label.setText(f"{_GLYPH[status]}  {name}")
            weight = "600" if status is StepStatus.ACTIVE else "400"
            label.setStyleSheet(f"color: {_COLOR[status]}; font-weight: {weight};")

    def retranslate(self, translator: Translator) -> None:
        self._t = translator
        self._refresh()

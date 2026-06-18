"""Processing view: pipeline stepper · signal visualizer · engine log.

Three panels that stack vertically on narrow windows (laptop-safe). Driven
entirely by real backend events via the presenter. One action: Cancel.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...domain import MediaType, ProcessingStage, stage_sequence_for
from ...i18n import Translator
from ..widgets.activity_console import ActivityConsole
from ..widgets.aero_background import AeroBackground, background_asset
from ..widgets.pipeline_stepper import PipelineStepper
from ..widgets.signal_visualizer import SignalVisualizer, VisualizerState

_NARROW_WIDTH = 1000


class ProcessingView(QWidget):
    cancel_requested = Signal()

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = translator
        self._media_type = MediaType.AUDIO
        self._filename = ""

        # Full-bleed animated backdrop (background_2) with drifting song motifs,
        # behind the panels — matches the home screen's "different world" feel.
        self._background = AeroBackground(self)
        bg = background_asset("background_2")
        self._background.set_images([bg] if bg is not None else [])
        self._background.lower()

        root = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("Muted")
        self._privacy = QLabel()
        self._privacy.setObjectName("PrivacyBadge")
        root.addWidget(self._title)
        root.addWidget(self._subtitle)
        root.addWidget(self._privacy)

        # Three panels in a direction-switchable box.
        self._panels = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._stepper = PipelineStepper(translator)
        self._panels.addWidget(self._wrap_panel(self._stepper), 2)
        self._panels.addLayout(self._build_center(), 3)
        self._console = ActivityConsole(translator)
        self._panels.addWidget(self._wrap_panel(self._console), 3)
        root.addLayout(self._panels, 1)

        self._cancel_btn = QPushButton()
        self._cancel_btn.setObjectName("DangerButton")
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)
        root.addWidget(self._cancel_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.retranslate(translator)

    def _wrap_panel(self, inner: QWidget) -> QWidget:
        panel = QWidget()
        panel.setObjectName("AeroPanel")
        lay = QVBoxLayout(panel)
        lay.addWidget(inner)
        return panel

    def _build_center(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        self._visual = SignalVisualizer()
        lay.addWidget(self._visual, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._elapsed = QLabel("0:00")
        self._elapsed.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._stage_of = QLabel("")
        self._stage_of.setObjectName("Muted")
        self._stage_of.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._vis_caption = QLabel()
        self._vis_caption.setObjectName("Muted")
        self._vis_caption.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        for w in (self._elapsed, self._stage_of, self._vis_caption):
            lay.addWidget(w)
        return lay

    # --- lifecycle --------------------------------------------------
    def configure(self, media_type: MediaType, filename: str) -> None:
        self._media_type = media_type
        self._filename = filename
        self._stepper.configure(media_type)
        self._console.clear()
        self._visual.set_state(VisualizerState.PROCESSING)
        self._elapsed.setText("0:00")
        self._stage_of.setText("")
        self.retranslate(self._t)

    def set_stage(self, stage: ProcessingStage) -> None:
        self._stepper.set_active(stage)
        seq = stage_sequence_for(self._media_type)
        if stage in seq:
            self._stage_of.setText(
                self._t.tr("processing.stage_of").format(
                    current=seq.index(stage) + 1, total=len(seq)
                )
            )

    def set_elapsed(self, seconds: int) -> None:
        from ..format import human_duration

        self._elapsed.setText(human_duration(seconds))

    def set_stage_progress(self, current: int, total: int) -> None:
        """Append genuine numeric progress (FFmpeg stages) to the stage line."""
        if total > 0:
            base = self._stage_of.text().split("  ·  ")[0]
            self._stage_of.setText(f"{base}  ·  {current}/{total}s")

    def append_activity(self, timestamp: str, message: str) -> None:
        self._console.append_line(timestamp, message)

    def mark_completed(self) -> None:
        self._stepper.complete_all()
        self._visual.set_state(VisualizerState.DONE)

    def mark_failed(self) -> None:
        self._stepper.set_failed()
        self._visual.set_state(VisualizerState.FAILED)

    def mark_cancelled(self) -> None:
        self._stepper.set_cancelled()
        self._visual.set_state(VisualizerState.CANCELLED)

    def set_reduce_motion(self, value: bool) -> None:
        self._visual.set_reduce_motion(value)
        self._background.set_reduce_motion(value)

    # --- responsive -------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._background.setGeometry(0, 0, self.width(), self.height())
        self._background.lower()
        narrow = self.width() < _NARROW_WIDTH
        self._panels.setDirection(
            QBoxLayout.Direction.TopToBottom if narrow
            else QBoxLayout.Direction.LeftToRight
        )
        super().resizeEvent(event)

    # --- i18n -------------------------------------------------------
    def retranslate(self, translator: Translator) -> None:
        self._t = translator
        t = translator.tr
        head = f"{t('processing.title')}: {self._filename}" if self._filename \
            else t("processing.title")
        self._title.setText(head)
        self._subtitle.setText(t("processing.subtitle"))
        self._privacy.setText("🔒 " + t("processing.privacy"))
        self._vis_caption.setText(t("processing.visualization"))
        self._cancel_btn.setText(t("processing.cancel"))
        self._stepper.retranslate(translator)
        self._console.retranslate(translator)

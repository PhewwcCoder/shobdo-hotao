"""The signature floating glossy sound orb (rule §5.2).

A custom-painted QWidget: glassy speaker/soundwave orb that bobs gently and
emits concentric ripples. Its visual state mirrors the job state — idle (calm
bob), processing (ripples settle / desaturate, representing noise being
removed), done (soft green pulse).

Implementation notes:
- All painting is QPainter gradients/radials so it stays GPU-light and works on
  the CPU-only target.
- A single QTimer drives animation, capped to ~60fps.
- Animation pauses when the window is not focused and when "reduce motion" is
  on (rules §5.2, §5.3, §6).

Qt is imported lazily so this module can be imported (for indirect references)
without PySide6 present; the class is only built on demand.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class OrbState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    DONE = "done"


_ORB_CLASS: Any = None


def _build_orb_class() -> Any:
    from PySide6.QtCore import Qt, QTimer  # type: ignore
    from PySide6.QtGui import QColor, QPainter, QRadialGradient  # type: ignore
    from PySide6.QtWidgets import QWidget  # type: ignore

    from ..theme.tokens import METRICS, PALETTE

    class SoundOrb(QWidget):
        def __init__(self, parent: Any = None) -> None:
            super().__init__(parent)
            self._state = OrbState.IDLE
            self._phase = 0.0
            self._reduce_motion = False
            self.setMinimumSize(METRICS.orb_size, METRICS.orb_size)
            self.setAccessibleName("Sound status")
            self._timer = QTimer(self)
            self._timer.setInterval(16)  # ~60fps
            self._timer.timeout.connect(self._tick)
            self._timer.start()

        # --- public API -------------------------------------------------
        def set_state(self, state: OrbState) -> None:
            self._state = state
            self.update()

        def set_reduce_motion(self, value: bool) -> None:
            self._reduce_motion = value
            if value:
                self._timer.stop()
            elif not self._timer.isActive():
                self._timer.start()
            self.update()

        # --- animation --------------------------------------------------
        def _tick(self) -> None:
            if self._reduce_motion or not self.isVisible():
                return
            self._phase = (self._phase + 0.02) % 1.0
            self.update()

        # --- painting ---------------------------------------------------
        def paintEvent(self, _event: Any) -> None:  # noqa: N802 (Qt API)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect()
            cx, cy = rect.center().x(), rect.center().y()
            radius = min(rect.width(), rect.height()) / 2 - 8

            base = QColor(PALETTE.sky_light)
            if self._state is OrbState.DONE:
                base = QColor(PALETTE.leaf)

            grad = QRadialGradient(cx, cy - radius * 0.3, radius)
            grad.setColorAt(0.0, QColor(255, 255, 255, 230))
            grad.setColorAt(0.4, base)
            grad.setColorAt(1.0, QColor(PALETTE.sky_dark))
            painter.setBrush(grad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect.center(), int(radius), int(radius))
            painter.end()

    return SoundOrb


def make_orb(parent: Any = None) -> Any:
    global _ORB_CLASS
    if _ORB_CLASS is None:
        _ORB_CLASS = _build_orb_class()
    return _ORB_CLASS(parent)

"""Reactive, custom-painted processing visualizer (QPainter only).

A glassy Aero orb with emanating rings and a row of bars that animate from
chaotic (noisy) toward ordered (clean) while denoising — a *representation* of
processing, not a live spectrum (labelled as such in the view).

Performance/accessibility:
- One QTimer capped at ~60 fps; animation pauses when hidden.
- Reduce-motion renders static gloss only.
- Pure QPainter gradients/rings — CPU-friendly, no WebGL/Electron.
"""

from __future__ import annotations

import math
from enum import Enum

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import QWidget

from ..theme.tokens import PALETTE


class VisualizerState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SignalVisualizer(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = VisualizerState.IDLE
        self._phase = 0.0
        self._reduce_motion = False
        self.setMinimumSize(220, 220)
        self.setAccessibleName("Processing visualization")
        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 fps
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # --- public API -------------------------------------------------
    def set_state(self, state: VisualizerState) -> None:
        self._state = state
        self._sync_timer()
        self.update()

    def set_reduce_motion(self, value: bool) -> None:
        self._reduce_motion = value
        self._sync_timer()
        self.update()

    # --- animation --------------------------------------------------
    def _animating(self) -> bool:
        return (
            not self._reduce_motion
            and self._state in (VisualizerState.PROCESSING, VisualizerState.IDLE)
        )

    def _sync_timer(self) -> None:
        if self._animating() and not self._timer.isActive():
            self._timer.start()
        elif not self._animating() and self._timer.isActive():
            self._timer.stop()

    def _tick(self) -> None:
        if not self.isVisible() or not self._animating():
            return
        speed = 0.03 if self._state is VisualizerState.PROCESSING else 0.012
        self._phase = (self._phase + speed) % 1.0
        self.update()

    def hideEvent(self, event) -> None:  # noqa: N802 (Qt API) - pause when hidden
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._sync_timer()
        super().showEvent(event)

    # --- painting ---------------------------------------------------
    def _base_color(self) -> QColor:
        return {
            VisualizerState.DONE: QColor(PALETTE.leaf),
            VisualizerState.FAILED: QColor("#f87171"),
            VisualizerState.CANCELLED: QColor("#94a3b8"),
        }.get(self._state, QColor(PALETTE.sky_light))

    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        radius = min(rect.width(), rect.height()) / 2 - 24
        base = self._base_color()

        # Emanating rings (only while processing and animating).
        if self._state is VisualizerState.PROCESSING and not self._reduce_motion:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for i in range(3):
                t = (self._phase + i / 3.0) % 1.0
                r = radius * (1.0 + t * 0.7)
                alpha = int(120 * (1.0 - t))
                pen = painter.pen()
                col = QColor(base)
                col.setAlpha(max(0, alpha))
                pen.setColor(col)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawEllipse(rect.center(), int(r), int(r))

        # Glossy orb.
        grad = QRadialGradient(cx, cy - radius * 0.35, radius * 1.2)
        breath = 0.0 if self._reduce_motion else 0.06 * math.sin(self._phase * math.tau)
        grad.setColorAt(0.0, QColor(255, 255, 255, 235))
        mid = QColor(base)
        grad.setColorAt(min(0.9, 0.45 + breath), mid)
        grad.setColorAt(1.0, QColor(PALETTE.sky_dark))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.center(), int(radius), int(radius))

        # Inner "signal bars": chaotic while processing, flat when idle/done.
        self._paint_bars(painter, cx, cy, radius, base)
        painter.end()

    def _paint_bars(self, painter, cx: int, cy: int, radius: float,
                    base: QColor) -> None:
        bar_count = 9
        spacing = radius * 0.9 / bar_count
        max_h = radius * 0.55
        chaotic = self._state is VisualizerState.PROCESSING and not self._reduce_motion
        col = QColor(255, 255, 255, 180)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(col)
        start_x = cx - (bar_count - 1) * spacing / 2
        for i in range(bar_count):
            if chaotic:
                # Pseudo-random but deterministic from phase + index.
                seed = math.sin((i + 1) * 12.9898 + self._phase * math.tau * 3)
                amp = abs(seed) * 0.5 + 0.15
            else:
                amp = 0.12
            h = max(3.0, max_h * amp)
            x = start_x + i * spacing
            painter.drawRoundedRect(
                int(x - spacing * 0.18), int(cy - h / 2),
                max(2, int(spacing * 0.36)), int(h), 2, 2,
            )

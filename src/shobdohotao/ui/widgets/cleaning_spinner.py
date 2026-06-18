"""Full-view "busy" overlay shown while a file is being read/probed.

A ring of little music notes orbits a centre; their colour flows from red
(noisy) round to green (clean), so the wait reads as "cleaning in progress"
rather than a frozen window. Pure QPainter + one timer. It dims the view and
swallows clicks while visible. Reduce-motion holds a static frame.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

_NOTES = 9          # notes around the ring
_SPIN_SECONDS = 2.4  # one full revolution


def _lerp_red_to_green(t: float) -> QColor:
    """t in 0..1: red -> amber -> green via HSV hue 0°..120°."""
    t = max(0.0, min(1.0, t))
    c = QColor()
    c.setHsvF(t / 3.0, 0.82, 1.0)  # hue 0 (red) .. 0.333 (green)
    return c


class CleaningSpinner(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._phase = 0.0
        self._reduce_motion = False
        self._caption = "Reading file…"
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 fps
        self._timer.timeout.connect(self._tick)
        self.hide()  # after _timer exists: hide() can fire hideEvent

    # --- public API -------------------------------------------------
    def set_caption(self, text: str) -> None:
        self._caption = text
        self.update()

    def set_reduce_motion(self, value: bool) -> None:
        self._reduce_motion = value
        if value:
            self._timer.stop()
        elif self.isVisible():
            self._timer.start()
        self.update()

    def start(self) -> None:
        self.show()
        self.raise_()
        if not self._reduce_motion:
            self._timer.start()
        self.update()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    # --- animation --------------------------------------------------
    def _tick(self) -> None:
        if not self.isVisible():
            return
        self._phase = (self._phase + self._timer.interval() / 1000.0
                       / _SPIN_SECONDS) % 1.0
        self.update()

    def hideEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._timer.stop()
        super().hideEvent(event)

    # --- painting ---------------------------------------------------
    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt API)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Dim veil over the whole view.
        p.fillRect(self.rect(), QColor(8, 14, 24, 165))

        cx, cy = self.width() / 2, self.height() / 2
        ring_r = min(self.width(), self.height()) * 0.10
        note_sz = ring_r * 0.5
        for i in range(_NOTES):
            frac = i / _NOTES
            ang = math.tau * (frac + self._phase)
            x = cx + ring_r * math.cos(ang)
            y = cy + ring_r * math.sin(ang)
            # Colour flows red -> green around the ring as it spins.
            colour = _lerp_red_to_green((frac + self._phase) % 1.0)
            # Leading notes brighter (a comet-like emphasis).
            colour.setAlpha(120 + int(135 * ((frac + self._phase) % 1.0)))
            self._draw_note(p, x, y, note_sz, colour)

        # Caption under the ring.
        p.setPen(QColor(234, 242, 248, 220))
        f = p.font()
        f.setPointSizeF(max(10.0, ring_r * 0.18))
        p.setFont(f)
        rect = self.rect().adjusted(0, int(cy + ring_r * 1.8), 0, 0)
        p.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                   self._caption)
        p.end()

    def _draw_note(self, p: QPainter, cx: float, cy: float,
                   size: float, colour: QColor) -> None:
        p.setPen(QPen(colour, max(1.5, size * 0.16)))
        p.setBrush(colour)
        head_w, head_h = size * 0.62, size * 0.48
        p.save()
        p.translate(cx, cy)
        p.rotate(-18)
        p.drawEllipse(QPointF(0.0, 0.0), head_w / 2, head_h / 2)
        # Stem up from the right of the head.
        sx = head_w * 0.42
        p.drawLine(QPointF(sx, 0.0), QPointF(sx, -size * 1.1))
        p.restore()

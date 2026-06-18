"""Transparent, glossy Aqua-glass button that gently lifts on hover.

The frosted-glass look comes from QSS (``#GlassButton`` / ``#GlassPrimary`` in
the theme). This widget adds the *dynamic* feel: on hover the button floats up a
few pixels and its soft drop-shadow grows, so it "pops" under the cursor. Honors
reduce-motion (no movement, just the static gloss).
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QPushButton, QWidget

_LIFT_PX = 4
_REST_BLUR = 16
_HOVER_BLUR = 28


class GlassButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._motion = True
        self._home_pos: QPoint | None = None

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(_REST_BLUR)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(self._shadow)

        self._lift = QPropertyAnimation(self, b"pos", self)
        self._lift.setDuration(120)
        self._blur = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._blur.setDuration(120)

    def set_motion_enabled(self, enabled: bool) -> None:
        self._motion = enabled

    # --- hover ------------------------------------------------------
    def enterEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if self._motion:
            self._home_pos = self.pos()
            self._animate_pos(self._home_pos - QPoint(0, _LIFT_PX))
            self._shadow.setOffset(0, 10)
            self._animate_blur(_HOVER_BLUR)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if self._motion and self._home_pos is not None:
            self._animate_pos(self._home_pos)
            self._shadow.setOffset(0, 4)
            self._animate_blur(_REST_BLUR)
        super().leaveEvent(event)

    def _animate_pos(self, end: QPoint) -> None:
        self._lift.stop()
        self._lift.setStartValue(self.pos())
        self._lift.setEndValue(end)
        self._lift.start()

    def _animate_blur(self, end: int) -> None:
        self._blur.stop()
        self._blur.setStartValue(self._shadow.blurRadius())
        self._blur.setEndValue(end)
        self._blur.start()

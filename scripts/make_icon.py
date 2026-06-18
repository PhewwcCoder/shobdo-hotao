"""Generate the ShobdoHotao app icon (Frutiger-Aero glass tile + sound bars).

Renders a crisp 256px master with QPainter, then packs a multi-size Windows
``assets/app.ico`` (plus a PNG preview). Re-run after tweaking to refresh both.

    .venv\\Scripts\\python.exe scripts\\make_icon.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication

S = 256  # master size (max standard .ico size)
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _star(cx: float, cy: float, outer: float, inner: float) -> QPainterPath:
    """A 4-point sparkle (clean/fresh accent)."""
    path = QPainterPath()
    for i in range(8):
        ang = math.pi / 2 + i * math.pi / 4
        r = outer if i % 2 == 0 else inner
        x, y = cx + r * math.cos(ang), cy - r * math.sin(ang)
        path.lineTo(x, y) if i else path.moveTo(x, y)
    path.closeSubpath()
    return path


def render() -> QPixmap:
    pm = QPixmap(S, S)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # --- glossy glass tile -----------------------------------------
    margin, radius = 14, 56
    tile = QRectF(margin, margin, S - 2 * margin, S - 2 * margin)
    grad = QLinearGradient(0, margin, 0, S - margin)
    grad.setColorAt(0.0, QColor("#8FDCFF"))
    grad.setColorAt(0.45, QColor("#3AA0E6"))
    grad.setColorAt(1.0, QColor("#15568F"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(grad)
    p.drawRoundedRect(tile, radius, radius)

    # Top sheen (the Aqua glass highlight across the upper half).
    sheen = QLinearGradient(0, margin, 0, S * 0.52)
    sheen.setColorAt(0.0, QColor(255, 255, 255, 150))
    sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
    top = QRectF(margin + 6, margin + 6, S - 2 * margin - 12, S * 0.42)
    clip = QPainterPath()
    clip.addRoundedRect(tile, radius, radius)
    p.setClipPath(clip)
    p.setBrush(sheen)
    p.drawRoundedRect(top, radius * 0.7, radius * 0.7)

    # Soft corner glow (sunlit-water optimism).
    glow = QRadialGradient(S * 0.30, S * 0.26, S * 0.5)
    glow.setColorAt(0.0, QColor(255, 255, 255, 90))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(glow)
    p.drawRect(tile)
    p.setClipping(False)

    # --- white sound / equalizer bars ------------------------------
    heights = [0.34, 0.58, 0.80, 0.50, 0.30]  # "spectrum" silhouette
    n = len(heights)
    bw = (S - 2 * margin) * 0.085
    gap = bw * 0.75
    total = n * bw + (n - 1) * gap
    x0 = S / 2 - total / 2
    base_y = S * 0.66
    p.setBrush(QColor(255, 255, 255, 235))
    p.setPen(Qt.PenStyle.NoPen)
    for i, h in enumerate(heights):
        bh = h * S * 0.34
        x = x0 + i * (bw + gap)
        p.drawRoundedRect(QRectF(x, base_y - bh, bw, bh), bw / 2, bw / 2)

    # --- sparkle (clean/fresh) -------------------------------------
    p.setBrush(QColor(255, 255, 255, 240))
    p.drawPath(_star(S * 0.74, S * 0.30, S * 0.085, S * 0.03))
    p.setBrush(QColor(255, 255, 255, 170))
    p.drawPath(_star(S * 0.84, S * 0.42, S * 0.04, S * 0.014))

    # Subtle bubble highlight, bottom-left.
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(255, 255, 255, 120), 3))
    p.drawEllipse(QPointF(S * 0.30, S * 0.74), S * 0.045, S * 0.045)

    p.end()
    return pm


def main() -> None:
    QApplication([])
    ASSETS.mkdir(parents=True, exist_ok=True)
    pm = render()
    png = ASSETS / "app_icon.png"
    pm.save(str(png), "PNG")

    from PIL import Image  # packed into a multi-size .ico

    Image.open(png).save(
        ASSETS / "app.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)],
    )
    print("wrote", png, "and", ASSETS / "app.ico")


if __name__ == "__main__":
    main()

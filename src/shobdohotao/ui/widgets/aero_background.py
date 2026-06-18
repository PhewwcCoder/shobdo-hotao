"""Full-bleed home background that shows the user's design image CRISP, with
song-related motifs (music notes + bubbles) that lift off the artwork and drift
gently up into the app — a calm, "different world" Frutiger-Aero feel.

The image (your exported Frutiger-Aero artwork) is scaled to cover and drawn
sharp — no blur. A light veil keeps the white title/text readable. Any number of
images crossfade slowly in sequence; a single image is static; with no image the
background is a plain deep-blue fill. On top of the image, faint white music
glyphs rise and sway like the equalizer/headphone/note motifs in the artwork.

Performance/accessibility:
- Scaled-to-cover pixmaps are cached per resize; paint just blends them.
- One QTimer (~30 fps) runs only while there is at least one image to animate;
  it pauses when hidden and under reduce-motion.
- Reduce-motion holds a single static frame with no drifting objects.
- ``WA_TransparentForMouseEvents`` so it never blocks the controls above it, and
  the glyphs stay low-opacity so the white title/text remain legible.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QWidget

# Seconds for one crossfade step from one image to the next (only with >1 image).
_CYCLE_SECONDS = 9.0
# Seconds for a music glyph to drift from below the frame up past the top.
_DRIFT_SECONDS = 14.0

# Where exported background artwork lives (ui/theme/assets/backgrounds/).
_BACKGROUNDS_DIR = (
    Path(__file__).resolve().parent.parent / "theme" / "assets" / "backgrounds"
)
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def background_asset(stem: str) -> Path | None:
    """Resolve a background image by stem (e.g. ``"background_2"``), trying each
    accepted extension. Returns ``None`` when no matching file is present."""
    for ext in _IMAGE_EXTS:
        candidate = _BACKGROUNDS_DIR / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


@dataclass(frozen=True)
class _FloatingObject:
    """A single song-motif that rises and sways. Coords are normalised 0..1."""

    kind: str          # "note" | "beamed" | "bubble"
    x: float           # base horizontal position (0..1)
    size: float        # glyph size as a fraction of the widget height
    speed: float       # vertical rise, fraction of one _DRIFT_SECONDS cycle/sec
    phase: float       # 0..1 offset so they don't all start together
    sway_amp: float    # horizontal sway amplitude (fraction of width)
    sway_freq: float   # sway cycles per second
    alpha: float       # peak opacity (0..1)


def _build_objects() -> list[_FloatingObject]:
    """Deterministic, pleasingly-scattered set of drifting song motifs."""
    rng = random.Random(0xA3D0)  # fixed seed -> stable, no per-frame randomness
    kinds = ["note", "beamed", "bubble", "note", "bubble", "beamed",
             "note", "bubble", "note"]
    objects: list[_FloatingObject] = []
    for i, kind in enumerate(kinds):
        is_bubble = kind == "bubble"
        objects.append(
            _FloatingObject(
                kind=kind,
                x=rng.uniform(0.06, 0.94),
                size=rng.uniform(0.05, 0.085) if not is_bubble
                else rng.uniform(0.02, 0.045),
                speed=rng.uniform(0.7, 1.25) / _DRIFT_SECONDS,
                phase=i / len(kinds) + rng.uniform(0.0, 0.05),
                sway_amp=rng.uniform(0.015, 0.05),
                sway_freq=rng.uniform(0.05, 0.13),
                alpha=rng.uniform(0.22, 0.42) if not is_bubble
                else rng.uniform(0.14, 0.28),
            )
        )
    return objects


def _veil(height: int) -> QLinearGradient:
    """Light readability veil — keeps the design visible while the white title
    and small text stay legible. Tune the alphas (0-255) to taste."""
    g = QLinearGradient(0, 0, 0, max(1, height))
    g.setColorAt(0.0, QColor(9, 16, 30, 60))    # ~0.24 near the top
    g.setColorAt(0.40, QColor(9, 16, 30, 90))   # ~0.35 content band
    g.setColorAt(0.75, QColor(9, 16, 30, 70))
    g.setColorAt(1.0, QColor(9, 16, 30, 110))   # a touch darker at the base
    return g


class AeroBackground(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.lower()
        self._sources: list[QPixmap] = []
        self._scaled: list[QPixmap] = []
        self._phase = 0.0          # crossfade progress within the current step
        self._index = 0            # which image we are fading FROM
        self._elapsed = 0.0        # seconds, drives the drifting objects
        self._objects = _build_objects()
        self._reduce_motion = False
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 fps
        self._timer.timeout.connect(self._tick)

    # --- configuration ----------------------------------------------
    def set_images(self, paths: list[Path]) -> None:
        self._sources = []
        for p in paths:
            if p and Path(p).exists():
                pix = QPixmap(str(p))
                if not pix.isNull():
                    self._sources.append(pix)
        self._index = 0
        self._phase = 0.0
        self._rescale()
        self._sync_timer()
        self.update()

    def set_reduce_motion(self, value: bool) -> None:
        self._reduce_motion = value
        self._sync_timer()
        self.update()

    # --- animation --------------------------------------------------
    def _animating(self) -> bool:
        # Animate whenever there's at least one image (drifting motifs) and the
        # user hasn't asked for reduced motion. Crossfade needs >1 image; the
        # rising song-objects play even over a single static photo.
        return not self._reduce_motion and len(self._sources) >= 1

    def _sync_timer(self) -> None:
        if self._animating() and self.isVisible() and not self._timer.isActive():
            self._timer.start()
        elif not self._animating() and self._timer.isActive():
            self._timer.stop()

    def _tick(self) -> None:
        if not self.isVisible() or not self._animating():
            return
        dt = self._timer.interval() / 1000.0
        self._elapsed += dt
        if len(self._sources) > 1:
            self._phase += dt / _CYCLE_SECONDS
            while self._phase >= 1.0:
                self._phase -= 1.0
                self._index = (self._index + 1) % len(self._sources)
        self.update()

    def hideEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._sync_timer()
        super().showEvent(event)

    # --- scaling ----------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._rescale()
        super().resizeEvent(event)

    def _rescale(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return
        size = self.size()
        self._scaled = [
            pix.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            for pix in self._sources
        ]

    # --- painting ---------------------------------------------------
    def _draw_cover(self, painter: QPainter, pix: QPixmap) -> None:
        x = (self.width() - pix.width()) // 2
        y = (self.height() - pix.height()) // 2
        painter.drawPixmap(x, y, pix)

    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._scaled:
            painter.fillRect(self.rect(), QColor(11, 22, 43))  # deep-blue fallback
            painter.end()
            return

        if len(self._scaled) == 1 or self._reduce_motion:
            self._draw_cover(painter, self._scaled[0])
        else:
            # Smooth crossfade from the current image to the next, no hard cut.
            t = (1 - math.cos(self._phase * math.pi)) / 2  # ease in/out 0..1
            nxt = (self._index + 1) % len(self._scaled)
            painter.setOpacity(1.0)
            self._draw_cover(painter, self._scaled[self._index])
            painter.setOpacity(t)
            self._draw_cover(painter, self._scaled[nxt])
            painter.setOpacity(1.0)

        painter.fillRect(self.rect(), _veil(self.height()))
        if not self._reduce_motion:
            self._draw_objects(painter)
        painter.end()

    # --- drifting song motifs ---------------------------------------
    def _draw_objects(self, painter: QPainter) -> None:
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        painter.save()
        for obj in self._objects:
            cycle = (obj.phase + self._elapsed * obj.speed) % 1.0
            # Rise from just below the frame (1.12) to just above it (-0.12).
            y = (1.12 - cycle * 1.24) * h
            x = (obj.x + obj.sway_amp
                 * math.sin(self._elapsed * obj.sway_freq * math.tau
                            + obj.phase * math.tau)) * w
            # Fade in at the bottom, fade out near the top.
            fade = min(1.0, cycle / 0.12, (1.0 - cycle) / 0.12)
            painter.setOpacity(max(0.0, obj.alpha * fade))
            self._draw_glyph(painter, obj.kind, x, y, obj.size * h)
        painter.restore()

    def _draw_glyph(self, painter: QPainter, kind: str,
                    cx: float, cy: float, size: float) -> None:
        white = QColor(255, 255, 255)
        if kind == "bubble":
            pen = QPen(white)
            pen.setWidthF(max(1.0, size * 0.06))
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = size / 2
            painter.drawEllipse(QPointF(cx, cy), r, r)
            # Top-left glass highlight.
            hl = QColor(255, 255, 255, 200)
            painter.setPen(QPen(hl, max(1.0, size * 0.05)))
            painter.drawArc(int(cx - r * 0.55), int(cy - r * 0.6),
                            int(r * 0.7), int(r * 0.7), 40 * 16, 90 * 16)
            return

        # Music note(s): filled head(s), a stem, and a flag/beam — same thin
        # white styling as the headphone/equalizer motifs in the artwork.
        pen = QPen(white)
        pen.setWidthF(max(1.2, size * 0.08))
        painter.setPen(pen)
        painter.setBrush(white)
        head_w = size * 0.42
        head_h = size * 0.32
        stem_h = size * 1.05

        def _note(hx: float, hy: float) -> None:
            painter.save()
            painter.translate(hx, hy)
            painter.rotate(-18)
            painter.drawEllipse(QPointF(0.0, 0.0), head_w / 2, head_h / 2)
            painter.restore()

        if kind == "beamed":
            x1 = cx - size * 0.28
            x2 = cx + size * 0.28
            _note(x1, cy + stem_h * 0.0)
            _note(x2, cy + stem_h * 0.12)
            top1 = QPointF(x1 + head_w * 0.42, cy - stem_h)
            top2 = QPointF(x2 + head_w * 0.42, cy + stem_h * 0.12 - stem_h)
            painter.drawLine(QPointF(x1 + head_w * 0.42, cy), top1)
            painter.drawLine(QPointF(x2 + head_w * 0.42, cy + stem_h * 0.12), top2)
            beam = QPen(white, max(1.6, size * 0.12))
            painter.setPen(beam)
            painter.drawLine(top1, top2)
        else:
            _note(cx, cy)
            top = QPointF(cx + head_w * 0.42, cy - stem_h)
            painter.drawLine(QPointF(cx + head_w * 0.42, cy), top)
            # A small flag off the top of the stem.
            flag = QPainterPath(top)
            flag.cubicTo(top.x() + size * 0.28, top.y() + size * 0.18,
                         top.x() + size * 0.30, top.y() + size * 0.40,
                         top.x() + size * 0.04, top.y() + size * 0.52)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(flag)

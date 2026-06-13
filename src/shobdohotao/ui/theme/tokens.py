"""Centralised Frutiger Aero design tokens (rule §5.3: one theme module).

Every gradient, radius, blur, and colour lives here so the whole look can be
tuned in one place and a future high-contrast theme can swap the palette. We
keep hex fallbacks because Qt Style Sheets do not parse OKLCH; the OKLCH source
values are kept in comments for designer reference.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AeroPalette:
    # Sky / primary  oklch(75% 0.13 230) -> oklch(55% 0.15 250)
    sky_light: str = "#5BC8F5"
    sky_dark: str = "#2E7DD1"
    # Nature / accent  oklch(78% 0.16 145)
    leaf: str = "#5FD06A"
    # Glass
    glass_fill: str = "rgba(255, 255, 255, 0.70)"
    glass_border: str = "rgba(255, 255, 255, 0.85)"
    glass_highlight: str = "rgba(255, 255, 255, 0.55)"
    # Text  oklch(20% 0.02 250)
    text: str = "#1A2530"
    text_muted: str = "#48586A"
    # Status (always paired with icon + text, never colour-only)
    success: str = "#3FB24A"
    warning: str = "#E6A12B"
    danger: str = "#D6453B"


@dataclass(frozen=True)
class AeroMetrics:
    radius_panel: int = 18
    radius_button: int = 14
    radius_pill: int = 22
    orb_size: int = 168
    spacing: int = 12
    focus_ring_width: int = 2


PALETTE = AeroPalette()
METRICS = AeroMetrics()


def build_stylesheet(*, reduce_transparency: bool = False) -> str:
    """Generate the global QSS from tokens.

    ``reduce_transparency`` swaps glass for near-solid surfaces for users who
    find translucency hard to read (rule §6).
    """
    p = PALETTE
    m = METRICS
    glass = "#F2F8FC" if reduce_transparency else p.glass_fill
    return f"""
    QWidget {{
        color: {p.text};
        font-size: 14px;
    }}
    #AeroPanel {{
        background: {glass};
        border: 1px solid {p.glass_border};
        border-radius: {m.radius_panel}px;
    }}
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {p.sky_light}, stop:1 {p.sky_dark});
        border: 1px solid {p.glass_border};
        border-radius: {m.radius_button}px;
        color: white;
        padding: 8px 16px;
    }}
    QPushButton:focus {{
        border: {m.focus_ring_width}px solid {p.leaf};
    }}
    QPushButton:disabled {{
        background: #B9C6D2;
        color: #EEF3F7;
    }}
    QLabel#Muted {{ color: {p.text_muted}; }}
    """

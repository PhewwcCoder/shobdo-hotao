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
    # Dark Aero theme: deep blue-black surfaces with light text and glossy
    # cyan buttons. Light text on dark surfaces keeps the Bengali title legible
    # (the previous theme used dark text on a dark window — §13 contrast fix).
    bg = "#0E1621"
    surface = "#16212E" if not reduce_transparency else "#1B2735"
    text = "#EAF2F8"
    muted = "#9FB0BE"
    field = "#1B2735"
    border = "#33465A"
    return f"""
    QMainWindow, QDialog {{ background-color: {bg}; }}
    QWidget {{
        color: {text};
        font-size: 14px;
    }}
    QLabel {{ background: transparent; }}
    #AeroPanel {{
        background: {surface};
        border: 1px solid {border};
        border-radius: {m.radius_panel}px;
    }}
    QLabel#Title {{
        color: #F4FAFF;
        font-size: 26px;
        font-weight: 600;
        padding: 6px 2px;
    }}
    /* Centered hero title + statement on the home landing. */
    QLabel#HeroTitle {{
        color: #F4FAFF;
        font-size: 44px;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 4px 2px;
    }}
    QLabel#HeroStatement {{
        color: #BFE6FF;
        font-size: 15px;
    }}
    QLabel#DropPrompt {{
        color: #EAF2F8;
        font-size: 20px;
        font-weight: 600;
    }}
    QLabel#Headline {{
        color: {p.leaf};
        font-size: 18px;
        font-weight: 600;
    }}
    QLabel#Muted {{ color: {muted}; }}
    QLabel#ValidationHint {{ color: #FF8A80; }}
    QLineEdit {{
        background: {field};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 6px 8px;
        selection-background-color: {p.sky_dark};
    }}
    QLineEdit:focus {{ border: {m.focus_ring_width}px solid {p.sky_light}; }}
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {p.sky_light}, stop:1 {p.sky_dark});
        border: 1px solid {border};
        border-radius: {m.radius_button}px;
        color: white;
        font-weight: 600;
        padding: 9px 16px;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #7AD4F8, stop:1 #3A8FE0);
    }}
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {p.sky_dark}, stop:1 #245FA3);
    }}
    QPushButton:focus {{ border: {m.focus_ring_width}px solid {p.leaf}; }}
    QPushButton:disabled {{
        background: #2A3744;
        color: #6B7B8A;
        border: 1px solid #2A3744;
    }}
    /* Glossy Aqua-glass buttons (old-Windows sheen: light top half, saturated
       bottom half). Dark navy text for contrast on the bright top sheen. */
    QPushButton#AquaButton, QPushButton#AquaPrimary {{
        color: #08304f;
        border: 1px solid rgba(255,255,255,0.55);
        border-radius: 16px;
        font-weight: 700;
        padding: 11px 26px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0    rgba(255,255,255,0.97),
            stop:0.49 rgba(196,233,252,0.97),
            stop:0.50 rgba(108,196,245,0.97),
            stop:1    rgba(46,155,224,0.99));
    }}
    QPushButton#AquaButton:hover, QPushButton#AquaPrimary:hover {{
        border: 1px solid rgba(255,255,255,0.85);
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0    rgba(255,255,255,1.0),
            stop:0.49 rgba(214,242,255,1.0),
            stop:0.50 rgba(130,210,250,1.0),
            stop:1    rgba(58,170,232,1.0));
    }}
    QPushButton#AquaButton:pressed, QPushButton#AquaPrimary:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0    rgba(170,210,235,0.97),
            stop:0.5  rgba(70,150,210,0.97),
            stop:1    rgba(36,95,163,0.99));
    }}
    QPushButton#AquaButton:focus, QPushButton#AquaPrimary:focus {{
        border: {m.focus_ring_width}px solid {p.leaf};
    }}
    QPushButton#AquaPrimary {{
        font-size: 17px;
        padding: 16px 40px;
        border-radius: {m.radius_pill}px;
    }}
    /* Transparent glossy glass buttons (see-through; the background shows
       through). White text + a top sheen; the GlassButton widget adds the
       hover lift. */
    QPushButton#GlassButton, QPushButton#GlassPrimary {{
        color: #ffffff;
        border: 1px solid rgba(255,255,255,0.55);
        border-radius: 16px;
        font-weight: 700;
        padding: 11px 26px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0    rgba(255,255,255,0.42),
            stop:0.49 rgba(255,255,255,0.16),
            stop:0.50 rgba(120,200,245,0.18),
            stop:1    rgba(46,155,224,0.34));
    }}
    QPushButton#GlassButton:hover, QPushButton#GlassPrimary:hover {{
        border: 1px solid rgba(255,255,255,0.95);
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0    rgba(255,255,255,0.60),
            stop:0.49 rgba(210,240,255,0.30),
            stop:0.50 rgba(140,212,250,0.32),
            stop:1    rgba(58,170,232,0.48));
    }}
    QPushButton#GlassButton:pressed, QPushButton#GlassPrimary:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0    rgba(150,200,235,0.40),
            stop:1    rgba(36,95,163,0.55));
    }}
    QPushButton#GlassButton:focus, QPushButton#GlassPrimary:focus {{
        border: {m.focus_ring_width}px solid {p.leaf};
    }}
    /* Selected segment in a segmented control (e.g. the strength picker):
       a bright leaf-accent border + lifted sheen marks the active choice. */
    QPushButton#GlassButton:checked {{
        border: 2px solid {p.leaf};
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0    rgba(255,255,255,0.66),
            stop:0.49 rgba(214,242,255,0.38),
            stop:0.50 rgba(140,212,250,0.40),
            stop:1    rgba(58,170,232,0.56));
    }}
    QPushButton#GlassPrimary {{
        font-size: 17px;
        padding: 16px 40px;
        border-radius: {m.radius_pill}px;
    }}
    /* Large glossy primary action (legacy id, kept for compatibility). */
    QPushButton#PrimaryOrb {{
        font-size: 16px;
        padding: 16px 28px;
        border-radius: {m.radius_pill}px;
    }}
    /* Cancel / destructive. */
    QPushButton#DangerButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #f87171, stop:1 #c0392b);
        padding: 12px 28px;
    }}
    QPushButton#DangerButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #ff9b94, stop:1 #d6453b);
    }}
    /* Flat header nav + language pill. */
    QPushButton#NavButton {{
        background: transparent;
        border: 1px solid transparent;
        color: {muted};
        font-weight: 500;
        padding: 6px 12px;
    }}
    QPushButton#NavButton:hover {{ color: {text}; border: 1px solid {border}; }}
    QPushButton#LangPill {{
        background: rgba(255,255,255,0.06);
        border: 1px solid {border};
        border-radius: {m.radius_pill}px;
        color: {text};
        padding: 6px 14px;
    }}
    /* Privacy badge + monospace engine log. */
    QLabel#PrivacyBadge {{ color: {p.leaf}; font-weight: 500; }}
    QLabel#MediaName {{ font-size: 16px; font-weight: 600; }}
    QPlainTextEdit#ActivityConsole {{
        background: #0a0f17;
        color: #cfe8f5;
        border: 1px solid {border};
        border-radius: 8px;
        font-family: Consolas, "Courier New", monospace;
        font-size: 12px;
    }}
    #AppHeader {{ border-bottom: 1px solid {border}; }}
    """

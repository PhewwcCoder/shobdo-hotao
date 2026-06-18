"""Headless Qt tests for the polish-stage widgets (offscreen, state-based)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from shobdohotao.domain import MediaInfo, MediaType, ProcessingStage  # noqa: E402
from shobdohotao.i18n import Language, Translator  # noqa: E402
from shobdohotao.ui.widgets.activity_console import ActivityConsole  # noqa: E402
from shobdohotao.ui.widgets.app_header import AppHeader  # noqa: E402
from shobdohotao.ui.widgets.media_card import MediaCard  # noqa: E402
from shobdohotao.ui.widgets.pipeline_stepper import PipelineStepper  # noqa: E402
from shobdohotao.ui.widgets.signal_visualizer import (  # noqa: E402
    SignalVisualizer,
    VisualizerState,
)


def _t() -> Translator:
    return Translator(Language.EN)


def _all_text(widget) -> str:
    from PySide6.QtWidgets import QLabel

    return " ".join(lbl.text() for lbl in widget.findChildren(QLabel))


def test_stepper_reflects_active_stage(qapp) -> None:
    s = PipelineStepper(_t())
    s.configure(MediaType.AUDIO)
    s.set_active(ProcessingStage.DENOISING)
    text = _all_text(s)
    assert "◉" in text and "Removing noise" in text
    assert "✓" in text  # earlier steps completed


def test_stepper_failed_and_cancelled_render(qapp) -> None:
    s = PipelineStepper(_t())
    s.configure(MediaType.VIDEO)
    s.set_active(ProcessingStage.DENOISING)
    s.set_failed()
    assert "✕" in _all_text(s)
    s2 = PipelineStepper(_t())
    s2.configure(MediaType.VIDEO)
    s2.set_active(ProcessingStage.EXTRACTING_AUDIO)
    s2.set_cancelled()
    assert "–" in _all_text(s2)


def test_stepper_retranslate_to_bangla(qapp) -> None:
    s = PipelineStepper(_t())
    s.configure(MediaType.AUDIO)
    s.retranslate(Translator(Language.BN))
    assert "আওয়াজ দূর করা হচ্ছে" in _all_text(s)


def test_activity_console_caps_lines_and_no_path_leak(qapp) -> None:
    c = ActivityConsole(_t())
    for i in range(250):
        c.append_line("10:00:00", f"event {i}")
    assert c.line_count() <= 200
    assert "/Temp/" not in c.text() and "\\Temp\\" not in c.text()


def test_activity_console_pause_toggle(qapp) -> None:
    c = ActivityConsole(_t())
    assert c._auto_scroll is True
    c._pause_btn.setChecked(True)
    assert c._auto_scroll is False


def test_signal_visualizer_reduce_motion_stops_timer(qapp) -> None:
    v = SignalVisualizer()
    v.set_state(VisualizerState.PROCESSING)
    v.set_reduce_motion(True)
    assert v._timer.isActive() is False  # no animation in reduce-motion
    # Terminal states are also static.
    v.set_reduce_motion(False)
    v.set_state(VisualizerState.FAILED)
    assert v._timer.isActive() is False


def test_media_card_audio_and_video(qapp) -> None:
    card = MediaCard(_t())
    card.set_media(MediaInfo(Path("lecture.mp3"), MediaType.AUDIO, "mp3",
                             2048, 12.0, 44100, 2))
    assert "lecture.mp3" in _all_text(card)
    card.set_media(MediaInfo(Path("clip.mp4"), MediaType.VIDEO, "mp4",
                             4096, 30.0, 48000, 2, 1920, 1080))
    assert "1920×1080" in _all_text(card)


def test_aero_background_is_decorative_and_missing_safe(qapp) -> None:
    from PySide6.QtCore import Qt

    from shobdohotao.ui.widgets.aero_background import AeroBackground

    bg = AeroBackground()
    assert bg.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    bg.set_images([Path("nope1.png"), Path("nope2.png")])  # safe no-op
    assert bg._timer.isActive() is False  # nothing to animate


def test_aero_background_reduce_motion_stops_timer(qapp, tmp_path) -> None:
    from PySide6.QtGui import QColor, QPixmap

    from shobdohotao.ui.widgets.aero_background import AeroBackground

    # Two real (solid-colour) images so the crossfade timer would run.
    paths = []
    for i, col in enumerate(("#123456", "#654321")):
        p = tmp_path / f"bg{i}.png"
        pm = QPixmap(64, 64)
        pm.fill(QColor(col))
        pm.save(str(p))
        paths.append(p)
    bg = AeroBackground()
    bg.resize(200, 120)
    bg.show()
    bg.set_images(paths)
    assert bg._timer.isActive() is True
    bg.set_reduce_motion(True)
    assert bg._timer.isActive() is False
    bg.hide()


def test_aero_background_cycles_three_images_and_drifts(qapp, tmp_path) -> None:
    from PySide6.QtGui import QColor, QPixmap

    from shobdohotao.ui.widgets.aero_background import AeroBackground

    paths = []
    for i, col in enumerate(("#112233", "#445566", "#778899")):
        p = tmp_path / f"bg{i}.png"
        pm = QPixmap(64, 64)
        pm.fill(QColor(col))
        pm.save(str(p))
        paths.append(p)
    bg = AeroBackground()
    bg.resize(200, 120)
    bg.show()
    bg.set_images(paths)
    assert len(bg._objects) > 0  # song motifs ready to drift
    assert bg._timer.isActive() is True
    # Drive enough frames to roll past at least one crossfade boundary.
    for _ in range(600):
        bg._tick()
    assert bg._elapsed > 0.0
    assert 0 <= bg._index < 3  # cycled through the three images, wrapped safely
    bg.set_reduce_motion(True)
    assert bg._timer.isActive() is False  # static frame, no drift
    bg.hide()


def test_strength_selector_value_signal_and_retranslate(qapp) -> None:
    from shobdohotao.domain import Strength
    from shobdohotao.ui.widgets.strength_selector import StrengthSelector

    sel = StrengthSelector(_t())
    assert sel.value() is Strength.BALANCED  # sensible default checked

    emitted = []
    sel.changed.connect(emitted.append)
    sel._on_click(Strength.STRONG)
    assert emitted == [Strength.STRONG]
    assert sel.value() is Strength.STRONG

    # Programmatic set must not re-emit, and exclusivity holds.
    sel.set_value(Strength.GENTLE)
    assert sel.value() is Strength.GENTLE
    assert emitted == [Strength.STRONG]

    sel.retranslate(Translator(Language.BN))
    assert sel._buttons[Strength.STRONG].text() == "কড়া"  # "Strong" in Bangla


def test_app_header_emits_signals(qapp) -> None:
    h = AppHeader(_t())
    fired = {"home": 0, "lib": 0, "lang": 0}
    h.home_requested.connect(lambda: fired.__setitem__("home", fired["home"] + 1))
    h.library_requested.connect(lambda: fired.__setitem__("lib", fired["lib"] + 1))
    h.language_toggled.connect(lambda: fired.__setitem__("lang", fired["lang"] + 1))
    h._home_btn.click()
    h._library_btn.click()
    h._lang_btn.click()
    assert fired == {"home": 1, "lib": 1, "lang": 1}

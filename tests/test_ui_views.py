"""Headless Qt tests for the views and the shell (offscreen, state-based)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from shobdohotao.domain import (  # noqa: E402
    AudioMetadata,
    MediaInfo,
    MediaType,
    ProcessingStage,
)
from shobdohotao.i18n import Language, Translator  # noqa: E402
from shobdohotao.ui.views.completion_view import CompletionView  # noqa: E402
from shobdohotao.ui.views.home_view import HomeView  # noqa: E402
from shobdohotao.ui.views.processing_view import ProcessingView  # noqa: E402


def _t() -> Translator:
    return Translator(Language.EN)


def _wait_until(predicate, timeout_s: float = 5.0) -> bool:
    """Pump the Qt event loop until ``predicate()`` is true (for async probes)."""
    import time

    from PySide6.QtWidgets import QApplication

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def _audio_info() -> MediaInfo:
    return MediaInfo(Path("speech.mp3"), MediaType.AUDIO, "mp3", 2048, 9.0, 44100, 2)


def _video_info() -> MediaInfo:
    return MediaInfo(Path("lecture.mp4"), MediaType.VIDEO, "mp4", 4096, 30.0,
                     48000, 2, 1280, 720)


# --- HomeView -------------------------------------------------------------

def test_home_starts_empty(qapp) -> None:
    h = HomeView(_t())
    assert h.is_selected() is False


def test_home_audio_selected_shows_clean_audio(qapp) -> None:
    h = HomeView(_t())
    h.show_selected(_audio_info())
    assert h.is_selected() is True
    assert h._clean_btn.text() == "Clean Audio"


def test_home_video_selected_shows_clean_video_audio(qapp) -> None:
    h = HomeView(_t())
    h.show_selected(_video_info())
    assert h._clean_btn.text() == "Clean Video Audio"


def test_home_open_and_clean_signals(qapp) -> None:
    h = HomeView(_t())
    fired = {"open": 0, "clean": 0}
    h.open_requested.connect(lambda: fired.__setitem__("open", 1))
    h.clean_requested.connect(lambda: fired.__setitem__("clean", 1))
    h._open_btn.click()
    h.show_selected(_audio_info())
    h._clean_btn.click()
    assert fired == {"open": 1, "clean": 1}


def test_home_hero_title_and_statement(qapp) -> None:
    h = HomeView(_t())
    assert h._hero.text() == _t().tr("app.title.native")  # centered hero title
    assert "Bangladesh" in h._statement.text()
    # Bengali statement after toggle.
    h.retranslate(Translator(Language.BN))
    assert "বাংলাদেশ" in h._statement.text()


def test_home_cleaned_files_button_emits_library(qapp) -> None:
    h = HomeView(_t())
    fired = {"lib": 0}
    h.library_requested.connect(lambda: fired.__setitem__("lib", 1))
    h._library_btn.click()
    assert fired["lib"] == 1


def test_home_has_crossfade_background(qapp) -> None:
    from shobdohotao.ui.widgets.aero_background import AeroBackground

    h = HomeView(_t())
    h.resize(1000, 700)
    h.show()
    qapp.processEvents()
    # The background fills the view and sits behind the content.
    assert isinstance(h._background, AeroBackground)
    assert h._background.width() == h.width()
    h.hide()


# --- ProcessingView -------------------------------------------------------

def test_processing_view_stage_and_terminal_states(qapp) -> None:
    v = ProcessingView(_t())
    v.configure(MediaType.AUDIO, "speech.mp3")
    v.set_stage(ProcessingStage.DENOISING)
    v.set_stage_progress(5, 30)
    v.append_activity("10:00:00", "Noise removal started")
    v.set_elapsed(12)
    # Terminal renders without error.
    v.mark_completed()
    v.mark_failed()
    v.mark_cancelled()
    assert "speech.mp3" in v._title.text()


def test_processing_view_cancel_signal(qapp) -> None:
    v = ProcessingView(_t())
    fired = {"cancel": 0}
    v.cancel_requested.connect(lambda: fired.__setitem__("cancel", 1))
    v._cancel_btn.click()
    assert fired["cancel"] == 1


# --- CompletionView -------------------------------------------------------

def test_completion_view_shows_result_and_actions(qapp) -> None:
    v = CompletionView(_t())
    f = Path(tempfile.mkdtemp(prefix="comp_")) / "out_cleaned.mp3"
    f.write_bytes(b"x" * 4096)
    v.set_result(f, MediaType.AUDIO, 9.0)
    assert v._name.text() == "out_cleaned.mp3"
    assert v._open_btn.text() == "Play Cleaned File"
    fired = {"open": 0, "another": 0}
    v.open_requested.connect(lambda: fired.__setitem__("open", 1))
    v.clean_another_requested.connect(lambda: fired.__setitem__("another", 1))
    v._open_btn.click()
    v._another_btn.click()
    assert fired == {"open": 1, "another": 1}


# --- Shell ----------------------------------------------------------------

@pytest.fixture()
def shell(qapp, tmp_path, monkeypatch):
    import shobdohotao.storage.app_paths as ap

    monkeypatch.setattr(ap, "resolve_documents_dir", lambda: tmp_path / "Documents")
    from shobdohotao.ui.main_window import _build_main_window_class

    return _build_main_window_class()()


def test_shell_starts_on_home(shell) -> None:
    assert shell._stack.currentWidget() is shell._home


def test_shell_language_toggle(shell) -> None:
    before = shell._t.language
    shell._toggle_language()
    assert shell._t.language is not before


def test_shell_select_file_shows_selected(shell, monkeypatch, tmp_path) -> None:
    from shobdohotao.services import media_probe

    src = tmp_path / "rec.mp3"
    src.write_bytes(b"x")
    monkeypatch.setattr(
        media_probe, "probe",
        lambda p: AudioMetadata(p, 10.0, 44100, 2, 1, "mp3"),
    )
    shell._select_file(src)  # probes on a worker thread
    assert _wait_until(lambda: shell._home.is_selected())
    assert shell._stack.currentWidget() is shell._home


def test_shell_begin_processing_switches_view(shell, tmp_path, monkeypatch) -> None:
    # Use a real worker object but neutralize run() so no job executes.
    from shobdohotao.domain import DenoiseRequest, OutputFormat
    from shobdohotao.workers.processing_worker import make_worker

    shell._input_path = tmp_path / "rec.mp3"
    shell._active_media_type = MediaType.AUDIO
    req = DenoiseRequest(tmp_path / "rec.mp3", tmp_path / "out", OutputFormat.MP3)
    worker = make_worker(req, shell._pipeline)
    monkeypatch.setattr(worker, "run", lambda: None)  # no-op slot
    shell._begin_processing(worker)
    assert shell._stack.currentWidget() is shell._processing
    shell._teardown_thread()


def test_shell_home_button_resets_after_file_selected(
    shell, monkeypatch, tmp_path
) -> None:
    # Regression: Home must return to the empty landing after a file is selected.
    from shobdohotao.services import media_probe

    src = tmp_path / "r.mp3"
    src.write_bytes(b"x")
    monkeypatch.setattr(
        media_probe, "probe",
        lambda p: AudioMetadata(p, 5.0, 44100, 2, 1, "mp3"),
    )
    shell._select_file(src)  # probes on a worker thread
    assert _wait_until(lambda: shell._home.is_selected())
    shell._go_home()  # header Home button
    assert shell._home.is_selected() is False
    assert shell._stack.currentWidget() is shell._home


def test_shell_clean_another_returns_home_empty(shell) -> None:
    shell._media_info = _audio_info()
    shell._home.show_selected(shell._media_info)
    shell._clean_another()
    assert shell._stack.currentWidget() is shell._home
    assert shell._home.is_selected() is False

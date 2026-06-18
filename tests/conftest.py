"""Shared pytest fixtures.

Forces Qt's offscreen platform so widget tests need no display, and provides a
session-wide QApplication. Qt tests should ``pytest.importorskip('PySide6')`` so
they skip cleanly on interpreters without PySide6 (e.g. CI running the pure
core).
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app

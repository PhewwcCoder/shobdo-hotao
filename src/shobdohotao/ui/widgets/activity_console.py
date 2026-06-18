"""Read-only, terminal-style engine activity log.

Shows real, structured events only (formatted from ActivityCode via i18n) with a
cyan timestamp accent. Caps visible lines, supports Copy and pause/resume of
auto-scroll. Never prints raw tracebacks or private temp paths — callers pass
``ActivityCode`` + safe params, not free-form strings.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...i18n import Translator

_MAX_LINES = 200


class ActivityConsole(QWidget):
    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = translator
        self._auto_scroll = True

        root = QVBoxLayout(self)
        self._view = QPlainTextEdit()
        self._view.setReadOnly(True)
        self._view.setObjectName("ActivityConsole")
        self._view.setMaximumBlockCount(_MAX_LINES)  # built-in line cap
        self._view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        root.addWidget(self._view)

        controls = QHBoxLayout()
        self._copy_btn = QPushButton()
        self._copy_btn.clicked.connect(self._copy)
        self._pause_btn = QPushButton()
        self._pause_btn.setCheckable(True)
        self._pause_btn.toggled.connect(self._on_pause_toggled)
        controls.addStretch(1)
        controls.addWidget(self._pause_btn)
        controls.addWidget(self._copy_btn)
        root.addLayout(controls)
        self.retranslate(translator)

    def append_line(self, timestamp: str, message: str) -> None:
        """Append one '[hh:mm:ss] message' line, honouring the visible cap."""
        self._view.appendPlainText(f"[{timestamp}] {message}")
        if self._auto_scroll:
            bar = self._view.verticalScrollBar()
            bar.setValue(bar.maximum())

    def clear(self) -> None:
        self._view.clear()

    def text(self) -> str:
        return self._view.toPlainText()

    def line_count(self) -> int:
        return self._view.blockCount()

    # --- controls ---------------------------------------------------
    def _copy(self) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(self.text())

    def _on_pause_toggled(self, paused: bool) -> None:
        self._auto_scroll = not paused
        self._pause_btn.setText(
            self._t.tr("console.resume_scroll") if paused
            else self._t.tr("console.pause_scroll")
        )

    def retranslate(self, translator: Translator) -> None:
        self._t = translator
        self._copy_btn.setText(translator.tr("console.copy"))
        self._pause_btn.setText(
            translator.tr("console.resume_scroll") if not self._auto_scroll
            else translator.tr("console.pause_scroll")
        )

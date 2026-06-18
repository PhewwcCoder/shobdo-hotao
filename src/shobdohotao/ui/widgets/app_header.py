"""Application header: Home / Cleaned Files nav + language pill.

No title here — the centered hero title on the home view carries the branding.
Emits ``home_requested``, ``library_requested``, and ``language_toggled`` so the
shell decides what to show; the header holds no business logic.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ...i18n import Translator


class AppHeader(QWidget):
    home_requested = Signal()
    library_requested = Signal()
    language_toggled = Signal()

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = translator
        self.setObjectName("AppHeader")

        row = QHBoxLayout(self)
        row.addStretch(1)  # push nav + language pill to the right

        self._home_btn = QPushButton()
        self._home_btn.setObjectName("NavButton")
        self._home_btn.clicked.connect(self.home_requested.emit)
        self._library_btn = QPushButton()
        self._library_btn.setObjectName("NavButton")
        self._library_btn.clicked.connect(self.library_requested.emit)
        self._lang_btn = QPushButton("বাংলা | EN")
        self._lang_btn.setObjectName("LangPill")
        self._lang_btn.clicked.connect(self.language_toggled.emit)

        for b in (self._home_btn, self._library_btn, self._lang_btn):
            row.addWidget(b)
        self.retranslate(translator)

    def retranslate(self, translator: Translator) -> None:
        self._t = translator
        self._home_btn.setText(translator.tr("nav.home"))
        self._library_btn.setText(translator.tr("nav.cleaned_files"))
        for b, key in (
            (self._home_btn, "nav.home"),
            (self._library_btn, "nav.cleaned_files"),
        ):
            b.setAccessibleName(translator.tr(key))

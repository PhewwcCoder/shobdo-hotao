"""Completion view shown after a cleaned file is named and saved."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...domain import MediaType
from ...i18n import Translator
from ..format import human_duration, human_size


class CompletionView(QWidget):
    open_requested = Signal()
    show_in_folder_requested = Signal()
    clean_another_requested = Signal()
    library_requested = Signal()

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = translator
        self._path: Path | None = None
        self._media_type = MediaType.AUDIO

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._headline = QLabel()
        self._headline.setObjectName("Headline")
        self._headline.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(self._headline)

        panel = QWidget()
        panel.setObjectName("AeroPanel")
        self._form = QFormLayout(panel)
        self._name = QLabel("—")
        self._folder = QLabel("—")
        self._folder.setObjectName("Muted")
        self._folder.setWordWrap(True)
        self._type = QLabel("—")
        self._size = QLabel("—")
        self._duration = QLabel("—")
        for value in (self._name, self._folder, self._type, self._size,
                      self._duration):
            self._form.addRow(QLabel(), value)
        root.addWidget(panel)

        self._open_btn = QPushButton()
        self._open_btn.clicked.connect(self.open_requested.emit)
        self._folder_btn = QPushButton()
        self._folder_btn.clicked.connect(self.show_in_folder_requested.emit)
        self._another_btn = QPushButton()
        self._another_btn.clicked.connect(self.clean_another_requested.emit)
        self._library_btn = QPushButton()
        self._library_btn.clicked.connect(self.library_requested.emit)
        row1 = QHBoxLayout()
        row1.addWidget(self._open_btn)
        row1.addWidget(self._folder_btn)
        row2 = QHBoxLayout()
        row2.addWidget(self._another_btn)
        row2.addWidget(self._library_btn)
        root.addLayout(row1)
        root.addLayout(row2)
        self.retranslate(translator)

    def set_result(self, path: Path, media_type: MediaType,
                   duration_seconds: float | None) -> None:
        self._path = path
        self._media_type = media_type
        size = path.stat().st_size if path.exists() else 0
        self._name.setText(path.name)
        self._folder.setText(str(path.parent))
        self._type.setText(path.suffix.lstrip(".").upper())
        self._size.setText(human_size(size))
        self._duration.setText(
            human_duration(duration_seconds) if duration_seconds else "—"
        )
        self.retranslate(self._t)

    def retranslate(self, translator: Translator) -> None:
        self._t = translator
        t = translator.tr
        self._headline.setText("✓  " + t("completion.ready"))
        labels = ["completion.filename", "completion.folder", "completion.type",
                  "completion.size", "completion.duration"]
        for i, key in enumerate(labels):
            item = self._form.itemAt(i, QFormLayout.ItemRole.LabelRole)
            if item and item.widget():
                item.widget().setText(t(key))
        is_video = self._media_type is MediaType.VIDEO
        self._open_btn.setText(
            t("action.open_cleaned_video") if is_video
            else t("action.play_cleaned_file")
        )
        self._folder_btn.setText(t("action.show_in_folder"))
        self._another_btn.setText(t("action.clean_another"))
        self._library_btn.setText(t("action.go_to_cleaned_files"))

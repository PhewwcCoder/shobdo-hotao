"""Glass media card showing real probed details of the selected file.

Long filenames are elided; the full path is in the tooltip. Populated from a
:class:`~shobdohotao.domain.MediaInfo` built by the probe services.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ...domain import MediaInfo, MediaType
from ...i18n import Translator
from ..format import human_duration, human_size


class MediaCard(QWidget):
    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = translator
        self._info: MediaInfo | None = None
        self.setObjectName("AeroPanel")

        root = QVBoxLayout(self)
        header = QHBoxLayout()
        self._icon = QLabel()
        self._icon.setObjectName("MediaIcon")
        self._name = QLabel()
        self._name.setObjectName("MediaName")
        self._name.setTextFormat(Qt.TextFormat.PlainText)
        header.addWidget(self._icon)
        header.addWidget(self._name, 1)
        root.addLayout(header)

        self._form = QFormLayout()
        self._rows: dict[str, QLabel] = {}
        for key in ("format", "size", "duration", "sample_rate", "resolution"):
            value = QLabel("—")
            self._rows[key] = value
            self._form.addRow(QLabel(), value)
        root.addLayout(self._form)

    def set_media(self, info: MediaInfo) -> None:
        self._info = info
        self._refresh()

    def _refresh(self) -> None:
        t = self._t.tr
        info = self._info
        if info is None:
            return
        is_video = info.media_type is MediaType.VIDEO
        self._icon.setText("🎬" if is_video else "🎵")
        self._name.setText(info.path.name)
        self._name.setToolTip(str(info.path))

        # Re-label rows (supports language switch) and fill values.
        labels = list(self._labelled_values(info, is_video))
        for i, (label_key, value_key, value_text) in enumerate(labels):
            label_item = self._form.itemAt(i, QFormLayout.ItemRole.LabelRole)
            if label_item and label_item.widget():
                label_item.widget().setText(t(label_key))
            self._rows[value_key].setText(value_text)

    def _labelled_values(self, info: MediaInfo, is_video: bool):
        yield ("media.format", "format", (info.container or "—").upper())
        yield ("media.size", "size", human_size(info.size_bytes))
        yield ("media.duration", "duration",
               human_duration(info.duration_seconds) if info.duration_seconds else "—")
        yield ("media.sample_rate", "sample_rate",
               f"{info.sample_rate} Hz" if info.sample_rate else "—")
        if is_video and info.width and info.height:
            yield ("media.resolution", "resolution", f"{info.width}×{info.height}")
        else:
            yield ("media.audio", "resolution",
                   f"{info.channels} ch" if info.channels else "—")

    def retranslate(self, translator: Translator) -> None:
        self._t = translator
        self._refresh()

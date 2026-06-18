"""Segmented noise-strength picker (Gentle · Balanced · Strong).

Three exclusive glossy glass buttons that map to :class:`Strength`. STRONG is
the "max clean" preset (the backend also enables DeepFilterNet's post-filter for
it). Emits :attr:`changed` with the chosen ``Strength`` and persists nothing
itself — the shell wires that to settings. Honours reduce-motion via the buttons.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QWidget

from ...domain import Strength
from ...i18n import Translator
from .glass_button import GlassButton

_ORDER = (Strength.GENTLE, Strength.BALANCED, Strength.STRONG)


class StrengthSelector(QWidget):
    changed = Signal(object)  # emits a Strength

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = translator
        self._buttons: dict[Strength, GlassButton] = {}

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._label = QLabel()
        self._label.setObjectName("Muted")
        lay.addWidget(self._label)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for strength in _ORDER:
            btn = GlassButton()
            btn.setObjectName("GlassButton")
            btn.setCheckable(True)
            self._buttons[strength] = btn
            self._group.addButton(btn)
            btn.clicked.connect(
                lambda _checked=False, s=strength: self._on_click(s)
            )
            lay.addWidget(btn)

        self._buttons[Strength.BALANCED].setChecked(True)
        self.retranslate(translator)

    # --- public API -------------------------------------------------
    def _on_click(self, strength: Strength) -> None:
        self.set_value(strength)
        self.changed.emit(strength)

    def set_value(self, strength: Strength) -> None:
        self._buttons[strength].setChecked(True)

    def value(self) -> Strength:
        for strength, btn in self._buttons.items():
            if btn.isChecked():
                return strength
        return Strength.BALANCED

    def set_motion_enabled(self, enabled: bool) -> None:
        for btn in self._buttons.values():
            btn.set_motion_enabled(enabled)

    def retranslate(self, translator: Translator) -> None:
        self._t = translator
        self._label.setText(translator.tr("strength.label"))
        for strength, btn in self._buttons.items():
            btn.setText(translator.tr(f"strength.{strength.value}"))

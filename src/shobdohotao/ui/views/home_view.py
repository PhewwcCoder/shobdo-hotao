"""Home view: Frutiger-Aero landing (hero + drop zone) ↔ selected-file card.

Emits user-intent signals; the shell performs the actual file work. Supports
drag-and-drop of a single file. Two decorative glass bubbles float off-kilter
behind the content for a calm "different world" feel (see frutiger-aero-ui).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from ...domain import MediaInfo, MediaType
from ...i18n import Translator
from ..widgets.aero_background import AeroBackground, background_asset
from ..widgets.cleaning_spinner import CleaningSpinner
from ..widgets.glass_button import GlassButton
from ..widgets.media_card import MediaCard
from ..widgets.signal_visualizer import SignalVisualizer, VisualizerState
from ..widgets.strength_selector import StrengthSelector

# Full-bleed background imagery. Drop your exported design(s) named
# background_1.* / background_2.* / background_3.* into ui/theme/assets/backgrounds/.
_CREDIT = "Created by Aryan Ahmad Sharar · BRAC University"


class HomeView(QWidget):
    open_requested = Signal()
    clean_requested = Signal()
    replace_requested = Signal()
    library_requested = Signal()
    file_dropped = Signal(str)
    strength_changed = Signal(object)  # emits a Strength

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = translator
        self._is_video = False
        self.setAcceptDrops(True)

        # Full-bleed crossfading background behind the stacked content. Drifting
        # song motifs (notes/bubbles) lift off the artwork — see AeroBackground.
        self._background = AeroBackground(self)
        images = [p for p in (background_asset("background_1"),
                              background_asset("background_2"),
                              background_asset("background_3"))
                  if p is not None]
        self._background.set_images(images)
        self._background.lower()

        self._stack = QStackedLayout(self)
        self._stack.addWidget(self._build_empty())
        self._stack.addWidget(self._build_selected())

        # Author credit, pinned bottom-right (positioned in resizeEvent).
        self._credit = QLabel(_CREDIT, self)
        self._credit.setObjectName("Credit")
        self._credit.adjustSize()
        # Busy overlay shown while a dropped/opened file is being probed.
        self._spinner = CleaningSpinner(self)

        self.show_empty()
        self.retranslate(translator)

    # --- empty state ------------------------------------------------
    def _build_empty(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 24, 40, 24)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._hero = QLabel()
        self._hero.setObjectName("HeroTitle")
        self._hero.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._statement = QLabel()
        self._statement.setObjectName("HeroStatement")
        self._statement.setWordWrap(True)
        self._statement.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._hero)
        lay.addWidget(self._statement)
        lay.addSpacing(8)

        self._orb = SignalVisualizer()
        self._orb.set_state(VisualizerState.IDLE)
        lay.addWidget(self._orb, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._drop_label = QLabel()
        self._drop_label.setObjectName("DropPrompt")
        self._drop_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._or_label = QLabel()
        self._or_label.setObjectName("Muted")
        self._or_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._drop_label)
        lay.addWidget(self._or_label)

        # Feature buttons row (transparent glossy glass).
        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._open_btn = GlassButton()
        self._open_btn.setObjectName("GlassButton")
        self._open_btn.clicked.connect(self.open_requested.emit)
        self._library_btn = GlassButton()
        self._library_btn.setObjectName("GlassButton")
        self._library_btn.clicked.connect(self.library_requested.emit)
        buttons.addWidget(self._open_btn)
        buttons.addWidget(self._library_btn)
        lay.addLayout(buttons)

        self._supported = QLabel()
        self._supported.setObjectName("Muted")
        self._supported.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._supported)
        return page

    # --- selected state ---------------------------------------------
    def _build_selected(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._card = MediaCard(self._t)
        lay.addWidget(self._card)
        # Noise-strength picker; STRONG enables the extra post-filter backend-side.
        self._strength = StrengthSelector(self._t)
        self._strength.changed.connect(self.strength_changed.emit)
        lay.addWidget(self._strength, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._clean_btn = GlassButton()
        self._clean_btn.setObjectName("GlassPrimary")
        self._clean_btn.clicked.connect(self.clean_requested.emit)
        self._replace_btn = GlassButton()
        self._replace_btn.setObjectName("GlassButton")
        self._replace_btn.clicked.connect(self.replace_requested.emit)
        lay.addWidget(self._clean_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._replace_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        return page

    # --- public API -------------------------------------------------
    def show_empty(self) -> None:
        self._stack.setCurrentIndex(0)

    def show_selected(self, info: MediaInfo) -> None:
        self._is_video = info.media_type is MediaType.VIDEO
        self._card.set_media(info)
        self._update_clean_label()
        self._stack.setCurrentIndex(1)

    def is_selected(self) -> bool:
        return self._stack.currentIndex() == 1

    def set_strength(self, strength) -> None:
        """Reflect the persisted strength preset in the picker (no signal)."""
        self._strength.set_value(strength)

    def show_loading(self) -> None:
        """Show the cleaning-spinner busy overlay (e.g. while probing a file)."""
        self._spinner.setGeometry(0, 0, self.width(), self.height())
        self._spinner.start()

    def hide_loading(self) -> None:
        self._spinner.stop()

    def set_reduce_motion(self, value: bool) -> None:
        self._orb.set_reduce_motion(value)
        self._background.set_reduce_motion(value)
        self._spinner.set_reduce_motion(value)
        self._strength.set_motion_enabled(not value)
        for btn in (self._open_btn, self._library_btn,
                    self._clean_btn, self._replace_btn):
            btn.set_motion_enabled(not value)

    # --- background -------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._background.setGeometry(0, 0, self.width(), self.height())
        self._background.lower()
        self._spinner.setGeometry(0, 0, self.width(), self.height())
        # Pin the credit to the bottom-right corner.
        self._credit.adjustSize()
        self._credit.move(self.width() - self._credit.width() - 16,
                          self.height() - self._credit.height() - 10)
        self._credit.raise_()
        super().resizeEvent(event)

    # --- i18n -------------------------------------------------------
    def _update_clean_label(self) -> None:
        key = "action.clean_video_audio" if self._is_video else "action.clean"
        self._clean_btn.setText(self._t.tr(key))

    def retranslate(self, translator: Translator) -> None:
        self._t = translator
        t = translator.tr
        self._hero.setText(t("app.title.native"))
        self._statement.setText(t("home.hero_statement"))
        self._drop_label.setText(t("home.drop"))
        self._or_label.setText(t("home.or_choose"))
        self._open_btn.setText(t("action.open"))
        self._library_btn.setText(t("action.cleaned_files"))
        self._supported.setText(t("home.supported"))
        self._replace_btn.setText(t("home.replace_file"))
        self._strength.retranslate(translator)
        self._spinner.set_caption(t("home.reading_file"))
        self._card.retranslate(translator)
        self._update_clean_label()

    # --- drag & drop ------------------------------------------------
    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802 (Qt API)
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            if path.is_file():
                self.file_dropped.emit(str(path))
                event.acceptProposedAction()

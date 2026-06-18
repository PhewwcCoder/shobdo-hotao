"""Modal "Save Cleaned File" dialog (lazy Qt).

Lets the user edit only the base filename; the extension is fixed by the
processing output and shown read-only. Live-validates against Windows filename
rules and disables Save until the name is valid. Returns the chosen stem via
:func:`prompt_save_name`.

No filesystem logic lives here — the caller passes a validator callback and a
destination summary string, and performs the actual move via StorageService.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...i18n import Translator
from ...storage.filename_validator import FilenameIssue, check_filename

_ISSUE_KEY = {
    FilenameIssue.EMPTY: "validate.empty",
    FilenameIssue.INVALID_CHARS: "validate.invalid_chars",
    FilenameIssue.RESERVED: "validate.reserved",
    FilenameIssue.TOO_LONG: "validate.too_long",
    FilenameIssue.TRAILING: "validate.trailing",
}


def prompt_save_name(
    parent: Any,
    translator: Translator,
    *,
    suggested_stem: str,
    extension: str,
    destination_dir: str,
    name_taken: Callable[[str], bool] | None = None,
) -> str | None:
    """Show the dialog. Returns the chosen stem, or ``None`` if cancelled.

    ``name_taken`` (optional) lets the dialog hint that a name already exists;
    saving still proceeds via collision-safe naming, so this is advisory only.
    """
    from PySide6.QtWidgets import (  # type: ignore
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QVBoxLayout,
    )

    t = translator.tr
    dialog = QDialog(parent)
    dialog.setWindowTitle(t("save.title"))
    dialog.setModal(True)
    dialog.setMinimumWidth(420)

    root = QVBoxLayout(dialog)
    form = QFormLayout()

    name_edit = QLineEdit(suggested_stem)
    name_edit.selectAll()
    form.addRow(t("save.filename"), name_edit)

    type_label = QLabel(f".{extension}")
    form.addRow(t("save.type"), type_label)

    dest_label = QLabel(destination_dir)
    dest_label.setObjectName("Muted")
    dest_label.setWordWrap(True)
    form.addRow(t("save.destination"), dest_label)
    root.addLayout(form)

    hint = QLabel("")
    hint.setObjectName("ValidationHint")
    hint.setWordWrap(True)
    root.addWidget(hint)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.button(QDialogButtonBox.StandardButton.Save).setText(t("save.button"))
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("action.cancel"))
    root.addWidget(buttons)

    save_btn = buttons.button(QDialogButtonBox.StandardButton.Save)

    def revalidate() -> None:
        issue = check_filename(name_edit.text())
        if issue is FilenameIssue.OK:
            hint.setText("")
            save_btn.setEnabled(True)
            if name_taken and name_taken(name_edit.text()):
                # Advisory only; collision-safe naming will append _2.
                hint.setText("")
        else:
            hint.setText(t(_ISSUE_KEY[issue]))
            save_btn.setEnabled(False)

    name_edit.textChanged.connect(revalidate)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    revalidate()

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return name_edit.text()
    return None

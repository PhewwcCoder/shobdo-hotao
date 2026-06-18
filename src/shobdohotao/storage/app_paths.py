"""Platform-aware resolution of the application's local storage layout.

The library lives under the user's Documents directory:

    Documents/
    └── ShobdoHotao/
        ├── Cleaned Files/
        │   ├── Audio/
        │   └── Video/
        ├── Database/
        │   └── library.db
        ├── Logs/
        └── Temp/

Design notes
------------
- The Documents directory is resolved via Qt's ``QStandardPaths`` when Qt is
  available (which correctly follows OneDrive/known-folder redirection on
  Windows), with a headless fallback to ``~/Documents`` so this module — and the
  whole storage layer — is importable and testable without PySide6.
- No username or drive letter is ever hardcoded.
- ``AppPaths`` accepts an explicit ``root`` so tests point it at a temp dir and
  never touch the real Documents folder.
- All accessors return :class:`pathlib.Path`; Unicode/Bengali names are fine.
"""

from __future__ import annotations

import os
from pathlib import Path

_APP_DIRNAME = "ShobdoHotao"
_CLEANED = "Cleaned Files"


def resolve_documents_dir() -> Path:
    """Best-effort path to the user's Documents directory.

    Tries Qt first (honours Windows known-folder/OneDrive redirection), then an
    environment/home fallback. Never raises; returns a sensible default.
    """
    try:
        from PySide6.QtCore import QStandardPaths  # type: ignore

        loc = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        if loc:
            return Path(loc)
    except Exception:  # pragma: no cover - exercised only without Qt
        pass

    # Fallbacks: USERPROFILE/Documents on Windows, else ~/Documents.
    profile = os.environ.get("USERPROFILE")
    base = Path(profile) if profile else Path.home()
    return base / "Documents"


class AppPaths:
    """Resolves and (optionally) creates the storage layout.

    Parameters
    ----------
    root:
        The ``ShobdoHotao`` application folder. When ``None`` it is derived as
        ``<Documents>/ShobdoHotao``. Tests pass a temp directory here.
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root is not None else (
            resolve_documents_dir() / _APP_DIRNAME
        )

    # --- core locations ---------------------------------------------
    def app_root(self) -> Path:
        return self._root

    def cleaned_files_dir(self) -> Path:
        return self._root / _CLEANED

    def audio_library(self) -> Path:
        return self.cleaned_files_dir() / "Audio"

    def video_library(self) -> Path:
        return self.cleaned_files_dir() / "Video"

    def database_dir(self) -> Path:
        return self._root / "Database"

    def database_path(self) -> Path:
        return self.database_dir() / "library.db"

    def logs_dir(self) -> Path:
        return self._root / "Logs"

    def temp_dir(self) -> Path:
        return self._root / "Temp"

    # --- helpers ----------------------------------------------------
    def library_for(self, media_type: object) -> Path:
        """Library folder for a :class:`~shobdohotao.domain.MediaType`."""
        from ..domain import MediaType

        return (
            self.video_library()
            if media_type is MediaType.VIDEO
            else self.audio_library()
        )

    def all_dirs(self) -> tuple[Path, ...]:
        return (
            self.app_root(),
            self.cleaned_files_dir(),
            self.audio_library(),
            self.video_library(),
            self.database_dir(),
            self.logs_dir(),
            self.temp_dir(),
        )

    def create_required_dirs(self) -> None:
        """Create every storage directory if missing (idempotent)."""
        for directory in self.all_dirs():
            directory.mkdir(parents=True, exist_ok=True)

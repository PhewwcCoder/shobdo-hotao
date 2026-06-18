"""Moves completed temporary outputs into the Documents library.

Processing writes its final file into a **staging temp dir** (outside the
library). After the user names the file, :meth:`StorageService.save_cleaned`
moves it into ``Cleaned Files/Audio`` or ``Cleaned Files/Video`` with a
collision-safe name. If the user cancels naming, :meth:`discard` removes the
staged file so nothing is left behind.

Keeping this logic here (not in Qt widgets) means it is fully unit-testable.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ..domain import ErrorCode, MediaType, ProcessingError
from .app_paths import AppPaths
from .filename_validator import FilenameIssue, check_filename, collision_safe_name


class StorageService:
    def __init__(self, paths: AppPaths) -> None:
        self._paths = paths

    @property
    def paths(self) -> AppPaths:
        return self._paths

    def save_cleaned(
        self,
        staged_output: Path,
        desired_stem: str,
        media_type: MediaType,
    ) -> Path:
        """Move ``staged_output`` into the library under ``desired_stem``.

        The extension is taken from the staged file (so the user only chooses
        the base name). Raises :class:`ProcessingError` with a translatable code
        on invalid name, missing staged file, or filesystem failure. Never
        overwrites an existing library file.
        """
        if check_filename(desired_stem) is not FilenameIssue.OK:
            raise ProcessingError(ErrorCode.INVALID_FILENAME, desired_stem)
        if not staged_output.exists():
            raise ProcessingError(ErrorCode.SAVE_FAILED, "staged output missing")

        library = self._paths.library_for(media_type)
        try:
            library.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ProcessingError(ErrorCode.OUTPUT_FOLDER_FAILED, str(exc)) from exc

        extension = staged_output.suffix.lstrip(".")
        # Strip any extension the user may have typed; we control it.
        stem = desired_stem
        if stem.lower().endswith(f".{extension.lower()}"):
            stem = stem[: -(len(extension) + 1)]

        final_path = collision_safe_name(library, stem, extension)
        try:
            shutil.move(str(staged_output), str(final_path))
        except OSError as exc:
            raise ProcessingError(ErrorCode.SAVE_FAILED, str(exc)) from exc
        return final_path

    def discard(self, staged_output: Path) -> None:
        """Delete a staged temporary output (best effort; never raises)."""
        try:
            if staged_output.exists():
                staged_output.unlink()
            # Remove the now-empty staging directory if it is under Temp.
            parent = staged_output.parent
            temp_root = self._paths.temp_dir()
            if parent != temp_root and temp_root in parent.parents:
                shutil.rmtree(parent, ignore_errors=True)
        except OSError:
            pass

    def suggested_stem(self, original_name: str) -> str:
        """A friendly default like ``lecture_cleaned`` from an input name."""
        return f"{Path(original_name).stem}_cleaned"

"""Open files and reveal them in the OS file manager.

Windows is the primary target; macOS and Linux have reasonable fallbacks. The
command *builders* are pure and unit-tested; the executor functions are thin
wrappers that raise a translatable :class:`ProcessingError` on failure so the UI
can show a friendly message ("Windows cannot open the selected file").

Note: this package is named ``platform`` per the project layout. We use
``sys.platform`` (not the stdlib ``platform`` module) to avoid any ambiguity.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ..domain import ErrorCode, ProcessingError

WINDOWS = "win32"
MACOS = "darwin"


def _is_windows(platform: str) -> bool:
    return platform.startswith("win")


def build_reveal_command(path: Path, platform: str) -> list[str]:
    """Command to reveal (select) ``path`` in the OS file manager."""
    if _is_windows(platform):
        # explorer /select,<path>  — selects the file inside its folder.
        return ["explorer", f"/select,{path}"]
    if platform == MACOS:
        return ["open", "-R", str(path)]
    # Linux: no portable "select"; open the containing folder.
    return ["xdg-open", str(path.parent)]


def build_open_directory_command(path: Path, platform: str) -> list[str]:
    """Command to open a directory in the OS file manager."""
    if _is_windows(platform):
        return ["explorer", str(path)]
    if platform == MACOS:
        return ["open", str(path)]
    return ["xdg-open", str(path)]


def build_open_file_command(path: Path, platform: str) -> list[str]:
    """Command to open a file with its default app (non-Windows).

    On Windows we use :func:`os.startfile` instead of a command, so this builder
    is for macOS/Linux (and for unit-testing the construction).
    """
    if platform == MACOS:
        return ["open", str(path)]
    return ["xdg-open", str(path)]


def _require_exists(path: Path) -> None:
    if not path.exists():
        raise ProcessingError(ErrorCode.FILE_MISSING, str(path))


def open_file(path: Path) -> None:
    """Open ``path`` with the user's default application."""
    _require_exists(path)
    try:
        if _is_windows(sys.platform):
            os.startfile(str(path))  # type: ignore[attr-defined]  # noqa: S606
        else:
            subprocess.Popen(build_open_file_command(path, sys.platform))
    except OSError as exc:
        raise ProcessingError(ErrorCode.CANNOT_OPEN, str(exc)) from exc


def reveal_in_file_manager(path: Path) -> None:
    """Open the file manager with ``path`` selected/highlighted."""
    _require_exists(path)
    try:
        subprocess.Popen(build_reveal_command(path, sys.platform))
    except OSError as exc:
        raise ProcessingError(ErrorCode.CANNOT_OPEN, str(exc)) from exc


def open_directory(path: Path) -> None:
    """Open a directory in the file manager."""
    if not path.exists():
        raise ProcessingError(ErrorCode.FILE_MISSING, str(path))
    try:
        subprocess.Popen(build_open_directory_command(path, sys.platform))
    except OSError as exc:
        raise ProcessingError(ErrorCode.CANNOT_OPEN, str(exc)) from exc

"""Windows-safe filename validation and collision-safe naming.

Pure stdlib so it is fully unit-testable. Validation operates on the *stem*
(the filename the user types, without the extension) but also tolerates a name
that includes an extension. Unicode and Bengali characters are allowed; only the
Windows-illegal set and reserved device names are rejected.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from pathlib import Path

# Characters Windows forbids in a filename.
INVALID_CHARS = set('<>:"/\\|?*')

# Reserved Windows device names (case-insensitive), with or without extension.
_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Practical cap well under the Windows MAX_PATH component limit.
MAX_STEM_LENGTH = 200


class FilenameIssue(Enum):
    """Result of validating a filename. ``OK`` means it is safe to use."""

    OK = "ok"
    EMPTY = "empty"
    INVALID_CHARS = "invalid_chars"
    RESERVED = "reserved"
    TOO_LONG = "too_long"
    TRAILING = "trailing"  # ends with space or dot (Windows trims these)


def _stem_of(name: str) -> str:
    """The base name without a trailing known-ish extension.

    We treat the text after the final dot as an extension only when it looks
    like one (1–5 chars, no spaces). This keeps names like "v1.2 final" intact.
    """
    if "." not in name:
        return name
    head, _, tail = name.rpartition(".")
    if head and 1 <= len(tail) <= 5 and " " not in tail:
        return head
    return name


def check_filename(name: str) -> FilenameIssue:
    """Validate a user-entered filename (with or without extension)."""
    if name is None or not name.strip():
        return FilenameIssue.EMPTY

    if any(ch in INVALID_CHARS for ch in name):
        return FilenameIssue.INVALID_CHARS

    # Windows silently strips trailing spaces/dots — reject so the saved name
    # matches what the user sees.
    if name != name.rstrip(" ."):
        return FilenameIssue.TRAILING

    stem = _stem_of(name)
    if stem.strip().upper() in _RESERVED:
        return FilenameIssue.RESERVED

    if len(stem) > MAX_STEM_LENGTH:
        return FilenameIssue.TOO_LONG

    return FilenameIssue.OK


def is_valid_filename(name: str) -> bool:
    return check_filename(name) is FilenameIssue.OK


def collision_safe_name(
    directory: Path,
    stem: str,
    extension: str,
    *,
    exists: Callable[[Path], bool] | None = None,
) -> Path:
    """Return ``directory/stem.ext``, appending ``_2``, ``_3`` … on collision.

    ``extension`` is the bare extension (no leading dot). ``exists`` is injected
    for pure testing; defaults to :meth:`pathlib.Path.exists`.
    """
    if exists is None:
        exists = Path.exists

    suffix = f".{extension.lstrip('.')}"
    candidate = directory / f"{stem}{suffix}"
    index = 2
    while exists(candidate):
        candidate = directory / f"{stem}_{index}{suffix}"
        index += 1
    return candidate

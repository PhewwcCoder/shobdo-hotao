"""Persistent settings backed by QSettings.

To keep this module importable without Qt (for tests and headless tooling), the
QSettings dependency is imported lazily inside ``_store``. An in-memory backend
is used automatically when Qt is unavailable, so settings logic stays testable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .domain import OutputFormat, Strength
from .i18n import Language

_ORG = "ShobdoHotao"
_APP = "ShobdoHotao"

# Setting keys
KEY_LANGUAGE = "ui/language"
KEY_OUTPUT_DIR = "io/output_dir"
KEY_OUTPUT_FORMAT = "io/output_format"
KEY_STRENGTH = "processing/strength"
KEY_REDUCE_MOTION = "ui/reduce_motion"
KEY_REDUCE_TRANSPARENCY = "ui/reduce_transparency"
KEY_FIRST_RUN_DONE = "ui/first_run_done"


class _MemoryBackend:
    """Fallback settings store used when QSettings is unavailable."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def value(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def setValue(self, key: str, value: Any) -> None:  # noqa: N802 (Qt API shape)
        self._data[key] = value


def _store() -> Any:
    try:
        from PySide6.QtCore import QSettings  # type: ignore

        return QSettings(_ORG, _APP)
    except Exception:  # pragma: no cover - exercised only without Qt
        return _MemoryBackend()


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if value is None:
        return default
    return bool(value)


class Settings:
    """Typed accessor over the key/value store."""

    def __init__(self, backend: Any | None = None) -> None:
        self._s = backend if backend is not None else _store()

    # Language
    def language(self) -> Language:
        raw = self._s.value(KEY_LANGUAGE, Language.EN.value)
        try:
            return Language(raw)
        except ValueError:
            return Language.EN

    def set_language(self, language: Language) -> None:
        self._s.setValue(KEY_LANGUAGE, language.value)

    # Output directory
    def output_dir(self) -> Path:
        raw = self._s.value(KEY_OUTPUT_DIR, "")
        return Path(raw) if raw else Path.home() / "ShobdoHotao"

    def set_output_dir(self, path: Path) -> None:
        self._s.setValue(KEY_OUTPUT_DIR, str(path))

    # Output format
    def output_format(self) -> OutputFormat:
        raw = self._s.value(KEY_OUTPUT_FORMAT, OutputFormat.MP3.value)
        try:
            return OutputFormat(raw)
        except ValueError:
            return OutputFormat.MP3

    def set_output_format(self, fmt: OutputFormat) -> None:
        self._s.setValue(KEY_OUTPUT_FORMAT, fmt.value)

    # Strength
    def strength(self) -> Strength:
        raw = self._s.value(KEY_STRENGTH, Strength.BALANCED.value)
        try:
            return Strength(raw)
        except ValueError:
            return Strength.BALANCED

    def set_strength(self, strength: Strength) -> None:
        self._s.setValue(KEY_STRENGTH, strength.value)

    # Reduce motion
    def reduce_motion(self) -> bool:
        return _as_bool(self._s.value(KEY_REDUCE_MOTION, False), False)

    def set_reduce_motion(self, value: bool) -> None:
        self._s.setValue(KEY_REDUCE_MOTION, value)

    # Reduce transparency
    def reduce_transparency(self) -> bool:
        return _as_bool(self._s.value(KEY_REDUCE_TRANSPARENCY, False), False)

    def set_reduce_transparency(self, value: bool) -> None:
        self._s.setValue(KEY_REDUCE_TRANSPARENCY, value)

    # First run
    def first_run_done(self) -> bool:
        return _as_bool(self._s.value(KEY_FIRST_RUN_DONE, False), False)

    def set_first_run_done(self, value: bool = True) -> None:
        self._s.setValue(KEY_FIRST_RUN_DONE, value)

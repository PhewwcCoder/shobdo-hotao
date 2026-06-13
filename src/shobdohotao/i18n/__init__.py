"""Dict-based offline i18n.

Design choice (documented): we use plain Python dict catalogs rather than Qt
``.ts``/``.qm`` files. Rationale — no compile step (``lrelease``) in the build,
trivial to diff in review, and zero runtime dependency beyond stdlib. The
trade-off is we lose Qt Linguist tooling; acceptable for a two-language app.

Usage::

    from shobdohotao.i18n import Translator, Language
    t = Translator(Language.BN)
    t.tr("action.clean")  # -> "আওয়াজ দূর করুন"
"""

from __future__ import annotations

from enum import Enum

from . import bn, en


class Language(Enum):
    EN = "en"
    BN = "bn"


_CATALOGS = {
    Language.EN: en.STRINGS,
    Language.BN: bn.STRINGS,
}

# English is the canonical key set; other catalogs must match it.
CANONICAL_KEYS = frozenset(en.STRINGS)


class Translator:
    """Resolves string keys for the active language with English fallback."""

    def __init__(self, language: Language = Language.EN) -> None:
        self._language = language

    @property
    def language(self) -> Language:
        return self._language

    def set_language(self, language: Language) -> None:
        self._language = language

    def tr(self, key: str) -> str:
        catalog = _CATALOGS[self._language]
        if key in catalog:
            return catalog[key]
        # Fall back to English, then to the raw key so missing strings are
        # visible in testing rather than crashing the UI.
        return en.STRINGS.get(key, key)


def missing_keys(language: Language) -> set[str]:
    """Keys present in English but absent in ``language``'s catalog."""
    return set(CANONICAL_KEYS) - set(_CATALOGS[language])


def extra_keys(language: Language) -> set[str]:
    """Keys in ``language``'s catalog that are not in the canonical set."""
    return set(_CATALOGS[language]) - set(CANONICAL_KEYS)

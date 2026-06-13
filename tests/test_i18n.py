"""i18n parity + behaviour tests."""

from __future__ import annotations

from shobdohotao.domain import ErrorCode
from shobdohotao.i18n import Language, Translator, extra_keys, missing_keys


def test_bangla_has_no_missing_or_extra_keys() -> None:
    # Every English key must exist in Bangla and vice-versa.
    assert missing_keys(Language.BN) == set()
    assert extra_keys(Language.BN) == set()


def test_translator_switches_language() -> None:
    t = Translator(Language.EN)
    assert t.tr("action.clean") == "Clean Audio"
    t.set_language(Language.BN)
    assert t.tr("action.clean") == "আওয়াজ দূর করুন"


def test_translator_falls_back_to_english_then_key() -> None:
    t = Translator(Language.BN)
    # Unknown key returns the raw key rather than crashing.
    assert t.tr("nonexistent.key") == "nonexistent.key"


def test_every_error_code_has_a_translation() -> None:
    t_en = Translator(Language.EN)
    t_bn = Translator(Language.BN)
    for code in ErrorCode:
        key = f"error.{code.value}"
        assert t_en.tr(key) != key, f"missing EN for {key}"
        assert t_bn.tr(key) != key, f"missing BN for {key}"

"""Format structured activity events into translated log lines (pure).

The processing layer emits ``(ActivityCode, params)`` only; this UI helper turns
each into a localized string via the ``activity.<code>`` i18n template. Keeping
it here (not in the service) keeps technical messages translatable and free of
private temp paths.
"""

from __future__ import annotations

from ..domain import ActivityCode
from ..i18n import Translator


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:  # leave unknown placeholders intact
        return "{" + key + "}"


def format_activity(translator: Translator, code: ActivityCode, params: dict) -> str:
    template = translator.tr(f"activity.{code.value}")
    try:
        return template.format_map(_SafeDict(params))
    except (ValueError, IndexError):
        return template

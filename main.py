"""Frozen-app entry point (PyInstaller).

Two things this launcher handles that ``python -m shobdohotao`` doesn't need:

1. PyInstaller runs its target script as top-level ``__main__`` with no package
   context, breaking the relative imports inside ``shobdohotao/__main__.py``.
   Importing the package here makes those imports resolve.
2. A ``--windowed`` app has no console, so ``sys.stdout``/``sys.stderr`` are
   ``None``. Libraries that log to them (DeepFilterNet via loguru) raise
   "Cannot log to objects of type 'NoneType'". We install harmless null sinks
   *before* importing the app so the model can load.
"""

from __future__ import annotations

import io
import sys


class _NullIO(io.TextIOBase):
    """A writable stream that silently discards everything."""

    def write(self, _s: str) -> int:
        return 0


if sys.stdout is None:
    sys.stdout = _NullIO()
if sys.stderr is None:
    sys.stderr = _NullIO()

from shobdohotao.__main__ import main  # noqa: E402  (must follow the stdio fix)

if __name__ == "__main__":
    sys.exit(main())

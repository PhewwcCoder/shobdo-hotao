"""Frozen-app entry point (PyInstaller).

PyInstaller runs its target script as top-level ``__main__`` with no package
context, which breaks the relative imports inside ``shobdohotao/__main__.py``.
This launcher imports the package properly so those imports resolve, then hands
off to the real entry. Running the module (``python -m shobdohotao``) still works
unchanged for development.
"""

from __future__ import annotations

import sys

from shobdohotao.__main__ import main

if __name__ == "__main__":
    sys.exit(main())

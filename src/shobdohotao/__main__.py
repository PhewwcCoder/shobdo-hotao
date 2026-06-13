"""Application entry point: ``python -m shobdohotao``.

Keeps startup minimal: configure logging, build the Qt app + window, show it,
and run the event loop. All real work lives behind the service layer.
"""

from __future__ import annotations

import sys

from .services.logging_service import get_logger


def main() -> int:
    logger = get_logger()
    logger.info("Starting ShobdoHotao")
    try:
        from .ui.main_window import create_app
    except ImportError as exc:  # PySide6 not installed
        sys.stderr.write(
            "PySide6 is required to run the UI. Install dependencies first.\n"
            f"({exc})\n"
        )
        return 2

    app, window = create_app()
    window.resize(560, 520)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

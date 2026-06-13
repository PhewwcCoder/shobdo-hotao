"""Rotating, local-only logging.

Logs stay on disk under a per-user app data folder. They contain full
exceptions for debugging but never leave the machine (rule §2: no telemetry).
File paths and filenames may appear in logs (local only) but are never
transmitted anywhere.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGER_NAME = "shobdohotao"
_configured = False


def log_dir() -> Path:
    """Per-user log directory. Uses %LOCALAPPDATA% on Windows."""
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / "ShobdoHotao" / "logs"


def configure(level: int = logging.INFO) -> logging.Logger:
    """Idempotently configure the app logger with a rotating file handler."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if _configured:
        return logger

    logger.setLevel(level)
    try:
        directory = log_dir()
        directory.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            directory / "shobdohotao.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    except OSError:
        # Never let logging setup crash the app; fall back to a null handler.
        logger.addHandler(logging.NullHandler())

    _configured = True
    return logger


def get_logger() -> logging.Logger:
    return configure()

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import LOG_DIR, ensure_runtime_dirs, load_config


def configure_logging() -> Path:
    ensure_runtime_dirs()
    log_path = LOG_DIR / "buddy.log"
    config = load_config()
    level = getattr(logging, config.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    if not any(getattr(handler, "_buddy_managed", False) for handler in root.handlers):
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler._buddy_managed = True

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._buddy_managed = True

        root.addHandler(file_handler)
        root.addHandler(console_handler)

    return log_path


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

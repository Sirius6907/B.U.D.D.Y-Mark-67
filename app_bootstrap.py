from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field

from buddy_logging import configure_logging, get_logger
from config import ensure_runtime_dirs, validate_runtime_config


@dataclass(slots=True)
class BootstrapReport:
    log_path: str
    warnings: list[str] = field(default_factory=list)


def _has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def bootstrap_application() -> BootstrapReport:
    ensure_runtime_dirs()
    log_path = str(configure_logging())
    logger = get_logger("buddy.bootstrap")

    warnings = validate_runtime_config()

    optional_modules = {
        "playwright": "Browser automation will be unavailable until Playwright is installed.",
        "PyQt6": "Desktop UI will be unavailable until PyQt6 is installed.",
        "sounddevice": "Voice input/output will be unavailable until sounddevice is installed.",
    }
    for module_name, warning in optional_modules.items():
        if not _has_module(module_name):
            warnings.append(warning)

    for warning in warnings:
        logger.warning(warning)

    logger.info("Bootstrap complete. Log file: %s", log_path)
    return BootstrapReport(log_path=log_path, warnings=warnings)

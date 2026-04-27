from __future__ import annotations

import importlib.util
import os
import shutil
import sys
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

    if sys.version_info < (3, 10):
        warnings.append(f"Buddy officially supports Python 3.10+. You are running {sys.version.split()[0]}. Expect bugs.")

    ui_mode = os.environ.get("BUDDY_UI_MODE", "web").strip().lower() or "web"
    optional_modules = {
        "playwright": "Browser automation will be unavailable until Playwright is installed.",
        "sounddevice": "Voice input/output will be unavailable until sounddevice is installed.",
    }
    if ui_mode == "legacy":
        optional_modules["PyQt6"] = "Legacy desktop UI will be unavailable until PyQt6 is installed."
    for module_name, warning in optional_modules.items():
        if not _has_module(module_name):
            warnings.append(warning)
    if ui_mode == "web" and shutil.which("npm") is None and shutil.which("npm.cmd") is None:
        warnings.append("Web dashboard shell requires npm/Node.js to launch the Electron frontend.")

    for warning in warnings:
        logger.warning(warning)

    logger.info("Bootstrap complete. Log file: %s", log_path)
    return BootstrapReport(log_path=log_path, warnings=warnings)

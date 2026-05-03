from __future__ import annotations

from importlib import import_module
from pathlib import Path

from .base import ActionRegistry


_ROOT = Path(__file__).resolve().parent
_SKIP_ROOT_MODULES = {"__init__", "base"}
_DOMAIN_PACKAGES = ("files", "storage", "process", "network", "agent", "memory", "mcp", "apps", "services", "windows", "input", "clipboard", "screen", "printers", "wifi", "bluetooth", "usb", "serial", "shares", "browser_nav", "browser_dom", "browser_auth", "browser_tabs", "browser_cookies", "browser_history", "browser_media", "browser_downloads", "browser_extensions")


def _load_root_action_modules() -> None:
    for module_path in sorted(_ROOT.glob("*.py")):
        if module_path.stem in _SKIP_ROOT_MODULES:
            continue
        import_module(f"actions.{module_path.stem}")


def _load_domain_packages() -> None:
    for package_name in _DOMAIN_PACKAGES:
        package_dir = _ROOT / package_name
        if package_dir.is_dir():
            import_module(f"actions.{package_name}")


_load_root_action_modules()
_load_domain_packages()


__all__ = ["ActionRegistry"]

"""
runtime.browser.session — Session lifecycle management.

Wraps BrowserEngine tab/session methods.
"""

from __future__ import annotations

from typing import Any

from runtime.browser.engine import BrowserEngine
from runtime.contracts.models import ToolResult


def open_new_tab(url: str = "", *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Open a new tab, optionally navigating to a URL."""
    return BrowserEngine().new_tab(url, browser=browser, player=player)


def close_current_tab(*, browser: str | None = None, player: Any = None) -> ToolResult:
    """Close the current tab."""
    return BrowserEngine().close_tab(browser=browser, player=player)


def take_screenshot(path: str | None = None, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Take a screenshot of the current page."""
    return BrowserEngine().screenshot(path, browser=browser, player=player)

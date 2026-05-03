"""
runtime.browser.dom — DOM interaction helpers.

Wraps BrowserEngine DOM methods with typed signatures
for the tool layer.
"""

from __future__ import annotations

from typing import Any

from runtime.browser.engine import BrowserEngine
from runtime.contracts.models import ToolResult


def click_element(selector: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Click an element by CSS selector."""
    return BrowserEngine().click(selector=selector, browser=browser, player=player)


def click_by_text(text: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Click an element by visible text."""
    return BrowserEngine().click(text=text, browser=browser, player=player)


def click_by_role(description: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Smart click by element description (tries role, text, placeholder, aria-label)."""
    return BrowserEngine().smart_click(description, browser=browser, player=player)


def get_page_text(*, browser: str | None = None, player: Any = None) -> ToolResult:
    """Get all visible text from the page."""
    return BrowserEngine().get_page_text(browser=browser, player=player)


def press_key(key: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Press a keyboard key."""
    return BrowserEngine().press_key(key, browser=browser, player=player)

"""
runtime.browser.navigation — Navigation-specific helper methods.

Wraps BrowserEngine navigation methods with domain-specific
parameter validation and smart defaults.
"""

from __future__ import annotations

from typing import Any

from runtime.browser.engine import BrowserEngine
from runtime.contracts.models import ToolResult


def navigate_to_url(url: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Navigate to a specific URL."""
    return BrowserEngine().navigate(url, browser=browser, player=player)


def navigate_to_domain(domain: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Navigate to a domain (auto-adds https:// and .com if needed)."""
    return BrowserEngine().navigate(domain, browser=browser, player=player)


def search_google(query: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Search using Google."""
    return BrowserEngine().search(query, "google", browser=browser, player=player)


def search_bing(query: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Search using Bing."""
    return BrowserEngine().search(query, "bing", browser=browser, player=player)


def search_duckduckgo(query: str, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Search using DuckDuckGo."""
    return BrowserEngine().search(query, "duckduckgo", browser=browser, player=player)


def refresh_page(*, browser: str | None = None, player: Any = None) -> ToolResult:
    """Refresh the current page."""
    return BrowserEngine().refresh(browser=browser, player=player)


def go_back(*, browser: str | None = None, player: Any = None) -> ToolResult:
    """Navigate back in history."""
    return BrowserEngine().go_back(browser=browser, player=player)


def go_forward(*, browser: str | None = None, player: Any = None) -> ToolResult:
    """Navigate forward in history."""
    return BrowserEngine().go_forward(browser=browser, player=player)


def get_current_url(*, browser: str | None = None, player: Any = None) -> ToolResult:
    """Get the current page URL."""
    return BrowserEngine().get_current_url(browser=browser, player=player)


def scroll_page_down(amount: int = 500, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Scroll page down."""
    return BrowserEngine().scroll("down", amount, browser=browser, player=player)


def scroll_page_up(amount: int = 500, *, browser: str | None = None, player: Any = None) -> ToolResult:
    """Scroll page up."""
    return BrowserEngine().scroll("up", amount, browser=browser, player=player)

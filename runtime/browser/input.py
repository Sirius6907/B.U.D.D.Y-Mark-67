"""
runtime.browser.input — Form input and typing helpers.

Wraps BrowserEngine input methods for type, smart_type, and fill_form.
"""

from __future__ import annotations

from typing import Any

from runtime.browser.engine import BrowserEngine
from runtime.contracts.models import ToolResult


def type_into_field(
    selector: str,
    text: str,
    clear_first: bool = True,
    *,
    browser: str | None = None,
    player: Any = None,
) -> ToolResult:
    """Type text into a field by CSS selector."""
    return BrowserEngine().type_text(selector, text, clear_first, browser=browser, player=player)


def type_by_label(
    description: str,
    text: str,
    *,
    browser: str | None = None,
    player: Any = None,
) -> ToolResult:
    """Smart type by field description (tries placeholder, label, role)."""
    return BrowserEngine().smart_type(description, text, browser=browser, player=player)


def fill_form_fields(
    fields: dict[str, str],
    *,
    browser: str | None = None,
    player: Any = None,
) -> ToolResult:
    """Fill multiple form fields at once."""
    return BrowserEngine().fill_form(fields, browser=browser, player=player)

"""
runtime.browser.state — Browser state capture and diff for multi-step reasoning.

BrowserState is a frozen snapshot of the browser at a point in time.
Used by the engine to:
1. Capture before/after state around every tool execution
2. Diff states to detect what changed (verification)
3. Feed state context into the planner for confidence scoring
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BrowserState:
    """Immutable snapshot of browser state at a point in time."""

    url: str = ""
    title: str = ""
    tab_count: int = 0
    visible_text_snippet: str = ""  # first 500 chars of body text
    dom_hash: str = ""              # hash of visible text for change detection
    load_state: str = "unknown"     # domcontentloaded | networkidle | loading | unknown
    navigation_id: str = ""         # unique ID per navigation event
    form_fields: tuple[tuple[str, str], ...] = ()  # ((name, value), ...) input field snapshots
    scroll_y: int = 0               # vertical scroll offset in pixels
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "tab_count": self.tab_count,
            "visible_text_snippet": self.visible_text_snippet[:200],
            "dom_hash": self.dom_hash,
            "load_state": self.load_state,
            "navigation_id": self.navigation_id,
            "form_fields": dict(self.form_fields),
            "scroll_y": self.scroll_y,
            "timestamp": self.timestamp,
        }


def _compute_dom_hash(text: str) -> str:
    """Hash visible text for lightweight change detection."""
    if not text:
        return ""
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()[:12]


def capture_state(session: Any) -> BrowserState:
    """
    Capture current browser state from a _BrowserSession.

    This is intentionally defensive — if any field fails to capture,
    we return what we can rather than crashing the tool execution.
    """
    url = ""
    title = ""
    tab_count = 0
    visible_text = ""
    load_state = "unknown"

    try:
        url = session.run(session.get_url())
    except Exception:
        pass

    try:
        page = session._page
        if page and not page.is_closed():
            title = session.run(_async_title(page))
    except Exception:
        pass

    try:
        page = session._page
        if page and not page.is_closed():
            ctx = page.context
            tab_count = len(ctx.pages)
    except Exception:
        pass

    try:
        text = session.run(session.get_text())
        visible_text = text[:500] if text else ""
    except Exception:
        pass

    dom_hash = _compute_dom_hash(visible_text)
    nav_id = f"{int(time.time() * 1000)}-{dom_hash}"

    return BrowserState(
        url=url,
        title=title,
        tab_count=tab_count,
        visible_text_snippet=visible_text,
        dom_hash=dom_hash,
        load_state=load_state,
        navigation_id=nav_id,
        timestamp=time.time(),
    )


async def _async_title(page: Any) -> str:
    """Get page title asynchronously."""
    return await page.title()


def diff_states(before: BrowserState, after: BrowserState) -> dict[str, Any]:
    """
    Compare two BrowserState snapshots and return what changed.

    Returns a dict with only the fields that changed, each containing
    {"before": old_value, "after": new_value}.
    """
    changes: dict[str, Any] = {}

    if before.url != after.url:
        changes["url"] = {"before": before.url, "after": after.url}
    if before.title != after.title:
        changes["title"] = {"before": before.title, "after": after.title}
    if before.tab_count != after.tab_count:
        changes["tab_count"] = {"before": before.tab_count, "after": after.tab_count}
    if before.dom_hash != after.dom_hash:
        changes["dom_hash"] = {"before": before.dom_hash, "after": after.dom_hash}
    if before.load_state != after.load_state:
        changes["load_state"] = {"before": before.load_state, "after": after.load_state}
    if before.form_fields != after.form_fields:
        changes["form_fields"] = {"before": before.form_fields, "after": after.form_fields}
    if before.scroll_y != after.scroll_y:
        changes["scroll_y"] = {"before": before.scroll_y, "after": after.scroll_y}

    return changes


class StateDiffAnalyzer:
    """Interpret state diffs to classify the kind of change that occurred.

    Used by the replanner and verification layer to understand
    what a tool actually did to the browser state.
    """

    @staticmethod
    def classify_change(diff: dict[str, Any]) -> str:
        """Classify the type of state change.

        Returns one of:
            "navigation" — URL changed
            "dom_mutation" — DOM hash changed but URL didn't
            "form_update" — Form fields changed
            "tab_change" — Tab count changed
            "scroll" — Scroll position changed
            "no_change" — Nothing changed
            "complex" — Multiple unrelated changes
        """
        if not diff:
            return "no_change"

        keys = set(diff.keys())

        if "url" in keys:
            return "navigation"
        if keys == {"form_fields"}:
            return "form_update"
        if keys == {"tab_count"}:
            return "tab_change"
        if keys == {"scroll_y"}:
            return "scroll"
        if keys == {"dom_hash"} or keys == {"dom_hash", "title"}:
            return "dom_mutation"
        if len(keys) >= 3:
            return "complex"
        return "dom_mutation"

    @staticmethod
    def did_navigate(diff: dict[str, Any]) -> bool:
        """Check if the diff represents a navigation event."""
        return "url" in diff

    @staticmethod
    def did_dom_change(diff: dict[str, Any]) -> bool:
        """Check if the DOM content changed."""
        return "dom_hash" in diff

    @staticmethod
    def did_form_change(diff: dict[str, Any]) -> bool:
        """Check if form fields changed."""
        return "form_fields" in diff

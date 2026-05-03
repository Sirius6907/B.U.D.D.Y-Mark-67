"""
runtime.browser.engine — Thin orchestration façade over _SessionRegistry.

BrowserEngine is a SINGLETON. It does NOT contain Playwright logic directly.
Instead, it delegates to the existing _BrowserSession methods in browser_control.py
and wraps every call with:
1. State capture (before/after)
2. ToolResult construction
3. Recovery-aware error handling
"""

from __future__ import annotations

import time
from typing import Any, Optional

from runtime.browser.state import BrowserState, capture_state, diff_states
from runtime.browser.recovery import RecoveryPolicy, ErrorType
from runtime.results.builder import build_tool_result
from runtime.contracts.models import RiskLevel, ToolResult


def _get_session(browser: str | None = None, player: Any = None) -> Any:
    """
    Get or create a _BrowserSession from the global registry.
    Lazy-imports to avoid circular dependency with browser_control.py.
    """
    from actions.browser_control import _registry
    return _registry.get(browser, player=player)


class BrowserEngine:
    """
    Singleton façade — all browser tools delegate here.

    Every public method:
    1. Gets the active session
    2. Captures state BEFORE
    3. Executes the Playwright operation
    4. Captures state AFTER
    5. Returns a structured ToolResult
    """

    _instance: Optional[BrowserEngine] = None

    def __new__(cls) -> BrowserEngine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate(
        self, url: str, *, browser: str | None = None, player: Any = None
    ) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.go_to(url))
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_nav_navigate_to_url",
                operation="navigate",
                risk_level=RiskLevel.LOW,
                status="success" if "Opened" in str(raw) else "partial",
                summary=str(raw),
                structured_data={
                    "url_requested": url,
                    "url_actual": after.url,
                    "state_diff": diff_states(before, after),
                },
                preconditions=["browser_session_active"],
                postconditions=["url_changed"],
            )
        except Exception as e:
            return self._error_result("browser_nav_navigate_to_url", "navigate", e)

    def search(
        self,
        query: str,
        engine: str = "google",
        *,
        browser: str | None = None,
        player: Any = None,
    ) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.search(query, engine))
            after = capture_state(sess)
            return build_tool_result(
                tool_name=f"browser_nav_search_{engine}",
                operation="search",
                risk_level=RiskLevel.LOW,
                status="success" if "Opened" in str(raw) else "partial",
                summary=str(raw),
                structured_data={
                    "query": query,
                    "engine": engine,
                    "url_actual": after.url,
                    "state_diff": diff_states(before, after),
                },
                preconditions=["browser_session_active"],
                postconditions=["search_results_loaded"],
            )
        except Exception as e:
            return self._error_result(f"browser_nav_search_{engine}", "search", e)

    def refresh(self, *, browser: str | None = None, player: Any = None) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.reload())
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_nav_refresh_page",
                operation="refresh",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=str(raw),
                structured_data={"state_diff": diff_states(before, after)},
                idempotent=True,
                preconditions=["browser_session_active"],
                postconditions=["page_reloaded"],
            )
        except Exception as e:
            return self._error_result("browser_nav_refresh_page", "refresh", e)

    def go_back(self, *, browser: str | None = None, player: Any = None) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.back())
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_nav_go_back",
                operation="go_back",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=str(raw),
                structured_data={"state_diff": diff_states(before, after)},
                preconditions=["browser_session_active", "history_has_back"],
                postconditions=["navigated_back"],
            )
        except Exception as e:
            return self._error_result("browser_nav_go_back", "go_back", e)

    def go_forward(self, *, browser: str | None = None, player: Any = None) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.forward())
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_nav_go_forward",
                operation="go_forward",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=str(raw),
                structured_data={"state_diff": diff_states(before, after)},
                preconditions=["browser_session_active", "history_has_forward"],
                postconditions=["navigated_forward"],
            )
        except Exception as e:
            return self._error_result("browser_nav_go_forward", "go_forward", e)

    def get_current_url(self, *, browser: str | None = None, player: Any = None) -> ToolResult:
        sess = _get_session(browser, player)
        try:
            url = sess.run(sess.get_url())
            return build_tool_result(
                tool_name="browser_nav_get_current_url",
                operation="get_current_url",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=f"Current URL: {url}",
                structured_data={"url": url},
                idempotent=True,
                preconditions=["browser_session_active"],
                postconditions=[],
            )
        except Exception as e:
            return self._error_result("browser_nav_get_current_url", "get_current_url", e)

    def scroll(
        self,
        direction: str = "down",
        amount: int = 500,
        *,
        browser: str | None = None,
        player: Any = None,
    ) -> ToolResult:
        sess = _get_session(browser, player)
        try:
            raw = sess.run(sess.scroll(direction, amount))
            return build_tool_result(
                tool_name=f"browser_nav_scroll_page_{direction}",
                operation="scroll",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=str(raw),
                structured_data={"direction": direction, "amount": amount},
                idempotent=True,
                preconditions=["browser_session_active"],
                postconditions=["page_scrolled"],
            )
        except Exception as e:
            return self._error_result(f"browser_nav_scroll_page_{direction}", "scroll", e)

    # ── DOM ────────────────────────────────────────────────────────────────────

    def click(
        self,
        selector: str | None = None,
        text: str | None = None,
        *,
        browser: str | None = None,
        player: Any = None,
    ) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.click(selector, text))
            after = capture_state(sess)
            tool_name = "browser_dom_click_by_text" if text else "browser_dom_click_element"
            return build_tool_result(
                tool_name=tool_name,
                operation="click",
                risk_level=RiskLevel.MEDIUM,
                status="success" if "Clicked" in str(raw) else "failed",
                summary=str(raw),
                structured_data={
                    "selector": selector,
                    "text": text,
                    "state_diff": diff_states(before, after),
                },
                preconditions=["browser_session_active", "element_visible"],
                postconditions=["element_clicked"],
            )
        except Exception as e:
            tool_name = "browser_dom_click_by_text" if text else "browser_dom_click_element"
            return self._error_result(tool_name, "click", e)

    def smart_click(
        self, description: str, *, browser: str | None = None, player: Any = None
    ) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.smart_click(description))
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_dom_click_by_role",
                operation="smart_click",
                risk_level=RiskLevel.MEDIUM,
                status="success" if "Clicked" in str(raw) else "failed",
                summary=str(raw),
                structured_data={
                    "description": description,
                    "state_diff": diff_states(before, after),
                },
                preconditions=["browser_session_active"],
                postconditions=["element_clicked"],
            )
        except Exception as e:
            return self._error_result("browser_dom_click_by_role", "smart_click", e)

    def get_page_text(self, *, browser: str | None = None, player: Any = None) -> ToolResult:
        sess = _get_session(browser, player)
        try:
            text = sess.run(sess.get_text())
            return build_tool_result(
                tool_name="browser_dom_get_page_text",
                operation="get_page_text",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=f"Got {len(text)} chars of page text",
                structured_data={"text": text, "length": len(text)},
                idempotent=True,
                preconditions=["browser_session_active"],
                postconditions=[],
            )
        except Exception as e:
            return self._error_result("browser_dom_get_page_text", "get_page_text", e)

    # ── Input ──────────────────────────────────────────────────────────────────

    def type_text(
        self,
        selector: str | None = None,
        text: str = "",
        clear_first: bool = True,
        *,
        browser: str | None = None,
        player: Any = None,
    ) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.type_text(selector, text, clear_first))
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_dom_type_into_field",
                operation="type_text",
                risk_level=RiskLevel.MEDIUM,
                status="success" if "typed" in str(raw).lower() else "failed",
                summary=str(raw),
                structured_data={
                    "selector": selector,
                    "text_length": len(text),
                    "clear_first": clear_first,
                    "state_diff": diff_states(before, after),
                },
                preconditions=["browser_session_active", "input_field_focused"],
                postconditions=["text_entered"],
            )
        except Exception as e:
            return self._error_result("browser_dom_type_into_field", "type_text", e)

    def smart_type(
        self,
        description: str,
        text: str,
        *,
        browser: str | None = None,
        player: Any = None,
    ) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.smart_type(description, text))
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_dom_type_by_label",
                operation="smart_type",
                risk_level=RiskLevel.MEDIUM,
                status="success" if "Typed" in str(raw) else "failed",
                summary=str(raw),
                structured_data={
                    "description": description,
                    "text_length": len(text),
                    "state_diff": diff_states(before, after),
                },
                preconditions=["browser_session_active"],
                postconditions=["text_entered"],
            )
        except Exception as e:
            return self._error_result("browser_dom_type_by_label", "smart_type", e)

    def fill_form(
        self,
        fields: dict[str, str],
        *,
        browser: str | None = None,
        player: Any = None,
    ) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.fill_form(fields))
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_dom_fill_form_fields",
                operation="fill_form",
                risk_level=RiskLevel.MEDIUM,
                status="success" if "✓" in str(raw) else "partial",
                summary=str(raw),
                structured_data={
                    "field_count": len(fields),
                    "state_diff": diff_states(before, after),
                },
                preconditions=["browser_session_active", "form_visible"],
                postconditions=["form_filled"],
            )
        except Exception as e:
            return self._error_result("browser_dom_fill_form_fields", "fill_form", e)

    def press_key(
        self, key: str, *, browser: str | None = None, player: Any = None
    ) -> ToolResult:
        sess = _get_session(browser, player)
        try:
            raw = sess.run(sess.press(key))
            return build_tool_result(
                tool_name="browser_dom_press_key",
                operation="press_key",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=str(raw),
                structured_data={"key": key},
                preconditions=["browser_session_active"],
                postconditions=["key_pressed"],
            )
        except Exception as e:
            return self._error_result("browser_dom_press_key", "press_key", e)

    # ── Tabs / Session ─────────────────────────────────────────────────────────

    def new_tab(
        self, url: str = "", *, browser: str | None = None, player: Any = None
    ) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.new_tab(url))
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_tabs_open_new_tab" if not url else "browser_tabs_open_url_in_new_tab",
                operation="new_tab",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=str(raw),
                structured_data={
                    "url": url,
                    "state_diff": diff_states(before, after),
                },
                preconditions=["browser_session_active"],
                postconditions=["new_tab_opened"],
            )
        except Exception as e:
            return self._error_result("browser_tabs_open_new_tab", "new_tab", e)

    def close_tab(self, *, browser: str | None = None, player: Any = None) -> ToolResult:
        sess = _get_session(browser, player)
        before = capture_state(sess)
        try:
            raw = sess.run(sess.close_tab())
            after = capture_state(sess)
            return build_tool_result(
                tool_name="browser_tabs_close_current_tab",
                operation="close_tab",
                risk_level=RiskLevel.MEDIUM,
                status="success",
                summary=str(raw),
                structured_data={"state_diff": diff_states(before, after)},
                preconditions=["browser_session_active", "tab_exists"],
                postconditions=["tab_closed"],
            )
        except Exception as e:
            return self._error_result("browser_tabs_close_current_tab", "close_tab", e)

    # ── Media ──────────────────────────────────────────────────────────────────

    def screenshot(
        self, path: str | None = None, *, browser: str | None = None, player: Any = None
    ) -> ToolResult:
        sess = _get_session(browser, player)
        try:
            raw = sess.run(sess.screenshot(path))
            return build_tool_result(
                tool_name="browser_media_take_screenshot",
                operation="screenshot",
                risk_level=RiskLevel.LOW,
                status="success" if "saved" in str(raw).lower() else "failed",
                summary=str(raw),
                structured_data={"path": path or "~/Desktop/buddy_screenshot.png"},
                idempotent=True,
                preconditions=["browser_session_active"],
                postconditions=["screenshot_saved"],
            )
        except Exception as e:
            return self._error_result("browser_media_take_screenshot", "screenshot", e)

    # ── Error helper ──────────────────────────────────────────────────────────

    @staticmethod
    def _error_result(tool_name: str, operation: str, error: Exception) -> ToolResult:
        error_type = RecoveryPolicy.classify_error(error)
        alternative = RecoveryPolicy.suggest_alternative(tool_name, error_type)
        return build_tool_result(
            tool_name=tool_name,
            operation=operation,
            risk_level=RiskLevel.LOW,
            status="error",
            summary=f"Error: {error}",
            structured_data={
                "error_type": error_type.value,
                "error_message": str(error),
                "retryable": RecoveryPolicy.should_retry(error_type, 0),
                "alternative_tool": alternative,
                "wait_seconds": RecoveryPolicy.wait_strategy(error_type, 0),
            },
        )

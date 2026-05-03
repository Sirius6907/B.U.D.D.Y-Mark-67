"""
runtime.browser.recovery — Tool-aware recovery and fallback strategies.

Uses the CapabilityRegistry to find alternative tools when one fails,
rather than hardcoding fallback chains.

Error classification drives retry decisions and wait strategies.
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Optional


class ErrorType(str, Enum):
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    NAVIGATION = "navigation"
    PERMISSION = "permission"
    STALE = "stale"
    DETACHED = "detached"
    UNKNOWN = "unknown"


# ── Fallback chains keyed by tool domain + operation pattern ──
# These map tool_name prefixes to ordered lists of alternative tool names
# that can be tried when the primary tool fails.
_FALLBACK_CHAINS: dict[str, list[str]] = {
    "browser_dom_click_element": [
        "browser_dom_click_by_text",
        "browser_dom_click_by_role",
        "browser_dom_click_link",
    ],
    "browser_dom_click_by_text": [
        "browser_dom_click_element",
        "browser_dom_click_by_role",
    ],
    "browser_dom_type_into_field": [
        "browser_dom_type_by_placeholder",
        "browser_dom_type_by_label",
    ],
    "browser_nav_navigate_to_url": [
        "browser_nav_navigate_to_domain",
    ],
    "browser_nav_search_google": [
        "browser_nav_search_bing",
        "browser_nav_search_duckduckgo",
    ],
}


class RecoveryPolicy:
    """Smart retry and fallback strategies for browser tool failures."""

    MAX_RETRIES = 3

    @staticmethod
    def classify_error(error: Exception | str) -> ErrorType:
        """Classify an error into a recovery-relevant category."""
        msg = str(error).lower()

        if "timeout" in msg or "timed out" in msg:
            return ErrorType.TIMEOUT
        if "not found" in msg or "no element" in msg or "could not find" in msg:
            return ErrorType.NOT_FOUND
        if "navigation" in msg or "net::" in msg or "err_" in msg:
            return ErrorType.NAVIGATION
        if "permission" in msg or "denied" in msg or "blocked" in msg:
            return ErrorType.PERMISSION
        if "stale" in msg or "detached" in msg:
            return ErrorType.STALE
        if "closed" in msg or "disposed" in msg:
            return ErrorType.DETACHED

        return ErrorType.UNKNOWN

    @staticmethod
    def should_retry(error_type: ErrorType, attempt: int) -> bool:
        """Decide if a retry is worthwhile given the error type and attempt count."""
        if attempt >= RecoveryPolicy.MAX_RETRIES:
            return False

        # Never retry permission or detached errors
        if error_type in (ErrorType.PERMISSION, ErrorType.DETACHED):
            return False

        # Timeout and stale are worth retrying
        if error_type in (ErrorType.TIMEOUT, ErrorType.STALE, ErrorType.NAVIGATION):
            return True

        # NOT_FOUND: retry once (DOM may still be loading)
        if error_type == ErrorType.NOT_FOUND:
            return attempt < 1

        # UNKNOWN: retry once
        return attempt < 1

    @staticmethod
    def suggest_alternative(tool_name: str, error_type: ErrorType) -> Optional[str]:
        """
        Suggest an alternative tool based on fallback chains.

        Returns None if no alternative is known.
        """
        chain = _FALLBACK_CHAINS.get(tool_name, [])
        if chain:
            return chain[0]
        return None

    @staticmethod
    def get_fallback_chain(tool_name: str) -> list[str]:
        """Return the full fallback chain for a tool (may be empty)."""
        return list(_FALLBACK_CHAINS.get(tool_name, []))

    @staticmethod
    def wait_strategy(error_type: ErrorType, attempt: int = 0) -> float:
        """
        Calculate wait time before retry using exponential backoff with jitter.

        Returns seconds to wait.
        """
        base_delays = {
            ErrorType.TIMEOUT: 2.0,
            ErrorType.NOT_FOUND: 1.0,
            ErrorType.NAVIGATION: 3.0,
            ErrorType.STALE: 0.5,
            ErrorType.UNKNOWN: 1.5,
        }
        base = base_delays.get(error_type, 1.5)
        delay = base * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.3)
        return min(delay + jitter, 30.0)  # Cap at 30s

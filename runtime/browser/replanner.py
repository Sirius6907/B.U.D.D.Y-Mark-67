"""
runtime.browser.replanner — True replanning engine for autonomous web workflows.

When the 3-tier recovery (retry → fallback → signal) exhausts all options,
the replanner analyzes the failure context and generates a modified plan.

Replanning strategies:
  1. INSERT — add preparatory steps before the failed step
  2. REPLACE — swap the failed tool for a different approach
  3. REDUCE — simplify the goal to an achievable subset
  4. ABORT — failure is unrecoverable, stop workflow

The replanner does NOT call the LLM.  It uses deterministic rules
based on error classification, DOM state, and tool domain knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from runtime.browser.recovery import ErrorType, RecoveryPolicy


class ReplanAction(str, Enum):
    INSERT = "insert"     # Add preparatory steps before retry
    REPLACE = "replace"   # Swap the tool for a different approach
    REDUCE = "reduce"     # Simplify the goal
    ABORT = "abort"       # Unrecoverable — stop workflow


@dataclass
class ReplanDecision:
    """Output of the replanner — what to do next."""
    action: ReplanAction
    reason: str
    # New steps to insert (INSERT) or replacement steps (REPLACE)
    new_steps: list[dict[str, Any]] = field(default_factory=list)
    # Which step index triggered the replan
    failed_step_index: int = -1
    # Original tool that failed
    failed_tool: str = ""
    # Confidence in the replan succeeding (0–1)
    replan_confidence: float = 0.3


# ── Preparatory step templates ──
# Maps (error_type, tool_domain) → list of preparatory step templates
_PREP_STEPS: dict[tuple[ErrorType, str], list[dict[str, Any]]] = {
    (ErrorType.NOT_FOUND, "browser_dom"): [
        {
            "tool": "browser_wait_wait_for_element",
            "parameters": {"timeout": 5000},
            "description": "Wait for element to appear in DOM",
            "is_mutating": False,
        },
        {
            "tool": "browser_dom_scroll_page_down",
            "parameters": {"distance": 500},
            "description": "Scroll down to reveal element",
            "is_mutating": True,
        },
    ],
    (ErrorType.NOT_FOUND, "browser_input"): [
        {
            "tool": "browser_wait_wait_for_element",
            "parameters": {"timeout": 5000},
            "description": "Wait for input field to appear",
            "is_mutating": False,
        },
    ],
    (ErrorType.TIMEOUT, "browser_nav"): [
        {
            "tool": "browser_wait_wait_for_network_idle",
            "parameters": {"timeout": 10000},
            "description": "Wait for network to settle",
            "is_mutating": False,
        },
    ],
    (ErrorType.TIMEOUT, "browser_dom"): [
        {
            "tool": "browser_wait_wait_for_page_load",
            "parameters": {"timeout": 10000},
            "description": "Wait for page load before DOM interaction",
            "is_mutating": False,
        },
    ],
    (ErrorType.STALE, "browser_dom"): [
        {
            "tool": "browser_nav_refresh_page",
            "parameters": {},
            "description": "Refresh page to get fresh DOM",
            "is_mutating": True,
        },
        {
            "tool": "browser_wait_wait_for_page_load",
            "parameters": {"timeout": 5000},
            "description": "Wait for page load after refresh",
            "is_mutating": False,
        },
    ],
    (ErrorType.NAVIGATION, "browser_nav"): [
        {
            "tool": "browser_wait_wait_for_network_idle",
            "parameters": {"timeout": 10000},
            "description": "Wait for network before navigation retry",
            "is_mutating": False,
        },
    ],
}

# ── Tool replacement map ──
# Maps failed_tool → alternative approach (different strategy, not just fallback)
_REPLACEMENT_MAP: dict[str, list[dict[str, Any]]] = {
    "browser_dom_click_element": [
        {
            "tool": "browser_js_execute_javascript",
            "parameters": {"script": "document.querySelector('{selector}').click()"},
            "description": "JS-based click as alternative to Playwright click",
            "is_mutating": True,
        },
    ],
    "browser_dom_type_into_field": [
        {
            "tool": "browser_js_execute_javascript",
            "parameters": {
                "script": (
                    "const el = document.querySelector('{selector}');"
                    "el.value = '{value}';"
                    "el.dispatchEvent(new Event('input', {bubbles: true}));"
                )
            },
            "description": "JS-based input as alternative to Playwright type",
            "is_mutating": True,
        },
    ],
    "browser_dom_submit_form": [
        {
            "tool": "browser_dom_press_key",
            "parameters": {"key": "Enter"},
            "description": "Press Enter as alternative form submission",
            "is_mutating": True,
        },
    ],
    "browser_dom_select_dropdown_option": [
        {
            "tool": "browser_js_execute_javascript",
            "parameters": {
                "script": (
                    "const sel = document.querySelector('{selector}');"
                    "sel.value = '{value}';"
                    "sel.dispatchEvent(new Event('change', {bubbles: true}));"
                )
            },
            "description": "JS-based select as alternative to Playwright select",
            "is_mutating": True,
        },
    ],
}


def _extract_domain(tool_name: str) -> str:
    """Extract domain prefix from a namespaced tool name.

    browser_dom_click_element → browser_dom
    browser_nav_navigate_to_url → browser_nav
    """
    parts = tool_name.split("_")
    if len(parts) >= 2:
        return f"{parts[0]}_{parts[1]}"
    return "unknown"


class Replanner:
    """Deterministic replanning engine for browser workflow failures.

    Called when the WorkflowExecutor's 3-tier recovery (retry → fallback → signal)
    has been exhausted.  Analyzes the failure and proposes a modified plan.
    """

    MAX_REPLAN_ATTEMPTS = 2  # Prevent infinite replan loops

    def __init__(self, capability_registry: Any = None):
        self._registry = capability_registry
        self._replan_count: dict[int, int] = {}  # step_index → replan count

    def reset(self) -> None:
        """Reset replan counters for a new workflow."""
        self._replan_count.clear()

    def analyze_and_replan(
        self,
        *,
        failed_step_index: int,
        failed_tool: str,
        error_message: str,
        state_diff: Optional[dict[str, Any]] = None,
        remaining_steps: Optional[list[dict[str, Any]]] = None,
    ) -> ReplanDecision:
        """Analyze a failure and produce a replan decision.

        Args:
            failed_step_index: Index of the step that failed
            failed_tool: Name of the tool that failed
            error_message: The error string from the failed execution
            state_diff: Browser state changes observed (if any)
            remaining_steps: Steps that haven't been executed yet

        Returns:
            ReplanDecision with action and new steps (if applicable)
        """
        # Guard: prevent infinite replan loops
        count = self._replan_count.get(failed_step_index, 0)
        if count >= self.MAX_REPLAN_ATTEMPTS:
            return ReplanDecision(
                action=ReplanAction.ABORT,
                reason=(
                    f"Replan limit ({self.MAX_REPLAN_ATTEMPTS}) reached "
                    f"for step {failed_step_index}"
                ),
                failed_step_index=failed_step_index,
                failed_tool=failed_tool,
                replan_confidence=0.0,
            )
        self._replan_count[failed_step_index] = count + 1

        # Classify the error
        error_type = RecoveryPolicy.classify_error(error_message)
        domain = _extract_domain(failed_tool)

        # PERMISSION and DETACHED are unrecoverable
        if error_type in (ErrorType.PERMISSION, ErrorType.DETACHED):
            return ReplanDecision(
                action=ReplanAction.ABORT,
                reason=f"Unrecoverable error type: {error_type.value}",
                failed_step_index=failed_step_index,
                failed_tool=failed_tool,
                replan_confidence=0.0,
            )

        # Strategy 1: INSERT preparatory steps
        prep_key = (error_type, domain)
        prep_steps = _PREP_STEPS.get(prep_key)
        if prep_steps and count == 0:
            return ReplanDecision(
                action=ReplanAction.INSERT,
                reason=(
                    f"Inserting {len(prep_steps)} preparatory step(s) before "
                    f"retrying {failed_tool} (error: {error_type.value})"
                ),
                new_steps=list(prep_steps),
                failed_step_index=failed_step_index,
                failed_tool=failed_tool,
                replan_confidence=0.6,
            )

        # Strategy 2: REPLACE with alternative approach
        replacements = _REPLACEMENT_MAP.get(failed_tool)
        if replacements:
            return ReplanDecision(
                action=ReplanAction.REPLACE,
                reason=(
                    f"Replacing {failed_tool} with alternative approach "
                    f"(error: {error_type.value})"
                ),
                new_steps=list(replacements),
                failed_step_index=failed_step_index,
                failed_tool=failed_tool,
                replan_confidence=0.4,
            )

        # Strategy 3: REDUCE — if there are remaining steps, try to skip
        if remaining_steps and len(remaining_steps) > 1:
            return ReplanDecision(
                action=ReplanAction.REDUCE,
                reason=(
                    f"Cannot recover {failed_tool}. Reducing scope by "
                    f"skipping to next step."
                ),
                new_steps=[],
                failed_step_index=failed_step_index,
                failed_tool=failed_tool,
                replan_confidence=0.2,
            )

        # Strategy 4: ABORT
        return ReplanDecision(
            action=ReplanAction.ABORT,
            reason=(
                f"No replan strategy available for {failed_tool} "
                f"with error type {error_type.value}"
            ),
            failed_step_index=failed_step_index,
            failed_tool=failed_tool,
            replan_confidence=0.0,
        )

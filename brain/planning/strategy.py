"""
brain.planning.strategy — Strategy layer for level-based decision making.

The strategy layer operates at two levels:

Level 1 (Strategy): High-level patterns like "search → extract → summarize"
Level 2 (Tools): Specific browser tools that implement each strategy step

Strategies are deterministic workflow templates selected by intent classification.
The planner selects a strategy, then the PlannerBridge resolves each step
to quality-ranked tools via the CapabilityRegistry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class StrategyType(str, Enum):
    SEARCH_EXTRACT = "search_extract"
    LOGIN_NAVIGATE = "login_navigate"
    FORM_FILL_SUBMIT = "form_fill_submit"
    SCRAPE_COLLECT = "scrape_collect"
    MULTI_TAB_COMPARE = "multi_tab_compare"
    NAVIGATE_AND_READ = "navigate_and_read"
    CUSTOM = "custom"


@dataclass
class StrategyStep:
    """A single step within a strategy, defined at the operation level."""
    domain: str        # e.g., "browser_nav", "browser_dom"
    operation: str     # e.g., "search_google", "click_element"
    description: str
    is_mutating: bool = True
    required: bool = True   # If False, failure doesn't abort strategy
    # Parameter template — keys are param names, values are
    # either literal values or "{variable_name}" references
    param_template: dict[str, Any] = field(default_factory=dict)


@dataclass
class Strategy:
    """A reusable workflow pattern composed of ordered steps."""
    strategy_type: StrategyType
    name: str
    description: str
    steps: list[StrategyStep]
    # Minimum confidence to proceed without human review
    min_confidence: float = 0.6
    # Expected overall success rate based on component reliability
    expected_reliability: float = 0.7

    def to_raw_steps(self, variables: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert strategy steps into raw planner-bridge-compatible dicts.

        Variable substitution: replaces {variable_name} in param_template
        with values from the variables dict.
        """
        raw_steps = []
        for step in self.steps:
            tool_name = f"{step.domain}_{step.operation}"
            params = {}
            for k, v in step.param_template.items():
                if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                    var_name = v[1:-1]
                    params[k] = variables.get(var_name, v)
                else:
                    params[k] = v

            raw_steps.append({
                "tool": tool_name,
                "parameters": params,
                "description": step.description,
                "is_mutating": step.is_mutating,
            })
        return raw_steps


# ── Built-in strategy library ──

STRATEGY_LIBRARY: dict[StrategyType, Strategy] = {
    StrategyType.SEARCH_EXTRACT: Strategy(
        strategy_type=StrategyType.SEARCH_EXTRACT,
        name="Search and Extract",
        description="Search the web for information and extract results",
        min_confidence=0.65,
        expected_reliability=0.8,
        steps=[
            StrategyStep(
                domain="browser_nav",
                operation="search_google",
                description="Search Google for query",
                is_mutating=True,
                param_template={"query": "{query}"},
            ),
            StrategyStep(
                domain="browser_wait",
                operation="wait_for_page_load",
                description="Wait for search results to load",
                is_mutating=False,
                param_template={"timeout": 5000},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="get_page_text",
                description="Extract text from results page",
                is_mutating=False,
                required=False,
                param_template={},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="get_links",
                description="Extract links from results page",
                is_mutating=False,
                required=False,
                param_template={},
            ),
        ],
    ),

    StrategyType.LOGIN_NAVIGATE: Strategy(
        strategy_type=StrategyType.LOGIN_NAVIGATE,
        name="Login and Navigate",
        description="Authenticate and navigate to a target page",
        min_confidence=0.5,
        expected_reliability=0.65,
        steps=[
            StrategyStep(
                domain="browser_nav",
                operation="navigate_to_url",
                description="Navigate to login page",
                is_mutating=True,
                param_template={"url": "{login_url}"},
            ),
            StrategyStep(
                domain="browser_wait",
                operation="wait_for_page_load",
                description="Wait for login page to load",
                is_mutating=False,
                param_template={"timeout": 5000},
            ),
            StrategyStep(
                domain="browser_auth",
                operation="login_with_credentials",
                description="Fill and submit login form",
                is_mutating=True,
                param_template={
                    "username": "{username}",
                    "password": "{password}",
                },
            ),
            StrategyStep(
                domain="browser_wait",
                operation="wait_for_page_load",
                description="Wait for post-login redirect",
                is_mutating=False,
                param_template={"timeout": 10000},
            ),
            StrategyStep(
                domain="browser_nav",
                operation="navigate_to_url",
                description="Navigate to target page",
                is_mutating=True,
                param_template={"url": "{target_url}"},
            ),
        ],
    ),

    StrategyType.FORM_FILL_SUBMIT: Strategy(
        strategy_type=StrategyType.FORM_FILL_SUBMIT,
        name="Form Fill and Submit",
        description="Navigate to a form, fill fields, and submit",
        min_confidence=0.55,
        expected_reliability=0.7,
        steps=[
            StrategyStep(
                domain="browser_nav",
                operation="navigate_to_url",
                description="Navigate to form page",
                is_mutating=True,
                param_template={"url": "{form_url}"},
            ),
            StrategyStep(
                domain="browser_wait",
                operation="wait_for_page_load",
                description="Wait for form to load",
                is_mutating=False,
                param_template={"timeout": 5000},
            ),
            StrategyStep(
                domain="browser_dom",
                operation="fill_form_fields",
                description="Fill form fields with provided data",
                is_mutating=True,
                param_template={"fields": "{form_data}"},
            ),
            StrategyStep(
                domain="browser_dom",
                operation="submit_form",
                description="Submit the form",
                is_mutating=True,
                param_template={},
            ),
            StrategyStep(
                domain="browser_wait",
                operation="wait_for_page_load",
                description="Wait for form submission result",
                is_mutating=False,
                param_template={"timeout": 10000},
            ),
        ],
    ),

    StrategyType.SCRAPE_COLLECT: Strategy(
        strategy_type=StrategyType.SCRAPE_COLLECT,
        name="Scrape and Collect",
        description="Navigate to a page and extract structured data",
        min_confidence=0.7,
        expected_reliability=0.85,
        steps=[
            StrategyStep(
                domain="browser_nav",
                operation="navigate_to_url",
                description="Navigate to target page",
                is_mutating=True,
                param_template={"url": "{url}"},
            ),
            StrategyStep(
                domain="browser_wait",
                operation="wait_for_page_load",
                description="Wait for page to fully load",
                is_mutating=False,
                param_template={"timeout": 10000},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="get_page_text",
                description="Extract page text content",
                is_mutating=False,
                param_template={},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="get_links",
                description="Extract all links",
                is_mutating=False,
                required=False,
                param_template={},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="screenshot",
                description="Capture screenshot for visual record",
                is_mutating=False,
                required=False,
                param_template={},
            ),
        ],
    ),

    StrategyType.NAVIGATE_AND_READ: Strategy(
        strategy_type=StrategyType.NAVIGATE_AND_READ,
        name="Navigate and Read",
        description="Simple page visit and content extraction",
        min_confidence=0.75,
        expected_reliability=0.9,
        steps=[
            StrategyStep(
                domain="browser_nav",
                operation="navigate_to_url",
                description="Navigate to URL",
                is_mutating=True,
                param_template={"url": "{url}"},
            ),
            StrategyStep(
                domain="browser_wait",
                operation="wait_for_page_load",
                description="Wait for page load",
                is_mutating=False,
                param_template={"timeout": 5000},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="get_title",
                description="Get page title",
                is_mutating=False,
                param_template={},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="get_page_text",
                description="Get page text content",
                is_mutating=False,
                param_template={},
            ),
        ],
    ),

    StrategyType.MULTI_TAB_COMPARE: Strategy(
        strategy_type=StrategyType.MULTI_TAB_COMPARE,
        name="Multi-Tab Compare",
        description="Open multiple pages in tabs for comparison",
        min_confidence=0.6,
        expected_reliability=0.7,
        steps=[
            StrategyStep(
                domain="browser_nav",
                operation="navigate_to_url",
                description="Open first URL",
                is_mutating=True,
                param_template={"url": "{url_1}"},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="get_page_text",
                description="Extract first page content",
                is_mutating=False,
                param_template={},
            ),
            StrategyStep(
                domain="browser_tab",
                operation="new_tab",
                description="Open new tab for second URL",
                is_mutating=True,
                param_template={},
            ),
            StrategyStep(
                domain="browser_nav",
                operation="navigate_to_url",
                description="Navigate to second URL in new tab",
                is_mutating=True,
                param_template={"url": "{url_2}"},
            ),
            StrategyStep(
                domain="browser_extract",
                operation="get_page_text",
                description="Extract second page content",
                is_mutating=False,
                param_template={},
            ),
        ],
    ),
}


class StrategySelector:
    """Select and instantiate strategies from the library.

    Intent classification is keyword-based (deterministic).
    The LLM is NOT involved in strategy selection.
    """

    # Intent → strategy type mapping (keyword-based)
    _INTENT_KEYWORDS: dict[str, StrategyType] = {
        "search": StrategyType.SEARCH_EXTRACT,
        "find": StrategyType.SEARCH_EXTRACT,
        "look up": StrategyType.SEARCH_EXTRACT,
        "google": StrategyType.SEARCH_EXTRACT,
        "login": StrategyType.LOGIN_NAVIGATE,
        "sign in": StrategyType.LOGIN_NAVIGATE,
        "authenticate": StrategyType.LOGIN_NAVIGATE,
        "fill form": StrategyType.FORM_FILL_SUBMIT,
        "submit form": StrategyType.FORM_FILL_SUBMIT,
        "fill out": StrategyType.FORM_FILL_SUBMIT,
        "scrape": StrategyType.SCRAPE_COLLECT,
        "extract data": StrategyType.SCRAPE_COLLECT,
        "collect": StrategyType.SCRAPE_COLLECT,
        "crawl": StrategyType.SCRAPE_COLLECT,
        "compare": StrategyType.MULTI_TAB_COMPARE,
        "side by side": StrategyType.MULTI_TAB_COMPARE,
        "go to": StrategyType.NAVIGATE_AND_READ,
        "visit": StrategyType.NAVIGATE_AND_READ,
        "open": StrategyType.NAVIGATE_AND_READ,
        "read": StrategyType.NAVIGATE_AND_READ,
        "navigate": StrategyType.NAVIGATE_AND_READ,
    }

    def classify_intent(self, intent: str) -> Optional[StrategyType]:
        """Classify a natural-language intent into a strategy type.

        Returns None if no strategy matches.
        """
        intent_lower = intent.lower()
        for keyword, strategy_type in self._INTENT_KEYWORDS.items():
            if keyword in intent_lower:
                return strategy_type
        return None

    def select(self, intent: str) -> Optional[Strategy]:
        """Select a strategy for the given intent.

        Returns None if no strategy matches.
        """
        strategy_type = self.classify_intent(intent)
        if strategy_type is None:
            return None
        return STRATEGY_LIBRARY.get(strategy_type)

    def get_strategy(self, strategy_type: StrategyType) -> Optional[Strategy]:
        """Get a specific strategy by type."""
        return STRATEGY_LIBRARY.get(strategy_type)

    def list_strategies(self) -> list[dict[str, Any]]:
        """List all available strategies with metadata."""
        return [
            {
                "type": s.strategy_type.value,
                "name": s.name,
                "description": s.description,
                "step_count": len(s.steps),
                "min_confidence": s.min_confidence,
                "expected_reliability": s.expected_reliability,
            }
            for s in STRATEGY_LIBRARY.values()
        ]

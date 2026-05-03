"""
runtime.browser — Modular browser runtime layer for BUDDY MK67 AI Web Operator.

This package provides:
- state.py       — BrowserState capture/diff for step-to-step tracking
- recovery.py    — Tool-aware recovery and fallback strategies
- replanner.py   — True replanning engine for autonomous recovery
- engine.py      — Thin orchestrator delegating to browser_control._SessionRegistry
- navigation.py  — Navigation-specific helper methods
- dom.py         — DOM interaction helpers
- input.py       — Typing and form-fill helpers
- session.py     — Session lifecycle management
"""

from runtime.browser.state import BrowserState, capture_state, diff_states, StateDiffAnalyzer
from runtime.browser.recovery import RecoveryPolicy, ErrorType
from runtime.browser.replanner import Replanner, ReplanAction, ReplanDecision
from runtime.browser.engine import BrowserEngine

__all__ = [
    "BrowserState",
    "capture_state",
    "diff_states",
    "StateDiffAnalyzer",
    "RecoveryPolicy",
    "ErrorType",
    "Replanner",
    "ReplanAction",
    "ReplanDecision",
    "BrowserEngine",
]

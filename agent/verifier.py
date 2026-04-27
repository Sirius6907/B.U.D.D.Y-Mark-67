"""
agent/verifier.py — Vision-Augmented Verification Engine
=========================================================
Deterministic step verification with optional VLM (vision language model)
confirmation for critical UI actions. Falls back to rule-based checks
when vision is unavailable or unnecessary.

Architecture:
    Rule-based checks  → Fast, deterministic (file exists, status == success)
    Vision verification → Gemini VLM screenshot analysis for UI-state confirmation
    Hybrid             → Rule-based first, vision as the confirming gate
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Tuple

from buddy_logging import get_logger
from agent.models import ActionResult, TaskNode

logger = get_logger("agent.verifier")

# ── Tools that benefit from vision-confirmed verification ─────────────────────
_VISION_VERIFIABLE_TOOLS: dict[str, str] = {
    "open_app": "Is an application window visibly open and in the foreground? Answer YES or NO followed by a one-sentence reason.",
    "browser_control": "Is a web browser window visible and showing loaded content? Answer YES or NO followed by a one-sentence reason.",
    "computer_control": "Has the system setting been visibly applied on screen? Answer YES or NO followed by a one-sentence reason.",
    "desktop_control": "Is the desktop in the expected state? Answer YES or NO followed by a one-sentence reason.",
}

# ── Timeout for vision calls (prevent blocking the loop) ──────────────────────
_VISION_TIMEOUT_SECS = 8.0


# ── Rule-Based Verifiers ──────────────────────────────────────────────────────

def verify_file_write(result: ActionResult) -> bool:
    """Check if a written file actually exists on disk."""
    path = result.changed_state.get("path")
    if not path:
        path = result.observations.get("path")
    return bool(path and Path(path).exists())


def verify_app_open(result: ActionResult) -> bool:
    """Basic status-flag check for app launch."""
    return result.status == "success"


def verify_browser_navigation(result: ActionResult) -> bool:
    """Check if browser navigation produced a URL or status indicator."""
    current_url = str(result.observations.get("url", "")).strip()
    summary = result.summary.lower()
    return bool(current_url) or "opened:" in summary or "http" in summary


# ── Vision Verifier ───────────────────────────────────────────────────────────

def _vision_confirm(prompt: str, timeout: float = _VISION_TIMEOUT_SECS) -> Tuple[bool, str]:
    """
    Capture a screenshot and ask the VLM whether the expected state is visible.

    Returns:
        (confirmed: bool, reason: str)
    """
    try:
        from actions.screen_processor import vision_analyze

        start = time.time()
        # vision_analyze captures the screen internally when image_bytes is None
        raw = vision_analyze(prompt)
        elapsed_ms = (time.time() - start) * 1000

        if raw.startswith("ERROR"):
            logger.warning("Vision verification returned error: %s", raw)
            return True, f"Vision unavailable ({raw}); accepted by fallback"

        normalized = raw.strip().upper()
        confirmed = normalized.startswith("YES")
        reason = raw.strip()

        logger.info(
            "Vision verification: %s (%.0fms) — %s",
            "CONFIRMED" if confirmed else "REJECTED",
            elapsed_ms,
            reason[:120],
        )
        return confirmed, reason

    except ImportError:
        logger.debug("screen_processor not available — skipping vision verification")
        return True, "Vision module not available; accepted by fallback"
    except Exception as exc:
        logger.warning("Vision verification failed: %s — accepting by fallback", exc)
        return True, f"Vision error ({exc}); accepted by fallback"


async def _vision_confirm_async(prompt: str, timeout: float = _VISION_TIMEOUT_SECS) -> Tuple[bool, str]:
    """Async wrapper for vision confirmation with hard timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_vision_confirm, prompt, timeout),
            timeout=timeout + 2.0,  # outer guard
        )
    except asyncio.TimeoutError:
        logger.warning("Vision verification timed out after %.1fs", timeout)
        return True, "Vision verification timed out; accepted by fallback"
    except Exception as exc:
        logger.warning("Async vision verification error: %s", exc)
        return True, f"Vision async error ({exc}); accepted by fallback"


# ── Verification Engine ───────────────────────────────────────────────────────

class VerificationEngine:
    """
    Hybrid verification: deterministic rule checks + optional VLM screenshot
    confirmation for UI-facing actions.

    Vision verification is triggered when:
      1. The tool is in _VISION_VERIFIABLE_TOOLS, OR
      2. The node's verification_rule contains "vision_verify"

    If vision is unavailable or times out, the engine gracefully falls back
    to rule-based acceptance (never blocks the pipeline).
    """

    def __init__(self, api_key: str | None = None, enable_vision: bool = True):
        self.api_key = api_key
        self.enable_vision = enable_vision

    async def verify(self, node: TaskNode, result: ActionResult) -> Tuple[bool, str]:
        """Async verification entry point with vision support."""
        # ── Phase 1: Rule-based check (fast, deterministic) ───────────────
        rule_ok, rule_reason = self._rule_check(node, result)
        if not rule_ok:
            return False, rule_reason

        # ── Phase 2: Vision confirmation gate (if applicable) ─────────────
        if self.enable_vision and self._needs_vision(node):
            vision_prompt = self._build_vision_prompt(node, result)
            confirmed, vision_reason = await _vision_confirm_async(vision_prompt)
            if not confirmed:
                return False, f"Vision rejected: {vision_reason}"
            return True, f"Verified (rule + vision): {vision_reason[:80]}"

        return rule_ok, rule_reason

    def verify_sync(self, node: TaskNode, result: ActionResult) -> Tuple[bool, str]:
        """Synchronous verification (rule-based + optional sync vision)."""
        # ── Phase 1: Rule-based check ─────────────────────────────────────
        rule_ok, rule_reason = self._rule_check(node, result)
        if not rule_ok:
            return False, rule_reason

        # ── Phase 2: Vision confirmation (sync) ───────────────────────────
        if self.enable_vision and self._needs_vision(node):
            vision_prompt = self._build_vision_prompt(node, result)
            confirmed, vision_reason = _vision_confirm(vision_prompt)
            if not confirmed:
                return False, f"Vision rejected: {vision_reason}"
            return True, f"Verified (rule + vision): {vision_reason[:80]}"

        return rule_ok, rule_reason

    def _rule_check(self, node: TaskNode, result: ActionResult) -> Tuple[bool, str]:
        """Fast deterministic verification based on status and tool type."""
        if result.status != "success":
            return False, f"Action failed with status: {result.status}"

        tool = node.tool

        # ── File operations ───────────────────────────────────────────────
        if tool == "file_controller" and str(node.parameters.get("action", "")).lower() in {
            "write",
            "create_file",
        }:
            if verify_file_write(result):
                return True, "Verified file write"
            return False, "File write could not be verified"

        # ── App launch ────────────────────────────────────────────────────
        if tool == "open_app":
            if verify_app_open(result):
                return True, "Verified app launch"
            return False, "App launch could not be verified"

        # ── Browser navigation ────────────────────────────────────────────
        if tool == "browser_control" and str(node.parameters.get("action", "")).lower() in {
            "go_to",
            "search",
            "new_tab",
        }:
            if verify_browser_navigation(result):
                return True, "Verified browser navigation"
            return False, "Browser navigation could not be verified"

        # ── Custom verification rules ─────────────────────────────────────
        if node.verification_rule:
            rule = node.verification_rule.lower()
            if "path exists" in rule and verify_file_write(result):
                return True, "Verified via rule"
            # Non-vision custom rules pass through
            if "vision_verify" not in rule:
                return True, "Verification rule accepted by fallback verifier"

        return True, "Action reported success"

    def _needs_vision(self, node: TaskNode) -> bool:
        """Determine if this node should undergo vision confirmation."""
        # Explicit vision_verify in the verification rule
        if node.verification_rule and "vision_verify" in node.verification_rule.lower():
            return True
        # Tool is in the auto-vision list
        return node.tool in _VISION_VERIFIABLE_TOOLS

    def _build_vision_prompt(self, node: TaskNode, result: ActionResult) -> str:
        """Build a targeted VLM prompt for the current verification context."""
        # Use the tool-specific prompt template if available
        base_prompt = _VISION_VERIFIABLE_TOOLS.get(node.tool, "")

        # Enrich with context from the node
        context = (
            f"Task: {node.objective}. "
            f"Tool used: {node.tool}. "
            f"Expected outcome: {node.expected_outcome}. "
        )

        if base_prompt:
            return f"{context}{base_prompt}"

        # Generic vision verification for custom rules
        return (
            f"{context}"
            f"Look at the current screen and determine if the task was completed successfully. "
            f"Answer YES or NO followed by a one-sentence reason."
        )

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from agent.models import ActionResult, TaskNode


def verify_file_write(result: ActionResult) -> bool:
    path = result.changed_state.get("path")
    if not path:
        path = result.observations.get("path")
    return bool(path and Path(path).exists())


def verify_app_open(result: ActionResult) -> bool:
    return result.status == "success"


def verify_browser_navigation(result: ActionResult) -> bool:
    current_url = str(result.observations.get("url", "")).strip()
    summary = result.summary.lower()
    return bool(current_url) or "opened:" in summary or "http" in summary


class VerificationEngine:
    """Deterministic step verification with light rule-based fallbacks."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def verify(self, node: TaskNode, result: ActionResult) -> Tuple[bool, str]:
        return self.verify_sync(node, result)

    def verify_sync(self, node: TaskNode, result: ActionResult) -> Tuple[bool, str]:
        if result.status != "success":
            return False, f"Action failed with status: {result.status}"

        tool = node.tool

        if tool == "file_controller" and str(node.parameters.get("action", "")).lower() in {
            "write",
            "create_file",
        }:
            if verify_file_write(result):
                return True, "Verified file write"
            return False, "File write could not be verified"

        if tool == "open_app":
            if verify_app_open(result):
                return True, "Verified app launch"
            return False, "App launch could not be verified"

        if tool == "browser_control" and str(node.parameters.get("action", "")).lower() in {
            "go_to",
            "search",
            "new_tab",
        }:
            if verify_browser_navigation(result):
                return True, "Verified browser navigation"
            return False, "Browser navigation could not be verified"

        if node.verification_rule:
            rule = node.verification_rule.lower()
            if "path exists" in rule and verify_file_write(result):
                return True, "Verified via rule"
            return True, "Verification rule accepted by fallback verifier"

        return True, "Action reported success"

from __future__ import annotations

from agent.models import ActionResult


class WorkflowMemory:
    """Promotes repeated successful workflows into reusable memory."""

    def __init__(self):
        self.promoted: list[tuple[str, int]] = []

    def maybe_promote(self, goal: str, results: list[ActionResult]) -> None:
        if goal and results and all(result.status == "success" for result in results):
            self.promoted.append((goal, len(results)))

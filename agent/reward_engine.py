from __future__ import annotations

from typing import Any


class RewardEngine:
    def score(self, result: Any) -> float:
        status = getattr(result, "status", None) or result.get("status", "")
        if status == "success":
            return 1.0
        if status == "partial":
            return 0.25
        if status == "pending_approval":
            return -0.1
        return -1.0

    def update_confidence(self, confidence: float, reward_score: float) -> float:
        return max(0.0, min(1.0, confidence + (reward_score * 0.1)))

from __future__ import annotations

from typing import Iterable


class PathOptimizer:
    def score(self, *, speed: float, success_rate: float, confidence: float, risk: float, latency: float) -> float:
        return speed + success_rate + confidence - risk - latency

    def best(self, candidates: Iterable[dict]) -> dict | None:
        best_candidate = None
        best_score = float("-inf")
        for candidate in candidates:
            score = self.score(
                speed=float(candidate.get("speed", 0.0)),
                success_rate=float(candidate.get("success_rate", 0.0)),
                confidence=float(candidate.get("confidence", 0.0)),
                risk=float(candidate.get("risk", 0.0)),
                latency=float(candidate.get("latency", 0.0)),
            )
            if score > best_score:
                best_score = score
                best_candidate = {**candidate, "path_score": score}
        return best_candidate

from __future__ import annotations


def score_plan_confidence(
    *,
    alias_match: float,
    preconditions_satisfied: bool,
    verification_mode: str,
    native_first: bool,
    telemetry_success_rate: float,
    ambiguity: float,
) -> float:
    score = alias_match * 0.35 + telemetry_success_rate * 0.25 + (0.15 if native_first else 0.0)
    score += 0.15 if preconditions_satisfied else -0.20
    score += 0.10 if verification_mode == "verified_where_practical" else 0.0
    score -= ambiguity * 0.25
    return max(0.0, min(1.0, round(score, 4)))

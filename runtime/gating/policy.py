from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GateDecision:
    status: str
    reason: str = ""


def evaluate_gate(risk_level: str, dry_run: bool) -> GateDecision:
    if dry_run:
        return GateDecision(status="allowed", reason="dry_run")
    if risk_level == "HIGH":
        return GateDecision(status="approval_required", reason="high_risk")
    if risk_level == "CRITICAL":
        return GateDecision(status="blocked", reason="critical_risk")
    return GateDecision(status="allowed", reason="auto")

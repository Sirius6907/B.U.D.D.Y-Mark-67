from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent.models import RiskTier, TaskNode


class PolicyDecision(str, Enum):
    AUTO_EXECUTE = "auto_execute"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"


RISK_ORDER: dict[RiskTier, int] = {
    RiskTier.TIER_0: 0,
    RiskTier.TIER_1: 1,
    RiskTier.TIER_2: 2,
    RiskTier.TIER_3: 3,
}


@dataclass(slots=True)
class PolicyCheck:
    allowed: bool
    decision: PolicyDecision
    reason: str


def _requires_sensitive_approval(node: TaskNode) -> bool:
    if node.tool == "send_message":
        return True

    if node.tool == "computer_control" and str(node.parameters.get("action", "")).lower() in {
        "shutdown",
        "restart",
        "sign_out",
        "log_out",
    }:
        return True

    if node.tool == "file_controller" and str(node.parameters.get("action", "")).lower() in {
        "delete",
    }:
        return True

    if node.tool == "screen_recorder" and str(node.parameters.get("action", "")).lower() in {
        "start",
    }:
        return True

    if node.tool == "vault_manager" and str(node.parameters.get("action", "")).lower() in {
        "encrypt",
        "decrypt",
    }:
        return True

    if node.tool == "backup_manager" and str(node.parameters.get("action", "")).lower() in {
        "backup_folder",
    }:
        return True

    if node.tool == "recovery_manager" and str(node.parameters.get("action", "")).lower() in {
        "create_restore_point",
    }:
        return True

    if node.tool == "process_shield" and str(node.parameters.get("action", "")).lower() in {
        "kill_rogue",
    }:
        return True

    if node.tool == "firewall_manager" and str(node.parameters.get("action", "")).lower() in {
        "lockdown",
    }:
        return True

    return False


def decide_policy(
    node: TaskNode,
    confidence: float = 1.0,
    auto_tier: RiskTier = RiskTier.TIER_1,
) -> PolicyDecision:
    if _requires_sensitive_approval(node):
        return PolicyDecision.REQUIRE_APPROVAL

    if node.risk_tier == RiskTier.TIER_3:
        return PolicyDecision.REQUIRE_APPROVAL

    if node.risk_tier == RiskTier.TIER_2 and confidence < 0.85:
        return PolicyDecision.REQUIRE_APPROVAL

    if RISK_ORDER[node.risk_tier] > RISK_ORDER[auto_tier]:
        return PolicyDecision.REQUIRE_APPROVAL

    return PolicyDecision.AUTO_EXECUTE


class PolicyEngine:
    """Supervision policy for runtime task execution."""

    def __init__(self, auto_tier: RiskTier = RiskTier.TIER_1):
        self.auto_approval_threshold = auto_tier

    def check_node(self, node: TaskNode, confidence: float = 1.0) -> PolicyCheck:
        decision = decide_policy(
            node=node,
            confidence=confidence,
            auto_tier=self.auto_approval_threshold,
        )
        if decision is PolicyDecision.AUTO_EXECUTE:
            return PolicyCheck(True, decision, "Policy OK")
        if decision is PolicyDecision.REQUIRE_APPROVAL:
            return PolicyCheck(False, decision, f"Approval required for {node.tool}")
        return PolicyCheck(False, decision, "Policy blocked action")

    def set_threshold(self, tier: RiskTier) -> None:
        self.auto_approval_threshold = tier

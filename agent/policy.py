from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Set

from agent.models import (
    DANGEROUS_SCOPES,
    DEFAULT_GRANTED_SCOPES,
    PermissionScope,
    RiskTier,
    TaskNode,
)


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


# ── Tool → Required Scopes Map ──────────────────────────────────────────────
# Every tool declares what capabilities it *needs*. The engine resolves
# required scopes from the node's own `required_scopes` OR this map.

TOOL_SCOPE_MAP: dict[str, set[PermissionScope]] = {
    # File operations
    "file_controller":      {PermissionScope.CAN_READ_FILES, PermissionScope.CAN_WRITE_FILES},
    "file_search":          {PermissionScope.CAN_READ_FILES},
    "pdf_reader":           {PermissionScope.CAN_READ_FILES},
    # Screen & Input
    "computer_control":     {PermissionScope.CAN_CONTROL_INPUT, PermissionScope.CAN_MODIFY_SYSTEM},
    "keyboard_controller":  {PermissionScope.CAN_CONTROL_INPUT},
    "screenshot":           {PermissionScope.CAN_READ_SCREEN},
    "screen_reader":        {PermissionScope.CAN_READ_SCREEN},
    "screen_recorder":      {PermissionScope.CAN_RECORD_SCREEN},
    # Apps
    "open_app":             {PermissionScope.CAN_LAUNCH_APP},
    # Web
    "browser_control":      {PermissionScope.CAN_BROWSE_WEB},
    "web_search":           {PermissionScope.CAN_BROWSE_WEB},
    # System
    "process_shield":       {PermissionScope.CAN_MODIFY_SYSTEM},
    "firewall_manager":     {PermissionScope.CAN_NETWORK_ADMIN},
    "bluetooth_manager":    {PermissionScope.CAN_MODIFY_SYSTEM},
    "recovery_manager":     {PermissionScope.CAN_MODIFY_SYSTEM},
    "backup_manager":       {PermissionScope.CAN_WRITE_FILES},
    # Vault
    "vault_manager":        {PermissionScope.CAN_ACCESS_VAULT},
    # Messaging & External
    "send_message":         {PermissionScope.CAN_SEND_MESSAGES},
    "email_sender":         {PermissionScope.CAN_SEND_MESSAGES},
    # Career / Public
    "linkedin_post":        {PermissionScope.CAN_POST_PUBLICLY},
    "resume_submit":        {PermissionScope.CAN_POST_PUBLICLY},
    # Shell
    "shell_command":        {PermissionScope.CAN_EXECUTE_SHELL},
    "run_script":           {PermissionScope.CAN_EXECUTE_SHELL},
    # Kali / Security Tools (adapter resolves per-tool scopes dynamically)
    "kali_tool":            {PermissionScope.CAN_EXECUTE_SHELL},
}

# Action-level overrides: when a specific tool+action combo upgrades scope
TOOL_ACTION_SCOPE_OVERRIDES: dict[tuple[str, str], set[PermissionScope]] = {
    ("file_controller", "delete"):       {PermissionScope.CAN_DELETE_FILES},
    ("computer_control", "shutdown"):    {PermissionScope.CAN_MODIFY_SYSTEM},
    ("computer_control", "restart"):     {PermissionScope.CAN_MODIFY_SYSTEM},
    ("computer_control", "sign_out"):    {PermissionScope.CAN_MODIFY_SYSTEM},
    ("computer_control", "log_out"):     {PermissionScope.CAN_MODIFY_SYSTEM},
    ("open_app", "run_as_admin"):        {PermissionScope.CAN_EXECUTE_SHELL},
}


@dataclass(slots=True)
class PolicyCheck:
    allowed: bool
    decision: PolicyDecision
    reason: str
    missing_scopes: list[str] = field(default_factory=list)
    dangerous_scopes_hit: list[str] = field(default_factory=list)


def _resolve_required_scopes(node: TaskNode) -> set[PermissionScope]:
    """Resolve the full set of required scopes for a node."""
    scopes: set[PermissionScope] = set()

    # 1. Node-declared scopes (highest priority)
    for s in node.required_scopes:
        try:
            scopes.add(PermissionScope(s))
        except ValueError:
            pass

    # 2. Tool-level map
    tool_scopes = TOOL_SCOPE_MAP.get(node.tool, set())
    scopes.update(tool_scopes)

    # 3. Action-level overrides
    action = str(node.parameters.get("action", "")).lower()
    override_key = (node.tool, action)
    if override_key in TOOL_ACTION_SCOPE_OVERRIDES:
        scopes.update(TOOL_ACTION_SCOPE_OVERRIDES[override_key])

    # 4. Special case: open_app with run_as_admin
    if node.tool == "open_app" and bool(node.parameters.get("run_as_admin")):
        scopes.add(PermissionScope.CAN_EXECUTE_SHELL)

    return scopes


def _requires_sensitive_approval(node: TaskNode) -> bool:
    """Legacy sensitive-action checks — preserved for backward compatibility."""
    if node.tool == "computer_control" and str(node.parameters.get("action", "")).lower() in {
        "shutdown", "restart", "sign_out", "log_out",
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
        "encrypt", "decrypt",
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

    if node.tool == "open_app" and bool(node.parameters.get("run_as_admin")):
        return True

    if node.tool == "send_message" and str(node.parameters.get("mode", "send")).lower() != "open_chat":
        return True

    if node.tool == "bluetooth_manager" and str(node.parameters.get("action", "")).lower() in {
        "toggle",
    }:
        return True

    return False


def load_user_grants(config_path: Path | None = None) -> set[PermissionScope]:
    """Load user-override grants from a YAML/JSON config file.

    Expected format (JSON):
        {"granted_scopes": ["can_write_files", "can_send_messages"]}

    Returns the default grant set if no config or config is unreadable.
    """
    if config_path is None:
        config_path = Path.home() / ".buddy" / "scopes.json"
    if not config_path.exists():
        return set(DEFAULT_GRANTED_SCOPES)
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        granted = set(DEFAULT_GRANTED_SCOPES)
        for s in data.get("granted_scopes", []):
            try:
                granted.add(PermissionScope(s))
            except ValueError:
                pass
        return granted
    except Exception:
        return set(DEFAULT_GRANTED_SCOPES)


def decide_policy(
    node: TaskNode,
    confidence: float = 1.0,
    auto_tier: RiskTier = RiskTier.TIER_1,
    granted_scopes: set[PermissionScope] | None = None,
) -> PolicyCheck:
    """Three-layer policy decision: Scopes × Sensitive-actions × RiskTier.

    Returns a full PolicyCheck with decision, missing scopes, and danger flags.
    """
    if granted_scopes is None:
        granted_scopes = set(DEFAULT_GRANTED_SCOPES)

    required = _resolve_required_scopes(node)
    missing = required - granted_scopes
    dangerous_hit = required & DANGEROUS_SCOPES

    # ── Layer 1: Scope check — missing scopes = BLOCK ────────────────────
    if missing:
        return PolicyCheck(
            allowed=False,
            decision=PolicyDecision.BLOCK,
            reason=f"Missing scopes: {', '.join(s.value for s in sorted(missing, key=lambda x: x.value))}",
            missing_scopes=[s.value for s in missing],
        )

    # ── Layer 2: Dangerous scope intersection = REQUIRE_APPROVAL ─────────
    if dangerous_hit:
        return PolicyCheck(
            allowed=False,
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason=f"Dangerous scopes active: {', '.join(s.value for s in sorted(dangerous_hit, key=lambda x: x.value))}",
            dangerous_scopes_hit=[s.value for s in dangerous_hit],
        )

    # ── Layer 3: Legacy sensitive-action checks ──────────────────────────
    if _requires_sensitive_approval(node):
        return PolicyCheck(
            allowed=False,
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason=f"Sensitive action requires approval for {node.tool}",
        )

    # ── Layer 4: RiskTier gating ─────────────────────────────────────────
    if node.risk_tier == RiskTier.TIER_3:
        return PolicyCheck(
            allowed=False,
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason=f"TIER_3 action: {node.tool}",
        )

    if node.risk_tier == RiskTier.TIER_2 and confidence < 0.85:
        return PolicyCheck(
            allowed=False,
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason=f"TIER_2 with low confidence ({confidence:.2f})",
        )

    if RISK_ORDER[node.risk_tier] > RISK_ORDER[auto_tier]:
        return PolicyCheck(
            allowed=False,
            decision=PolicyDecision.REQUIRE_APPROVAL,
            reason=f"Risk tier {node.risk_tier.value} exceeds auto-approval threshold {auto_tier.value}",
        )

    # ── All clear ────────────────────────────────────────────────────────
    return PolicyCheck(
        allowed=True,
        decision=PolicyDecision.AUTO_EXECUTE,
        reason="Policy OK",
    )


class PolicyEngine:
    """Supervision policy for runtime task execution.

    Supports:
    - Tool-declared required scopes (TOOL_SCOPE_MAP)
    - User-override grants (~/.buddy/scopes.json)
    - RiskTier gating
    - Sensitive-action approval
    """

    def __init__(
        self,
        auto_tier: RiskTier = RiskTier.TIER_1,
        granted_scopes: set[PermissionScope] | None = None,
        scopes_config_path: Path | None = None,
    ):
        self.auto_approval_threshold = auto_tier
        if granted_scopes is not None:
            self.granted_scopes = granted_scopes
        else:
            self.granted_scopes = load_user_grants(scopes_config_path)

    def check_node(self, node: TaskNode, confidence: float = 1.0) -> PolicyCheck:
        return decide_policy(
            node=node,
            confidence=confidence,
            auto_tier=self.auto_approval_threshold,
            granted_scopes=self.granted_scopes,
        )

    def grant_scope(self, scope: PermissionScope) -> None:
        """Dynamically grant a scope at runtime."""
        self.granted_scopes.add(scope)

    def revoke_scope(self, scope: PermissionScope) -> None:
        """Dynamically revoke a scope at runtime."""
        self.granted_scopes.discard(scope)

    def set_threshold(self, tier: RiskTier) -> None:
        self.auto_approval_threshold = tier

    def get_granted_scopes(self) -> set[PermissionScope]:
        return set(self.granted_scopes)

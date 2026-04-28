"""Tests for PermissionScope, PolicyEngine scope-aware gating, and TOOL_SCOPE_MAP."""
import pytest
from agent.models import PermissionScope, TaskNode, DEFAULT_GRANTED_SCOPES, DANGEROUS_SCOPES
from agent.policy import PolicyEngine, PolicyDecision, TOOL_SCOPE_MAP


# ── Scope enum basics ──────────────────────────────────────────────
def test_scope_enum_values():
    assert len(PermissionScope) >= 14
    assert PermissionScope.CAN_READ_FILES.value == "can_read_files"
    assert PermissionScope.CAN_MODIFY_SYSTEM in DANGEROUS_SCOPES


def test_default_grants_exclude_dangerous():
    for s in DANGEROUS_SCOPES:
        assert s not in DEFAULT_GRANTED_SCOPES


# ── Helper ─────────────────────────────────────────────────────────
def _node(tool="open_app", risk="medium"):
    return TaskNode(
        node_id="t1",
        objective="test",
        tool=tool,
        parameters={},
        expected_outcome="done",
        risk=risk,
    )


# ── PolicyEngine scope checks ─────────────────────────────────────
def test_allow_with_default_scopes():
    """open_app needs CAN_LAUNCH_APP which is in DEFAULT_GRANTED_SCOPES."""
    pe = PolicyEngine()
    check = pe.check_node(_node("open_app", "low"))
    # Should at least not be BLOCK since open_app scope is in defaults
    assert check.decision in (PolicyDecision.AUTO_EXECUTE, PolicyDecision.REQUIRE_APPROVAL)


def test_block_missing_scope():
    """If user grants are empty, any tool with required scopes must block."""
    pe = PolicyEngine(granted_scopes=set())
    node = _node("shell_command", "low")
    check = pe.check_node(node)
    assert check.decision is PolicyDecision.BLOCK
    assert len(check.missing_scopes) > 0


def test_dangerous_scope_requires_approval():
    """Granting a dangerous scope should still trigger approval gating."""
    pe = PolicyEngine(granted_scopes={PermissionScope.CAN_MODIFY_SYSTEM})
    node = _node("process_shield", "low")
    check = pe.check_node(node)
    assert check.decision is PolicyDecision.REQUIRE_APPROVAL


def test_full_grant_allows():
    """Granting all scopes allows non-dangerous low-risk tools."""
    all_scopes = set(PermissionScope)
    pe = PolicyEngine(granted_scopes=all_scopes)
    node = _node("screenshot", "low")
    check = pe.check_node(node)
    assert check.decision is PolicyDecision.AUTO_EXECUTE


def test_tool_scope_map_coverage():
    """Every mapped tool should have at least one scope."""
    for tool, scopes in TOOL_SCOPE_MAP.items():
        assert len(scopes) >= 1, f"Tool {tool} has no scopes"


def test_unknown_tool_gets_handled():
    """Unknown tools should not crash the engine."""
    pe = PolicyEngine()
    node = _node("unknown_tool_xyz", "low")
    check = pe.check_node(node)
    assert check.decision in (PolicyDecision.AUTO_EXECUTE, PolicyDecision.BLOCK, PolicyDecision.REQUIRE_APPROVAL)

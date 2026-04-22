from agent.models import ActionResult, RiskTier, TaskNode
from agent.policy import PolicyDecision, PolicyEngine, decide_policy


def test_action_result_defaults_to_successful_shape():
    result = ActionResult(status="success", summary="opened chrome")

    assert result.status == "success"
    assert result.retryable is False
    assert result.needs_approval is False
    assert result.changed_state == {}


def test_task_node_carries_risk_tier_and_expected_outcome():
    node = TaskNode(
        node_id="open-browser",
        objective="Open Chrome",
        tool="open_app",
        parameters={"app_name": "Chrome"},
        expected_outcome="Chrome is focused",
        risk_tier=RiskTier.TIER_1,
    )

    assert node.risk_tier is RiskTier.TIER_1
    assert node.depends_on == []


def test_tier_1_tasks_auto_execute():
    node = TaskNode(
        node_id="open-browser",
        objective="Open browser",
        tool="open_app",
        parameters={"app_name": "Chrome"},
        expected_outcome="Browser is open",
        risk_tier=RiskTier.TIER_1,
    )

    decision = decide_policy(node, confidence=0.95)
    assert decision is PolicyDecision.AUTO_EXECUTE


def test_tier_3_tasks_always_require_approval():
    node = TaskNode(
        node_id="send-message",
        objective="Send WhatsApp message",
        tool="send_message",
        parameters={"receiver": "Alex", "message_text": "hi", "platform": "WhatsApp"},
        expected_outcome="Message sent",
        risk_tier=RiskTier.TIER_3,
    )

    decision = decide_policy(node, confidence=0.99)
    assert decision is PolicyDecision.REQUIRE_APPROVAL


def test_policy_engine_uses_explicit_check_object():
    node = TaskNode(
        node_id="shutdown-machine",
        objective="Shutdown the PC",
        tool="computer_control",
        parameters={"action": "shutdown"},
        expected_outcome="PC begins shutdown",
        risk_tier=RiskTier.TIER_2,
    )

    check = PolicyEngine().check_node(node)
    assert check.allowed is False
    assert check.decision is PolicyDecision.REQUIRE_APPROVAL

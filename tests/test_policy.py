from agent.models import RiskTier, TaskNode
from agent.policy import PolicyDecision, decide_policy


def test_send_message_requires_approval():
    node = TaskNode(
        node_id="1",
        objective="Send a WhatsApp message",
        tool="send_message",
        parameters={"receiver": "Rajaa", "message_text": "Hii", "platform": "WhatsApp"},
        expected_outcome="Message is sent",
        risk_tier=RiskTier.TIER_1,
    )

    assert decide_policy(node) is PolicyDecision.REQUIRE_APPROVAL


def test_open_chat_is_auto_execute():
    node = TaskNode(
        node_id="1",
        objective="Open the chat with Rajaa",
        tool="send_message",
        parameters={"receiver": "Rajaa", "message_text": "", "platform": "WhatsApp", "mode": "open_chat"},
        expected_outcome="Chat opens",
        risk_tier=RiskTier.TIER_1,
    )

    assert decide_policy(node) is PolicyDecision.AUTO_EXECUTE


def test_open_app_as_admin_requires_approval():
    node = TaskNode(
        node_id="1",
        objective="Open Command Prompt as administrator",
        tool="open_app",
        parameters={"app_name": "command prompt", "run_as_admin": True},
        expected_outcome="Command Prompt opens with elevation",
        risk_tier=RiskTier.TIER_3,
    )

    assert decide_policy(node) is PolicyDecision.REQUIRE_APPROVAL

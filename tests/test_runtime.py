import asyncio

from agent.models import ActionResult, PermissionScope, RiskTier, TaskNode
from agent.policy import PolicyEngine
from agent.runtime import AgentRuntime, RuntimeStatus


def _all_scopes_policy():
    return PolicyEngine(granted_scopes=set(PermissionScope))


class FakeExecutor:
    def execute_node(self, node):
        return ActionResult(status="success", summary=f"done:{node.node_id}")


class FakeWorkflowMemory:
    def __init__(self):
        self.promoted = []

    def maybe_promote(self, goal, results):
        self.promoted.append((goal, len(results)))


def test_runtime_executes_nodes_in_order():
    runtime = AgentRuntime(executor=FakeExecutor())
    nodes = [
        TaskNode(
            node_id="step-1",
            objective="Open Chrome",
            tool="open_app",
            parameters={"app_name": "Chrome"},
            expected_outcome="Chrome open",
            risk_tier=RiskTier.TIER_1,
        ),
        TaskNode(
            node_id="step-2",
            objective="Search weather",
            tool="web_search",
            parameters={"query": "weather"},
            expected_outcome="Weather results",
            risk_tier=RiskTier.TIER_0,
            depends_on=["step-1"],
        ),
    ]

    results = runtime.run(nodes, goal="Open Chrome and search weather")
    assert [item.summary for item in results] == ["done:step-1", "done:step-2"]


def test_runtime_promotes_successful_workflows():
    memory = FakeWorkflowMemory()
    runtime = AgentRuntime(executor=FakeExecutor(), workflow_memory=memory)
    nodes = [
        TaskNode(
            node_id="step-1",
            objective="Open Chrome",
            tool="open_app",
            parameters={"app_name": "Chrome"},
            expected_outcome="Chrome open",
            risk_tier=RiskTier.TIER_1,
        )
    ]

    runtime.run(nodes, goal="Open Chrome")
    assert memory.promoted == [("Open Chrome", 1)]


def test_runtime_status_defaults_to_idle():
    status = RuntimeStatus()
    assert status.current_goal == ""
    assert status.current_step == ""
    assert status.pending_approval is False


def test_runtime_stops_when_approval_denied():
    runtime = AgentRuntime(
        executor=FakeExecutor(),
        policy=_all_scopes_policy(),
        approval_callback=lambda message: False,
    )
    nodes = [
        TaskNode(
            node_id="step-1",
            objective="Send a message",
            tool="send_message",
            parameters={"receiver": "Alex", "message_text": "hi", "platform": "WhatsApp"},
            expected_outcome="Message sent",
            risk_tier=RiskTier.TIER_3,
        )
    ]

    results = runtime.run(nodes, goal="Ping Alex")
    assert results[0].status == "pending_approval"


def test_runtime_coordinator_execute_workflow_respects_approval():
    from agent.models import WorkflowRecipe, WorkflowStep, WorkflowVerification
    from agent.runtime import RuntimeCoordinator

    coordinator = RuntimeCoordinator(approval_callback=lambda message: False, policy=_all_scopes_policy())
    recipe = WorkflowRecipe(
        recipe_id="send_message_test",
        intent_family="send_message",
        goal="message Rajaa hello",
        steps=[
            WorkflowStep(
                kind="tool",
                action="send_message",
                parameters={"receiver": "Rajaa", "platform": "WhatsApp", "mode": "send", "message_text": "hello"},
                verify=WorkflowVerification(method="result_contains", target="summary", expected_state="sent"),
            )
        ],
        requires_approval=True,
        approval_tool="send_message",
        approval_parameters={"receiver": "Rajaa", "platform": "WhatsApp", "mode": "send", "message_text": "hello"},
        risk_tier=RiskTier.TIER_1,
        success_reply_key="send_message",
    )

    result = asyncio.run(
        coordinator.execute_workflow(
            recipe,
            lambda recipe, speak=None: ActionResult(status="success", summary="Message sent to Rajaa via WhatsApp."),
        )
    )

    assert result.status == "pending_approval"

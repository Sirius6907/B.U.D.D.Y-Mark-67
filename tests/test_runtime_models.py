import pytest
from agent.models import TaskNode, TaskPlan, RiskTier, ActionResult

def test_task_node_validation():
    node = TaskNode(
        node_id="1",
        objective="Test",
        tool="browser",
        parameters={"url": "google.com"},
        expected_outcome="Loaded"
    )
    assert node.node_id == "1"
    assert node.risk_tier == RiskTier.TIER_1

def test_task_plan_duplicate_ids():
    node1 = TaskNode(
        node_id="1",
        objective="Step 1",
        tool="browser",
        parameters={},
        expected_outcome="Done"
    )
    node2 = TaskNode(
        node_id="1", # Duplicate ID
        objective="Step 2",
        tool="search",
        parameters={},
        expected_outcome="Done"
    )
    
    with pytest.raises(ValueError, match="IDs must be unique"):
        TaskPlan(plan_id="plan_1", goal="Goal", nodes=[node1, node2])

def test_action_result_assignment():
    res = ActionResult(status="success", summary="All good")
    node = TaskNode(
        node_id="1",
        objective="Test",
        tool="browser",
        parameters={},
        expected_outcome="Done",
        result=res
    )
    assert node.result.status == "success"

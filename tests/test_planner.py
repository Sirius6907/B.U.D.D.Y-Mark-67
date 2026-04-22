from agent.models import RiskTier
from agent.planner import normalize_plan


def test_normalize_plan_builds_typed_nodes():
    raw_plan = {
        "goal": "Open Chrome and search weather",
        "steps": [
            {
                "step": 1,
                "tool": "open_app",
                "description": "Open Chrome",
                "parameters": {"app_name": "Chrome"},
                "critical": True,
            },
            {
                "step": 2,
                "tool": "web_search",
                "description": "Search weather",
                "parameters": {"query": "weather today"},
                "critical": True,
            },
        ],
    }

    nodes = normalize_plan(raw_plan)
    assert [node.node_id for node in nodes] == ["step-1", "step-2"]
    assert nodes[0].risk_tier is RiskTier.TIER_1
    assert nodes[1].depends_on == ["step-1"]

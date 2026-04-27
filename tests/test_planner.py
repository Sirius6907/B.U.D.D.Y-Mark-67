from types import SimpleNamespace

from agent.planner import _fallback_plan, create_plan, normalize_plan


def test_normalize_plan_builds_typed_nodes():
    raw_plan = {
        "goal": "Open Chrome and search weather",
        "steps": [
            {
                "step": 1,
                "tool": "open_app",
                "description": "Open Chrome",
                "parameters": {"app_name": "Chrome"},
            },
            {
                "step": 2,
                "tool": "web_search",
                "description": "Search weather",
                "parameters": {"query": "weather today"},
            },
        ],
    }

    nodes = normalize_plan(raw_plan)
    assert [node.node_id for node in nodes] == ["step-1", "step-2"]
    assert nodes[1].depends_on == ["step-1"]


def test_fallback_plan_uses_web_search_when_planning_fails():
    plan = _fallback_plan("open whatsapp and search for contact Rajaa and open the chat")

    assert plan.nodes[0].tool == "web_search"
    assert plan.nodes[0].parameters["query"] == "open whatsapp and search for contact Rajaa and open the chat"


def test_create_plan_extracts_json_wrapped_in_extra_text(monkeypatch):
    wrapped = """
Here is the plan:
{
  "plan_id": "plan-1",
  "goal": "open youtube",
  "nodes": [
    {
      "node_id": "1",
      "objective": "Play suave on YouTube",
      "tool": "youtube_video",
      "parameters": {"action": "play", "query": "suave"},
      "expected_outcome": "Video starts playing",
      "risk_tier": "tier_1",
      "depends_on": []
    }
  ]
}
"""
    monkeypatch.setattr(
        "agent.llm_gateway.llm_generate",
        lambda **kwargs: SimpleNamespace(text=wrapped, model="openrouter/free"),
    )

    plan = create_plan("open youtube and play suave")
    assert plan.nodes[0].tool == "youtube_video"


def test_create_plan_normalizes_legacy_steps_output(monkeypatch):
    wrapped = {
        "goal": "Open Chrome",
        "steps": [
            {
                "step": 1,
                "tool": "open_app",
                "description": "Open Chrome",
                "parameters": {"app_name": "Chrome"},
                "expected_outcome": "Chrome opens",
            }
        ],
    }
    monkeypatch.setattr(
        "agent.llm_gateway.llm_generate",
        lambda **kwargs: SimpleNamespace(text=str(wrapped).replace("'", '"'), model="openrouter/free"),
    )

    plan = create_plan("Open Chrome")
    assert plan.nodes[0].tool == "open_app"


def test_create_plan_short_circuits_direct_shutdown():
    plan = create_plan("Shutdown")
    assert plan.nodes[0].tool == "shutdown_buddy"

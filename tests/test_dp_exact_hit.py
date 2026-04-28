import shutil
from pathlib import Path

from agent.dp_brain import DPBrain
from agent.models import SubproblemValue, WorkflowRecipe, WorkflowStep


def _tmp_dir(name: str) -> Path:
    base = Path.cwd() / "tests" / ".tmp_dp" / name
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    return base


def test_dp_brain_exact_hit_reuses_cached_workflow():
    temp_dir = _tmp_dir("exact_hit")
    brain = DPBrain(db_path=temp_dir / "dp.sqlite3")
    goal = "Open WhatsApp and search for contact Rajaa and open the chat"
    context = {
        "intent_family": "open_chat",
        "tool_surface": "messaging",
        "state_snapshot": {"window": "whatsapp", "screen": "chat-list"},
    }
    recipe = WorkflowRecipe(
        recipe_id="recipe-1",
        intent_family="open_chat",
        goal=goal,
        steps=[WorkflowStep(kind="tool", action="send_message", parameters={"mode": "open_chat"})],
    )
    key = brain.state_encoder.build_key(goal, context)
    brain.store_success(
        key,
        SubproblemValue(
            status="solved",
            solution_steps=recipe.model_dump()["steps"],
            evidence={"recipe": recipe.model_dump()},
            confidence=0.92,
            reward_score=0.8,
        ),
    )

    hit = brain.lookup(goal, context)

    assert hit is not None
    assert hit.hit_type == "exact"
    composed = brain.compose(goal, context)
    assert composed is not None
    assert composed.intent_family == "open_chat"
    assert composed.metadata["dp_hit_type"] == "exact"
    assert composed.steps[0].parameters["mode"] == "open_chat"
    brain.close()
    shutil.rmtree(temp_dir)

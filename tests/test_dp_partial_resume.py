import shutil
from pathlib import Path

from agent.dp_brain import DPBrain
from agent.models import SubproblemValue


def _tmp_dir(name: str) -> Path:
    base = Path.cwd() / "tests" / ".tmp_dp" / name
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    return base


def test_dp_brain_partial_resume_returns_remaining_steps():
    temp_dir = _tmp_dir("partial_resume")
    brain = DPBrain(db_path=temp_dir / "dp.sqlite3")
    goal = "Open WhatsApp and search for contact Rajaa and send hello"
    context = {
        "intent_family": "send_message",
        "tool_surface": "messaging",
        "state_snapshot": {"window": "whatsapp", "screen": "chat-open"},
    }
    key = brain.state_encoder.build_key(goal, context)
    brain.store_partial(
        key,
        SubproblemValue(
            status="partial",
            solution_steps=[
                {"kind": "tool", "action": "open_app", "parameters": {"app_name": "WhatsApp"}},
                {"kind": "tool", "action": "send_message", "parameters": {"receiver": "Rajaa", "message_text": "hello", "mode": "send"}},
            ],
            verified_boundaries={"last_completed_step": 1, "solution_type": "workflow_recipe"},
            evidence={"intent_family": "send_message", "goal": goal},
            confidence=0.88,
            reward_score=0.4,
        ),
    )

    composed = brain.compose(goal, context)

    assert composed is not None
    assert len(composed.steps) == 1
    assert composed.steps[0].action == "send_message"
    assert composed.metadata["dp_reuse_strategy"] == "resume"
    assert composed.metadata["dp_resume_from_step"] == 1
    brain.close()
    shutil.rmtree(temp_dir)

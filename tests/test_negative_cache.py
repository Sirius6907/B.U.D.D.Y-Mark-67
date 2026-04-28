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


def test_negative_cache_hit_is_reported_and_compose_returns_none():
    temp_dir = _tmp_dir("negative_cache")
    brain = DPBrain(db_path=temp_dir / "dp.sqlite3")
    goal = "Delete every file in downloads"
    context = {
        "intent_family": "dangerous_delete",
        "tool_surface": "filesystem",
        "state_snapshot": {"cwd": "downloads"},
    }
    key = brain.state_encoder.build_key(goal, context)
    brain.store_failure(
        key,
        SubproblemValue(
            status="failed",
            solution_steps=[],
            evidence={"reason": "policy_denied"},
            confidence=0.95,
            reward_score=-1.0,
        ),
    )

    hit = brain.lookup(goal, context)

    assert hit is not None
    assert hit.reuse_strategy == "avoid"
    assert brain.compose(goal, context) is None
    brain.close()
    shutil.rmtree(temp_dir)

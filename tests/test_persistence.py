import shutil
from pathlib import Path

from memory.dp_store import DPStore


def _tmp_dir(name: str) -> Path:
    base = Path.cwd() / "tests" / ".tmp_dp" / name
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    return base


def test_dp_store_persists_entries_and_negative_cache():
    temp_dir = _tmp_dir("persistence")
    store = DPStore(db_path=temp_dir / "dp.sqlite3")
    record = {
        "normalized_goal": "open whatsapp",
        "intent_family": "open_chat",
        "environment_signature": "env-1",
        "state_hash": "state-1",
        "tool_surface": "messaging",
        "schema_version": "dp-v2",
        "status": "failed",
        "solution_steps": [],
        "verified_boundaries": {},
        "confidence": 0.7,
        "evidence": {"reason": "not_logged_in"},
        "reward_score": -0.5,
        "use_count": 0,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }

    store.upsert(record)
    exact = store.lookup_exact("open_chat", "env-1", "state-1", "messaging", "open whatsapp")

    assert exact is not None
    assert exact["status"] == "failed"
    negatives = store.lookup_negative("open_chat", "env-1", "messaging", "open whatsapp")
    assert negatives is not None
    store.increment_use_count(record)
    updated = store.lookup_exact("open_chat", "env-1", "state-1", "messaging", "open whatsapp")
    assert updated["use_count"] == 1
    store.close()
    shutil.rmtree(temp_dir)

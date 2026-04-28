from __future__ import annotations

import sqlite3
import threading
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agent.checkpoint_manager import CheckpointManager
from agent.dp_brain import DPBrain
from agent.models import SubproblemKey, SubproblemValue
from memory.dp_store import DPStore
from memory.memory_manager import HybridMemory


def _tmp_dir(name: str) -> Path:
    base = Path.cwd() / "tests" / ".tmp_dp_resilience" / name
    if base.exists():
        for child in sorted(base.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        base.rmdir()
    base.mkdir(parents=True, exist_ok=True)
    return base


def _record(goal: str = "open whatsapp") -> dict[str, object]:
    return {
        "normalized_goal": goal,
        "intent_family": "open_chat",
        "environment_signature": "env-1",
        "state_hash": "state-1",
        "tool_surface": "messaging",
        "schema_version": "dp-v2",
        "status": "solved",
        "solution_steps": [{"kind": "tool", "action": "open_app", "parameters": {"app_name": "WhatsApp"}}],
        "verified_boundaries": {"solution_type": "workflow_recipe"},
        "confidence": 0.9,
        "evidence": {"recipe": {"recipe_id": "r1", "intent_family": "open_chat", "goal": goal, "steps": []}},
        "reward_score": 0.5,
        "use_count": 0,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


def test_dp_store_lookup_by_goal_hash_and_checkpoint_schema():
    store = DPStore(_tmp_dir("store_lookup") / "dp.sqlite3")
    record = _record()

    store.upsert(record)
    saved = store.lookup_exact("open_chat", "env-1", "state-1", "messaging", "open whatsapp")

    assert saved is not None
    loaded = store.lookup_by_goal_hash(saved["goal_hash"])
    assert loaded is not None
    assert loaded["normalized_goal"] == "open whatsapp"

    table_names = {
        row["name"]
        for row in store._conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert "dp_checkpoints" in table_names
    store.close()


def test_memory_manager_get_dp_entry_uses_goal_hash_lookup():
    memory = HybridMemory.__new__(HybridMemory)
    memory.dp_store = SimpleNamespace(
        lookup_by_goal_hash=Mock(return_value={"goal_hash": "goal-123", "status": "solved"})
    )
    memory.cursor = Mock()

    record = memory.get_dp_entry("goal-123")

    assert record == {"goal_hash": "goal-123", "status": "solved"}
    memory.dp_store.lookup_by_goal_hash.assert_called_once_with("goal-123")
    memory.cursor.execute.assert_not_called()


def test_checkpoint_manager_persists_via_store_and_cleans_stale_entries():
    store = DPStore(_tmp_dir("checkpoints") / "dp.sqlite3")
    manager = CheckpointManager(store=store)
    payload = {"completed_steps": 1, "remaining_steps": [{"action": "send_message"}]}

    manager.save("goal-1", payload)
    restored = manager.load("goal-1")

    assert restored is not None
    assert restored["remaining_steps"][0]["action"] == "send_message"

    rows = store._conn.execute("SELECT checkpoint_id FROM dp_checkpoints").fetchall()
    assert [row["checkpoint_id"] for row in rows] == ["goal-1"]

    deleted = manager.cleanup_stale("9999-01-01T00:00:00+00:00")
    assert deleted == 1
    assert manager.load("goal-1") is None
    store.close()


def test_dp_brain_caps_hot_cache_and_tracks_lru_eviction():
    brain = DPBrain(db_path=_tmp_dir("brain_cache") / "dp.sqlite3")
    first_key = SubproblemKey(
        normalized_goal="goal 0",
        intent_family="generic",
        environment_signature="env",
        state_hash="state-0",
        tool_surface="ui",
    ).cache_key

    for index in range(1005):
        goal = f"goal {index}"
        key = SubproblemKey(
            normalized_goal=goal,
            intent_family="generic",
            environment_signature="env",
            state_hash=f"state-{index}",
            tool_surface="ui",
        )
        value = SubproblemValue(status="solved", solution_steps=[], evidence={}, confidence=0.5)
        brain.store_success(key, value)

    assert isinstance(brain._hot_cache, OrderedDict)
    assert len(brain._hot_cache) == 1000
    assert first_key not in brain._hot_cache
    brain.close()


def test_dp_store_retries_locked_writes_before_succeeding(monkeypatch: pytest.MonkeyPatch):
    store = DPStore(_tmp_dir("locked_write") / "dp.sqlite3")
    record = _record("locked goal")
    attempts = {"count": 0}
    original_conn = store._conn

    class FlakyConnection:
        def __init__(self, inner):
            self._inner = inner

        def execute(self, query, params=()):
            if query.lstrip().startswith("INSERT INTO dp_entries") and attempts["count"] < 2:
                attempts["count"] += 1
                raise sqlite3.OperationalError("database is locked")
            return self._inner.execute(query, params)

        def __getattr__(self, name):
            return getattr(self._inner, name)

    monkeypatch.setattr(store, "_conn", FlakyConnection(original_conn))

    store.upsert(record)

    assert attempts["count"] == 2
    saved = store.lookup_exact("open_chat", "env-1", "state-1", "messaging", "locked goal")
    assert saved is not None
    store.close()


def test_dp_store_handles_concurrent_writes_across_large_swarm():
    store = DPStore(_tmp_dir("swarm") / "dp.sqlite3")
    errors: list[Exception] = []

    def worker(index: int) -> None:
        try:
            record = _record(f"goal {index}")
            record["state_hash"] = f"state-{index}"
            record["created_at"] = f"2026-01-01T00:00:{index % 60:02d}+00:00"
            record["updated_at"] = f"2026-01-01T00:00:{index % 60:02d}+00:00"
            store.upsert(record)
        except Exception as exc:  # pragma: no cover - failure path is asserted below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(50)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    count = store._conn.execute("SELECT COUNT(*) AS count FROM dp_entries").fetchone()["count"]
    assert count == 50
    store.close()


def test_dp_store_falls_back_when_database_file_is_corrupted():
    db_path = _tmp_dir("corrupt") / "dp.sqlite3"
    db_path.write_bytes(b"not-a-sqlite-database")

    store = DPStore(db_path)

    assert store._memory_fallback is True
    store.upsert(_record("recover after corruption"))
    recovered = store.lookup_exact("open_chat", "env-1", "state-1", "messaging", "recover after corruption")
    assert recovered is not None
    store.close()

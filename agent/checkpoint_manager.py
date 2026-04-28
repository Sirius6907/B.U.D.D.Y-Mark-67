from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from memory.dp_store import DPStore


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CheckpointManager:
    def __init__(self, store: DPStore | None = None):
        self._lock = Lock()
        self._checkpoints: dict[str, dict[str, Any]] = {}
        self._store = store

    def save(self, goal: str, payload: dict[str, Any]) -> None:
        snapshot = deepcopy(payload)
        snapshot.setdefault("goal", goal)
        snapshot["updated_at"] = _utc_now()
        with self._lock:
            self._checkpoints[goal] = snapshot
            if self._store is not None:
                self._store.save_checkpoint(goal, snapshot)

    def load(self, goal: str) -> dict[str, Any] | None:
        with self._lock:
            checkpoint = self._checkpoints.get(goal)
        if checkpoint is not None:
            return deepcopy(checkpoint)
        if self._store is None:
            return None
        checkpoint = self._store.load_checkpoint(goal)
        if checkpoint is None:
            return None
        with self._lock:
            self._checkpoints[goal] = deepcopy(checkpoint)
        return checkpoint

    def clear(self, goal: str) -> None:
        with self._lock:
            self._checkpoints.pop(goal, None)

    def cleanup_stale(self, older_than: str) -> int:
        deleted = 0
        with self._lock:
            stale_goals = [
                goal
                for goal, payload in self._checkpoints.items()
                if str(payload.get("updated_at", "")) < older_than
            ]
            for goal in stale_goals:
                self._checkpoints.pop(goal, None)
            deleted += len(stale_goals)
        if self._store is not None:
            deleted = max(deleted, self._store.delete_stale_checkpoints(older_than))
        return deleted

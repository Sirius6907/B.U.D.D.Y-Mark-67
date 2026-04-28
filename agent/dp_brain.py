from __future__ import annotations

import sqlite3
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from buddy_logging import get_logger
from agent.checkpoint_manager import CheckpointManager
from agent.metrics import MetricsTracker
from agent.models import DPHit, SubproblemKey, SubproblemValue, TaskPlan, TaskNode, WorkflowRecipe, WorkflowStep
from agent.path_optimizer import PathOptimizer
from agent.repair_engine import RepairEngine
from agent.reward_engine import RewardEngine
from agent.state_encoder import StateEncoder
from memory.dp_store import DPStore

logger = get_logger("agent.dp_brain")


@dataclass
class ComposeResult:
    artifact: WorkflowRecipe | TaskPlan | None
    hit: DPHit | None


class DPBrain:
    def __init__(self, db_path: str | Path | None = None, store: DPStore | None = None):
        if store is None:
            db_path = Path(db_path) if db_path is not None else Path("memory") / "dp_brain.sqlite3"
            store = DPStore(db_path)
        self.store = store
        self.state_encoder = StateEncoder()
        self.path_optimizer = PathOptimizer()
        self.checkpoint_manager = CheckpointManager(store=self.store)
        self.reward_engine = RewardEngine()
        self.repair_engine = RepairEngine()
        self.metrics = MetricsTracker(store=self.store)
        self._hot_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._hot_cache_limit = 1000
        self._failure_counts: dict[str, int] = {}
        self._last_lookup: dict[str, Any] | None = None

    def warm_preload(self, records: list[dict[str, Any]]) -> None:
        for record in records:
            self._remember_record(dict(record))

    def lookup(self, goal: str, context: dict[str, Any] | None = None) -> DPHit | None:
        key = self.state_encoder.build_key(goal, context)
        cache_key = key.cache_key
        record = self._hot_cache.get(cache_key)
        if record is not None:
            self._hot_cache.move_to_end(cache_key)
        if record is None:
            record = self.store.lookup_by_goal_hash(cache_key)
        if record is None:
            negative = self.store.lookup_negative(
                key.intent_family,
                key.environment_signature,
                key.tool_surface,
                key.normalized_goal,
            )
            if negative is not None:
                record = negative
            else:
                candidates = self.store.lookup_prefix(
                    key.intent_family,
                    key.environment_signature,
                    key.tool_surface,
                    key.normalized_goal,
                )
                if not candidates:
                    candidates = self.store.lookup_related(
                        key.intent_family,
                        key.environment_signature,
                        key.tool_surface,
                    )
                scored_candidates = [self._score_candidate(candidate) for candidate in candidates]
                record = self.path_optimizer.best(scored_candidates) if scored_candidates else None
        if record is None:
            self._last_lookup = None
            return None

        self._remember_record(dict(record))
        goal_hash = record.get("goal_hash", cache_key)
        value = self._value_from_record(record)
        hit_type = "exact"
        reuse_strategy = "direct"
        if record["status"] == "partial":
            hit_type = "partial-prefix"
            reuse_strategy = "resume"
        elif record["status"] == "failed":
            hit_type = "exact"
            reuse_strategy = "avoid"
        elif record["normalized_goal"] != key.normalized_goal:
            hit_type = "related"
            reuse_strategy = "replan-tail"
        hit = DPHit(
            hit_type=hit_type,
            reuse_strategy=reuse_strategy,
            key=SubproblemKey(**{**record, "normalized_goal": record["normalized_goal"]}),
            value=value,
            source="session" if cache_key in self._hot_cache else "disk",
        )
        self._last_lookup = {"key": key, "record": record, "hit": hit}
        if reuse_strategy != "avoid":
            self.store.increment_use_count(record)
            record["use_count"] = int(record.get("use_count", 0)) + 1
            self._remember_record(record)
        else:
            self._failure_counts[goal_hash] = self._failure_counts.get(goal_hash, 0) + 1
        self.metrics.record("lookup", {"hit_type": hit_type, "reuse_strategy": reuse_strategy})
        return hit

    def fast_lookup(self, normalized_text: str) -> WorkflowRecipe | TaskPlan | None:
        for record in reversed(self._hot_cache.values()):
            if record.get("normalized_goal") != normalized_text:
                continue
            if record.get("status") == "failed":
                return None
            value = self._value_from_record(record)
            hit = DPHit(
                hit_type="exact",
                reuse_strategy="direct",
                key=SubproblemKey(
                    normalized_goal=record["normalized_goal"],
                    intent_family=record["intent_family"],
                    environment_signature=record["environment_signature"],
                    state_hash=record.get("state_hash", ""),
                    tool_surface=record.get("tool_surface", "generic"),
                    schema_version=record.get("schema_version", "dp-v2"),
                ),
                value=value,
                source="session",
            )
            return self._compose_from_hit(hit, normalized_text)
        return None

    def store_success(self, key: SubproblemKey, value: SubproblemValue) -> None:
        self._store(key, value)

    def store_partial(self, key: SubproblemKey, value: SubproblemValue) -> None:
        self._store(key, value)

    def store_failure(self, key: SubproblemKey, value: SubproblemValue) -> None:
        self._store(key, value)

    def _store(self, key: SubproblemKey, value: SubproblemValue) -> None:
        record = self._record_from_models(key, value)
        self.store.upsert(record)
        self._remember_record(record)
        if value.status == "failed":
            self._failure_counts[key.goal_hash or key.cache_key] = self._failure_counts.get(key.goal_hash or key.cache_key, 0) + 1
        self.metrics.record("store", {"status": value.status, "intent_family": key.intent_family})

    def compose(self, goal: str, context: dict[str, Any] | None = None) -> WorkflowRecipe | TaskPlan | None:
        hit = self.lookup(goal, context)
        if hit is None or hit.reuse_strategy == "avoid":
            return None
        artifact = self._compose_from_hit(hit, goal)
        if artifact is not None:
            self.metrics.record("compose", {"reuse_strategy": hit.reuse_strategy, "hit_type": hit.hit_type})
        return artifact

    def predict_next(self) -> dict[str, Any] | None:
        checkpoint = self.checkpoint_manager.load(self._last_lookup["key"].normalized_goal) if self._last_lookup else None
        if checkpoint and checkpoint.get("remaining_steps"):
            return checkpoint["remaining_steps"][0]
        return None

    def repair(self, error: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        repair = self.repair_engine.repair(error, context)
        self.metrics.record("repair", {"strategy": repair.get("strategy", "unknown")})
        return repair

    def update_reward(self, result: Any) -> float:
        reward = self.reward_engine.score(result)
        if self._last_lookup is None:
            self.metrics.record("reward", {"reward_score": reward, "orphan": True})
            return reward
        record = dict(self._last_lookup["record"])
        confidence = self.reward_engine.update_confidence(float(record.get("confidence", 0.5)), reward)
        self.store.update_confidence(record, confidence, reward)
        record["confidence"] = confidence
        record["reward_score"] = reward
        self._remember_record(record)
        self.metrics.record("reward", {"reward_score": reward, "confidence": confidence})
        return reward

    def save_checkpoint(self, goal: str, nodes: list[TaskNode], completed_steps: int, context: dict[str, Any] | None = None) -> None:
        remaining_steps = [node.model_dump() for node in nodes[completed_steps:]]
        self.checkpoint_manager.save(
            goal,
            {
                "completed_steps": completed_steps,
                "remaining_steps": remaining_steps,
                "context": context or {},
            },
        )

    def close(self) -> None:
        self.store.close()

    def _compose_from_hit(self, hit: DPHit, goal: str) -> WorkflowRecipe | TaskPlan | None:
        value = hit.value
        solution_type = value.verified_boundaries.get("solution_type") or value.solution_type
        if solution_type == "workflow_recipe":
            payload = value.evidence.get("recipe") or {
                "recipe_id": f"dp_{hit.key.cache_key[:8]}",
                "intent_family": hit.key.intent_family,
                "goal": goal,
                "steps": value.solution_steps,
                "metadata": {},
            }
            if hit.reuse_strategy == "resume":
                start = int(value.verified_boundaries.get("last_completed_step", 0))
                payload = dict(payload)
                payload["steps"] = payload.get("steps", [])[start:]
                payload.setdefault("metadata", {})
                payload["metadata"] = {
                    **payload["metadata"],
                    "dp_resume_from_step": start,
                }
            recipe = WorkflowRecipe.model_validate(payload)
            recipe.metadata = {
                **dict(recipe.metadata),
                "dp_hit_type": hit.hit_type,
                "dp_reuse_strategy": hit.reuse_strategy,
                "dp_confidence": value.confidence,
            }
            return recipe
        payload = value.evidence.get("plan") or {
            "plan_id": f"dp_{hit.key.cache_key[:8]}",
            "goal": goal,
            "nodes": value.solution_steps,
            "metadata": {},
        }
        if hit.reuse_strategy == "resume":
            start = int(value.verified_boundaries.get("last_completed_step", 0))
            payload = dict(payload)
            payload["nodes"] = payload.get("nodes", [])[start:]
            payload.setdefault("metadata", {})
            payload["metadata"] = {
                **payload["metadata"],
                "dp_resume_from_step": start,
            }
        plan = TaskPlan.model_validate(payload)
        plan.metadata = {
            **dict(plan.metadata),
            "dp_hit_type": hit.hit_type,
            "dp_reuse_strategy": hit.reuse_strategy,
            "dp_confidence": value.confidence,
        }
        return plan

    def _record_from_models(self, key: SubproblemKey, value: SubproblemValue) -> dict[str, Any]:
        return {
            "normalized_goal": key.normalized_goal,
            "intent_family": key.intent_family,
            "environment_signature": key.environment_signature,
            "state_hash": key.state_hash,
            "tool_surface": key.tool_surface,
            "schema_version": key.schema_version,
            "status": value.status,
            "solution_steps": value.solution_steps,
            "verified_boundaries": value.verified_boundaries,
            "confidence": value.confidence,
            "evidence": value.evidence,
            "reward_score": value.reward_score,
            "use_count": value.use_count,
            "created_at": value.created_at,
            "updated_at": value.updated_at,
        }

    def _value_from_record(self, record: dict[str, Any]) -> SubproblemValue:
        return SubproblemValue(
            status=record["status"],
            solution_steps=record.get("solution_steps", []),
            verified_boundaries=record.get("verified_boundaries", {}),
            confidence=float(record.get("confidence", 0.5)),
            evidence=record.get("evidence", {}),
            reward_score=float(record.get("reward_score", 0.0)),
            use_count=int(record.get("use_count", 0)),
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at"),
            solution_type=record.get("verified_boundaries", {}).get("solution_type")
            or ("workflow_recipe" if "recipe" in (record.get("evidence") or {}) else "task_plan"),
        )

    @staticmethod
    def _cache_key_from_record(record: dict[str, Any]) -> str:
        return (
            record.get("goal_hash")
            or SubproblemKey(
                normalized_goal=record["normalized_goal"],
                intent_family=record["intent_family"],
                environment_signature=record["environment_signature"],
                state_hash=record.get("state_hash", ""),
                tool_surface=record.get("tool_surface", "generic"),
                schema_version=record.get("schema_version", "dp-v2"),
            ).cache_key
        )

    def _remember_record(self, record: dict[str, Any]) -> None:
        cache_key = self._cache_key_from_record(record)
        record["goal_hash"] = cache_key
        self._hot_cache[cache_key] = record
        self._hot_cache.move_to_end(cache_key)
        while len(self._hot_cache) > self._hot_cache_limit:
            self._hot_cache.popitem(last=False)

    def _score_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        goal_hash = self._cache_key_from_record(candidate)
        failure_count = self._failure_counts.get(goal_hash, 0)
        confidence = float(candidate.get("confidence", 0.0))
        confidence = max(0.0, confidence - self._confidence_decay(candidate) - (failure_count * 0.1))
        return {
            **candidate,
            "goal_hash": goal_hash,
            "confidence": confidence,
            "success_rate": max(0.0, min(1.0, confidence)),
            "risk": 1.0 if candidate.get("status") == "failed" else failure_count * 0.1,
            "latency": 0.0,
            "speed": 1.0,
        }

    @staticmethod
    def _confidence_decay(candidate: dict[str, Any]) -> float:
        updated_at = candidate.get("updated_at")
        if not updated_at:
            return 0.0
        try:
            age_seconds = (datetime.now(timezone.utc) - datetime.fromisoformat(updated_at)).total_seconds()
        except ValueError:
            return 0.0
        return min(0.35, max(0.0, age_seconds / 86400.0) * 0.01)


_dp_brain: DPBrain | None = None


def get_dp_brain() -> DPBrain:
    global _dp_brain
    if _dp_brain is None:
        default_db = Path("memory") / "dp_brain.sqlite3"
        _dp_brain = DPBrain(db_path=default_db)
    return _dp_brain

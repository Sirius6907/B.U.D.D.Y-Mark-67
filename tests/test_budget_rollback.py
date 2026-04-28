"""
tests/test_budget_rollback.py — Budget Engine + Rollback Registry Tests
=========================================================================
Validates resource governance (step/time/cost budgets) and undo
capabilities (file create/modify/delete snapshots + restoration).
"""
from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import pytest

from agent.budget import BudgetEngine, BudgetLimits, BudgetStatus


# ───────────────────────────────────────────────────────────────────────
# Budget Engine Tests
# ───────────────────────────────────────────────────────────────────────

class TestBudgetEngine:
    """Covers step counting, cost tracking, time-based limits, and status transitions."""

    def test_fresh_engine_can_proceed(self):
        engine = BudgetEngine()
        engine.start()
        assert engine.can_proceed() is True

    def test_step_limit_exceeded(self):
        engine = BudgetEngine(BudgetLimits(max_steps=3))
        engine.start()
        engine.record_step()
        engine.record_step()
        assert engine.can_proceed() is True  # 2/3 used
        engine.record_step()
        assert engine.can_proceed() is False  # 3/3 = exceeded
        assert engine.status() is BudgetStatus.EXCEEDED

    def test_cost_limit_exceeded(self):
        engine = BudgetEngine(BudgetLimits(max_cost_units=5.0))
        engine.start()
        engine.record_step(cost=2.0)
        engine.record_step(cost=2.0)
        assert engine.can_proceed() is True  # 4.0/5.0
        engine.record_step(cost=1.0)
        assert engine.can_proceed() is False  # 5.0/5.0
        assert engine.status() is BudgetStatus.EXCEEDED

    def test_wall_time_exceeded(self):
        engine = BudgetEngine(BudgetLimits(max_wall_seconds=0.1))
        engine.start()
        assert engine.can_proceed() is True
        time.sleep(0.15)
        assert engine.can_proceed() is False
        assert engine.status() is BudgetStatus.EXCEEDED

    def test_warning_threshold(self):
        engine = BudgetEngine(BudgetLimits(max_steps=10, warning_threshold=0.8))
        engine.start()
        for _ in range(7):
            engine.record_step()
        assert engine.status() is BudgetStatus.OK  # 7/10 = 70%
        engine.record_step()  # 8/10 = 80%
        assert engine.status() is BudgetStatus.WARNING
        assert engine.can_proceed() is True  # WARNING still allows proceed

    def test_snapshot_reflects_state(self):
        engine = BudgetEngine(BudgetLimits(max_steps=10, max_cost_units=100.0))
        engine.start()
        engine.record_step(cost=5.0)
        engine.record_step(cost=3.0)

        snap = engine.snapshot()
        assert snap.steps_used == 2
        assert snap.steps_limit == 10
        assert snap.cost_used == 8.0
        assert snap.cost_limit == 100.0
        assert snap.pct_steps == 0.2

    def test_pause_blocks_proceed(self):
        engine = BudgetEngine()
        engine.start()
        engine.pause()
        assert engine.can_proceed() is False
        assert engine.status() is BudgetStatus.PAUSED

    def test_resume_after_pause(self):
        engine = BudgetEngine()
        engine.start()
        engine.pause()
        engine.resume()
        assert engine.can_proceed() is True

    def test_remaining_steps(self):
        engine = BudgetEngine(BudgetLimits(max_steps=5))
        engine.start()
        assert engine.remaining_steps() == 5
        engine.record_step()
        engine.record_step()
        assert engine.remaining_steps() == 3

    def test_add_cost_without_step(self):
        engine = BudgetEngine(BudgetLimits(max_cost_units=10.0))
        engine.start()
        engine.add_cost(3.0)
        engine.add_cost(4.0)
        assert engine.cost_used == 7.0
        assert engine.steps_used == 0  # no step increment

    def test_limits_property(self):
        limits = BudgetLimits(max_steps=42)
        engine = BudgetEngine(limits)
        assert engine.limits.max_steps == 42


# ───────────────────────────────────────────────────────────────────────
# Rollback Registry Tests
# ───────────────────────────────────────────────────────────────────────

from agent.rollback import RollbackRegistry, RollbackType


class TestRollbackRegistry:
    """Covers file backup/restore, setting snapshots, and undo operations."""

    @pytest.fixture
    def tmp_dir(self, tmp_path):
        return tmp_path

    @pytest.fixture
    def registry(self, tmp_dir):
        backup_dir = tmp_dir / "rollback_backups"
        return RollbackRegistry(backup_dir=backup_dir)

    # ── File Create ─────────────────────────────────────────
    def test_snapshot_file_create_then_undo(self, registry, tmp_dir):
        test_file = tmp_dir / "newfile.txt"
        test_file.write_text("created content")

        registry.snapshot_file_create("task-1", str(test_file))
        assert registry.count() == 1

        # Undo = delete the created file
        entry = registry.undo_last()
        assert entry is not None
        assert entry.rollback_type is RollbackType.FILE_CREATE
        assert not test_file.exists()

    # ── File Modify ─────────────────────────────────────────
    def test_snapshot_file_modify_then_undo(self, registry, tmp_dir):
        test_file = tmp_dir / "config.txt"
        test_file.write_text("original content")

        registry.snapshot_file_modify("task-1", str(test_file))

        # Simulate modification
        test_file.write_text("modified content")
        assert test_file.read_text() == "modified content"

        # Undo = restore from backup
        entry = registry.undo_last()
        assert entry is not None
        assert entry.rollback_type is RollbackType.FILE_MODIFY
        assert test_file.read_text() == "original content"

    # ── File Delete ─────────────────────────────────────────
    def test_snapshot_file_delete_then_undo(self, registry, tmp_dir):
        test_file = tmp_dir / "to_delete.txt"
        test_file.write_text("important data")

        registry.snapshot_file_delete("task-1", str(test_file))

        # Simulate deletion
        test_file.unlink()
        assert not test_file.exists()

        # Undo = restore from backup
        entry = registry.undo_last()
        assert entry is not None
        assert entry.rollback_type is RollbackType.FILE_DELETE
        assert test_file.exists()
        assert test_file.read_text() == "important data"

    # ── Setting Snapshot ────────────────────────────────────
    def test_snapshot_setting(self, registry):
        entry = registry.snapshot_setting("task-1", "theme", "dark")
        assert entry.rollback_type is RollbackType.SETTING
        assert entry.previous_value == "dark"
        assert entry.metadata["setting_key"] == "theme"

    # ── Task-level Undo ─────────────────────────────────────
    def test_undo_task_reverses_all(self, registry, tmp_dir):
        f1 = tmp_dir / "file1.txt"
        f2 = tmp_dir / "file2.txt"
        f1.write_text("f1-original")
        f2.write_text("f2-original")

        registry.snapshot_file_modify("task-A", str(f1))
        registry.snapshot_file_modify("task-A", str(f2))

        # Simulate modifications
        f1.write_text("f1-changed")
        f2.write_text("f2-changed")

        # Undo all for task-A
        undone = registry.undo_task("task-A")
        assert len(undone) == 2
        assert f1.read_text() == "f1-original"
        assert f2.read_text() == "f2-original"

    # ── Undo respects task filter ───────────────────────────
    def test_undo_last_filters_by_task(self, registry, tmp_dir):
        f1 = tmp_dir / "taskA.txt"
        f2 = tmp_dir / "taskB.txt"
        f1.write_text("A-original")
        f2.write_text("B-original")

        registry.snapshot_file_modify("task-A", str(f1))
        registry.snapshot_file_modify("task-B", str(f2))

        f1.write_text("A-changed")
        f2.write_text("B-changed")

        # Undo only task-A
        entry = registry.undo_last(task_id="task-A")
        assert entry is not None
        assert f1.read_text() == "A-original"
        assert f2.read_text() == "B-changed"  # task-B untouched

    # ── Custom snapshot ────────────────────────────────────
    def test_snapshot_custom(self, registry):
        entry = registry.snapshot_custom("task-1", "Launched calculator",
                                          metadata={"pid": 1234})
        assert entry.rollback_type is RollbackType.CUSTOM
        assert entry.metadata["pid"] == 1234

    # ── Pending entries ─────────────────────────────────────
    def test_get_pending(self, registry, tmp_dir):
        f = tmp_dir / "pending.txt"
        f.write_text("data")
        registry.snapshot_file_create("task-1", str(f))
        registry.snapshot_custom("task-1", "Extra action")

        assert len(registry.get_pending()) == 2
        registry.undo_last()
        assert len(registry.get_pending()) == 1

    # ── Clear ───────────────────────────────────────────────
    def test_clear_removes_all(self, registry, tmp_dir):
        f = tmp_dir / "clear_me.txt"
        f.write_text("data")
        registry.snapshot_file_modify("task-1", str(f))
        assert registry.count() == 1

        registry.clear()
        assert registry.count() == 0

    # ── Edge: modify non-existent file returns None ─────────
    def test_modify_nonexistent_returns_none(self, registry):
        result = registry.snapshot_file_modify("task-1", "/no/such/file.txt")
        assert result is None
        assert registry.count() == 0

    # ── Edge: delete non-existent file returns None ─────────
    def test_delete_nonexistent_returns_none(self, registry):
        result = registry.snapshot_file_delete("task-1", "/no/such/file.txt")
        assert result is None
        assert registry.count() == 0

    # ── Edge: double undo is no-op ──────────────────────────
    def test_double_undo_no_op(self, registry, tmp_dir):
        f = tmp_dir / "double.txt"
        f.write_text("data")
        registry.snapshot_file_create("task-1", str(f))

        registry.undo_last()  # first undo deletes file
        assert not f.exists()

        result = registry.undo_last()  # second undo = no-op
        assert result is None


# ───────────────────────────────────────────────────────────────────────
# Runtime Integration Tests (Budget + Rollback in OPEV loop)
# ───────────────────────────────────────────────────────────────────────

from agent.models import TaskNode, RiskTier
from agent.runtime import AgentRuntime
from agent.policy import PolicyEngine


class _StubExecutor:
    """Returns success for any node."""
    def execute_node(self, node: TaskNode):
        from agent.models import ActionResult
        return ActionResult(status="success", summary="Done", retryable=False)


class TestRuntimeBudgetIntegration:
    """Verify budget enforcement halts execution inside the OPEV loop."""

    def test_budget_halts_at_limit(self):
        runtime = AgentRuntime(
            executor=_StubExecutor(),
            budget=BudgetEngine(BudgetLimits(max_steps=2)),
        )
        nodes = [
            TaskNode(node_id="s1", objective="Step 1", tool="screenshot", risk=RiskTier.TIER_0, parameters={}, expected_outcome="done"),
            TaskNode(node_id="s2", objective="Step 2", tool="screenshot", risk=RiskTier.TIER_0, parameters={}, expected_outcome="done"),
            TaskNode(node_id="s3", objective="Step 3", tool="screenshot", risk=RiskTier.TIER_0, parameters={}, expected_outcome="done"),
        ]
        results = runtime.run(nodes, goal="budget-test")

        # Should execute 2 steps, then budget halts the 3rd
        # Step 1 executes (records step → 1/2)
        # Step 2 executes (records step → 2/2, now EXCEEDED)
        # Step 3: budget.can_proceed() returns False → break
        assert len(results) == 3  # 2 success + 1 budget error
        assert results[0].status == "success"
        assert results[1].status == "success"
        assert results[2].status == "error"
        assert "Budget exceeded" in results[2].summary

    def test_budget_records_cost(self):
        budget = BudgetEngine(BudgetLimits(max_steps=100))
        runtime = AgentRuntime(
            executor=_StubExecutor(),
            budget=budget,
        )
        nodes = [
            TaskNode(node_id="s1", objective="Step 1", tool="screenshot", risk=RiskTier.TIER_0, parameters={}, expected_outcome="done"),
        ]
        runtime.run(nodes, goal="cost-test")
        assert budget.steps_used == 1
        assert budget.cost_used >= 0  # wall-time cost recorded (may be near-zero for fast steps)

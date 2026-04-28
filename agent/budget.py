"""
agent/budget.py — Resource Budget Engine
==========================================
Enforces step count, wall-clock time, and estimated cost limits
per task execution. The runtime queries this before each step.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BudgetStatus(str, Enum):
    OK           = "ok"
    WARNING      = "warning"      # >= 80% consumed
    EXCEEDED     = "exceeded"     # hard limit hit
    PAUSED       = "paused"       # manually paused by user


@dataclass(slots=True)
class BudgetLimits:
    """Configurable per-task budget limits."""
    max_steps: int = 20              # maximum tool invocations
    max_wall_seconds: float = 120.0  # max wall-clock time
    max_cost_units: float = 10.0     # abstract cost units (tokens, API calls, etc.)
    warning_threshold: float = 0.8   # emit warning at this % consumed


@dataclass(slots=True)
class BudgetSnapshot:
    """Point-in-time snapshot of budget consumption."""
    steps_used: int
    steps_limit: int
    wall_elapsed: float
    wall_limit: float
    cost_used: float
    cost_limit: float
    status: BudgetStatus
    pct_steps: float       # 0.0 – 1.0
    pct_wall: float
    pct_cost: float


class BudgetEngine:
    """
    Tracks and enforces resource budgets for a single task execution.

    Usage:
        budget = BudgetEngine(limits)
        budget.start()
        while budget.can_proceed():
            budget.record_step(cost=0.5)
            ...
    """

    def __init__(self, limits: BudgetLimits | None = None):
        self._limits = limits or BudgetLimits()
        self._steps_used: int = 0
        self._cost_used: float = 0.0
        self._start_time: float = 0.0
        self._paused: bool = False
        self._started: bool = False

    # ── Lifecycle ────────────────────────────────────────
    def start(self) -> None:
        self._start_time = time.monotonic()
        self._steps_used = 0
        self._cost_used = 0.0
        self._paused = False
        self._started = True

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    # ── Recording ────────────────────────────────────────
    def record_step(self, cost: float = 0.0) -> BudgetStatus:
        """Record a single step and optional cost. Returns current status."""
        self._steps_used += 1
        self._cost_used += cost
        return self.status()

    def add_cost(self, amount: float) -> None:
        """Add cost without incrementing step count (e.g. LLM token usage)."""
        self._cost_used += amount

    # ── Querying ─────────────────────────────────────────
    def can_proceed(self) -> bool:
        """Returns True if execution may continue."""
        s = self.status()
        return s in (BudgetStatus.OK, BudgetStatus.WARNING)

    def status(self) -> BudgetStatus:
        if self._paused:
            return BudgetStatus.PAUSED

        elapsed = self._elapsed()
        if (self._steps_used >= self._limits.max_steps
                or elapsed >= self._limits.max_wall_seconds
                or self._cost_used >= self._limits.max_cost_units):
            return BudgetStatus.EXCEEDED

        pct = max(
            self._steps_used / self._limits.max_steps,
            elapsed / self._limits.max_wall_seconds,
            self._cost_used / self._limits.max_cost_units,
        )
        if pct >= self._limits.warning_threshold:
            return BudgetStatus.WARNING

        return BudgetStatus.OK

    def snapshot(self) -> BudgetSnapshot:
        elapsed = self._elapsed()
        return BudgetSnapshot(
            steps_used=self._steps_used,
            steps_limit=self._limits.max_steps,
            wall_elapsed=round(elapsed, 3),
            wall_limit=self._limits.max_wall_seconds,
            cost_used=round(self._cost_used, 4),
            cost_limit=self._limits.max_cost_units,
            status=self.status(),
            pct_steps=round(self._steps_used / self._limits.max_steps, 3),
            pct_wall=round(elapsed / self._limits.max_wall_seconds, 3),
            pct_cost=round(self._cost_used / self._limits.max_cost_units, 3),
        )

    def remaining_steps(self) -> int:
        return max(0, self._limits.max_steps - self._steps_used)

    def remaining_seconds(self) -> float:
        return max(0.0, self._limits.max_wall_seconds - self._elapsed())

    @property
    def limits(self) -> BudgetLimits:
        return self._limits

    @property
    def steps_used(self) -> int:
        return self._steps_used

    @property
    def cost_used(self) -> float:
        return self._cost_used

    # ── Internal ─────────────────────────────────────────
    def _elapsed(self) -> float:
        if not self._started:
            return 0.0
        return time.monotonic() - self._start_time

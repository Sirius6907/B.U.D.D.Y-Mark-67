"""
runtime.browser.workflow — Strict step-by-step workflow executor.

Enforces:
  - Sequential execution (no uncontrolled recursion)
  - Execution state per step (index, previous result, retry count)
  - Max steps limit (default 15)
  - Max retries per step (default 3)
  - Mandatory verification for mutating tools

Each step follows:
  1. validate preconditions
  2. execute tool
  3. verify result
  4. update state
  5. decide next step
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RECOVERY = "recovery"


class WorkflowStatus(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    tool_name: str
    parameters: dict[str, Any]
    description: str = ""
    # Preconditions to validate before execution
    preconditions: list[str] = field(default_factory=list)
    # Whether this step mutates browser state (requires verification)
    is_mutating: bool = True
    # Expected postconditions after execution
    expected_postconditions: list[str] = field(default_factory=list)
    # Confidence score assigned by planner (0–1)
    confidence: float = 0.5


@dataclass
class StepResult:
    """Execution result for a single step."""
    step_index: int
    tool_name: str
    status: StepStatus
    result: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    recovery_tool: Optional[str] = None
    replan_action: Optional[str] = None  # ReplanAction if replanning occurred
    duration_ms: float = 0.0
    verified: bool = False


@dataclass
class WorkflowState:
    """Full execution state for a workflow."""
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.NOT_STARTED
    current_step: int = 0
    steps: list[WorkflowStep] = field(default_factory=list)
    results: list[StepResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    @property
    def completed_steps(self) -> int:
        return sum(1 for r in self.results if r.status == StepStatus.SUCCESS)

    @property
    def failed_steps(self) -> int:
        return sum(1 for r in self.results if r.status == StepStatus.FAILED)

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "total_steps": len(self.steps),
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "total_duration_ms": self.total_duration_ms,
            "results": [
                {
                    "step": r.step_index,
                    "tool": r.tool_name,
                    "status": r.status.value,
                    "retries": r.retry_count,
                    "verified": r.verified,
                    "duration_ms": r.duration_ms,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


class WorkflowExecutor:
    """Strict step-by-step workflow executor.

    Follows the plan → act → verify → adapt loop.
    Uses capability registry for tool resolution and recovery.
    """

    DEFAULT_MAX_STEPS = 15
    DEFAULT_MAX_RETRIES = 3

    def __init__(
        self,
        tool_executor: Callable[[str, dict], dict[str, Any]],
        recovery_policy: Any = None,
        capability_registry: Any = None,
        replanner: Any = None,
        max_steps: int = DEFAULT_MAX_STEPS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self._execute_tool = tool_executor
        self._recovery = recovery_policy
        self._registry = capability_registry
        self._replanner = replanner
        self._max_steps = max_steps
        self._max_retries = max_retries

    def execute(self, workflow_id: str, steps: list[WorkflowStep]) -> WorkflowState:
        """Execute a workflow step-by-step with verification, recovery, and replanning."""
        if len(steps) > self._max_steps:
            raise ValueError(
                f"Workflow has {len(steps)} steps, exceeding max of {self._max_steps}"
            )

        # Reset replanner state for new workflow
        if self._replanner:
            self._replanner.reset()

        state = WorkflowState(workflow_id=workflow_id, steps=steps)
        state.status = WorkflowStatus.RUNNING
        start_time = time.monotonic()

        # Use a mutable list so replanning can insert steps
        pending_steps = list(enumerate(steps))
        step_cursor = 0

        while step_cursor < len(pending_steps):
            idx, step = pending_steps[step_cursor]
            state.current_step = idx
            step_result = self._execute_step(idx, step, state)
            state.results.append(step_result)

            if step_result.status == StepStatus.FAILED:
                # Tier 1+2: Try recovery (retry + fallback)
                recovered = self._attempt_recovery(idx, step, step_result, state)
                if recovered is not None:
                    state.results[-1] = recovered
                else:
                    # Tier 3: Replanning
                    replan_result = self._attempt_replan(
                        idx, step, step_result, state,
                        pending_steps[step_cursor + 1:],
                    )
                    if replan_result is not None:
                        state.results[-1] = replan_result
                    else:
                        state.status = WorkflowStatus.FAILED
                        break

            # Guard against exceeding max steps (including inserted steps)
            if len(state.results) >= self._max_steps:
                state.status = WorkflowStatus.ABORTED
                break

            step_cursor += 1

        if state.status == WorkflowStatus.RUNNING:
            state.status = WorkflowStatus.COMPLETED

        state.total_duration_ms = (time.monotonic() - start_time) * 1000
        return state

    def _execute_step(
        self, idx: int, step: WorkflowStep, state: WorkflowState
    ) -> StepResult:
        """Execute a single step with precondition validation and verification."""
        step_start = time.monotonic()

        # 1. Validate preconditions
        if not self._validate_preconditions(step, state):
            return StepResult(
                step_index=idx,
                tool_name=step.tool_name,
                status=StepStatus.FAILED,
                error="Precondition validation failed",
                duration_ms=(time.monotonic() - step_start) * 1000,
            )

        # 2. Execute tool
        try:
            result = self._execute_tool(step.tool_name, step.parameters)
        except Exception as e:
            return StepResult(
                step_index=idx,
                tool_name=step.tool_name,
                status=StepStatus.FAILED,
                error=str(e),
                duration_ms=(time.monotonic() - step_start) * 1000,
            )

        # 3. Verify result
        tool_status = result.get("status", "unknown")
        verified = False

        if tool_status in ("success", "ok"):
            if step.is_mutating:
                # NO skipping verification for mutating tools
                verified = self._verify_result(step, result)
                if not verified:
                    return StepResult(
                        step_index=idx,
                        tool_name=step.tool_name,
                        status=StepStatus.FAILED,
                        result=result,
                        error="Post-execution verification failed",
                        verified=False,
                        duration_ms=(time.monotonic() - step_start) * 1000,
                    )
            else:
                verified = True  # Read-only tools pass verification

            return StepResult(
                step_index=idx,
                tool_name=step.tool_name,
                status=StepStatus.SUCCESS,
                result=result,
                verified=verified,
                duration_ms=(time.monotonic() - step_start) * 1000,
            )

        # Preserve tool's original error message for recovery classification
        tool_error = result.get("error", f"Tool returned status: {tool_status}")
        return StepResult(
            step_index=idx,
            tool_name=step.tool_name,
            status=StepStatus.FAILED,
            result=result,
            error=tool_error,
            duration_ms=(time.monotonic() - step_start) * 1000,
        )

    def _validate_preconditions(
        self, step: WorkflowStep, state: WorkflowState
    ) -> bool:
        """Validate step preconditions against workflow state."""
        if not step.preconditions:
            return True

        # Check that required postconditions from previous steps were met
        achieved = set()
        for r in state.results:
            if r.status == StepStatus.SUCCESS:
                post = r.result.get("postconditions", [])
                achieved.update(post)

        for pre in step.preconditions:
            if pre not in achieved and pre != "browser_session_active":
                return False
        return True

    def _verify_result(self, step: WorkflowStep, result: dict) -> bool:
        """Verify that a mutating tool achieved its expected postconditions."""
        if not step.expected_postconditions:
            # If no specific postconditions required, accept tool's own status
            return result.get("status") in ("success", "ok")

        # Check tool-reported postconditions
        actual_post = set(result.get("postconditions", []))
        for expected in step.expected_postconditions:
            if expected not in actual_post:
                return False
        return True

    def _attempt_recovery(
        self,
        idx: int,
        step: WorkflowStep,
        failed_result: StepResult,
        state: WorkflowState,
    ) -> Optional[StepResult]:
        """Attempt recovery using the mandated 3-tier strategy:
        1. Retry same tool (with wait)
        2. Alternate tool (same capability via registry)
        3. Signal replan if confidence drops
        """
        if not self._recovery:
            return None

        error_type = self._recovery.classify_error(failed_result.error or "")

        # Tier 1: Retry same tool
        for attempt in range(1, self._max_retries + 1):
            if not self._recovery.should_retry(error_type, attempt):
                break

            wait = self._recovery.wait_strategy(error_type, attempt)
            time.sleep(min(wait, 5.0))  # Cap at 5s in workflows

            try:
                result = self._execute_tool(step.tool_name, step.parameters)
                if result.get("status") in ("success", "ok"):
                    verified = True
                    if step.is_mutating:
                        verified = self._verify_result(step, result)
                    if verified:
                        return StepResult(
                            step_index=idx,
                            tool_name=step.tool_name,
                            status=StepStatus.SUCCESS,
                            result=result,
                            retry_count=attempt,
                            verified=verified,
                        )
            except Exception:
                continue

        # Tier 2: Alternate tool via capability registry
        if self._registry:
            alt_name = self._recovery.suggest_alternative(step.tool_name, error_type)
            if alt_name:
                try:
                    result = self._execute_tool(alt_name, step.parameters)
                    if result.get("status") in ("success", "ok"):
                        verified = True
                        if step.is_mutating:
                            verified = self._verify_result(step, result)
                        if verified:
                            return StepResult(
                                step_index=idx,
                                tool_name=alt_name,
                                status=StepStatus.RECOVERY,
                                result=result,
                                recovery_tool=alt_name,
                                verified=verified,
                            )
                except Exception:
                    pass

        # Tier 3: Signal replan (return None to caller)
        return None

    def _attempt_replan(
        self,
        idx: int,
        step: WorkflowStep,
        failed_result: StepResult,
        state: WorkflowState,
        remaining_steps: list[tuple[int, WorkflowStep]],
    ) -> Optional[StepResult]:
        """Tier 3 recovery: consult the replanner for intelligent recovery.

        The replanner can:
        - INSERT: Add preparatory steps before retrying the failed tool
        - REPLACE: Swap the failed tool for an alternative approach
        - REDUCE: Skip remaining steps and complete with partial results
        - ABORT: Signal unrecoverable failure (returns None)
        """
        if not self._replanner:
            return None

        from runtime.browser.replanner import ReplanAction

        error_type_name = "unknown"
        if self._recovery:
            error_type_name = self._recovery.classify_error(
                failed_result.error or ""
            ).value

        decision = self._replanner.replan(
            failed_tool=step.tool_name,
            error_type=error_type_name,
            error_message=failed_result.error or "",
            remaining_steps=[s.tool_name for _, s in remaining_steps],
        )

        if decision.action == ReplanAction.INSERT:
            # Execute preparatory steps, then retry original tool
            for prep_tool in decision.inserted_steps:
                try:
                    prep_result = self._execute_tool(prep_tool, step.parameters)
                    if prep_result.get("status") not in ("success", "ok"):
                        return None  # Prep step failed, abort
                except Exception:
                    return None

            # Retry original tool after prep steps
            try:
                result = self._execute_tool(step.tool_name, step.parameters)
                if result.get("status") in ("success", "ok"):
                    return StepResult(
                        step_index=idx,
                        tool_name=step.tool_name,
                        status=StepStatus.RECOVERY,
                        result=result,
                        replan_action=ReplanAction.INSERT.value,
                        verified=self._verify_result(step, result)
                        if step.is_mutating
                        else True,
                    )
            except Exception:
                return None

        elif decision.action == ReplanAction.REPLACE:
            # Execute replacement tool instead
            replacement = decision.replacement_tool
            if replacement:
                try:
                    result = self._execute_tool(replacement, step.parameters)
                    if result.get("status") in ("success", "ok"):
                        return StepResult(
                            step_index=idx,
                            tool_name=replacement,
                            status=StepStatus.RECOVERY,
                            result=result,
                            recovery_tool=replacement,
                            replan_action=ReplanAction.REPLACE.value,
                            verified=self._verify_result(step, result)
                            if step.is_mutating
                            else True,
                        )
                except Exception:
                    return None

        elif decision.action == ReplanAction.REDUCE:
            # Accept partial completion — mark step as skipped
            return StepResult(
                step_index=idx,
                tool_name=step.tool_name,
                status=StepStatus.SKIPPED,
                result={"reason": decision.reason, "scope_reduced": True},
                replan_action=ReplanAction.REDUCE.value,
            )

        # ABORT or all replan attempts failed
        return None

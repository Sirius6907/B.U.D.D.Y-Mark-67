"""
agent/runtime.py — Supervised Execution Runtime (Vision-Optimized OPEV)
========================================================================
Coordinates task execution with policy enforcement, vision-augmented
verification, execution timing, and episodic memory recording.

Architecture:
    AgentRuntime        — Supervised executor with policy gates + vision verification
    RuntimeCoordinator  — Compatibility layer for main.py integration
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from buddy_logging import get_logger
from agent.budget import BudgetEngine, BudgetLimits, BudgetStatus
from agent.executor import call_tool_structured
from agent.journal import ExecutionJournal
from agent.metrics import MetricsTracker
from agent.models import ActionResult, RiskTier, TaskNode, TaskPlan, WorkflowRecipe
from agent.policy import PolicyCheck, PolicyDecision, PolicyEngine
from agent.rollback import RollbackRegistry
from agent.safety import ContentSafetyScanner, ScanResult
from agent.verifier import VerificationEngine
from agent.workflow_memory import WorkflowMemory
from agent.dp_brain import DPBrain, get_dp_brain

logger = get_logger("agent.runtime")

try:
    from memory.memory_manager import get_memory
except Exception:
    get_memory = None


@dataclass
class RuntimeStatus:
    """Live status of the runtime for UI dashboards."""
    current_goal: str = ""
    current_step: str = ""
    pending_approval: bool = False
    voice_state: str = "idle"
    total_steps: int = 0
    completed_steps: int = 0
    elapsed_ms: float = 0.0
    active_workflow_id: str = ""
    active_draft_id: str = ""
    watchdog_timeout_state: str = ""


class AgentRuntime:
    """
    Supervised task executor. Runs a list of TaskNodes sequentially with:
    - Policy gating (approval for high-risk actions)
    - Vision-augmented step verification (rule-based + VLM screenshot checks)
    - Execution timing (per-step + total)
    - Structured journal logging
    - Pre-execution vision observation (optional)
    """

    def __init__(
        self,
        executor=None,
        verifier: VerificationEngine | None = None,
        policy: PolicyEngine | None = None,
        workflow_memory=None,
        dp_brain: DPBrain | None = None,
        approval_callback: Callable[[str], bool] | None = None,
        status_callback: Callable[[RuntimeStatus], None] | None = None,
        metrics: MetricsTracker | None = None,
        budget: BudgetEngine | None = None,
        rollback: RollbackRegistry | None = None,
        safety_scanner: ContentSafetyScanner | None = None,
    ):
        self.executor = executor or _StructuredExecutorAdapter()
        self.verifier = verifier or VerificationEngine(enable_vision=os.getenv("BUDDY_ENV", "").lower() != "test")
        self.policy = policy or PolicyEngine()
        self.workflow_memory = workflow_memory
        self.dp_brain = dp_brain
        self.approval_callback = approval_callback
        self.status_callback = status_callback
        self.metrics = metrics or MetricsTracker()
        self.journal = ExecutionJournal()
        self.status = RuntimeStatus()
        self.budget = budget or BudgetEngine()
        self.rollback = rollback or RollbackRegistry()
        self.safety = safety_scanner or ContentSafetyScanner()

    def run(self, nodes: list[TaskNode], goal: str = "") -> list[ActionResult]:
        """Synchronous OPEV loop — Observe-Plan-Execute-Verify."""
        run_start = time.time()
        self.budget.start()
        self.status.current_goal = goal
        self.status.total_steps = len(nodes)
        self.status.completed_steps = 0
        self._emit_status()
        if self.dp_brain is not None and goal:
            self.dp_brain.save_checkpoint(goal, nodes, 0)

        results: list[ActionResult] = []
        completed: set[str] = set()

        logger.info(
            "Runtime started: goal=%r, steps=%d",
            goal[:80] if goal else "(none)",
            len(nodes),
        )

        for idx, node in enumerate(nodes):
            step_label = f"[{idx + 1}/{len(nodes)}]"

            # ── BUDGET CHECK ──────────────────────────────────────────────
            if not self.budget.can_proceed():
                snap = self.budget.snapshot()
                result = ActionResult(
                    status="error",
                    summary=f"Budget exceeded ({snap.status.value}): {snap.steps_used}/{snap.steps_limit} steps, {snap.wall_elapsed:.1f}s/{snap.wall_limit:.0f}s",
                    retryable=False,
                )
                node.result = result
                self.journal.record(node.node_id, result.status, result.summary)
                results.append(result)
                logger.warning("%s Budget exceeded — halting", step_label)
                break

            # ── OBSERVE: Dependency check ─────────────────────────────────
            unmet = [dep for dep in node.depends_on if dep not in completed]
            if unmet:
                result = ActionResult(
                    status="error",
                    summary=f"Skipped {node.node_id}; unmet dependencies: {', '.join(unmet)}",
                    retryable=False,
                )
                node.result = result
                self.journal.record(node.node_id, result.status, result.summary)
                results.append(result)
                if self.dp_brain is not None:
                    self.dp_brain.update_reward(result)
                logger.warning("%s Skipped %s — unmet deps: %s", step_label, node.node_id, unmet)
                break

            self.status.current_step = node.objective
            self.status.pending_approval = False
            self._emit_status()

            # ── PLAN: Policy gate ─────────────────────────────────────────
            check = self.policy.check_node(node)

            # Scope violation → block + telemetry
            if check.decision is PolicyDecision.BLOCK:
                self.metrics.record_scope_violation(node.node_id, node.tool, check.missing_scopes)
                result = ActionResult(
                    status="error",
                    summary=f"Blocked: {check.reason}",
                    retryable=False,
                )
                node.result = result
                self.journal.record(node.node_id, result.status, result.summary, tool=node.tool, scope_check="blocked")
                results.append(result)
                logger.warning("%s BLOCKED %s: %s", step_label, node.node_id, check.reason)
                break

            if check.decision is PolicyDecision.REQUIRE_APPROVAL:
                self.status.pending_approval = True
                self._emit_status()
                logger.info("%s Approval required for %s (%s)", step_label, node.node_id, node.tool)

                approval_start = time.time()
                approved = self._request_approval(node)
                approval_ms = (time.time() - approval_start) * 1000
                self.metrics.record_approval(node.node_id, node.tool, approved, approval_ms)
                self.status.pending_approval = False
                self._emit_status()

                if not approved:
                    result = ActionResult(
                        status="pending_approval",
                        summary=f"Approval denied for {node.objective}",
                        needs_approval=True,
                        retryable=False,
                    )
                    node.result = result
                    self.journal.record(node.node_id, result.status, result.summary, tool=node.tool, scope_check="denied")
                    results.append(result)
                    if self.dp_brain is not None:
                        self.dp_brain.update_reward(result)
                    logger.info("%s User denied approval for %s", step_label, node.node_id)
                    break

            # ── ROLLBACK SNAPSHOT ─────────────────────────────────────────
            self._snapshot_before_execute(node, task_id=goal or "unknown")

            # ── SAFETY SCAN ──────────────────────────────────────────────
            scan = self.safety.scan_node(node.tool, node.parameters, node.objective)
            if scan.blocked:
                threat_desc = scan.summary()
                self.metrics.record_scope_violation(
                    node.node_id, node.tool,
                    [s.category.value for s in scan.signals],
                )
                result = ActionResult(
                    status="error",
                    summary=f"Safety blocked: {threat_desc}",
                    retryable=False,
                )
                node.result = result
                self.journal.record(
                    node.node_id, result.status, result.summary,
                    tool=node.tool, scope_check="safety_blocked",
                )
                results.append(result)
                logger.warning(
                    "%s SAFETY BLOCKED %s: %s",
                    step_label, node.node_id, threat_desc,
                )
                break
            elif scan.needs_approval and not check.decision == PolicyDecision.REQUIRE_APPROVAL:
                # Medium severity: if not already approved, require approval now
                logger.info(
                    "%s Safety concern detected for %s: %s",
                    step_label, node.node_id, scan.summary(),
                )

            # ── EXECUTE ───────────────────────────────────────────────────
            result, step_ms = self._execute_with_retries_sync(node)

            # Record budget step + cost
            step_cost = step_ms / 1000.0  # wall-seconds as cost proxy
            budget_status = self.budget.record_step(cost=step_cost)

            node.result = result
            self.metrics.record_step(node.node_id, node.tool, result.status, step_ms, goal=goal)
            scope_label = "approved" if check.decision is PolicyDecision.REQUIRE_APPROVAL else "passed"
            snap = self.budget.snapshot()
            budget_str = f"{snap.steps_used}/{snap.steps_limit} steps, {snap.remaining_seconds:.0f}s left" if hasattr(snap, 'remaining_seconds') else f"{snap.steps_used}/{snap.steps_limit} steps"
            self.journal.record(node.node_id, result.status, result.summary, tool=node.tool, latency_ms=step_ms, scope_check=scope_label, budget_remaining=f"{self.budget.remaining_steps()}/{snap.steps_limit} steps", rollback_available=bool(self.rollback.get_pending()))
            results.append(result)

            logger.info(
                "%s Step %s [%s] → %s (%.0fms)",
                step_label,
                node.node_id,
                node.tool,
                result.status,
                step_ms,
            )

            # ── VERIFY (hybrid: rule-based + optional vision) ─────────────
            verified = True
            critique = ""
            verify_ms = 0.0
            if result.status == "success":
                verify_start = time.time()
                verified, critique = self.verifier.verify_sync(node, result)
                verify_ms = (time.time() - verify_start) * 1000
                self.metrics.record_verification(node.node_id, verified, "hybrid", verify_ms)

            if result.status == "success" and verify_ms > 100:
                logger.info("%s Verification took %.0fms", step_label, verify_ms)

            if not verified:
                failure = ActionResult(
                    status="error",
                    summary=critique,
                    observations={"verification_failed_for": node.node_id},
                    retryable=result.retryable,
                )
                node.result = failure
                self.journal.record(node.node_id, failure.status, failure.summary)
                results[-1] = failure
                if self.dp_brain is not None:
                    self.dp_brain.update_reward(failure)
                logger.warning("%s Verification failed for %s: %s", step_label, node.node_id, critique)
                break
            if result.status != "success":
                if self.dp_brain is not None:
                    self.dp_brain.update_reward(result)
                logger.warning("%s Step %s failed: %s", step_label, node.node_id, result.summary)
                break

            completed.add(node.node_id)
            self.status.completed_steps = len(completed)
            if self.dp_brain is not None:
                self.dp_brain.save_checkpoint(goal, nodes, len(completed))
                self.dp_brain.update_reward(result)
            self._emit_status()

        # ── Post-run ──────────────────────────────────────────────────────
        total_ms = (time.time() - run_start) * 1000
        self.status.elapsed_ms = total_ms

        if self.workflow_memory is not None:
            self.workflow_memory.maybe_promote(goal, results)

        success_count = sum(1 for r in results if r.status == "success")
        logger.info(
            "Runtime finished: %d/%d steps succeeded in %.0fms",
            success_count,
            len(nodes),
            total_ms,
        )

        self.status.current_step = ""
        self._emit_status()
        return results

    async def run_async(self, nodes: list[TaskNode], goal: str = "") -> list[ActionResult]:
        """
        Async OPEV loop — uses async vision verification for lower latency.
        Preferred entry point when running inside an asyncio event loop.
        """
        run_start = time.time()
        self.status.current_goal = goal
        self.status.total_steps = len(nodes)
        self.status.completed_steps = 0
        self._emit_status()
        if self.dp_brain is not None and goal:
            self.dp_brain.save_checkpoint(goal, nodes, 0)

        results: list[ActionResult] = []
        completed: set[str] = set()

        logger.info(
            "Runtime (async) started: goal=%r, steps=%d",
            goal[:80] if goal else "(none)",
            len(nodes),
        )

        for idx, node in enumerate(nodes):
            step_label = f"[{idx + 1}/{len(nodes)}]"

            # ── OBSERVE: Dependency check ─────────────────────────────────
            unmet = [dep for dep in node.depends_on if dep not in completed]
            if unmet:
                result = ActionResult(
                    status="error",
                    summary=f"Skipped {node.node_id}; unmet dependencies: {', '.join(unmet)}",
                    retryable=False,
                )
                node.result = result
                self.journal.record(node.node_id, result.status, result.summary)
                results.append(result)
                logger.warning("%s Skipped %s — unmet deps: %s", step_label, node.node_id, unmet)
                break

            self.status.current_step = node.objective
            self.status.pending_approval = False
            self._emit_status()

            # ── PLAN: Policy gate ─────────────────────────────────────────
            check = self.policy.check_node(node)
            if check.decision is PolicyDecision.REQUIRE_APPROVAL:
                self.status.pending_approval = True
                self._emit_status()

                approved = self._request_approval(node)
                self.status.pending_approval = False
                self._emit_status()

                if not approved:
                    result = ActionResult(
                        status="pending_approval",
                        summary=f"Approval denied for {node.objective}",
                        needs_approval=True,
                        retryable=False,
                    )
                    node.result = result
                    self.journal.record(node.node_id, result.status, result.summary)
                    results.append(result)
                    if self.dp_brain is not None:
                        self.dp_brain.update_reward(result)
                    break

            # ── EXECUTE (offload to thread to avoid blocking) ─────────────
            result, step_ms = await self._execute_with_retries_async(node)

            node.result = result
            self.journal.record(node.node_id, result.status, result.summary)
            results.append(result)

            logger.info(
                "%s Step %s [%s] → %s (%.0fms)",
                step_label,
                node.node_id,
                node.tool,
                result.status,
                step_ms,
            )

            # ── VERIFY (async vision-augmented) ───────────────────────────
            verified = True
            critique = ""
            verify_ms = 0.0
            if result.status == "success":
                verify_start = time.time()
                verified, critique = await self.verifier.verify(node, result)
                verify_ms = (time.time() - verify_start) * 1000

            if result.status == "success" and verify_ms > 100:
                logger.info("%s Async verification took %.0fms", step_label, verify_ms)

            if not verified:
                failure = ActionResult(
                    status="error",
                    summary=critique,
                    observations={"verification_failed_for": node.node_id},
                    retryable=result.retryable,
                )
                node.result = failure
                self.journal.record(node.node_id, failure.status, failure.summary)
                results[-1] = failure
                if self.dp_brain is not None:
                    self.dp_brain.update_reward(failure)
                logger.warning("%s Verification failed for %s: %s", step_label, node.node_id, critique)
                break
            if result.status != "success":
                if self.dp_brain is not None:
                    self.dp_brain.update_reward(result)
                logger.warning("%s Step %s failed: %s", step_label, node.node_id, result.summary)
                break

            completed.add(node.node_id)
            self.status.completed_steps = len(completed)
            if self.dp_brain is not None:
                self.dp_brain.save_checkpoint(goal, nodes, len(completed))
                self.dp_brain.update_reward(result)
            self._emit_status()

        # ── Post-run ──────────────────────────────────────────────────────
        total_ms = (time.time() - run_start) * 1000
        self.status.elapsed_ms = total_ms

        if self.workflow_memory is not None:
            self.workflow_memory.maybe_promote(goal, results)

        success_count = sum(1 for r in results if r.status == "success")
        logger.info(
            "Runtime (async) finished: %d/%d steps succeeded in %.0fms",
            success_count,
            len(nodes),
            total_ms,
        )

        self.status.current_step = ""
        self._emit_status()
        return results

    def _request_approval(self, node: TaskNode) -> bool:
        if self.approval_callback is None:
            return False
        message = f"Approve {node.tool}: {node.objective}?"
        return bool(self.approval_callback(message))

    def _execute_with_retries_sync(self, node: TaskNode) -> tuple[ActionResult, float]:
        started = time.time()
        attempts = max(1, int(node.retry_limit))
        last_result: ActionResult | None = None
        for attempt in range(1, attempts + 1):
            result = self._execute_once_sync(node)
            last_result = result
            if result.status == "success" or not result.retryable or attempt >= attempts:
                return result, (time.time() - started) * 1000
            delay = float(2 ** (attempt - 1))
            logger.info(
                "Retrying %s after retryable failure (%d/%d) in %.1fs: %s",
                node.node_id,
                attempt,
                attempts,
                delay,
                result.summary,
            )
            time.sleep(delay)
        return last_result or ActionResult(status="error", summary="Execution failed", retryable=False), (time.time() - started) * 1000

    async def _execute_with_retries_async(self, node: TaskNode) -> tuple[ActionResult, float]:
        started = time.time()
        attempts = max(1, int(node.retry_limit))
        last_result: ActionResult | None = None
        for attempt in range(1, attempts + 1):
            result = await self._execute_once_async(node)
            last_result = result
            if result.status == "success" or not result.retryable or attempt >= attempts:
                return result, (time.time() - started) * 1000
            delay = float(2 ** (attempt - 1))
            logger.info(
                "Retrying %s after retryable failure (%d/%d) in %.1fs: %s",
                node.node_id,
                attempt,
                attempts,
                delay,
                result.summary,
            )
            await asyncio.sleep(delay)
        return last_result or ActionResult(status="error", summary="Execution failed", retryable=False), (time.time() - started) * 1000

    def _execute_once_sync(self, node: TaskNode) -> ActionResult:
        timeout = max(float(node.timeout), 0.01)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.executor.execute_node, node)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                self.status.watchdog_timeout_state = f"{node.node_id} timed out"
                self._emit_status()
                return ActionResult(
                    status="error",
                    summary=f"Step {node.node_id} timed out after {timeout:.2f}s",
                    retryable=False,
                    error_message="timeout",
                    observations={"timeout_seconds": timeout},
                )
            except Exception as exc:
                return ActionResult(
                    status="error",
                    summary=f"Step {node.node_id} failed: {exc}",
                    retryable=True,
                    error_message=str(exc),
                )

    async def _execute_once_async(self, node: TaskNode) -> ActionResult:
        timeout = max(float(node.timeout), 0.01)
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self.executor.execute_node, node),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            self.status.watchdog_timeout_state = f"{node.node_id} timed out"
            self._emit_status()
            return ActionResult(
                status="error",
                summary=f"Step {node.node_id} timed out after {timeout:.2f}s",
                retryable=False,
                error_message="timeout",
                observations={"timeout_seconds": timeout},
            )
        except Exception as exc:
            return ActionResult(
                status="error",
                summary=f"Step {node.node_id} failed: {exc}",
                retryable=True,
                error_message=str(exc),
            )

    # ── Rollback integration ──────────────────────────────
    # Tools whose actions need rollback protection
    _FILE_WRITE_TOOLS = {"file_controller", "backup_manager"}
    _FILE_DELETE_TOOLS = {"file_controller"}
    _SYSTEM_TOOLS = {"computer_control", "process_shield", "firewall_manager",
                     "bluetooth_manager", "recovery_manager"}

    def _snapshot_before_execute(self, node: TaskNode, task_id: str) -> None:
        """Take a rollback snapshot before executing a potentially destructive action."""
        tool = node.tool
        params = node.parameters if hasattr(node, "parameters") else {}
        action = params.get("action", "") if isinstance(params, dict) else ""
        file_path = params.get("file_path", "") or params.get("path", "") if isinstance(params, dict) else ""

        try:
            if tool in self._FILE_WRITE_TOOLS and action in ("create", "write", "append"):
                if file_path and Path(file_path).exists():
                    self.rollback.snapshot_file_modify(task_id, file_path)
                elif file_path:
                    self.rollback.snapshot_file_create(task_id, file_path)

            elif tool in self._FILE_DELETE_TOOLS and action == "delete":
                if file_path:
                    self.rollback.snapshot_file_delete(task_id, file_path)

            elif tool in self._SYSTEM_TOOLS:
                self.rollback.snapshot_custom(
                    task_id,
                    description=f"System action: {tool}.{action}",
                    metadata={"tool": tool, "action": action, "node_id": node.node_id},
                )
        except Exception as exc:
            logger.debug("Rollback snapshot failed for %s: %s", node.node_id, exc)

    def _emit_status(self) -> None:
        if self.status_callback is not None:
            try:
                self.status_callback(self.status)
            except Exception as exc:
                logger.debug("Status callback error: %s", exc)


class RuntimeCoordinator:
    """
    Compatibility layer for the existing app. Keeps the old API while routing
    execution through the supervised runtime.
    """

    def __init__(
        self,
        api_key: str | None = None,
        speak_fn: Optional[Callable] = None,
        approval_callback: Callable[[str], bool] | None = None,
        status_callback: Callable[[RuntimeStatus], None] | None = None,
        policy: PolicyEngine | None = None,
    ):
        self.api_key = api_key
        self.speak = speak_fn
        self.memory = None
        self._external_status_callback = status_callback
        self.runtime = AgentRuntime(
            verifier=VerificationEngine(api_key),
            policy=policy or PolicyEngine(),
            workflow_memory=WorkflowMemory(),
            dp_brain=get_dp_brain(),
            approval_callback=approval_callback,
            status_callback=self._handle_status_update,
        )

    async def execute_plan(self, plan: TaskPlan) -> bool:
        """Execute a task plan using the async OPEV loop."""
        memory = self._get_memory()
        self.runtime.status.active_workflow_id = plan.plan_id

        # Recall similar past episodes for context
        if memory is not None:
            try:
                await asyncio.to_thread(
                    memory.search_episodes, plan.goal, n_results=1
                )
            except Exception:
                pass

        # Use the async runtime for vision-verified execution
        results = await self.runtime.run_async(plan.nodes, plan.goal)
        success = bool(results) and all(result.status == "success" for result in results)
        self.runtime.status.active_workflow_id = ""
        self.runtime._emit_status()
        self._record_episode(plan, success)
        return success

    async def execute_workflow(
        self,
        recipe: WorkflowRecipe,
        runner: Callable[[WorkflowRecipe, Optional[Callable]], ActionResult],
    ) -> ActionResult:
        self.runtime.status.active_workflow_id = recipe.recipe_id
        self.runtime.status.current_goal = recipe.goal
        self.runtime.status.current_step = recipe.intent_family
        self.runtime.status.total_steps = len(recipe.steps)
        self.runtime.status.completed_steps = 0
        self.runtime._emit_status()
        memory = self._get_memory()

        if memory is not None:
            try:
                await asyncio.to_thread(memory.search_episodes, recipe.goal, n_results=1)
            except Exception:
                pass

        approval_node = TaskNode(
            node_id="workflow-approval",
            objective=recipe.goal,
            tool=recipe.approval_tool or (recipe.steps[0].action if recipe.steps else "workflow"),
            parameters=recipe.approval_parameters or (recipe.steps[0].parameters if recipe.steps else {}),
            expected_outcome=recipe.goal,
            risk_tier=recipe.risk_tier if isinstance(recipe.risk_tier, RiskTier) else RiskTier.TIER_1,
        )

        check = self.runtime.policy.check_node(approval_node)
        if check.decision is PolicyDecision.REQUIRE_APPROVAL:
            self.runtime.status.current_goal = recipe.goal
            self.runtime.status.total_steps = len(recipe.steps)
            self.runtime.status.pending_approval = True
            self.runtime._emit_status()
            approved = self.runtime._request_approval(approval_node)
            self.runtime.status.pending_approval = False
            self.runtime._emit_status()
            if not approved:
                self.runtime.status.active_workflow_id = ""
                self.runtime._emit_status()
                return ActionResult(
                    status="pending_approval",
                    summary=f"Approval denied for {recipe.goal}",
                    needs_approval=True,
                    retryable=False,
                )

        result = await asyncio.to_thread(runner, recipe, self.speak)
        self.runtime.status.completed_steps = len(recipe.steps) if result.status == "success" else 0
        if self.runtime.dp_brain is not None:
            completed_steps = len(recipe.steps) if result.status == "success" else int(result.observations.get("completed_steps", 0))
            recipe_nodes = [
                TaskNode(
                    node_id=f"{recipe.recipe_id}:{index}",
                    objective=step.action,
                    tool=step.action,
                    parameters=step.parameters,
                    expected_outcome=step.verify.expected_state if step.verify else recipe.goal,
                    risk_tier=recipe.risk_tier,
                )
                for index, step in enumerate(recipe.steps, start=1)
            ]
            self.runtime.dp_brain.save_checkpoint(recipe.goal, recipe_nodes, completed_steps)
            self.runtime.dp_brain.update_reward(result)
        self.runtime.status.current_step = ""
        self.runtime.status.active_workflow_id = ""
        self.runtime._emit_status()
        success = result.status == "success"
        self._record_workflow_episode(recipe, result, success)
        return result

    def _handle_status_update(self, status: RuntimeStatus) -> None:
        memory = self._get_memory()
        if memory is not None:
            try:
                memory.update_heartbeat(
                    {
                        "current_goal": status.current_goal,
                        "current_step": status.current_step,
                        "pending_approval": status.pending_approval,
                        "voice_state": status.voice_state,
                        "total_steps": status.total_steps,
                        "completed_steps": status.completed_steps,
                        "elapsed_ms": round(status.elapsed_ms, 2),
                        "active_workflow_id": status.active_workflow_id,
                        "active_draft_id": status.active_draft_id,
                        "watchdog_timeout_state": status.watchdog_timeout_state,
                    }
                )
            except Exception as exc:
                logger.debug("Failed to persist heartbeat: %s", exc)
        if self._external_status_callback is not None:
            try:
                self._external_status_callback(status)
            except Exception as exc:
                logger.debug("External status callback error: %s", exc)

    def _record_episode(self, plan: TaskPlan, success: bool) -> None:
        memory = self._get_memory()
        if memory is None:
            return

        summary = []
        for node in plan.nodes:
            summary.append(
                {
                    "id": node.node_id,
                    "tool": node.tool,
                    "status": node.result.status if node.result else "skipped",
                }
            )

        episode = {
            "plan_id": plan.plan_id or str(uuid.uuid4()),
            "goal": plan.goal,
            "success": success,
            "nodes_summary": summary,
            "learned_lesson": "Task completed successfully" if success else "Task failed",
        }
        try:
            memory.save_episode(episode)
            logger.info("Episode recorded: %s (success=%s)", episode["plan_id"], success)
        except Exception as exc:
            logger.debug("Failed to record episode: %s", exc)

    def _record_workflow_episode(self, recipe: WorkflowRecipe, result: ActionResult, success: bool) -> None:
        memory = self._get_memory()
        if memory is None:
            return

        episode = {
            "plan_id": recipe.recipe_id,
            "goal": recipe.goal,
            "success": success,
            "nodes_summary": [
                {
                    "id": f"{recipe.recipe_id}:{index}",
                    "tool": step.action,
                    "status": result.status if index == len(recipe.steps) else "success",
                }
                for index, step in enumerate(recipe.steps, start=1)
            ],
            "learned_lesson": result.summary,
        }
        try:
            memory.save_episode(episode)
            logger.info("Workflow episode recorded: %s (success=%s)", recipe.recipe_id, success)
        except Exception as exc:
            logger.debug("Failed to record workflow episode: %s", exc)

    def _get_memory(self):
        if self.memory is None and get_memory is not None:
            try:
                self.memory = get_memory()
            except Exception:
                self.memory = None
        return self.memory


class _StructuredExecutorAdapter:
    """Adapts the functional call_tool_structured() into the executor interface."""

    def execute_node(self, node: TaskNode) -> ActionResult:
        return call_tool_structured(node)

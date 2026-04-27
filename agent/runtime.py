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
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Optional

from buddy_logging import get_logger
from agent.executor import call_tool_structured
from agent.journal import ExecutionJournal
from agent.models import ActionResult, RiskTier, TaskNode, TaskPlan, WorkflowRecipe
from agent.policy import PolicyDecision, PolicyEngine
from agent.verifier import VerificationEngine
from agent.workflow_memory import WorkflowMemory

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
        approval_callback: Callable[[str], bool] | None = None,
        status_callback: Callable[[RuntimeStatus], None] | None = None,
    ):
        self.executor = executor or _StructuredExecutorAdapter()
        self.verifier = verifier or VerificationEngine()
        self.policy = policy or PolicyEngine()
        self.workflow_memory = workflow_memory
        self.approval_callback = approval_callback
        self.status_callback = status_callback
        self.journal = ExecutionJournal()
        self.status = RuntimeStatus()

    def run(self, nodes: list[TaskNode], goal: str = "") -> list[ActionResult]:
        """Synchronous OPEV loop — Observe-Plan-Execute-Verify."""
        run_start = time.time()
        self.status.current_goal = goal
        self.status.total_steps = len(nodes)
        self.status.completed_steps = 0
        self._emit_status()

        results: list[ActionResult] = []
        completed: set[str] = set()

        logger.info(
            "Runtime started: goal=%r, steps=%d",
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
                logger.info("%s Approval required for %s (%s)", step_label, node.node_id, node.tool)

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
                    logger.info("%s User denied approval for %s", step_label, node.node_id)
                    break

            # ── EXECUTE ───────────────────────────────────────────────────
            step_start = time.time()
            result = self.executor.execute_node(node)
            step_ms = (time.time() - step_start) * 1000

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

            # ── VERIFY (hybrid: rule-based + optional vision) ─────────────
            verify_start = time.time()
            verified, critique = self.verifier.verify_sync(node, result)
            verify_ms = (time.time() - verify_start) * 1000

            if verify_ms > 100:
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
                logger.warning("%s Verification failed for %s: %s", step_label, node.node_id, critique)
                break

            completed.add(node.node_id)
            self.status.completed_steps = len(completed)
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
                    break

            # ── EXECUTE (offload to thread to avoid blocking) ─────────────
            step_start = time.time()
            result = await asyncio.to_thread(self.executor.execute_node, node)
            step_ms = (time.time() - step_start) * 1000

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
            verify_start = time.time()
            verified, critique = await self.verifier.verify(node, result)
            verify_ms = (time.time() - verify_start) * 1000

            if verify_ms > 100:
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
                logger.warning("%s Verification failed for %s: %s", step_label, node.node_id, critique)
                break

            completed.add(node.node_id)
            self.status.completed_steps = len(completed)
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
    ):
        self.api_key = api_key
        self.speak = speak_fn
        self.memory = None
        self.runtime = AgentRuntime(
            verifier=VerificationEngine(api_key),
            policy=PolicyEngine(),
            workflow_memory=WorkflowMemory(),
            approval_callback=approval_callback,
            status_callback=status_callback,
        )

    async def execute_plan(self, plan: TaskPlan) -> bool:
        """Execute a task plan using the async OPEV loop."""
        memory = self._get_memory()

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
        self._record_episode(plan, success)
        return success

    async def execute_workflow(
        self,
        recipe: WorkflowRecipe,
        runner: Callable[[WorkflowRecipe, Optional[Callable]], ActionResult],
    ) -> ActionResult:
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
                return ActionResult(
                    status="pending_approval",
                    summary=f"Approval denied for {recipe.goal}",
                    needs_approval=True,
                    retryable=False,
                )

        result = await asyncio.to_thread(runner, recipe, self.speak)
        self.runtime.status.completed_steps = len(recipe.steps) if result.status == "success" else 0
        self.runtime.status.current_step = ""
        self.runtime._emit_status()
        success = result.status == "success"
        self._record_workflow_episode(recipe, result, success)
        return result

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

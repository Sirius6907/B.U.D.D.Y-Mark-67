from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable, Optional

from agent.executor import _call_tool_structured
from agent.journal import ExecutionJournal
from agent.models import ActionResult, TaskNode, TaskPlan
from agent.policy import PolicyDecision, PolicyEngine
from agent.verifier import VerificationEngine
from agent.workflow_memory import WorkflowMemory

try:
    from memory.memory_manager import get_memory
except Exception:
    get_memory = None


@dataclass
class RuntimeStatus:
    current_goal: str = ""
    current_step: str = ""
    pending_approval: bool = False
    voice_state: str = "idle"


class AgentRuntime:
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
        self.status.current_goal = goal
        self._emit_status()
        results: list[ActionResult] = []
        completed: set[str] = set()

        for node in nodes:
            unmet_dependencies = [dep for dep in node.depends_on if dep not in completed]
            if unmet_dependencies:
                result = ActionResult(
                    status="error",
                    summary=f"Skipped {node.node_id}; unmet dependencies: {', '.join(unmet_dependencies)}",
                    retryable=False,
                )
                node.result = result
                self.journal.record(node.node_id, result.status, result.summary)
                results.append(result)
                break

            self.status.current_step = node.objective
            self.status.pending_approval = False
            self._emit_status()

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

            result = self.executor.execute_node(node)
            node.result = result
            self.journal.record(node.node_id, result.status, result.summary)
            results.append(result)

            verified, critique = self.verifier.verify_sync(node, result)
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
                break

            completed.add(node.node_id)

        if self.workflow_memory is not None:
            self.workflow_memory.maybe_promote(goal, results)

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
            self.status_callback(self.status)


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
        import asyncio

        memory = self._get_memory()
        if memory is not None:
            try:
                past_episodes = await asyncio.to_thread(
                    memory.search_episodes, plan.goal, n_results=1
                )
                documents = past_episodes.get("documents") if isinstance(past_episodes, dict) else None
                if documents and documents[0] and self.speak:
                    self.speak("Recalling a similar task I completed earlier, sir.")
            except Exception:
                pass

        # Offload the synchronous runtime.run() to a thread to avoid blocking the event loop
        results = await asyncio.to_thread(self.runtime.run, plan.nodes, plan.goal)
        success = bool(results) and all(result.status == "success" for result in results)
        self._record_episode(plan, success)
        return success

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
        except Exception:
            pass

    def _get_memory(self):
        if self.memory is None and get_memory is not None:
            try:
                self.memory = get_memory()
            except Exception:
                self.memory = None
        return self.memory


class _StructuredExecutorAdapter:
    def execute_node(self, node: TaskNode) -> ActionResult:
        return _call_tool_structured(node)

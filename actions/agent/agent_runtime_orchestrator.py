from __future__ import annotations

import asyncio

from actions.base import Action, ActionRegistry
from agent.kernel import kernel
from agent.planner import create_plan
from agent.personality import build_task_failed_reply
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result

class RuntimeOrchestratorAction(Action):
    @property
    def name(self) -> str:
        return "runtime_orchestrator"

    @property
    def description(self) -> str:
        return (
            "The ELITE TIER execution engine. Use for complex, high-risk, or multi-step tasks "
            "that require strict verification, policy checks, and learning from past experience. "
            "This is 10000x more powerful than standard agent_task."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "goal": {"type": "STRING", "description": "The complex goal to achieve"}
            },
            "required": ["goal"]
        }

    def execute(self, parameters: dict, player=None, speak=None, orchestrator=None, **kwargs):
        goal = parameters.get("goal", "")
        plan = create_plan(goal)
        
        if orchestrator and hasattr(orchestrator, "runtime"):
            loop = kernel.loop or asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(orchestrator.runtime.execute_plan(plan), loop)
            success = future.result()
            msg = "I handled that full workflow for you, Buddy." if success else build_task_failed_reply()
            status = "success" if success else "failed"
            return build_tool_result(
                tool_name=self.name,
                operation="orchestrate",
                risk_level=RiskLevel.HIGH,
                status=status,
                summary=msg,
                structured_data={"success": success, "goal": goal},
                idempotent=False,
                preconditions=[],
                postconditions=[],
            )
        else:
            return build_tool_result(
                tool_name=self.name,
                operation="orchestrate",
                risk_level=RiskLevel.HIGH,
                status="failed",
                summary="I could not reach the deeper runtime for that one, Buddy.",
                structured_data={"error": "no orchestrator.runtime available"},
                idempotent=False,
                preconditions=[],
                postconditions=[],
            )

ActionRegistry.register(RuntimeOrchestratorAction)

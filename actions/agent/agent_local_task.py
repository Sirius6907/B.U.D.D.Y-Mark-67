from __future__ import annotations

import asyncio

from actions.base import Action, ActionRegistry
from agent.kernel import kernel
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result

class LocalTaskAction(Action):
    @property
    def name(self) -> str:
        return "local_task"

    @property
    def description(self) -> str:
        return (
            "Executes a cognitive task using the Gemini brain. "
            "Use for private reasoning, quick answers, or when a focused LLM response is preferred. "
            "Supports 'fast' (Gemini Flash) and 'deep' (Gemini Pro) modes."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "prompt": {"type": "STRING", "description": "The task or question for the brain"},
                "mode":   {"type": "STRING", "description": "fast | deep (default: fast)"}
            },
            "required": ["prompt"]
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        prompt = parameters.get("prompt", "")
        mode   = parameters.get("mode", "fast").lower()
        loop = kernel.loop or asyncio.get_event_loop()
        
        if mode == "deep":
            future = asyncio.run_coroutine_threadsafe(kernel.models.invoke_deep(prompt), loop)
            result = future.result()
        else:
            future = asyncio.run_coroutine_threadsafe(kernel.models.invoke_fast(prompt), loop)
            result = future.result()

        return build_tool_result(
            tool_name=self.name,
            operation="local_task",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Executed local task in {mode} mode",
            structured_data={"result": result, "mode": mode},
            idempotent=True,
            preconditions=[],
            postconditions=["task output returned"],
        )

ActionRegistry.register(LocalTaskAction)

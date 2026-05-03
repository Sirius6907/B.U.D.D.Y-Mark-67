from __future__ import annotations

from actions.base import Action, ActionRegistry
from agent.task_queue import get_queue, TaskPriority
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result

class AgentTaskAction(Action):
    @property
    def name(self) -> str:
        return "agent_task"

    @property
    def description(self) -> str:
        return (
            "Executes complex multi-step tasks requiring multiple different tools. "
            "Examples: 'research X and save to file', 'find and organize files'. "
            "DO NOT use for single commands. NEVER use for Steam/Epic — use game_updater."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "goal":     {"type": "STRING", "description": "Complete description of what to accomplish"},
                "priority": {"type": "STRING", "description": "low | normal | high (default: normal)"}
            },
            "required": ["goal"]
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
        priority = priority_map.get(parameters.get("priority", "normal").lower(), TaskPriority.NORMAL)
        goal = parameters.get("goal", "")
        task_id  = get_queue().submit(goal=goal, priority=priority, speak=speak)
        
        return build_tool_result(
            tool_name=self.name,
            operation="submit_task",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"I have started working on that for you, Buddy. Tracking ID: {task_id}.",
            structured_data={"task_id": str(task_id), "goal": goal, "priority": parameters.get("priority", "normal")},
            idempotent=False,
            preconditions=[],
            postconditions=["task submitted to queue"],
        )

ActionRegistry.register(AgentTaskAction)

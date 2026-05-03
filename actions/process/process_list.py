from __future__ import annotations

import psutil

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class ProcessListAction(Action):
    @property
    def name(self) -> str:
        return "process_list"

    @property
    def description(self) -> str:
        return "List running processes."

    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}}

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        processes = []
        for proc in psutil.process_iter(attrs=["pid", "name", "status"]):
            processes.append(proc.info)
        return build_tool_result(
            tool_name=self.name,
            operation="list",
            risk_level=RiskLevel.LOW,
            status="success",
            summary="Listed running processes",
            structured_data={"processes": processes},
            idempotent=True,
            preconditions=[],
            postconditions=["process snapshot returned"],
        )


ActionRegistry.register(ProcessListAction)

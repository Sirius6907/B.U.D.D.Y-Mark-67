from __future__ import annotations

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result

class FileSplitAction(Action):
    @property
    def name(self) -> str:
        return "file_split"

    @property
    def description(self) -> str:
        return "Dummy tool file_split."

    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}}

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        return build_tool_result(
            tool_name=self.name,
            operation="file_split",
            risk_level=RiskLevel.LOW,
            status="success",
            summary="Dummy executed",
            structured_data={},
            idempotent=True,
            preconditions=[],
            postconditions=[],
        )

ActionRegistry.register(FileSplitAction)

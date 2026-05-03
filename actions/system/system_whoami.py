from __future__ import annotations

import getpass

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class SystemWhoamiAction(Action):
    @property
    def name(self) -> str:
        return "system_whoami"

    @property
    def description(self) -> str:
        return "Get the current operating system user."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {},
            "required": [],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        user = getpass.getuser()
        return build_tool_result(
            tool_name=self.name,
            operation="whoami",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Current user: {user}",
            structured_data={"username": user},
            idempotent=True,
            preconditions=[],
            postconditions=["username retrieved"],
        )


ActionRegistry.register(SystemWhoamiAction)

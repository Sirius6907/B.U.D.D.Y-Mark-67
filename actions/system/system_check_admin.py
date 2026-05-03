from __future__ import annotations

import ctypes
import os

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class SystemCheckAdminAction(Action):
    @property
    def name(self) -> str:
        return "system_check_admin"

    @property
    def description(self) -> str:
        return "Check if the agent process is running with Administrator privileges on Windows."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {},
            "required": [],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        is_admin = False
        if os.name == 'nt':
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except AttributeError:
                is_admin = False
                
        return build_tool_result(
            tool_name=self.name,
            operation="check_admin",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Admin privileges: {'Yes' if is_admin else 'No'}",
            structured_data={"is_admin": is_admin},
            idempotent=True,
            preconditions=[],
            postconditions=["admin status checked"],
        )


ActionRegistry.register(SystemCheckAdminAction)

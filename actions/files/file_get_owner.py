from __future__ import annotations

import os
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileGetOwnerAction(Action):
    @property
    def name(self) -> str:
        return "file_get_owner"

    @property
    def description(self) -> str:
        return "Get the owner/security descriptor of a file on Windows."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        import subprocess
        path = validate_existing_path(parameters["path"])
        result_ps = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Acl '{path}').Owner"],
            capture_output=True, text=True, timeout=10,
        )
        owner = result_ps.stdout.strip() if result_ps.returncode == 0 else "unknown"
        return build_tool_result(
            tool_name=self.name,
            operation="get_owner",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Owner of {path}: {owner}",
            structured_data={"path": str(path), "owner": owner},
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["owner info returned"],
        )


ActionRegistry.register(FileGetOwnerAction)

from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class DirCreateAction(Action):
    @property
    def name(self) -> str:
        return "dir_create"

    @property
    def description(self) -> str:
        return "Create a directory, including parents if needed."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "parents": {"type": "BOOLEAN"},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = Path(parameters["path"]).expanduser()
        parents = parameters.get("parents", True)
        existed = path.exists()
        path.mkdir(parents=parents, exist_ok=True)
        verified = path.is_dir()
        result = build_tool_result(
            tool_name=self.name,
            operation="create_dir",
            risk_level=RiskLevel.LOW,
            status="success" if verified else "failed",
            summary=f"{'Existing' if existed else 'Created'} directory {path}",
            structured_data={"path": str(path), "already_existed": existed},
            idempotent=True,
            preconditions=[],
            postconditions=["directory exists"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"is_dir": path.is_dir()},
        }
        return result


ActionRegistry.register(DirCreateAction)

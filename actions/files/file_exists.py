from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class FileExistsAction(Action):
    @property
    def name(self) -> str:
        return "file_exists"

    @property
    def description(self) -> str:
        return "Check if a file or directory exists."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = Path(parameters["path"]).expanduser()
        exists = path.exists()
        data = {"path": str(path), "exists": exists}
        if exists:
            data["is_file"] = path.is_file()
            data["is_dir"] = path.is_dir()
            data["is_symlink"] = path.is_symlink()
        return build_tool_result(
            tool_name=self.name,
            operation="exists",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"{path} {'exists' if exists else 'does not exist'}",
            structured_data=data,
            idempotent=True,
            preconditions=[],
            postconditions=["existence check returned"],
        )


ActionRegistry.register(FileExistsAction)

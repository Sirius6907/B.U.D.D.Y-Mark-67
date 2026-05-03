from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class FileTouchAction(Action):
    @property
    def name(self) -> str:
        return "file_touch"

    @property
    def description(self) -> str:
        return "Create an empty file or update its modification time."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = Path(parameters["path"]).expanduser()
        if not path.parent.exists():
            raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
        existed = path.exists()
        path.touch()
        verified = path.exists()
        return build_tool_result(
            tool_name=self.name,
            operation="touch",
            risk_level=RiskLevel.LOW,
            status="success" if verified else "failed",
            summary=f"{'Updated' if existed else 'Created'} {path}",
            structured_data={"path": str(path), "created": not existed},
            idempotent=True,
            preconditions=["parent directory exists"],
            postconditions=["file exists"],
        )


ActionRegistry.register(FileTouchAction)

from __future__ import annotations

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReadTextAction(Action):
    @property
    def name(self) -> str:
        return "file_read_text"

    @property
    def description(self) -> str:
        return "Read text content from a file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        content = path.read_text(encoding="utf-8")
        return build_tool_result(
            tool_name=self.name,
            operation="read_text",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Read text from {path}",
            structured_data={"path": str(path), "content": content},
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["file content returned"],
        )


ActionRegistry.register(FileReadTextAction)

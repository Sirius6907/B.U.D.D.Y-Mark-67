from __future__ import annotations

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReadTailAction(Action):
    @property
    def name(self) -> str:
        return "file_read_tail"

    @property
    def description(self) -> str:
        return "Read the last N lines of a text file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "lines": {"type": "INTEGER"},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        n = parameters.get("lines", 10)
        all_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = all_lines[-n:] if n < len(all_lines) else all_lines
        return build_tool_result(
            tool_name=self.name,
            operation="read_tail",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Read last {len(tail)} lines from {path}",
            structured_data={
                "path": str(path),
                "total_lines": len(all_lines),
                "returned": len(tail),
                "lines": tail,
            },
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["tail lines returned"],
        )


ActionRegistry.register(FileReadTailAction)

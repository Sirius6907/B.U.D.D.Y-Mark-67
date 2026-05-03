from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReadHeadAction(Action):
    @property
    def name(self) -> str:
        return "file_read_head"

    @property
    def description(self) -> str:
        return "Read the first N lines of a text file."

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
        head = all_lines[:n]
        return build_tool_result(
            tool_name=self.name,
            operation="read_head",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Read first {len(head)} lines from {path}",
            structured_data={
                "path": str(path),
                "total_lines": len(all_lines),
                "returned": len(head),
                "lines": head,
            },
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["head lines returned"],
        )


ActionRegistry.register(FileReadHeadAction)

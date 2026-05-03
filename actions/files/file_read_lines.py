from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReadLinesAction(Action):
    @property
    def name(self) -> str:
        return "file_read_lines"

    @property
    def description(self) -> str:
        return "Read specific line range from a text file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "start": {"type": "INTEGER"},
                "end": {"type": "INTEGER"},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        all_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        start = parameters.get("start", 1) - 1
        end = parameters.get("end", len(all_lines))
        start = max(0, start)
        end = min(len(all_lines), end)
        selected = all_lines[start:end]
        return build_tool_result(
            tool_name=self.name,
            operation="read_lines",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Read lines {start+1}-{end} from {path}",
            structured_data={
                "path": str(path),
                "total_lines": len(all_lines),
                "start": start + 1,
                "end": end,
                "lines": selected,
            },
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["requested lines returned"],
        )


ActionRegistry.register(FileReadLinesAction)

from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileCountLinesAction(Action):
    @property
    def name(self) -> str:
        return "file_count_lines"

    @property
    def description(self) -> str:
        return "Count lines, words, and characters in a text file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        content = path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        words = content.split()
        return build_tool_result(
            tool_name=self.name,
            operation="count_lines",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"{path}: {len(lines)} lines, {len(words)} words, {len(content)} chars",
            structured_data={
                "path": str(path),
                "lines": len(lines),
                "words": len(words),
                "characters": len(content),
                "bytes": path.stat().st_size,
            },
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["counts returned"],
        )


ActionRegistry.register(FileCountLinesAction)

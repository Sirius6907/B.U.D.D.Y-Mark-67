from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileSearchContentAction(Action):
    @property
    def name(self) -> str:
        return "file_search_content"

    @property
    def description(self) -> str:
        return "Search for a text pattern in a file and return matching lines."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "pattern": {"type": "STRING"},
                "case_sensitive": {"type": "BOOLEAN"},
            },
            "required": ["path", "pattern"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        pattern = parameters["pattern"]
        case_sensitive = parameters.get("case_sensitive", True)
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        matches = []
        search_pat = pattern if case_sensitive else pattern.lower()
        for i, line in enumerate(lines, 1):
            compare = line if case_sensitive else line.lower()
            if search_pat in compare:
                matches.append({"line_number": i, "content": line})
        return build_tool_result(
            tool_name=self.name,
            operation="search_content",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Found {len(matches)} matches in {path}",
            structured_data={
                "path": str(path),
                "pattern": pattern,
                "match_count": len(matches),
                "matches": matches[:200],
            },
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["matching lines returned"],
        )


ActionRegistry.register(FileSearchContentAction)

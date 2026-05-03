from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReplaceTextAction(Action):
    @property
    def name(self) -> str:
        return "file_replace_text"

    @property
    def description(self) -> str:
        return "Find and replace text in a file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "find": {"type": "STRING"},
                "replace": {"type": "STRING"},
                "max_replacements": {"type": "INTEGER"},
            },
            "required": ["path", "find", "replace"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        find = parameters["find"]
        replace = parameters["replace"]
        max_repl = parameters.get("max_replacements", -1)
        original = path.read_text(encoding="utf-8")
        count = original.count(find)
        if max_repl > 0:
            new_content = original.replace(find, replace, max_repl)
            replaced = min(count, max_repl)
        else:
            new_content = original.replace(find, replace)
            replaced = count
        path.write_text(new_content, encoding="utf-8")
        return build_tool_result(
            tool_name=self.name,
            operation="replace_text",
            risk_level=RiskLevel.MEDIUM,
            status="success",
            summary=f"Replaced {replaced} occurrences in {path}",
            structured_data={
                "path": str(path),
                "find": find,
                "replace": replace,
                "occurrences_found": count,
                "replacements_made": replaced,
            },
            idempotent=False,
            preconditions=["file exists"],
            postconditions=["text replaced in file"],
        )


ActionRegistry.register(FileReplaceTextAction)

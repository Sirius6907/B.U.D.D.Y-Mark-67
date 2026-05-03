from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class FileAppendTextAction(Action):
    @property
    def name(self) -> str:
        return "file_append_text"

    @property
    def description(self) -> str:
        return "Append text to a file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "text": {"type": "STRING"},
            },
            "required": ["path", "text"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = Path(parameters["path"]).expanduser()
        if not path.parent.exists():
            raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
            
        with path.open("a", encoding="utf-8") as f:
            f.write(parameters["text"])
            
        verified = path.exists()
        result = build_tool_result(
            tool_name=self.name,
            operation="append_text",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Appended {len(parameters['text'])} chars to {path}",
            structured_data={"path": str(path), "size": path.stat().st_size},
            idempotent=False,
            preconditions=["parent directory exists"],
            postconditions=["file appended with text"],
        )
        return result


ActionRegistry.register(FileAppendTextAction)

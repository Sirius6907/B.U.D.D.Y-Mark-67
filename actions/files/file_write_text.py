from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class FileWriteTextAction(Action):
    @property
    def name(self) -> str:
        return "file_write_text"

    @property
    def description(self) -> str:
        return "Write text to a file, overwriting existing content."

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
            
        path.write_text(parameters["text"], encoding="utf-8")
        verified = path.exists() and path.stat().st_size >= len(parameters["text"].encode("utf-8"))
        result = build_tool_result(
            tool_name=self.name,
            operation="write_text",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Wrote {len(parameters['text'])} chars to {path}",
            structured_data={"path": str(path), "size": path.stat().st_size},
            idempotent=True,
            preconditions=["parent directory exists"],
            postconditions=["file overwritten with text"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"size": path.stat().st_size},
        }
        return result


ActionRegistry.register(FileWriteTextAction)

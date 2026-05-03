from __future__ import annotations

import json
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class FileWriteJsonAction(Action):
    @property
    def name(self) -> str:
        return "file_write_json"

    @property
    def description(self) -> str:
        return "Serialize and write structured data as a JSON file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "json_data": {"type": "OBJECT", "additionalProperties": True},
                "indent": {"type": "INTEGER"},
            },
            "required": ["path", "json_data"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = Path(parameters["path"]).expanduser()
        if not path.parent.exists():
            raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
        data = parameters["json_data"]
        indent = parameters.get("indent", 2)
        json_str = json.dumps(data, indent=indent, ensure_ascii=False)
        path.write_text(json_str, encoding="utf-8")
        verified = path.exists() and path.stat().st_size > 0
        return build_tool_result(
            tool_name=self.name,
            operation="write_json",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Wrote JSON data to {path}",
            structured_data={"path": str(path), "size": path.stat().st_size},
            idempotent=False,
            preconditions=["parent directory exists"],
            postconditions=["json file created/overwritten"],
        )


ActionRegistry.register(FileWriteJsonAction)

from __future__ import annotations

import json
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReadJsonAction(Action):
    @property
    def name(self) -> str:
        return "file_read_json"

    @property
    def description(self) -> str:
        return "Read and parse a JSON file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")
        
        # Determine summary of structure
        if isinstance(data, dict):
            summary_info = f"dict with {len(data)} keys"
        elif isinstance(data, list):
            summary_info = f"list with {len(data)} items"
        else:
            summary_info = f"scalar {type(data).__name__}"

        return build_tool_result(
            tool_name=self.name,
            operation="read_json",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Parsed {path} ({summary_info})",
            structured_data={"path": str(path), "json_data": data},
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["json parsed and returned"],
        )


ActionRegistry.register(FileReadJsonAction)

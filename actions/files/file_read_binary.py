from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReadBinaryAction(Action):
    @property
    def name(self) -> str:
        return "file_read_binary"

    @property
    def description(self) -> str:
        return "Read binary content from a file as base64."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "max_bytes": {"type": "INTEGER"},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        import base64
        path = validate_existing_path(parameters["path"])
        max_bytes = parameters.get("max_bytes", 10 * 1024 * 1024)
        size = path.stat().st_size
        if size > max_bytes:
            raise ValueError(f"File too large ({size} bytes), max {max_bytes}")
        raw = path.read_bytes()
        encoded = base64.b64encode(raw).decode("ascii")
        return build_tool_result(
            tool_name=self.name,
            operation="read_binary",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Read {size} bytes from {path}",
            structured_data={"path": str(path), "size": size, "base64": encoded},
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["binary content returned as base64"],
        )


ActionRegistry.register(FileReadBinaryAction)

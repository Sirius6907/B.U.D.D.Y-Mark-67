from __future__ import annotations

import base64
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class FileWriteBinaryAction(Action):
    @property
    def name(self) -> str:
        return "file_write_binary"

    @property
    def description(self) -> str:
        return "Write binary content from base64 to a file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "base64_data": {"type": "STRING"},
            },
            "required": ["path", "base64_data"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = Path(parameters["path"]).expanduser()
        if not path.parent.exists():
            raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
        raw = base64.b64decode(parameters["base64_data"])
        path.write_bytes(raw)
        verified = path.exists() and path.stat().st_size == len(raw)
        result = build_tool_result(
            tool_name=self.name,
            operation="write_binary",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Wrote {len(raw)} bytes to {path}",
            structured_data={"path": str(path), "size": len(raw)},
            idempotent=False,
            preconditions=["parent directory exists"],
            postconditions=["file written with correct size"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"size": path.stat().st_size if path.exists() else None},
        }
        return result


ActionRegistry.register(FileWriteBinaryAction)

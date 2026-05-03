from __future__ import annotations

import ctypes
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileGetAttributesAction(Action):
    @property
    def name(self) -> str:
        return "file_get_attributes"

    @property
    def description(self) -> str:
        return "Read Windows file attributes (hidden, readonly, system, archive)."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        return build_tool_result(
            tool_name=self.name,
            operation="get_attributes",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Read attributes for {path}",
            structured_data={
                "path": str(path),
                "raw": attrs,
                "hidden": bool(attrs & 0x2),
                "readonly": bool(attrs & 0x1),
                "system": bool(attrs & 0x4),
                "archive": bool(attrs & 0x20),
                "directory": bool(attrs & 0x10),
                "compressed": bool(attrs & 0x800),
                "encrypted": bool(attrs & 0x4000),
            },
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["attributes returned"],
        )


ActionRegistry.register(FileGetAttributesAction)

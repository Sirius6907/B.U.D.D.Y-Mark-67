from __future__ import annotations

import os
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileSetAttributesAction(Action):
    @property
    def name(self) -> str:
        return "file_set_attributes"

    @property
    def description(self) -> str:
        return "Set Windows file attributes (hidden, readonly, system, archive)."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "hidden": {"type": "BOOLEAN"},
                "readonly": {"type": "BOOLEAN"},
                "system": {"type": "BOOLEAN"},
                "archive": {"type": "BOOLEAN"},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        import ctypes
        path = validate_existing_path(parameters["path"])
        FILE_ATTRIBUTE_HIDDEN = 0x2
        FILE_ATTRIBUTE_READONLY = 0x1
        FILE_ATTRIBUTE_SYSTEM = 0x4
        FILE_ATTRIBUTE_ARCHIVE = 0x20
        FILE_ATTRIBUTE_NORMAL = 0x80

        attrs = 0
        if parameters.get("hidden"):
            attrs |= FILE_ATTRIBUTE_HIDDEN
        if parameters.get("readonly"):
            attrs |= FILE_ATTRIBUTE_READONLY
        if parameters.get("system"):
            attrs |= FILE_ATTRIBUTE_SYSTEM
        if parameters.get("archive", True):
            attrs |= FILE_ATTRIBUTE_ARCHIVE
        if attrs == 0:
            attrs = FILE_ATTRIBUTE_NORMAL

        ctypes.windll.kernel32.SetFileAttributesW(str(path), attrs)
        return build_tool_result(
            tool_name=self.name,
            operation="set_attributes",
            risk_level=RiskLevel.MEDIUM,
            status="success",
            summary=f"Set attributes on {path}",
            structured_data={"path": str(path), "attributes": attrs},
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["attributes applied"],
        )


ActionRegistry.register(FileSetAttributesAction)

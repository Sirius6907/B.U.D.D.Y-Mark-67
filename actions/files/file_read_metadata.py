from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReadMetadataAction(Action):
    @property
    def name(self) -> str:
        return "file_read_metadata"

    @property
    def description(self) -> str:
        return "Read file or directory metadata."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        stat = path.stat()
        return build_tool_result(
            tool_name=self.name,
            operation="read_metadata",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Read metadata for {path}",
            structured_data={
                "path": str(path),
                "is_dir": path.is_dir(),
                "size": stat.st_size,
                "modified_at": stat.st_mtime,
            },
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["metadata returned"],
        )


ActionRegistry.register(FileReadMetadataAction)

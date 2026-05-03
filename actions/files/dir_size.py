from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class DirSizeAction(Action):
    @property
    def name(self) -> str:
        return "dir_size"

    @property
    def description(self) -> str:
        return "Calculate total size of a directory recursively."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        total = 0
        file_count = 0
        dir_count = 0
        for p in path.rglob("*"):
            try:
                if p.is_file():
                    total += p.stat().st_size
                    file_count += 1
                elif p.is_dir():
                    dir_count += 1
            except OSError:
                pass
        return build_tool_result(
            tool_name=self.name,
            operation="dir_size",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"{path}: {total:,} bytes across {file_count} files",
            structured_data={
                "path": str(path),
                "total_bytes": total,
                "total_mb": round(total / (1024 * 1024), 2),
                "file_count": file_count,
                "dir_count": dir_count,
            },
            idempotent=True,
            preconditions=["path exists", "path is directory"],
            postconditions=["size computed"],
        )


ActionRegistry.register(DirSizeAction)

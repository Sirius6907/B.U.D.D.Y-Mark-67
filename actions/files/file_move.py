from __future__ import annotations

import os
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class FileMoveAction(Action):
    @property
    def name(self) -> str:
        return "file_move"

    @property
    def description(self) -> str:
        return "Move a file to a new location."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "source": {"type": "STRING"},
                "destination": {"type": "STRING"},
            },
            "required": ["source", "destination"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        from runtime.validation.files import validate_existing_path
        src = validate_existing_path(parameters["source"])
        if not src.is_file():
            raise FileNotFoundError(f"Not a file: {src}")
        dst = Path(parameters["destination"]).expanduser()
        if dst.exists():
            raise FileExistsError(f"Destination already exists: {dst}")
        if not dst.parent.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            
        src.rename(dst)
        verified = dst.is_file() and not src.exists()
        result = build_tool_result(
            tool_name=self.name,
            operation="move_file",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Moved file {src} -> {dst}",
            structured_data={"source": str(src), "destination": str(dst)},
            idempotent=False,
            preconditions=["source exists", "source is file", "destination does not exist"],
            postconditions=["file moved to destination"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"destination_is_file": dst.is_file(), "source_exists": src.exists()},
        }
        return result


ActionRegistry.register(FileMoveAction)

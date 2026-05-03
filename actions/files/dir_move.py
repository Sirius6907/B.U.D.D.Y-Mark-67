from __future__ import annotations

import shutil
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class DirMoveAction(Action):
    @property
    def name(self) -> str:
        return "dir_move"

    @property
    def description(self) -> str:
        return "Move a directory to a new location."

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
        src = validate_existing_path(parameters["source"])
        if not src.is_dir():
            raise NotADirectoryError(f"Not a directory: {src}")
        dst = Path(parameters["destination"]).expanduser()
        if dst.exists():
            raise FileExistsError(f"Destination already exists: {dst}")
        
        shutil.move(str(src), str(dst))
        verified = dst.is_dir() and not src.exists()
        result = build_tool_result(
            tool_name=self.name,
            operation="move_dir",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Moved directory {src} -> {dst}",
            structured_data={"source": str(src), "destination": str(dst)},
            idempotent=False,
            preconditions=["source exists", "source is directory", "destination does not exist"],
            postconditions=["directory moved to destination"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"destination_is_dir": dst.is_dir(), "source_exists": src.exists()},
        }
        return result


ActionRegistry.register(DirMoveAction)

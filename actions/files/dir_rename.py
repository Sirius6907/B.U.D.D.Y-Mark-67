from __future__ import annotations

import shutil
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class DirRenameAction(Action):
    @property
    def name(self) -> str:
        return "dir_rename"

    @property
    def description(self) -> str:
        return "Rename a directory in place."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "new_name": {"type": "STRING"},
            },
            "required": ["path", "new_name"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        new_path = path.parent / parameters["new_name"]
        if new_path.exists():
            raise FileExistsError(f"Target name already exists: {new_path}")
        path.rename(new_path)
        verified = new_path.is_dir() and not path.exists()
        result = build_tool_result(
            tool_name=self.name,
            operation="rename_dir",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Renamed directory {path.name} -> {new_path.name}",
            structured_data={"old_path": str(path), "new_path": str(new_path)},
            idempotent=False,
            preconditions=["source exists", "source is directory", "new name not taken"],
            postconditions=["directory renamed"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"new_exists": new_path.exists()},
        }
        return result


ActionRegistry.register(DirRenameAction)

from __future__ import annotations

import shutil

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class DirDeleteAction(Action):
    @property
    def name(self) -> str:
        return "dir_delete"

    @property
    def description(self) -> str:
        return "Delete a directory and all its contents recursively."

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
        shutil.rmtree(str(path))
        verified = not path.exists()
        result = build_tool_result(
            tool_name=self.name,
            operation="delete_dir",
            risk_level=RiskLevel.HIGH,
            status="success" if verified else "partial",
            summary=f"Deleted directory {path}",
            structured_data={"path": str(path)},
            idempotent=False,
            preconditions=["path exists", "path is directory"],
            postconditions=["directory removed"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"exists": path.exists()},
        }
        return result


ActionRegistry.register(DirDeleteAction)

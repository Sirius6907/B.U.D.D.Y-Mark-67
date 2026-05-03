from __future__ import annotations

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileDeleteAction(Action):
    @property
    def name(self) -> str:
        return "file_delete"

    @property
    def description(self) -> str:
        return "Delete a file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        if not path.is_file():
            raise FileNotFoundError(f"Not a file: {path}")
            
        path.unlink()
        verified = not path.exists()
        result = build_tool_result(
            tool_name=self.name,
            operation="delete_file",
            risk_level=RiskLevel.HIGH,
            status="success" if verified else "partial",
            summary=f"Deleted file {path}",
            structured_data={"path": str(path)},
            idempotent=False,
            preconditions=["path exists", "path is file"],
            postconditions=["file removed"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"exists": path.exists()},
        }
        return result


ActionRegistry.register(FileDeleteAction)

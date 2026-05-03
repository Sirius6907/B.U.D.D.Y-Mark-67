from __future__ import annotations

import shutil

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class DirCopyAction(Action):
    @property
    def name(self) -> str:
        return "dir_copy"

    @property
    def description(self) -> str:
        return "Copy a directory tree to a new location."

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
        from pathlib import Path
        src = validate_existing_path(parameters["source"])
        if not src.is_dir():
            raise NotADirectoryError(f"Not a directory: {src}")
        dst = Path(parameters["destination"]).expanduser()
        if dst.exists():
            raise FileExistsError(f"Destination already exists: {dst}")
        shutil.copytree(str(src), str(dst))
        verified = dst.is_dir()
        result = build_tool_result(
            tool_name=self.name,
            operation="copy_dir",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Copied directory {src} -> {dst}",
            structured_data={"source": str(src), "destination": str(dst)},
            idempotent=False,
            preconditions=["source exists", "source is directory", "destination does not exist"],
            postconditions=["destination directory tree exists"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"destination_is_dir": dst.is_dir()},
        }
        return result


ActionRegistry.register(DirCopyAction)

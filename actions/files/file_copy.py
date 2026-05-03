from __future__ import annotations

import shutil
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileCopyAction(Action):
    @property
    def name(self) -> str:
        return "file_copy"

    @property
    def description(self) -> str:
        return "Copy a file to a new location."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "source": {"type": "STRING"},
                "destination": {"type": "STRING"},
                "overwrite": {"type": "BOOLEAN"},
            },
            "required": ["source", "destination"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        src = validate_existing_path(parameters["source"])
        if not src.is_file():
            raise FileNotFoundError(f"Not a file: {src}")
        dst = Path(parameters["destination"]).expanduser()
        overwrite = parameters.get("overwrite", False)
        
        if dst.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists: {dst}")
        
        if not dst.parent.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            
        shutil.copy2(src, dst)
        verified = dst.is_file() and dst.stat().st_size == src.stat().st_size
        result = build_tool_result(
            tool_name=self.name,
            operation="copy_file",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Copied file {src} -> {dst}",
            structured_data={"source": str(src), "destination": str(dst)},
            idempotent=True,
            preconditions=["source exists", "source is file"],
            postconditions=["destination file matches source file size"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"destination_is_file": dst.is_file()},
        }
        return result


ActionRegistry.register(FileCopyAction)

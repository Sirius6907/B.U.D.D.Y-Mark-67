from __future__ import annotations

import zipfile
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileExtractZipAction(Action):
    @property
    def name(self) -> str:
        return "file_extract_zip"

    @property
    def description(self) -> str:
        return "Extract files from a ZIP archive."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "archive": {"type": "STRING"},
                "destination": {"type": "STRING"},
            },
            "required": ["archive", "destination"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        archive = validate_existing_path(parameters["archive"])
        dst = Path(parameters["destination"]).expanduser()
        dst.mkdir(parents=True, exist_ok=True)
        count = 0
        with zipfile.ZipFile(archive, "r") as zf:
            count = len(zf.infolist())
            zf.extractall(dst)
        verified = dst.exists() and any(dst.iterdir())
        result = build_tool_result(
            tool_name=self.name,
            operation="extract_zip",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Extracted {count} files to {dst}",
            structured_data={
                "archive": str(archive),
                "destination": str(dst),
                "files_extracted": count,
            },
            idempotent=False,
            preconditions=["archive exists"],
            postconditions=["archive contents extracted to destination"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"destination_has_files": verified},
        }
        return result


ActionRegistry.register(FileExtractZipAction)

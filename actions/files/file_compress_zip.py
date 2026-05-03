from __future__ import annotations

import zipfile
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileCompressZipAction(Action):
    @property
    def name(self) -> str:
        return "file_compress_zip"

    @property
    def description(self) -> str:
        return "Compress files or a directory into a ZIP archive."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "source": {"type": "STRING"},
                "output": {"type": "STRING"},
            },
            "required": ["source", "output"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        src = validate_existing_path(parameters["source"])
        out = Path(parameters["output"]).expanduser()
        count = 0
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            if src.is_dir():
                for f in src.rglob("*"):
                    if f.is_file():
                        zf.write(f, f.relative_to(src))
                        count += 1
            else:
                zf.write(src, src.name)
                count = 1
        verified = out.exists() and out.stat().st_size > 0
        result = build_tool_result(
            tool_name=self.name,
            operation="compress_zip",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Compressed {count} files into {out}",
            structured_data={
                "source": str(src),
                "output": str(out),
                "file_count": count,
                "archive_size": out.stat().st_size if out.exists() else 0,
            },
            idempotent=False,
            preconditions=["source exists"],
            postconditions=["zip archive created"],
        )
        result["verification"] = {
            "status": "verified" if verified else "failed",
            "observed_state": {"archive_exists": out.exists()},
        }
        return result


ActionRegistry.register(FileCompressZipAction)

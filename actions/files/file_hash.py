from __future__ import annotations

import hashlib
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileHashAction(Action):
    @property
    def name(self) -> str:
        return "file_hash"

    @property
    def description(self) -> str:
        return "Compute hash digest of a file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "algorithm": {"type": "STRING", "enum": ["md5", "sha1", "sha256", "sha512"]},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        algo = parameters.get("algorithm", "sha256")
        h = hashlib.new(algo)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        digest = h.hexdigest()
        return build_tool_result(
            tool_name=self.name,
            operation="hash",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"{algo} hash of {path}",
            structured_data={"path": str(path), "algorithm": algo, "digest": digest},
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["hash digest computed"],
        )


ActionRegistry.register(FileHashAction)

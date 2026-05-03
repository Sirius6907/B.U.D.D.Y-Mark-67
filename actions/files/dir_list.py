from __future__ import annotations

from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class DirListAction(Action):
    @property
    def name(self) -> str:
        return "dir_list"

    @property
    def description(self) -> str:
        return "List contents of a directory with metadata."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "recursive": {"type": "BOOLEAN"},
                "pattern": {"type": "STRING"},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        recursive = parameters.get("recursive", False)
        pattern = parameters.get("pattern", "*")
        glob_fn = path.rglob if recursive else path.glob
        entries = []
        for p in sorted(glob_fn(pattern)):
            try:
                stat = p.stat()
                entries.append({
                    "name": p.name,
                    "path": str(p),
                    "is_dir": p.is_dir(),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
            except OSError:
                entries.append({"name": p.name, "path": str(p), "error": "access denied"})
            if len(entries) >= 1000:
                break
        return build_tool_result(
            tool_name=self.name,
            operation="list_dir",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Listed {len(entries)} entries in {path}",
            structured_data={"path": str(path), "count": len(entries), "entries": entries},
            idempotent=True,
            preconditions=["path exists", "path is directory"],
            postconditions=["directory listing returned"],
        )


ActionRegistry.register(DirListAction)

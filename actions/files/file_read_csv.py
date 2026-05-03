from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.files import validate_existing_path


class FileReadCsvAction(Action):
    @property
    def name(self) -> str:
        return "file_read_csv"

    @property
    def description(self) -> str:
        return "Read and parse a CSV file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "has_header": {"type": "BOOLEAN"},
                "delimiter": {"type": "STRING"},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = validate_existing_path(parameters["path"])
        has_header = parameters.get("has_header", True)
        delimiter = parameters.get("delimiter", ",")
        content = path.read_text(encoding="utf-8", errors="replace")
        f = StringIO(content)
        
        rows = []
        if has_header:
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)
        else:
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)

        return build_tool_result(
            tool_name=self.name,
            operation="read_csv",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Parsed CSV from {path} ({len(rows)} rows)",
            structured_data={
                "path": str(path),
                "row_count": len(rows),
                "rows": rows[:1000],  # cap at 1000 rows to prevent massive output
            },
            idempotent=True,
            preconditions=["path exists"],
            postconditions=["csv parsed and returned"],
        )


ActionRegistry.register(FileReadCsvAction)

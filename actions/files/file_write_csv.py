from __future__ import annotations

import csv
from pathlib import Path

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class FileWriteCsvAction(Action):
    @property
    def name(self) -> str:
        return "file_write_csv"

    @property
    def description(self) -> str:
        return "Write rows to a CSV file."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "rows": {"type": "ARRAY", "items": {"type": ["ARRAY", "OBJECT"]}},
                "fieldnames": {"type": "ARRAY", "items": {"type": "STRING"}},
                "delimiter": {"type": "STRING"},
            },
            "required": ["path", "rows"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        path = Path(parameters["path"]).expanduser()
        if not path.parent.exists():
            raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
        rows = parameters["rows"]
        fieldnames = parameters.get("fieldnames")
        delimiter = parameters.get("delimiter", ",")
        
        with open(path, "w", newline="", encoding="utf-8") as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                for row in rows:
                    if isinstance(row, dict):
                        writer.writerow(row)
                    else:
                        writer.writerow(dict(zip(fieldnames, row)))
            else:
                writer = csv.writer(f, delimiter=delimiter)
                for row in rows:
                    if isinstance(row, dict):
                        writer.writerow(row.values())
                    else:
                        writer.writerow(row)
        
        verified = path.exists() and path.stat().st_size > 0
        return build_tool_result(
            tool_name=self.name,
            operation="write_csv",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verified else "partial",
            summary=f"Wrote {len(rows)} rows to {path}",
            structured_data={"path": str(path), "row_count": len(rows)},
            idempotent=False,
            preconditions=["parent directory exists"],
            postconditions=["csv file created/overwritten"],
        )


ActionRegistry.register(FileWriteCsvAction)

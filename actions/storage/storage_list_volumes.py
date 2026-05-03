from __future__ import annotations

from pathlib import Path

import psutil

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class StorageListVolumesAction(Action):
    @property
    def name(self) -> str:
        return "storage_list_volumes"

    @property
    def description(self) -> str:
        return "List local storage volumes and mount points."

    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}}

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        volumes = [
            {
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "exists": Path(part.mountpoint).exists(),
            }
            for part in psutil.disk_partitions(all=False)
        ]
        return build_tool_result(
            tool_name=self.name,
            operation="list_volumes",
            risk_level=RiskLevel.LOW,
            status="success",
            summary="Listed storage volumes",
            structured_data={"volumes": volumes},
            idempotent=True,
            preconditions=[],
            postconditions=["volume inventory returned"],
        )


ActionRegistry.register(StorageListVolumesAction)

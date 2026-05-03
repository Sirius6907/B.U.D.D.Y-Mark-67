from __future__ import annotations

import psutil

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class NetworkListAdaptersAction(Action):
    @property
    def name(self) -> str:
        return "network_list_adapters"

    @property
    def description(self) -> str:
        return "List network adapters and addresses."

    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}}

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        adapters = {
            name: [str(address.address) for address in addresses]
            for name, addresses in psutil.net_if_addrs().items()
        }
        return build_tool_result(
            tool_name=self.name,
            operation="list_adapters",
            risk_level=RiskLevel.LOW,
            status="success",
            summary="Listed network adapters",
            structured_data={"adapters": adapters},
            idempotent=True,
            preconditions=[],
            postconditions=["network adapter inventory returned"],
        )


ActionRegistry.register(NetworkListAdaptersAction)

from __future__ import annotations

import socket

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.validation.network import validate_hostname
from runtime.verification.network import verify_reachability


class NetworkReachabilityCheckAction(Action):
    @property
    def name(self) -> str:
        return "network_reachability_check"

    @property
    def description(self) -> str:
        return "Check whether a host is reachable on a TCP port."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "hostname": {"type": "STRING"},
                "port": {"type": "INTEGER"},
                "timeout": {"type": "NUMBER"},
            },
            "required": ["hostname"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        hostname = validate_hostname(parameters["hostname"])
        port = int(parameters.get("port", 80))
        timeout = float(parameters.get("timeout", 1.0))
        reachable = False
        try:
            with socket.create_connection((hostname, port), timeout=timeout):
                reachable = True
        except OSError:
            reachable = False

        verification = verify_reachability(hostname, reachable)
        result = build_tool_result(
            tool_name=self.name,
            operation="reachability_check",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Checked reachability for {hostname}:{port}",
            structured_data={"hostname": hostname, "port": port, "reachable": reachable},
            idempotent=True,
            preconditions=["hostname is valid"],
            postconditions=["reachability result returned"],
        )
        result["verification"] = {
            "status": verification.status,
            "observed_state": verification.observed_state,
        }
        return result


ActionRegistry.register(NetworkReachabilityCheckAction)

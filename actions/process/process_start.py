from __future__ import annotations

import subprocess

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result
from runtime.verification.process import verify_process_running


class ProcessStartAction(Action):
    @property
    def name(self) -> str:
        return "process_start"

    @property
    def description(self) -> str:
        return "Start a process from a command."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "command": {"type": "STRING"},
            },
            "required": ["command"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        proc = subprocess.Popen(parameters["command"], shell=True)
        verification = verify_process_running(proc.pid, proc.poll() is None)
        result = build_tool_result(
            tool_name=self.name,
            operation="start",
            risk_level=RiskLevel.MEDIUM,
            status="success" if verification.status == "verified" else "partial",
            summary=f"Started process {proc.pid}",
            structured_data={"pid": proc.pid, "command": parameters["command"]},
            idempotent=False,
            preconditions=["command is valid"],
            postconditions=["process is running"],
        )
        result["verification"] = {
            "status": verification.status,
            "observed_state": verification.observed_state,
        }
        return result


ActionRegistry.register(ProcessStartAction)

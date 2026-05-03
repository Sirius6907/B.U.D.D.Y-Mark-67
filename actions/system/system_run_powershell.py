from __future__ import annotations

import os

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class SystemRunPowershellAction(Action):
    @property
    def name(self) -> str:
        return "system_run_powershell"

    @property
    def description(self) -> str:
        return "Run a PowerShell command and capture output."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "command": {"type": "STRING"},
                "timeout": {"type": "INTEGER"},
            },
            "required": ["command"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        import subprocess
        
        command = parameters["command"]
        timeout = parameters.get("timeout", 30)
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return build_tool_result(
                tool_name=self.name,
                operation="run_powershell",
                risk_level=RiskLevel.HIGH,
                status="success" if result.returncode == 0 else "failed",
                summary=f"PowerShell command exited with code {result.returncode}",
                structured_data={
                    "command": command,
                    "returncode": result.returncode,
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                },
                idempotent=False,
                preconditions=[],
                postconditions=["command executed"],
            )
            
        except subprocess.TimeoutExpired as e:
            return build_tool_result(
                tool_name=self.name,
                operation="run_powershell",
                risk_level=RiskLevel.HIGH,
                status="failed",
                summary=f"PowerShell command timed out after {timeout}s",
                structured_data={
                    "command": command,
                    "timeout": timeout,
                    "stdout": e.stdout.decode('utf-8', errors='replace').strip() if e.stdout else "",
                    "stderr": e.stderr.decode('utf-8', errors='replace').strip() if e.stderr else "",
                },
                idempotent=False,
                preconditions=[],
                postconditions=[],
            )


ActionRegistry.register(SystemRunPowershellAction)

from __future__ import annotations

import psutil

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class SystemKillProcessAction(Action):
    @property
    def name(self) -> str:
        return "system_kill_process"

    @property
    def description(self) -> str:
        return "Kill a running process by PID."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "pid": {"type": "INTEGER"},
                "force": {"type": "BOOLEAN"},
            },
            "required": ["pid"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        pid = parameters["pid"]
        force = parameters.get("force", False)
        
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            if force:
                proc.kill()
            else:
                proc.terminate()
            
            try:
                proc.wait(timeout=3)
                alive = False
            except psutil.TimeoutExpired:
                alive = proc.is_running()
                
            verified = not alive
            return build_tool_result(
                tool_name=self.name,
                operation="kill_process",
                risk_level=RiskLevel.HIGH,
                status="success" if verified else "failed",
                summary=f"Sent {'kill' if force else 'terminate'} to process {pid} ({name})",
                structured_data={
                    "pid": pid,
                    "name": name,
                    "force": force,
                    "process_dead": verified
                },
                idempotent=False,
                preconditions=[f"process {pid} exists"],
                postconditions=[f"process {pid} killed"],
            )
            
        except psutil.NoSuchProcess:
            return build_tool_result(
                tool_name=self.name,
                operation="kill_process",
                risk_level=RiskLevel.HIGH,
                status="failed",
                summary=f"Process {pid} not found",
                structured_data={"pid": pid, "error": "NoSuchProcess"},
                idempotent=False,
                preconditions=[f"process {pid} exists"],
                postconditions=[],
            )
        except psutil.AccessDenied:
            return build_tool_result(
                tool_name=self.name,
                operation="kill_process",
                risk_level=RiskLevel.HIGH,
                status="failed",
                summary=f"Access denied to kill process {pid}",
                structured_data={"pid": pid, "error": "AccessDenied"},
                idempotent=False,
                preconditions=[f"process {pid} exists"],
                postconditions=[],
            )


ActionRegistry.register(SystemKillProcessAction)

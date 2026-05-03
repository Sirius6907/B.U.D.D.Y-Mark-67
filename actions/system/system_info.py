from __future__ import annotations

import psutil

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class SystemInfoAction(Action):
    @property
    def name(self) -> str:
        return "system_info"

    @property
    def description(self) -> str:
        return "Get system overview: OS, CPU, RAM, disk."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {},
            "required": [],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        import platform
        
        cpu_usage = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "cpu_cores": psutil.cpu_count(logical=True),
            "cpu_usage_pct": cpu_usage,
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "memory_used_pct": mem.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_pct": disk.percent,
        }

        return build_tool_result(
            tool_name=self.name,
            operation="get_sysinfo",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"System: {info['os']} {info['os_release']}, CPU: {info['cpu_usage_pct']}%, RAM: {info['memory_used_pct']}%",
            structured_data=info,
            idempotent=True,
            preconditions=[],
            postconditions=["system info collected"],
        )


ActionRegistry.register(SystemInfoAction)

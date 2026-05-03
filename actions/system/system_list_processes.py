from __future__ import annotations

import psutil

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class SystemListProcessesAction(Action):
    @property
    def name(self) -> str:
        return "system_list_processes"

    @property
    def description(self) -> str:
        return "List running processes with resource usage."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "limit": {"type": "INTEGER"},
                "sort_by": {"type": "STRING", "enum": ["cpu", "memory", "pid", "name"]},
            },
            "required": [],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        limit = parameters.get("limit", 20)
        sort_by = parameters.get("sort_by", "cpu")
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
            try:
                pinfo = proc.info
                pinfo['memory_mb'] = round(pinfo['memory_info'].rss / (1024 * 1024), 2)
                del pinfo['memory_info']
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if sort_by == "cpu":
            processes.sort(key=lambda p: p.get('cpu_percent', 0), reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda p: p.get('memory_mb', 0), reverse=True)
        elif sort_by == "pid":
            processes.sort(key=lambda p: p.get('pid', 0))
        elif sort_by == "name":
            processes.sort(key=lambda p: str(p.get('name', '')).lower())
            
        top_procs = processes[:limit]

        return build_tool_result(
            tool_name=self.name,
            operation="list_processes",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Listed {len(top_procs)} processes sorted by {sort_by}",
            structured_data={
                "total_processes": len(processes),
                "returned": len(top_procs),
                "sort_by": sort_by,
                "processes": top_procs,
            },
            idempotent=True,
            preconditions=[],
            postconditions=["process list collected"],
        )


ActionRegistry.register(SystemListProcessesAction)

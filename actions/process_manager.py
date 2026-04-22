"""
Process Manager — list, inspect, and safely terminate processes.
Safety: Protected-process blocklist prevents killing system-critical processes.
"""

import psutil
from actions.base import Action, ActionRegistry


PROTECTED_PROCESSES = frozenset({
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "services.exe", "lsass.exe", "svchost.exe",
    "dwm.exe", "explorer.exe", "fontdrvhost.exe", "sihost.exe",
    "taskhostw.exe", "ctfmon.exe", "conhost.exe", "audiodg.exe",
    "searchhost.exe", "runtimebroker.exe", "securityhealthservice.exe",
    "msmpeng.exe", "nissrv.exe",
})


def process_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "list").lower()

    if action == "list":
        return _list_processes(parameters)
    if action == "info":
        return _process_info(parameters)
    if action == "kill_safe":
        return _kill_safe(parameters)
    if action == "top":
        return _top_processes(parameters)
    return f"Unknown process_manager action: {action}"


def _list_processes(params: dict) -> str:
    """List all running processes with basic info."""
    filter_name = params.get("name", "").lower()
    procs = []
    for proc in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            info = proc.info
            if filter_name and filter_name not in info["name"].lower():
                continue
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not procs:
        return "No matching processes found."

    # Sort by memory usage descending
    procs.sort(key=lambda p: p.get("memory_percent", 0) or 0, reverse=True)
    lines = [f"{'PID':>8}  {'Memory%':>8}  {'CPU%':>6}  Name"]
    lines.append("-" * 50)
    for p in procs[:50]:
        mem = f"{p.get('memory_percent', 0):.1f}%"
        cpu = f"{p.get('cpu_percent', 0):.1f}%"
        lines.append(f"{p['pid']:>8}  {mem:>8}  {cpu:>6}  {p['name']}")

    return f"Running processes ({len(procs)} total, showing top 50):\n" + "\n".join(lines)


def _process_info(params: dict) -> str:
    """Detailed info about a process by name."""
    name = params.get("name", "")
    if not name:
        return "Please specify a process name."

    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent",
                                      "memory_info", "create_time", "status", "username"]):
        try:
            info = proc.info
            if name.lower() in info["name"].lower():
                mem_mb = (info.get("memory_info") and info["memory_info"].rss / (1024 * 1024)) or 0
                return (
                    f"Process: {info['name']}\n"
                    f"  PID: {info['pid']}\n"
                    f"  Status: {info.get('status', 'unknown')}\n"
                    f"  CPU: {info.get('cpu_percent', 0):.1f}%\n"
                    f"  Memory: {mem_mb:.1f} MB ({info.get('memory_percent', 0):.1f}%)\n"
                    f"  User: {info.get('username', 'N/A')}"
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return f"Process '{name}' not found."


def _kill_safe(params: dict) -> str:
    """Terminate a process by name — with safety guardrails."""
    name = params.get("name", "")
    if not name:
        return "Please specify a process name to terminate."

    if name.lower() in PROTECTED_PROCESSES or f"{name.lower()}.exe" in PROTECTED_PROCESSES:
        return f"⛔ BLOCKED: '{name}' is a system-critical process and cannot be terminated."

    killed = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if name.lower() in proc.info["name"].lower():
                if proc.info["name"].lower() in PROTECTED_PROCESSES:
                    continue
                proc.terminate()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed == 0:
        return f"No running process matching '{name}' could be terminated."
    return f"✅ Terminated {killed} instance(s) of '{name}'."


def _top_processes(params: dict) -> str:
    """Show top N processes by CPU or memory usage."""
    count = min(int(params.get("count", 10)), 25)
    sort_by = params.get("sort_by", "memory").lower()

    key = "memory_percent" if sort_by == "memory" else "cpu_percent"
    procs = []
    for proc in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            procs.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda p: p.get(key, 0) or 0, reverse=True)
    lines = [f"Top {count} processes by {sort_by}:"]
    lines.append(f"{'#':>3}  {'PID':>8}  {'Memory%':>8}  {'CPU%':>6}  Name")
    lines.append("-" * 55)
    for i, p in enumerate(procs[:count], 1):
        mem = f"{p.get('memory_percent', 0):.1f}%"
        cpu = f"{p.get('cpu_percent', 0):.1f}%"
        lines.append(f"{i:>3}  {p['pid']:>8}  {mem:>8}  {cpu:>6}  {p['name']}")

    return "\n".join(lines)


# ----------- Action Class for ActionRegistry -----------
class ProcessManagerAction(Action):
    @property
    def name(self) -> str:
        return "process_manager"

    @property
    def description(self) -> str:
        return (
            "Manage running processes on the device. "
            "List all processes, get info about a specific process, "
            "safely terminate a process, or show top resource consumers. "
            "System-critical processes are protected and cannot be killed."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "list | info | kill_safe | top"
                },
                "name": {
                    "type": "STRING",
                    "description": "Process name to filter, inspect, or terminate"
                },
                "count": {
                    "type": "STRING",
                    "description": "Number of processes to show (for top, default 10)"
                },
                "sort_by": {
                    "type": "STRING",
                    "description": "Sort by 'cpu' or 'memory' (for top, default memory)"
                },
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return process_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(ProcessManagerAction)

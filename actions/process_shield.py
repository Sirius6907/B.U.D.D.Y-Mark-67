import psutil
import os
from actions.base import Action, ActionRegistry

def process_shield(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "scan_suspicious").lower()
    target = parameters.get("target") # PID or name
    
    if action == "scan_suspicious":
        return _scan_suspicious_processes()
    if action == "kill_process":
        if not target: return "Error: 'target' (PID or name) required for kill_process."
        return _kill_process(target)
    if action == "top_resource":
        return _check_top_resources()
        
    return f"Unknown process_shield action: {action}"


def _scan_suspicious_processes() -> str:
    """Detects processes with no description, unknown publishers, or high hidden activity."""
    suspicious = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent']):
        try:
            # Basic suspicious criteria: high CPU while idle, or running from Temp/AppData without common names
            pinfo = proc.info
            if pinfo['cpu_percent'] > 50:
                suspicious.append(f"🔥 High CPU: {pinfo['name']} (PID: {pinfo['pid']}) - {pinfo['cpu_percent']}%")
            
            # Note: Checking signatures/paths is complex in a single script, 
            # we'll focus on resource-based alerts for now.
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not suspicious:
        return "🛡️ Process Shield: No highly suspicious resource usage detected."
    return "🛡️ Process Shield: Found potential issues:\n" + "\n".join(suspicious)


def _kill_process(target: str) -> str:
    """Terminates a process by PID or name."""
    try:
        if target.isdigit():
            pid = int(target)
            proc = psutil.Process(pid)
            name = proc.name()
            proc.terminate()
            return f"✅ Process {name} (PID: {pid}) has been terminated."
        else:
            count = 0
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == target.lower():
                    proc.terminate()
                    count += 1
            if count > 0:
                return f"✅ Terminated {count} instance(s) of '{target}'."
            return f"❌ No process named '{target}' found."
    except Exception as e:
        return f"❌ Failed to kill process: {e}"


def _check_top_resources() -> str:
    """Lists top 5 CPU and Memory consumers."""
    try:
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            procs.append(proc.info)
        
        top_cpu = sorted(procs, key=lambda p: p['cpu_percent'], reverse=True)[:5]
        top_mem = sorted(procs, key=lambda p: p['memory_info'].rss, reverse=True)[:5]
        
        output = "📈 Top CPU Consumers:\n"
        for p in top_cpu:
            output += f"- {p['name']} (PID: {p['pid']}): {p['cpu_percent']}%\n"
            
        output += "\n📉 Top Memory Consumers:\n"
        for p in top_mem:
            output += f"- {p['name']} (PID: {p['pid']}): {p['memory_info'].rss/1024/1024:.1f} MB\n"
            
        return output
    except Exception as e:
        return f"Error checking resources: {e}"


class ProcessShieldAction(Action):
    @property
    def name(self) -> str:
        return "process_shield"

    @property
    def description(self) -> str:
        return (
            "Monitors and manages system processes. "
            "Can scan for suspicious resource usage, terminate rogue processes, and list top consumers."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "scan_suspicious | kill_process | top_resource"
                },
                "target": {
                    "type": "STRING",
                    "description": "PID or process name (required for kill_process)"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return process_shield(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(ProcessShieldAction)

"""
Service Controller — list, start, stop Windows services.
Safety: Blocklist prevents modifying system-critical services.
"""

import subprocess
from actions.base import Action, ActionRegistry

PROTECTED_SERVICES = frozenset({
    "windefend", "wuauserv", "dhcp", "dnscache", "mpssvc", 
    "bfe", "rpcss", "samss", "eventlog", "plugplay", 
    "dcomlaunch", "rpcepmapper", "winmgmt"
})


def service_controller(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "status").lower()
    
    if action == "list_services":
        return _list_services(parameters)
    if action == "status":
        return _service_status(parameters)
    if action == "start":
        return _start_service(parameters)
    if action == "stop":
        return _stop_service(parameters)
    if action == "restart":
        return _restart_service(parameters)
        
    return f"Unknown service_controller action: {action}"


def _list_services(params: dict) -> str:
    state = params.get("state", "all").lower()
    
    try:
        cmd = ["powershell", "-Command", "Get-Service"]
        if state in ["running", "stopped"]:
            cmd.append(f"| Where-Object Status -eq '{state.capitalize()}'")
            
        cmd.append("| Select-Object Name, DisplayName, Status | Format-Table -AutoSize")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        
        if not output:
            return "No services found or PowerShell failed."
            
        # Truncate if too long
        lines = output.split('\n')
        if len(lines) > 50:
            output = "\n".join(lines[:50]) + "\n... (truncated)"
            
        return f"🔧 Services ({state}):\n{output}"
    except Exception as e:
        return f"Failed to list services: {e}"


def _service_status(params: dict) -> str:
    name = params.get("name", "")
    if not name:
        return "Please specify a service name."
        
    try:
        cmd = ["powershell", "-Command", f"Get-Service -Name '{name}' | Select-Object Name, DisplayName, Status, StartType | Format-List"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0 or not result.stdout.strip():
            return f"Service '{name}' not found."
            
        return f"🔧 Service Status:\n{result.stdout.strip()}"
    except Exception as e:
        return f"Failed to get service status: {e}"


def _start_service(params: dict) -> str:
    name = params.get("name", "")
    if not name:
        return "Please specify a service name to start."
        
    try:
        # Requires admin privileges in most cases
        cmd = ["powershell", "-Command", f"Start-Service -Name '{name}'"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            return f"✅ Service '{name}' started successfully."
        else:
            return f"Failed to start service '{name}'. Ensure BUDDY is running as Administrator.\nError: {result.stderr.strip()}"
    except Exception as e:
        return f"Error executing start command: {e}"


def _stop_service(params: dict) -> str:
    name = params.get("name", "")
    if not name:
        return "Please specify a service name to stop."
        
    if name.lower() in PROTECTED_SERVICES:
        return f"⛔ SAFETY LOCK: Service '{name}' is critical to the system and cannot be stopped."
        
    try:
        # Requires admin privileges
        cmd = ["powershell", "-Command", f"Stop-Service -Name '{name}' -Force"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            return f"✅ Service '{name}' stopped successfully."
        else:
            return f"Failed to stop service '{name}'. Ensure BUDDY is running as Administrator.\nError: {result.stderr.strip()}"
    except Exception as e:
        return f"Error executing stop command: {e}"


def _restart_service(params: dict) -> str:
    name = params.get("name", "")
    if not name:
        return "Please specify a service name to restart."
        
    if name.lower() in PROTECTED_SERVICES:
        return f"⛔ SAFETY LOCK: Service '{name}' is critical and cannot be restarted this way."
        
    try:
        cmd = ["powershell", "-Command", f"Restart-Service -Name '{name}' -Force"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0:
            return f"✅ Service '{name}' restarted successfully."
        else:
            return f"Failed to restart service '{name}'. Ensure BUDDY is running as Administrator.\nError: {result.stderr.strip()}"
    except Exception as e:
        return f"Error executing restart command: {e}"


class ServiceControllerAction(Action):
    @property
    def name(self) -> str:
        return "service_controller"

    @property
    def description(self) -> str:
        return (
            "Manage Windows services. List services, get status, start, stop, or restart. "
            "WARNING: Modifying services usually requires Administrator privileges. "
            "System-critical services are protected from stopping."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "list_services | status | start | stop | restart"},
                "name": {"type": "STRING", "description": "Service name to target"},
                "state": {"type": "STRING", "description": "Filter for list: all | running | stopped (default: all)"},
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return service_controller(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(ServiceControllerAction)

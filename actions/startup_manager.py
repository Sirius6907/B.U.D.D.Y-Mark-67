"""
Startup Manager — list, enable, and disable startup programs.
Safety: Modifying startup entries requires precision; blocklist applied.
"""

import subprocess
from actions.base import Action, ActionRegistry

PROTECTED_STARTUP = frozenset({
    "windows defender", "securityhealth", "onedrive", 
    "igfxtray", "hkcmd", "igfxpers"
})


def startup_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "list").lower()
    
    if action == "list":
        return _list_startup()
    if action == "disable":
        return _disable_startup(parameters)
    if action == "enable":
        return _enable_startup(parameters)
        
    return f"Unknown startup_manager action: {action}"


def _list_startup() -> str:
    try:
        # Using PowerShell to query WMI for startup items
        cmd = [
            "powershell", "-Command",
            "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | Format-Table -AutoSize"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        
        if not output:
            return "No startup items found or query failed."
            
        return f"🚀 Startup Programs:\n{output}"
    except Exception as e:
        return f"Failed to list startup items: {e}"


def _disable_startup(params: dict) -> str:
    # Requires registry modification or task manager modification.
    # Advanced feature: placeholder for explicit safety.
    name = params.get("name", "")
    if not name:
        return "Please specify a startup item name to disable."
        
    if any(p in name.lower() for p in PROTECTED_STARTUP):
        return f"⛔ SAFETY LOCK: Startup item '{name}' is protected."
        
    return f"To disable '{name}', please use the Windows Task Manager (Ctrl+Shift+Esc) -> Startup tab. Automated registry modification is currently disabled for safety."


def _enable_startup(params: dict) -> str:
    name = params.get("name", "")
    if not name:
        return "Please specify a startup item name to enable."
        
    return f"To enable '{name}', please use the Windows Task Manager (Ctrl+Shift+Esc) -> Startup tab. Automated registry modification is currently disabled for safety."


class StartupManagerAction(Action):
    @property
    def name(self) -> str:
        return "startup_manager"

    @property
    def description(self) -> str:
        return "List programs that run on Windows startup. (Enable/Disable via Task Manager suggested for safety)."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "list | disable | enable"},
                "name": {"type": "STRING", "description": "Startup item name"},
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return startup_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(StartupManagerAction)

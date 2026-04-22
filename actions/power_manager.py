"""
Power Manager — shutdown, restart, sleep, lock, logoff.
Safety: Requires explicit confirmation to prevent accidental power operations.
"""

import subprocess
import ctypes
from actions.base import Action, ActionRegistry


def power_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "").lower()
    confirm = parameters.get("confirm", False)
    
    if not action:
        return "Please specify a power action: shutdown | restart | sleep | lock | logoff"
        
    if str(confirm).lower() not in ["true", "1", "yes"]:
        return f"⛔ SAFETY LOCK: The '{action}' action requires 'confirm: true' parameter."
        
    if action == "shutdown":
        return _shutdown()
    if action == "restart":
        return _restart()
    if action == "sleep":
        return _sleep()
    if action == "lock":
        return _lock()
    if action == "logoff":
        return _logoff()
        
    return f"Unknown power_manager action: {action}"


def _shutdown() -> str:
    try:
        subprocess.run(["shutdown", "/s", "/t", "5"], check=True)
        return "System will shut down in 5 seconds."
    except Exception as e:
        return f"Failed to initiate shutdown: {e}"


def _restart() -> str:
    try:
        subprocess.run(["shutdown", "/r", "/t", "5"], check=True)
        return "System will restart in 5 seconds."
    except Exception as e:
        return f"Failed to initiate restart: {e}"


def _sleep() -> str:
    try:
        # Requires hibernation to be disabled or uses hybrid sleep if enabled
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
        return "System going to sleep."
    except Exception as e:
        return f"Failed to initiate sleep: {e}"


def _lock() -> str:
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked."
    except Exception as e:
        return f"Failed to lock workstation: {e}"


def _logoff() -> str:
    try:
        subprocess.run(["shutdown", "/l"], check=True)
        return "Logging off user."
    except Exception as e:
        return f"Failed to initiate logoff: {e}"


class PowerManagerAction(Action):
    @property
    def name(self) -> str:
        return "power_manager"

    @property
    def description(self) -> str:
        return (
            "Control system power state. Actions: shutdown, restart, sleep, lock, logoff. "
            "WARNING: All actions require 'confirm: true' to be explicitly passed."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "shutdown | restart | sleep | lock | logoff"},
                "confirm": {"type": "BOOLEAN", "description": "Must be True to execute the action"},
            },
            "required": ["action", "confirm"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        if speak and parameters.get("confirm"):
            action = parameters.get("action", "")
            speak(f"Initiating system {action}.")
        return power_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(PowerManagerAction)

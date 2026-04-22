import subprocess
import os
from actions.base import Action, ActionRegistry

def access_monitor(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "check_sessions").lower()
    
    if action == "check_sessions":
        return _check_active_sessions()
    if action == "login_history":
        return _check_login_history()
    if action == "check_shares":
        return _check_network_shares()
        
    return f"Unknown access_monitor action: {action}"


def _check_active_sessions() -> str:
    """Checks for active users and remote desktop sessions."""
    try:
        # quser provides info about logged in users and their session state
        result = subprocess.run(["quser"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout.strip()
            if "rdp-tcp" in output.lower():
                return f"⚠️ ALERT: Active Remote Desktop (RDP) session detected!\n\n{output}"
            return f"👤 Active Sessions:\n{output}"
        elif result.returncode == 1 and not result.stdout:
            return "👤 No active sessions found (other than system)."
        return f"Failed to check sessions: {result.stderr}"
    except Exception as e:
        return f"Error checking sessions: {e}"


def _check_login_history() -> str:
    """Checks for recent successful and failed login attempts via Event Viewer."""
    try:
        # Event ID 4624 is successful logon, 4625 is failed
        script = """
        $logins = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624,4625} -MaxEvents 10 | 
        Select-Object TimeCreated, Id, @{N='User';E={$_.Properties[5].Value}}, @{N='Type';E={$_.Properties[8].Value}} | 
        Format-Table -AutoSize
        $logins
        """
        cmd = ["powershell", "-Command", script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return f"📜 Recent Login Activity:\n{result.stdout.strip()}"
        return f"Failed to get login history (requires Administrator privileges): {result.stderr}"
    except Exception as e:
        return f"Error checking login history: {e}"


def _check_network_shares() -> str:
    """Checks for open network shares that might expose data."""
    try:
        cmd = ["net", "share"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return f"📂 Active Network Shares:\n{result.stdout.strip()}"
        return f"Failed to check shares: {result.stderr}"
    except Exception as e:
        return f"Error checking shares: {e}"


class AccessMonitorAction(Action):
    @property
    def name(self) -> str:
        return "access_monitor"

    @property
    def description(self) -> str:
        return (
            "Monitors user access and remote connections. "
            "Can check for active RDP sessions, recent login history (success/fail), and network shares. "
            "Crucial for detecting unauthorized access."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "check_sessions | login_history | check_shares"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return access_monitor(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(AccessMonitorAction)

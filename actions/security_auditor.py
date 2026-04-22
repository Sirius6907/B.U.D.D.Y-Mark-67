import subprocess
from actions.base import Action, ActionRegistry

def security_auditor(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "full_audit").lower()
    
    if action == "full_audit":
        return _full_audit()
    if action == "check_remote_access":
        return _check_remote_access()
    if action == "check_startup":
        return _check_startup()
        
    return f"Unknown security_auditor action: {action}"


def _full_audit() -> str:
    remote_access_report = _check_remote_access()
    startup_report = _check_startup()
    
    report = [
        "🛡️ SECURITY AUDIT REPORT 🛡️",
        "=" * 30,
        "--- Remote Access Check ---",
        remote_access_report,
        "",
        "--- Startup Items Check ---",
        startup_report
    ]
    return "\n".join(report)


def _check_remote_access() -> str:
    try:
        # Check active established connections on standard RDP (3389) and SSH (22) ports
        cmd = ["netstat", "-n", "-p", "TCP"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        suspicious_connections = []
        for line in result.stdout.splitlines():
            if "ESTABLISHED" in line:
                if ":3389 " in line or ":22 " in line:
                    suspicious_connections.append(line.strip())
                    
        if suspicious_connections:
            msg = "⚠️ WARNING: Active Remote Desktop or SSH connections detected!\n"
            msg += "\n".join(suspicious_connections)
            return msg
        return "✅ No active unauthorized RDP/SSH connections detected."
    except Exception as e:
        return f"Error checking remote access: {e}"


def _check_startup() -> str:
    try:
        cmd = ["powershell", "-Command", "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | Format-List"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            # We won't analyze the whole list automatically, we'll just return it so the agent can read it
            # To prevent huge output, we'll summarize how many items there are
            output = result.stdout.strip()
            item_count = output.count("Name :")
            
            # Truncate if it's too big, just to be safe
            lines = output.splitlines()
            if len(lines) > 60:
                output = "\n".join(lines[:60]) + "\n... (truncated)"
                
            return f"Found {item_count} startup items.\n{output}"
        return f"Failed to check startup items: {result.stderr}"
    except Exception as e:
        return f"Error checking startup items: {e}"


class SecurityAuditorAction(Action):
    @property
    def name(self) -> str:
        return "security_auditor"

    @property
    def description(self) -> str:
        return (
            "Audits the system for security threats. "
            "Checks for active unauthorized remote access (RDP/SSH) and lists startup programs. "
            "Helps warn the user if anyone gets unauthorized access."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "full_audit | check_remote_access | check_startup"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return security_auditor(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(SecurityAuditorAction)

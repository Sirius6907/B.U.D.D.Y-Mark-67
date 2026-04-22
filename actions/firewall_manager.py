import subprocess
from actions.base import Action, ActionRegistry

def firewall_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "status").lower()
    
    if action == "status":
        return _firewall_status()
    if action == "enable":
        return _enable_firewall()
    if action == "disable":
        return _disable_firewall()
    if action == "block_ip":
        return _block_ip(parameters)
    if action == "block_app":
        return _block_app(parameters)
    if action == "lockdown":
        return _lockdown_mode()
    if action == "stealth_mode":
        return _stealth_mode()
        
    return f"Unknown firewall_manager action: {action}"


def _firewall_status() -> str:
    try:
        cmd = ["powershell", "-Command", "Get-NetFirewallProfile | Select-Object Name, Enabled"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return f"🛡️ Firewall Status:\n{result.stdout.strip()}"
        return f"Failed to get firewall status: {result.stderr}"
    except Exception as e:
        return f"Error executing firewall status: {e}"


def _enable_firewall() -> str:
    try:
        cmd = ["powershell", "-Command", "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return "✅ Firewall has been ENABLED for all profiles."
        return f"Failed to enable firewall (requires Administrator privileges): {result.stderr}"
    except Exception as e:
        return f"Error enabling firewall: {e}"


def _disable_firewall() -> str:
    try:
        cmd = ["powershell", "-Command", "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return "⚠️ Firewall has been DISABLED for all profiles. Device is vulnerable."
        return f"Failed to disable firewall (requires Administrator privileges): {result.stderr}"
    except Exception as e:
        return f"Error disabling firewall: {e}"


def _block_ip(params: dict) -> str:
    ip = params.get("ip", "")
    if not ip:
        return "Please specify an IP address to block."
        
    try:
        rule_name = f"BUDDY_Block_{ip.replace('.', '_')}"
        cmd = [
            "powershell", "-Command", 
            f"New-NetFirewallRule -DisplayName '{rule_name}' -Direction Inbound -Action Block -RemoteAddress {ip}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return f"⛔ Inbound traffic from IP {ip} has been blocked."
        return f"Failed to block IP (requires Administrator privileges): {result.stderr}"
    except Exception as e:
        return f"Error blocking IP: {e}"


def _block_app(params: dict) -> str:
    app_path = params.get("app_path", "")
    if not app_path:
        return "Please specify the full application path to block."
        
    try:
        app_name = app_path.split('\\')[-1]
        rule_name = f"BUDDY_BlockApp_{app_name}"
        cmd = [
            "powershell", "-Command", 
            f"New-NetFirewallRule -DisplayName '{rule_name}' -Direction Outbound -Program '{app_path}' -Action Block"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return f"⛔ Outbound network access for {app_name} has been blocked."
        return f"Failed to block app (requires Administrator privileges): {result.stderr}"
    except Exception as e:
        return f"Error blocking app: {e}"


def _lockdown_mode() -> str:
    """Blocks all outbound traffic by default and enables firewall."""
    try:
        cmds = [
            ["powershell", "-Command", "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True"],
            ["powershell", "-Command", "Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Block"]
        ]
        for cmd in cmds:
            subprocess.run(cmd, check=True, timeout=15)
        return "🚨 LOCKDOWN ACTIVE: All profiles enabled and default Outbound traffic is BLOCKED."
    except Exception as e:
        return f"Failed to initiate lockdown: {e}"


def _stealth_mode() -> str:
    """Blocks ICMP (Ping) to make the device 'invisible' on the network."""
    try:
        cmd = ["powershell", "-Command", "New-NetFirewallRule -DisplayName 'BUDDY_Stealth' -Direction Inbound -Protocol ICMPv4 -Action Block"]
        subprocess.run(cmd, check=True, timeout=15)
        return "🕵️ STEALTH MODE: Inbound ICMP (Ping) is now BLOCKED."
    except Exception as e:
        return f"Failed to enable stealth mode: {e}"


class FirewallManagerAction(Action):
    @property
    def name(self) -> str:
        return "firewall_manager"

    @property
    def description(self) -> str:
        return (
            "Advanced offensive and defensive firewall management. "
            "Can check status, enable/disable firewall, or block specific IP addresses and applications. "
            "WARNING: Modifying firewall rules requires Administrator privileges."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "status | enable | disable | block_ip | block_app | lockdown | stealth_mode"
                },
                "ip": {
                    "type": "STRING", 
                    "description": "IP address to block (for block_ip)"
                },
                "app_path": {
                    "type": "STRING", 
                    "description": "Absolute path to the application executable to block (for block_app)"
                },
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return firewall_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(FirewallManagerAction)

import subprocess
import os
import psutil
from actions.base import Action, ActionRegistry

def network_security(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "check_ports").lower()
    
    if action == "check_ports":
        return _check_listening_ports()
    if action == "check_bandwidth":
        return _check_bandwidth_usage()
    if action == "wifi_audit":
        return _wifi_audit()
        
    return f"Unknown network_security action: {action}"


def _check_listening_ports() -> str:
    """Lists all listening TCP/UDP ports."""
    try:
        cmd = ["netstat", "-ano", "-p", "TCP"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            listening = [line for line in lines if "LISTENING" in line]
            return f"🔌 Listening TCP Ports:\n" + "\n".join(listening[:20]) + ("\n... (truncated)" if len(listening) > 20 else "")
        return f"Failed to check ports: {result.stderr}"
    except Exception as e:
        return f"Error checking ports: {e}"


def _check_bandwidth_usage() -> str:
    """Checks current network interface throughput."""
    try:
        net_io = psutil.net_io_counters(pernic=True)
        stats = []
        for interface, data in net_io.items():
            if data.bytes_sent > 0 or data.bytes_recv > 0:
                stats.append(f"🌐 {interface}: Sent={data.bytes_sent/1024/1024:.2f}MB, Recv={data.bytes_recv/1024/1024:.2f}MB")
        return "📊 Bandwidth Usage (since boot):\n" + "\n".join(stats)
    except Exception as e:
        return f"Error checking bandwidth: {e}"


def _wifi_audit() -> str:
    """Scans for visible Wi-Fi networks and checks if current is secure."""
    try:
        cmd = ["netsh", "wlan", "show", "interfaces"]
        res1 = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        cmd2 = ["netsh", "wlan", "show", "networks"]
        res2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=10)
        
        output = "📶 Wi-Fi Audit:\n"
        if res1.returncode == 0:
            output += "Current Connection:\n" + res1.stdout.strip() + "\n\n"
        if res2.returncode == 0:
            output += "Visible Networks:\n" + res2.stdout.strip()
            
        return output
    except Exception as e:
        return f"Error auditing Wi-Fi: {e}"


class NetworkSecurityAction(Action):
    @property
    def name(self) -> str:
        return "network_security"

    @property
    def description(self) -> str:
        return (
            "Audits network safety and connectivity. "
            "Can list listening ports, check cumulative bandwidth usage, and scan for visible Wi-Fi networks."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "check_ports | check_bandwidth | wifi_audit"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return network_security(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(NetworkSecurityAction)

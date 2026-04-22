"""
Network Monitor — connection status, interfaces, active connections, speed test.
All read-only — no system modifications.
"""

import socket
import time
import urllib.request
import urllib.error

import psutil
from actions.base import Action, ActionRegistry


def network_monitor(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "status").lower()

    if action == "status":
        return _network_status()
    if action == "connections":
        return _active_connections(parameters)
    if action == "speed_test":
        return _speed_test()
    if action == "interfaces":
        return _interfaces()
    if action == "wifi":
        return _wifi_info()
    return f"Unknown network_monitor action: {action}"


def _network_status() -> str:
    """Check if online and get public IP."""
    online = False
    public_ip = "N/A"

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        online = True
    except OSError:
        pass

    if online:
        try:
            resp = urllib.request.urlopen("https://httpbin.org/ip", timeout=5)
            import json
            data = json.loads(resp.read().decode())
            public_ip = data.get("origin", "N/A")
        except Exception:
            public_ip = "Could not determine"

    hostname = socket.gethostname()
    local_ip = "N/A"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    status_icon = "🟢 Online" if online else "🔴 Offline"
    return (
        f"🌐 Network Status\n"
        f"  Status: {status_icon}\n"
        f"  Hostname: {hostname}\n"
        f"  Local IP: {local_ip}\n"
        f"  Public IP: {public_ip}"
    )


def _active_connections(params: dict) -> str:
    """List active network connections."""
    kind = params.get("kind", "inet").lower()
    conns = psutil.net_connections(kind=kind)

    if not conns:
        return "No active network connections found."

    lines = ["🔗 Active Connections"]
    lines.append(f"{'Proto':>6}  {'Local Address':>25}  {'Remote Address':>25}  {'Status':>15}  PID")
    lines.append("-" * 90)

    shown = 0
    for c in conns:
        if shown >= 30:
            break
        local = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "N/A"
        remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A"
        proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
        status = c.status if hasattr(c, "status") else "N/A"
        lines.append(f"{proto:>6}  {local:>25}  {remote:>25}  {status:>15}  {c.pid or 'N/A'}")
        shown += 1

    lines.append(f"\nTotal connections: {len(conns)} (showing {shown})")
    return "\n".join(lines)


def _speed_test() -> str:
    """Simple download speed test using a small test file."""
    test_url = "http://speedtest.tele2.net/1MB.zip"
    try:
        start = time.time()
        resp = urllib.request.urlopen(test_url, timeout=15)
        data = resp.read()
        elapsed = time.time() - start
        size_mb = len(data) / (1024 * 1024)
        speed_mbps = (size_mb * 8) / elapsed

        return (
            f"🚀 Speed Test Results\n"
            f"  Downloaded: {size_mb:.2f} MB\n"
            f"  Time: {elapsed:.2f} seconds\n"
            f"  Speed: {speed_mbps:.2f} Mbps"
        )
    except Exception as exc:
        return f"Speed test failed: {exc}"


def _interfaces() -> str:
    """List all network interfaces with addresses."""
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    lines = ["📡 Network Interfaces"]
    for iface, addr_list in addrs.items():
        iface_stat = stats.get(iface)
        is_up = iface_stat.isup if iface_stat else False
        speed = f"{iface_stat.speed} Mbps" if iface_stat and iface_stat.speed else "N/A"
        status_icon = "🟢" if is_up else "🔴"

        lines.append(f"\n  {status_icon} {iface} (Speed: {speed})")
        for addr in addr_list:
            family = {socket.AF_INET: "IPv4", socket.AF_INET6: "IPv6"}.get(addr.family, "MAC")
            lines.append(f"    {family}: {addr.address}")

    return "\n".join(lines)


def _wifi_info() -> str:
    """Get current Wi-Fi network info (Windows-only)."""
    import subprocess
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return f"📶 Wi-Fi Info:\n{result.stdout.strip()}"
        return "📶 No Wi-Fi interface found or not connected."
    except Exception as exc:
        return f"Wi-Fi info unavailable: {exc}"


# ----------- Action Class for ActionRegistry -----------
class NetworkMonitorAction(Action):
    @property
    def name(self) -> str:
        return "network_monitor"

    @property
    def description(self) -> str:
        return (
            "Monitor network status and connectivity. "
            "Check if online, get IP addresses, list active connections, "
            "run a speed test, or view network interfaces. "
            "Read-only — no system modifications."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "status | connections | speed_test | interfaces | wifi"
                },
                "kind": {
                    "type": "STRING",
                    "description": "Connection kind filter: inet | inet4 | inet6 | tcp | udp (default: inet)"
                },
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return network_monitor(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(NetworkMonitorAction)

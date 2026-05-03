from __future__ import annotations

import platform
import socket

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class SystemNetworkInfoAction(Action):
    @property
    def name(self) -> str:
        return "system_network_info"

    @property
    def description(self) -> str:
        return "Get basic network configuration and status."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {},
            "required": [],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        import psutil
        
        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
        except Exception:
            ip = "unknown"
            
        net_io = psutil.net_io_counters()
        interfaces = psutil.net_if_addrs()
        
        active_interfaces = []
        for iface_name, iface_addrs in interfaces.items():
            for addr in iface_addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    active_interfaces.append({
                        "name": iface_name,
                        "ip": addr.address,
                        "netmask": addr.netmask
                    })

        info = {
            "hostname": hostname,
            "primary_ip": ip,
            "interfaces": active_interfaces,
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }

        return build_tool_result(
            tool_name=self.name,
            operation="get_network_info",
            risk_level=RiskLevel.LOW,
            status="success",
            summary=f"Network Info: Hostname {hostname}, IP {ip}",
            structured_data=info,
            idempotent=True,
            preconditions=[],
            postconditions=["network info collected"],
        )


ActionRegistry.register(SystemNetworkInfoAction)

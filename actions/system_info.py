"""
System Info Action — Retrieves detailed hardware and OS information.
"""

import platform
import psutil
import datetime
from actions.base import Action, ActionRegistry

def system_info_action(parameters: dict, **kwargs) -> str:
    info = []
    
    # OS Info
    info.append(f"OS: {platform.system()} {platform.release()} (Version: {platform.version()})")
    info.append(f"Architecture: {platform.machine()}")
    info.append(f"Hostname: {platform.node()}")
    
    # CPU Info
    info.append(f"CPU: {platform.processor()}")
    info.append(f"Physical Cores: {psutil.cpu_count(logical=False)}")
    info.append(f"Total Threads: {psutil.cpu_count(logical=True)}")
    
    # Memory Info
    mem = psutil.virtual_memory()
    total_mem = mem.total / (1024**3)
    avail_mem = mem.available / (1024**3)
    info.append(f"Total RAM: {total_mem:.2f} GB")
    info.append(f"Available RAM: {avail_mem:.2f} GB")
    
    # Boot Time
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    info.append(f"System Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(info)

class SystemInfoAction(Action):
    @property
    def name(self) -> str:
        return "system_info"

    @property
    def description(self) -> str:
        return "Retrieves detailed system specifications including OS, CPU, RAM, and boot time."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return system_info_action(parameters, **kwargs)

ActionRegistry.register(SystemInfoAction)

"""
Hardware Monitor — real-time CPU, memory, disk, and battery diagnostics.
All read-only — no system modifications.
"""

import platform
from datetime import datetime

import psutil
from actions.base import Action, ActionRegistry


def hardware_monitor(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "full_report").lower()

    if action == "cpu":
        return _cpu_info()
    if action == "memory":
        return _memory_info()
    if action == "disk":
        return _disk_info()
    if action == "battery":
        return _battery_info()
    if action == "gpu":
        return _gpu_info()
    if action == "full_report":
        return _full_report()
    return f"Unknown hardware_monitor action: {action}"


def _cpu_info() -> str:
    freq = psutil.cpu_freq()
    usage_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
    avg_usage = sum(usage_per_core) / len(usage_per_core) if usage_per_core else 0

    lines = [
        "🖥️ CPU Report",
        f"  Processor: {platform.processor() or 'N/A'}",
        f"  Physical cores: {psutil.cpu_count(logical=False)}",
        f"  Logical cores: {psutil.cpu_count(logical=True)}",
        f"  Average usage: {avg_usage:.1f}%",
    ]
    if freq:
        lines.append(f"  Frequency: {freq.current:.0f} MHz (max {freq.max:.0f} MHz)")

    lines.append(f"  Per-core usage: {', '.join(f'{u:.0f}%' for u in usage_per_core)}")
    return "\n".join(lines)


def _memory_info() -> str:
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    return (
        "🧠 Memory Report\n"
        f"  RAM Total: {vm.total / (1024**3):.1f} GB\n"
        f"  RAM Used: {vm.used / (1024**3):.1f} GB ({vm.percent}%)\n"
        f"  RAM Available: {vm.available / (1024**3):.1f} GB\n"
        f"  Swap Total: {sw.total / (1024**3):.1f} GB\n"
        f"  Swap Used: {sw.used / (1024**3):.1f} GB ({sw.percent}%)"
    )


def _disk_info() -> str:
    lines = ["💾 Disk Report"]
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            lines.append(
                f"  {part.device} ({part.mountpoint}):\n"
                f"    Total: {usage.total / (1024**3):.1f} GB | "
                f"Used: {usage.used / (1024**3):.1f} GB ({usage.percent}%) | "
                f"Free: {usage.free / (1024**3):.1f} GB"
            )
        except PermissionError:
            lines.append(f"  {part.device} ({part.mountpoint}): Access denied")
    return "\n".join(lines)


def _battery_info() -> str:
    battery = psutil.sensors_battery()
    if battery is None:
        return "🔋 No battery detected (desktop system)."

    status = "🔌 Charging" if battery.power_plugged else "🔋 On battery"
    time_left = "N/A"
    if battery.secsleft > 0 and not battery.power_plugged:
        hours = battery.secsleft // 3600
        minutes = (battery.secsleft % 3600) // 60
        time_left = f"{hours}h {minutes}m"

    return (
        f"🔋 Battery Report\n"
        f"  Level: {battery.percent}%\n"
        f"  Status: {status}\n"
        f"  Time remaining: {time_left}"
    )


def _gpu_info() -> str:
    """Basic GPU info — tries GPUtil, falls back to WMI/platform info."""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if not gpus:
            return "🎮 No dedicated GPU detected by GPUtil."
        lines = ["🎮 GPU Report"]
        for gpu in gpus:
            lines.append(
                f"  {gpu.name}\n"
                f"    Load: {gpu.load * 100:.1f}%\n"
                f"    Memory: {gpu.memoryUsed:.0f} / {gpu.memoryTotal:.0f} MB ({gpu.memoryUtil * 100:.1f}%)\n"
                f"    Temperature: {gpu.temperature}°C"
            )
        return "\n".join(lines)
    except ImportError:
        return "🎮 GPU: GPUtil not installed. Install with: pip install gputil"
    except Exception as exc:
        return f"🎮 GPU info unavailable: {exc}"


def _full_report() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = [
        f"📊 FULL HARDWARE REPORT — {timestamp}",
        f"  System: {platform.system()} {platform.release()} ({platform.machine()})",
        f"  Hostname: {platform.node()}",
        f"  Boot time: {datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        _cpu_info(),
        "",
        _memory_info(),
        "",
        _disk_info(),
        "",
        _battery_info(),
    ]
    return "\n".join(sections)


# ----------- Action Class for ActionRegistry -----------
class HardwareMonitorAction(Action):
    @property
    def name(self) -> str:
        return "hardware_monitor"

    @property
    def description(self) -> str:
        return (
            "Monitor device hardware in real-time. "
            "Get CPU usage, memory stats, disk space, battery level, or a full system report. "
            "Read-only — no system modifications."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "cpu | memory | disk | battery | gpu | full_report"
                },
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return hardware_monitor(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(HardwareMonitorAction)

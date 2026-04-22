import subprocess
import psutil
import platform
from actions.base import Action, ActionRegistry

def hardware_diagnostics(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "summary").lower()
    
    if action == "summary":
        return _hardware_summary()
    if action == "gpu_check":
        return _gpu_check()
    if action == "battery":
        return _battery_status()
        
    return f"Unknown hardware_diagnostics action: {action}"


def _hardware_summary() -> str:
    """Provides a quick health check of CPU, RAM, and OS."""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        
        output = "🖥️ Hardware Health Summary:\n"
        output += f"Processor: {platform.processor()}\n"
        output += f"CPU Usage: {cpu_usage}%\n"
        output += f"RAM Usage: {ram.percent}% ({ram.available/1024/1024/1024:.1f}GB available of {ram.total/1024/1024/1024:.1f}GB)\n"
        
        # CPU Temp is tricky on Windows without specialized libs, 
        # we'll mention if we can't get it.
        return output
    except Exception as e:
        return f"Error gathering summary: {e}"


def _gpu_check() -> str:
    """Checks NVIDIA GPU status using nvidia-smi."""
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            return (f"🎮 NVIDIA GPU Detected: {parts[0]}\n"
                    f"Temperature: {parts[1]}°C\n"
                    f"Utilization: {parts[2]}%\n"
                    f"Memory: {parts[3]}MB / {parts[4]}MB")
        return "🎮 No NVIDIA GPU detected or nvidia-smi not found."
    except Exception:
        return "🎮 GPU Check: NVIDIA SMI utility not available."


def _battery_status() -> str:
    """Checks battery percentage and power source."""
    if not hasattr(psutil, "sensors_battery"):
        return "🔋 Battery info not available on this platform."
        
    battery = psutil.sensors_battery()
    if battery is None:
        return "🔋 No battery detected (Desktop PC)."
        
    percent = battery.percent
    power_plugged = "Plugged In" if battery.power_plugged else "On Battery"
    return f"🔋 Battery: {percent}% ({power_plugged})"


class HardwareDiagnosticsAction(Action):
    @property
    def name(self) -> str:
        return "hardware_diagnostics"

    @property
    def description(self) -> str:
        return (
            "Monitors physical hardware health. "
            "Can provide a summary of CPU/RAM, check NVIDIA GPU metrics (temp/usage), and battery status."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "summary | gpu_check | battery"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return hardware_diagnostics(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(HardwareDiagnosticsAction)

import os
import psutil
import platform
import logging
from .base import Action

logger = logging.getLogger(__name__)

class SystemDiagnosticsAction(Action):
    """Generates a comprehensive system health report."""
    
    name = "system_diagnostics"
    description = "Generates a detailed system health diagnostic report (CPU, RAM, Disk, Network) and saves it to a Markdown file."
    parameters_schema = {
        "type": "object",
        "properties": {
            "output_path": {
                "type": "string",
                "description": "Absolute path to save the diagnostic report (e.g., C:\\report.md)."
            }
        },
        "required": ["output_path"]
    }
    
    def execute(self, output_path: str) -> str:
        try:
            report = [
                "# System Diagnostics Report",
                f"**OS:** {platform.system()} {platform.release()} (Version: {platform.version()})",
                f"**Architecture:** {platform.machine()}",
                f"**Processor:** {platform.processor()}",
                "",
                "## CPU Info",
                f"- Cores (Physical): {psutil.cpu_count(logical=False)}",
                f"- Cores (Logical): {psutil.cpu_count(logical=True)}",
                f"- Current Utilization: {psutil.cpu_percent(interval=1)}%",
                "",
                "## Memory Info"
            ]
            
            svmem = psutil.virtual_memory()
            report.append(f"- Total: {svmem.total / (1024 ** 3):.2f} GB")
            report.append(f"- Available: {svmem.available / (1024 ** 3):.2f} GB")
            report.append(f"- Used: {svmem.percent}%")
            report.append("")
            
            report.append("## Disk Info")
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    report.append(f"- Device: {partition.device}")
                    report.append(f"  - Total Size: {usage.total / (1024 ** 3):.2f} GB")
                    report.append(f"  - Used: {usage.used / (1024 ** 3):.2f} GB ({usage.percent}%)")
                    report.append(f"  - Free: {usage.free / (1024 ** 3):.2f} GB")
                except PermissionError:
                    continue
            
            report.append("")
            report.append("## Network Info")
            net_io = psutil.net_io_counters()
            report.append(f"- Bytes Sent: {net_io.bytes_sent / (1024 ** 2):.2f} MB")
            report.append(f"- Bytes Received: {net_io.bytes_recv / (1024 ** 2):.2f} MB")
            
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(report))
                
            return f"Successfully generated system diagnostics report at {output_path}."
        except Exception as e:
            logger.error(f"System diagnostics failed: {e}")
            return f"Error generating system diagnostics: {str(e)}"

import os
import shutil
import subprocess
from actions.base import Action, ActionRegistry

def maintenance_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "check_disk").lower()
    
    if action == "check_disk":
        return _check_disk_space()
    if action == "cleanup_temp":
        return _cleanup_temp_files()
    if action == "empty_recycle":
        return _empty_recycle_bin()
        
    return f"Unknown maintenance_manager action: {action}"


def _check_disk_space() -> str:
    """Checks free space on all local drives."""
    try:
        output = "💾 Disk Space Usage:\n"
        import psutil
        for partition in psutil.disk_partitions():
            if partition.fstype:
                usage = psutil.disk_usage(partition.mountpoint)
                output += f"- {partition.device} ({partition.mountpoint}): Total={usage.total/1024/1024/1024:.1f}GB, Free={usage.free/1024/1024/1024:.1f}GB, Used={usage.percent}%\n"
        return output
    except Exception as e:
        return f"Error checking disk: {e}"


def _cleanup_temp_files() -> str:
    """Cleans up Windows Temp and User Temp folders."""
    paths = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')
    ]
    
    freed_total = 0
    errors = 0
    
    for path in paths:
        if not path or not os.path.exists(path): continue
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                size = 0
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    size = os.path.getsize(item_path)
                    os.unlink(item_path)
                elif os.path.is_dir(item_path):
                    # shutil.rmtree might fail if files are in use
                    shutil.rmtree(item_path)
                freed_total += size
            except Exception:
                errors += 1
                
    return f"🧹 Cleanup Complete: Freed approx {freed_total/1024/1024:.1f} MB. (Skipped {errors} files currently in use)."


def _empty_recycle_bin() -> str:
    """Empties the recycle bin using PowerShell."""
    try:
        cmd = ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"]
        subprocess.run(cmd, capture_output=True, timeout=10)
        return "🗑️ Recycle Bin emptied successfully."
    except Exception as e:
        return f"Error emptying recycle bin: {e}"


class MaintenanceManagerAction(Action):
    @property
    def name(self) -> str:
        return "maintenance_manager"

    @property
    def description(self) -> str:
        return (
            "Performs system maintenance and optimization. "
            "Can check disk space, clean up temporary files, and empty the recycle bin."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "check_disk | cleanup_temp | empty_recycle"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return maintenance_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(MaintenanceManagerAction)

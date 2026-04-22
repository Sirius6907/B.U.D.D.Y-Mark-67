"""
System Optimizer Action — Cleans temporary files, flushes DNS, empties recycle bin.
"""

import os
import shutil
import tempfile
import subprocess
import ctypes
from actions.base import Action, ActionRegistry

def system_optimizer_action(parameters: dict, **kwargs) -> str:
    task = parameters.get("task", "all").lower().strip()
    results = []

    if task in ["temp", "all"]:
        temp_dir = tempfile.gettempdir()
        freed = 0
        try:
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        size = os.path.getsize(item_path)
                        os.unlink(item_path)
                        freed += size
                    elif os.path.isdir(item_path):
                        size = sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, _, filenames in os.walk(item_path) for filename in filenames)
                        shutil.rmtree(item_path)
                        freed += size
                except Exception:
                    pass
            results.append(f"Cleared {freed / (1024*1024):.2f} MB of temporary files.")
        except Exception as e:
            results.append(f"Failed to clear temp files: {e}")

    if task in ["dns", "all"]:
        try:
            output = subprocess.check_output("ipconfig /flushdns", shell=True, text=True)
            results.append("DNS Cache flushed successfully.")
        except Exception as e:
            results.append(f"Failed to flush DNS: {e}")

    if task in ["recycle", "all", "recycle_bin", "recyclebin"]:
        try:
            # SHEmptyRecycleBinW flags: SHERB_NOCONFIRMATION = 1, SHERB_NOPROGRESSUI = 2, SHERB_NOSOUND = 4
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            if result == 0:
                results.append("Recycle Bin emptied successfully.")
            else:
                results.append("Recycle Bin is already empty or could not be emptied.")
        except Exception as e:
            results.append(f"Failed to empty Recycle Bin: {e}")

    if not results:
        return "No valid optimization task selected. Use 'temp', 'dns', 'recycle', or 'all'."
    
    return "\n".join(results)

class SystemOptimizerAction(Action):
    @property
    def name(self) -> str:
        return "system_optimizer"

    @property
    def description(self) -> str:
        return "Optimizes the system by clearing temporary files, flushing DNS, and emptying the recycle bin."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "task": {
                    "type": "STRING",
                    "description": "Task to perform: 'temp', 'dns', 'recycle', or 'all' (default is 'all')."
                }
            },
            "required": []
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return system_optimizer_action(parameters, **kwargs)

ActionRegistry.register(SystemOptimizerAction)

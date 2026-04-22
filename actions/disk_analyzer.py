"""
Disk Analyzer Action — Analyzes storage to find large files or folders.
"""

import os
from pathlib import Path
from actions.base import Action, ActionRegistry

def get_size(path):
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total = 0
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
            return total
    except Exception:
        pass
    return 0

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

def disk_analyzer_action(parameters: dict, **kwargs) -> str:
    target_path = parameters.get("path", "").strip()
    if not target_path:
        target_path = os.path.expanduser("~")  # Default to user home directory
        
    if not os.path.exists(target_path):
        return f"Path '{target_path}' does not exist."
        
    try:
        items = []
        # We only look at immediate children for performance
        for entry in os.scandir(target_path):
            size = get_size(entry.path)
            items.append((entry.name, size, "Dir" if entry.is_dir() else "File"))
            
        items.sort(key=lambda x: x[1], reverse=True)
        
        lines = [f"Storage Analysis for {target_path} (Top 15 items):", "-"*50]
        for name, size, type_ in items[:15]:
            lines.append(f"[{type_}] {name}: {format_size(size)}")
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error analyzing disk: {e}"

class DiskAnalyzerAction(Action):
    @property
    def name(self) -> str:
        return "disk_analyzer"

    @property
    def description(self) -> str:
        return "Analyzes a directory to find the largest files and subdirectories. Helps in managing disk space."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {
                    "type": "STRING",
                    "description": "Directory path to analyze (defaults to the user's home directory)."
                }
            },
            "required": []
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return disk_analyzer_action(parameters, **kwargs)

ActionRegistry.register(DiskAnalyzerAction)

import shutil
import os
import datetime
from typing import Optional
from actions.base import Action, ActionRegistry

def backup_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "copy").lower()
    source = parameters.get("source")
    destination = parameters.get("destination")
    
    if not source: return "Error: 'source' path required."
    
    if action == "copy":
        if not destination: return "Error: 'destination' path required for copy."
        return _copy_backup(source, destination)
    if action == "zip":
        return _zip_backup(source, destination)
        
    return f"Unknown backup_manager action: {action}"


def _copy_backup(source: str, destination: str) -> str:
    """Copies a file or folder to a backup destination."""
    try:
        if not os.path.exists(source): return f"❌ Source not found: {source}"
        
        # Create a timestamped folder in destination
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(destination, f"backup_{timestamp}")
        
        if os.path.isdir(source):
            shutil.copytree(source, dest_path)
        else:
            if not os.path.exists(destination): os.makedirs(destination)
            shutil.copy2(source, os.path.join(destination, f"{timestamp}_{os.path.basename(source)}"))
            
        return f"✅ Backup successful! Created at: {dest_path if os.path.isdir(source) else destination}"
    except Exception as e:
        return f"❌ Backup failed: {e}"


def _zip_backup(source: str, destination: Optional[str] = None) -> str:
    """Compresses a folder into a .zip archive."""
    try:
        if not os.path.exists(source): return f"❌ Source not found: {source}"
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(source.rstrip(os.sep))
        output_name = f"{base_name}_{timestamp}"
        
        if destination:
            if not os.path.exists(destination): os.makedirs(destination)
            output_path = os.path.join(destination, output_name)
        else:
            output_path = os.path.join(os.path.dirname(source), output_name)
            
        final_file = shutil.make_archive(output_path, 'zip', source)
        return f"📦 Compression complete: {final_file}"
    except Exception as e:
        return f"❌ Compression failed: {e}"


class BackupManagerAction(Action):
    @property
    def name(self) -> str:
        return "backup_manager"

    @property
    def description(self) -> str:
        return (
            "Manages file and folder backups. "
            "Can copy files/folders to a destination or compress them into a .zip archive with timestamps."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "copy | zip"
                },
                "source": {
                    "type": "STRING",
                    "description": "Source file or directory path"
                },
                "destination": {
                    "type": "STRING",
                    "description": "Destination directory path"
                }
            },
            "required": ["action", "source"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return backup_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(BackupManagerAction)

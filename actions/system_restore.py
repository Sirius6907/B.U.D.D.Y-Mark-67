"""
System Restore Action — Creates a Windows system restore point.
"""

import subprocess
from actions.base import Action, ActionRegistry

def system_restore_action(parameters: dict, **kwargs) -> str:
    description = parameters.get("description", "Buddy Checkpoint").strip()
    
    ps_cmd = f'Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"'
    
    try:
        # This command usually requires administrative privileges
        result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
        if result.returncode == 0:
            return f"System Restore point '{description}' created successfully."
        else:
            if "Access is denied" in result.stderr or "Administrator" in result.stderr:
                return "Failed to create restore point: Administrator privileges required."
            return f"Failed to create restore point. Error:\n{result.stderr}"
    except Exception as e:
        return f"An error occurred while creating restore point: {e}"

class SystemRestoreAction(Action):
    @property
    def name(self) -> str:
        return "system_restore"

    @property
    def description(self) -> str:
        return "Creates a Windows System Restore point. Useful before making significant system changes. May require admin privileges."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "description": {
                    "type": "STRING",
                    "description": "Name or description for the restore point."
                }
            },
            "required": []
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return system_restore_action(parameters, **kwargs)

ActionRegistry.register(SystemRestoreAction)

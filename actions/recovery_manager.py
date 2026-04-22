import subprocess
from actions.base import Action, ActionRegistry

def recovery_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "check_updates").lower()
    
    if action == "check_updates":
        return _check_windows_updates()
    if action == "create_restore":
        description = parameters.get("description", "BUDDY Auto Restore Point")
        return _create_restore_point(description)
        
    return f"Unknown recovery_manager action: {action}"


def _check_windows_updates() -> str:
    """Checks for pending Windows Updates using PowerShell."""
    try:
        script = """
        $Searcher = New-Object -ComObject Microsoft.Update.Searcher
        $SearchResult = $Searcher.Search("IsInstalled=0 and Type='Software'")
        $SearchResult.Updates | Select-Object Title, Description | Format-List
        """
        cmd = ["powershell", "-Command", script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            output = result.stdout.strip()
            if not output:
                return "✅ Windows is up to date."
            return f"🔄 Pending Updates:\n{output}"
        return f"Failed to check updates: {result.stderr}"
    except Exception as e:
        return f"Error checking updates: {e}"


def _create_restore_point(description: str) -> str:
    """Creates a Windows System Restore point. Requires Admin privileges."""
    try:
        # Check if System Restore is enabled on C:
        check_cmd = ["powershell", "-Command", "Get-ComputerRestorePoint"]
        # Creating a restore point
        create_script = f"Checkpoint-Computer -Description '{description}' -RestorePointType 'MODIFY_SETTINGS'"
        cmd = ["powershell", "-Command", create_script]
        
        # This command is slow and requires admin. 
        # We'll run it and hope for the best.
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return f"🛡️ System Restore Point '{description}' created successfully."
        return f"❌ Failed to create restore point (likely missing Administrator privileges): {result.stderr}"
    except Exception as e:
        return f"Error creating restore point: {e}"


class RecoveryManagerAction(Action):
    @property
    def name(self) -> str:
        return "recovery_manager"

    @property
    def description(self) -> str:
        return (
            "Manages system recovery and updates. "
            "Can check for pending Windows Updates and create System Restore points. "
            "Essential before making major system changes."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "check_updates | create_restore"
                },
                "description": {
                    "type": "STRING",
                    "description": "Custom label for the restore point (for create_restore)"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return recovery_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(RecoveryManagerAction)

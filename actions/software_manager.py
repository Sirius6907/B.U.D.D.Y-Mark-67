import subprocess
from actions.base import Action, ActionRegistry

def software_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "list_installed").lower()
    
    if action == "list_installed":
        return _list_installed(parameters)
    if action == "uninstall":
        return _uninstall_software(parameters)
        
    return f"Unknown software_manager action: {action}"


def _list_installed(params: dict) -> str:
    filter_name = params.get("name", "")
    try:
        # Using Get-Package which covers MSI, Programs, and more in PowerShell
        cmd = ["powershell", "-Command", "Get-Package | Select-Object Name, Version, ProviderName | Format-Table -AutoSize"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return f"Failed to list installed software: {result.stderr}"
            
        output = result.stdout.strip()
        lines = output.splitlines()
        
        filtered_lines = []
        if filter_name:
            filtered_lines.append(lines[0]) # Header
            filtered_lines.append(lines[1]) # Separator
            for line in lines[2:]:
                if filter_name.lower() in line.lower():
                    filtered_lines.append(line)
            if len(filtered_lines) == 2:
                return f"No software found matching '{filter_name}'."
            return "\n".join(filtered_lines)
            
        # Truncate if too long
        if len(lines) > 80:
            return "\n".join(lines[:80]) + "\n... (truncated)"
        return output
        
    except Exception as e:
        return f"Error listing software: {e}"


def _uninstall_software(params: dict) -> str:
    name = params.get("name", "")
    if not name:
        return "Please specify the exact name of the software to uninstall."
        
    try:
        # This uses wmic to call uninstall. Note: This can be dangerous and usually requires Admin rights.
        # It's an exact match on name in wmic, so we'll use a LIKE clause
        cmd = ["wmic", "product", "where", f"name like '%{name}%'", "call", "uninstall", "/nointeractive"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        output = result.stdout.strip()
        if "ReturnValue = 0" in output or "ReturnValue = 1614" in output: # 0 or 1614 (already uninstalled)
            return f"✅ Uninstall command executed successfully for '{name}'."
        elif "No Instance(s) Available" in output:
            return f"Software matching '{name}' was not found in WMIC registry."
        else:
            return f"Uninstall command completed, but please check the output. (Admin privileges may be required)\nOutput: {output}"
            
    except Exception as e:
        return f"Error uninstalling software: {e}"


class SoftwareManagerAction(Action):
    @property
    def name(self) -> str:
        return "software_manager"

    @property
    def description(self) -> str:
        return (
            "Maintains installed software. "
            "Can list installed software or attempt to uninstall software by name. "
            "WARNING: Uninstallation requires Administrator privileges."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "list_installed | uninstall"
                },
                "name": {
                    "type": "STRING", 
                    "description": "Name of the software to filter by or uninstall"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return software_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(SoftwareManagerAction)

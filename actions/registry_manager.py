import winreg
import logging
from .base import Action

logger = logging.getLogger(__name__)

# Strict safety filter
SAFE_ROOT_PATHS = [
    r"Environment",
    r"Software",
    r"Console",
    r"Control Panel"
]
DANGEROUS_PATHS = [
    r"Software\Microsoft\Windows\CurrentVersion\Run",
    r"Software\Microsoft\Windows\CurrentVersion\Policies"
]

class RegistryManagerAction(Action):
    """Safely reads, writes, and deletes Windows Registry keys (HKCU only)."""
    
    name = "registry_manager"
    description = "Safely reads, writes, or deletes Windows Registry keys in HKCU (Current User). Critical system paths are blocked."
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to perform: 'read', 'write', or 'delete'.",
                "enum": ["read", "write", "delete"]
            },
            "sub_key": {
                "type": "string",
                "description": "The registry sub-key path (e.g., 'Environment' or 'Software\\MyApp')."
            },
            "value_name": {
                "type": "string",
                "description": "The name of the value to read, write, or delete."
            },
            "value_data": {
                "type": "string",
                "description": "The data to write (required for 'write' action)."
            },
            "value_type": {
                "type": "string",
                "description": "The registry value type (e.g., 'REG_SZ', 'REG_DWORD'). Default is 'REG_SZ'.",
                "default": "REG_SZ"
            }
        },
        "required": ["action", "sub_key", "value_name"]
    }
    
    def _is_safe(self, sub_key: str) -> bool:
        normalized = sub_key.replace("/", "\\")
        for dangerous in DANGEROUS_PATHS:
            if dangerous.lower() in normalized.lower():
                return False
        for safe in SAFE_ROOT_PATHS:
            if normalized.lower().startswith(safe.lower()):
                return True
        return False

    def execute(self, action: str, sub_key: str, value_name: str, value_data: str = None, value_type: str = "REG_SZ") -> str:
        if not self._is_safe(sub_key):
            return f"Security Error: Access to registry path '{sub_key}' is blocked by safety filters."
            
        try:
            if action == "read":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_READ) as key:
                    data, reg_type = winreg.QueryValueEx(key, value_name)
                    return f"Successfully read registry value: {value_name} = {data}"
            
            elif action == "write":
                if value_data is None:
                    return "Error: 'value_data' must be provided for 'write' action."
                
                type_map = {
                    "REG_SZ": winreg.REG_SZ,
                    "REG_DWORD": winreg.REG_DWORD,
                    "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
                    "REG_MULTI_SZ": winreg.REG_MULTI_SZ
                }
                actual_type = type_map.get(value_type.upper(), winreg.REG_SZ)
                
                if actual_type == winreg.REG_DWORD:
                    try:
                        value_data = int(value_data)
                    except ValueError:
                        return "Error: value_data must be an integer for REG_DWORD."
                
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                    winreg.SetValueEx(key, value_name, 0, actual_type, value_data)
                return f"Successfully wrote to registry: {sub_key}\\{value_name} = {value_data}"
                
            elif action == "delete":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, value_name)
                return f"Successfully deleted registry value: {sub_key}\\{value_name}"
            
            else:
                return f"Error: Unknown action '{action}'"
                
        except FileNotFoundError:
            return f"Error: Registry key or value not found."
        except PermissionError:
            return f"Error: Permission denied accessing registry key."
        except Exception as e:
            logger.error(f"Registry operation failed: {e}")
            return f"Error during registry operation: {str(e)}"

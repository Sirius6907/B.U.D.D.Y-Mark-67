import winreg
import logging
from .base import Action

logger = logging.getLogger(__name__)

class EnvVarsManagerAction(Action):
    """Safely manages user environment variables (HKCU)."""
    
    name = "env_vars_manager"
    description = "Safely reads, sets, or deletes User Environment Variables in the Windows Registry (HKCU\\Environment)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to perform: 'read', 'set', or 'delete'.",
                "enum": ["read", "set", "delete"]
            },
            "var_name": {
                "type": "string",
                "description": "The name of the environment variable."
            },
            "var_value": {
                "type": "string",
                "description": "The value to set (required for 'set')."
            }
        },
        "required": ["action", "var_name"]
    }
    
    def execute(self, action: str, var_name: str, var_value: str = None) -> str:
        # Hardcoded safe path for User Environment Variables
        sub_key = r"Environment"
        
        try:
            if action == "read":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_READ) as key:
                    data, reg_type = winreg.QueryValueEx(key, var_name)
                    return f"User Environment Variable: {var_name} = {data}"
            
            elif action == "set":
                if var_value is None:
                    return "Error: 'var_value' must be provided to set a variable."
                
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                    winreg.SetValueEx(key, var_name, 0, winreg.REG_EXPAND_SZ, var_value)
                return f"Successfully set User Environment Variable: {var_name} = {var_value}\nNote: Programs may need to be restarted to detect the new variable."
                
            elif action == "delete":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, var_name)
                return f"Successfully deleted User Environment Variable: {var_name}\nNote: Programs may need to be restarted to detect the change."
            
            else:
                return f"Error: Unknown action '{action}'"
                
        except FileNotFoundError:
            return f"Error: Environment variable '{var_name}' not found."
        except Exception as e:
            logger.error(f"Environment variable operation failed: {e}")
            return f"Error during environment variable operation: {str(e)}"

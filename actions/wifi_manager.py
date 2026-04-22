"""
WiFi Manager Action — View current WiFi and available networks.
"""

import subprocess
from actions.base import Action, ActionRegistry

def wifi_manager_action(parameters: dict, **kwargs) -> str:
    command = parameters.get("command", "info").lower().strip()
    
    if command == "info":
        try:
            output = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True)
            return f"Current WiFi Info:\n{output.strip()}"
        except subprocess.CalledProcessError:
            return "Could not retrieve WiFi information. Are you on Windows with WiFi enabled?"
            
    elif command == "list":
        try:
            output = subprocess.check_output("netsh wlan show networks", shell=True, text=True)
            return f"Available WiFi Networks:\n{output.strip()}"
        except subprocess.CalledProcessError:
            return "Could not retrieve available networks. Are you on Windows with WiFi enabled?"
            
    else:
        return f"Unknown command '{command}'. Use 'info' or 'list'."

class WifiManagerAction(Action):
    @property
    def name(self) -> str:
        return "wifi_manager"

    @property
    def description(self) -> str:
        return "Manages WiFi on Windows. Can get info about current connection or list available networks."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "'info' for current connection, 'list' for available networks."
                }
            },
            "required": ["command"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return wifi_manager_action(parameters, **kwargs)

ActionRegistry.register(WifiManagerAction)

"""
USB Manager Action — Lists connected USB devices.
"""

import subprocess
from actions.base import Action, ActionRegistry

def usb_manager_action(parameters: dict, **kwargs) -> str:
    try:
        # Uses PowerShell and WMI to list connected USB devices
        ps_cmd = "Get-WmiObject Win32_USBControllerDevice | % { [wmi]($_.Dependent) } | Where-Object { $_.Description -ne $null } | Select-Object Description, DeviceID | Format-Table -AutoSize"
        result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            return f"Connected USB Devices:\n{result.stdout.strip()}"
        elif result.returncode == 0:
            return "No connected USB devices found with descriptions."
        else:
            return f"Failed to retrieve USB devices: {result.stderr}"
    except Exception as e:
        return f"Error executing USB enumeration: {e}"

class UsbManagerAction(Action):
    @property
    def name(self) -> str:
        return "usb_manager"

    @property
    def description(self) -> str:
        return "Lists connected Plug and Play USB devices on the system."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return usb_manager_action(parameters, **kwargs)

ActionRegistry.register(UsbManagerAction)

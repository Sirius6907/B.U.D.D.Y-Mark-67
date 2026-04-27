import platform
import subprocess
import time
from typing import Optional, Any, Callable

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.08
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

from actions.base import Action, ActionRegistry

_SYSTEM = platform.system()


def _run_powershell(script: str, timeout: int = 12) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _open_windows_bluetooth_settings() -> str:
    subprocess.Popen("start ms-settings:bluetooth", shell=True)
    time.sleep(1.5)
    return "Opened Bluetooth settings."


def _windows_bluetooth_status() -> str:
    result = _run_powershell(
        "$svc = Get-Service bthserv -ErrorAction SilentlyContinue; "
        "$devices = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | "
        "Select-Object -ExpandProperty Status -ErrorAction SilentlyContinue; "
        "if (-not $svc) { 'Bluetooth service not found.' } "
        "elseif ($devices) { 'Bluetooth device statuses: ' + ($devices -join ', ') } "
        "else { 'Bluetooth service is ' + $svc.Status }"
    )
    output = (result.stdout or result.stderr).strip()
    return output or "Could not determine Bluetooth status."


def _windows_toggle_bluetooth() -> str:
    result = _run_powershell(
        "$adapter = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | "
        "Where-Object { $_.FriendlyName -match 'adapter|radio|bluetooth' } | Select-Object -First 1; "
        "if (-not $adapter) { Write-Output 'No Bluetooth adapter found.'; exit 0 } "
        "if ($adapter.Status -eq 'OK') { "
        "Disable-PnpDevice -InstanceId $adapter.InstanceId -Confirm:$false -ErrorAction Stop; "
        "Write-Output 'Bluetooth adapter disabled.' "
        "} else { "
        "Enable-PnpDevice -InstanceId $adapter.InstanceId -Confirm:$false -ErrorAction Stop; "
        "Write-Output 'Bluetooth adapter enabled.' "
        "}"
    )
    output = (result.stdout or result.stderr).strip()
    return output or "Bluetooth toggle command completed."


def _windows_bluetooth_guided_action(device_name: str, pair_new: bool = False, accept_pairing: bool = False) -> str:
    _open_windows_bluetooth_settings()
    if not _PYAUTOGUI:
        if pair_new:
            return "Opened Bluetooth settings for new device pairing."
        if accept_pairing:
            return "Opened Bluetooth settings for pairing confirmation."
        return f"Opened Bluetooth settings to connect to {device_name}."

    time.sleep(1.2)
    if pair_new:
        pyautogui.press("tab", presses=2, interval=0.12)
        pyautogui.press("enter")
        return "Opened Bluetooth settings and started the Add device flow."

    if accept_pairing:
        pyautogui.press("enter")
        return "Attempted to accept the current Bluetooth pairing prompt."

    if device_name:
        pyautogui.hotkey("ctrl", "l")
        pyautogui.write(device_name, interval=0.03)
        time.sleep(0.5)
        pyautogui.press("enter")
        return f"Opened Bluetooth settings and attempted to connect to {device_name}."

    return "Opened Bluetooth settings."


def bluetooth_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = str((parameters or {}).get("action", "status")).strip().lower()
    device_name = str((parameters or {}).get("device_name", "")).strip()

    if _SYSTEM != "Windows":
        if action in {"open_settings", "pair_new", "connect_saved", "accept_pairing"}:
            return "Bluetooth guided control is currently implemented for Windows."
        return "Bluetooth device control is currently implemented for Windows."

    if action == "status":
        return _windows_bluetooth_status()
    if action == "open_settings":
        return _open_windows_bluetooth_settings()
    if action == "toggle":
        return _windows_toggle_bluetooth()
    if action == "connect_saved":
        return _windows_bluetooth_guided_action(device_name=device_name)
    if action == "pair_new":
        return _windows_bluetooth_guided_action(device_name=device_name, pair_new=True)
    if action == "accept_pairing":
        return _windows_bluetooth_guided_action(device_name=device_name, accept_pairing=True)

    return f"Unknown bluetooth_manager action: {action}"


class BluetoothManagerAction(Action):
    @property
    def name(self) -> str:
        return "bluetooth_manager"

    @property
    def description(self) -> str:
        return "Controls Bluetooth on the system: check status, open settings, toggle the adapter, connect saved devices, start pairing, and accept pairing prompts."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "status | open_settings | toggle | connect_saved | pair_new | accept_pairing",
                },
                "device_name": {
                    "type": "STRING",
                    "description": "Saved or target Bluetooth device name when applicable",
                },
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player: Optional[Any] = None, speak: Optional[Callable] = None, **kwargs) -> str:
        return bluetooth_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(BluetoothManagerAction)

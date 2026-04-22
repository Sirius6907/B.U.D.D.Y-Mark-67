"""
Volume Controller — get, set, mute, and unmute system volume.
"""

import subprocess
import re
from actions.base import Action, ActionRegistry


def volume_controller(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "get").lower()
    
    if action == "get":
        return _get_volume()
    if action == "set":
        return _set_volume(parameters)
    if action == "mute":
        return _mute_volume()
    if action == "unmute":
        return _unmute_volume()
        
    return f"Unknown volume_controller action: {action}"


def _get_volume() -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        current_volume = round(volume.GetMasterVolumeLevelScalar() * 100)
        is_muted = volume.GetMute()
        
        status = "🔇 Muted" if is_muted else "🔊 Unmuted"
        return f"System Volume: {current_volume}% ({status})"
    except ImportError:
        pass
    except Exception as e:
        return f"Failed to get volume via pycaw: {e}"

    # Fallback to NirCmd or PowerShell if possible
    return "Could not determine system volume (pycaw not installed or error)."


def _set_volume(params: dict) -> str:
    level_str = params.get("level", "")
    if not level_str:
        return "Please specify a volume level (0-100)."
        
    try:
        level = max(0.0, min(100.0, float(level_str)))
    except ValueError:
        return "Invalid volume level. Must be a number between 0 and 100."
        
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level:.0f}%."
    except ImportError:
        pass
    except Exception as e:
        return f"Failed to set volume via pycaw: {e}"
        
    return "Could not set system volume (pycaw not installed or error)."


def _mute_volume() -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        volume.SetMute(1, None)
        return "System volume muted 🔇."
    except ImportError:
        pass
    except Exception as e:
        return f"Failed to mute volume via pycaw: {e}"
        
    return "Could not mute system volume (pycaw not installed or error)."


def _unmute_volume() -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        volume.SetMute(0, None)
        return "System volume unmuted 🔊."
    except ImportError:
        pass
    except Exception as e:
        return f"Failed to unmute volume via pycaw: {e}"
        
    return "Could not unmute system volume (pycaw not installed or error)."


class VolumeControllerAction(Action):
    @property
    def name(self) -> str:
        return "volume_controller"

    @property
    def description(self) -> str:
        return "Manage system audio volume. Get, set level (0-100), mute, or unmute."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "get | set | mute | unmute"},
                "level": {"type": "STRING", "description": "Volume percentage 0-100 (for set)"},
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return volume_controller(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(VolumeControllerAction)

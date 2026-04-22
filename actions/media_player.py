"""
Media Player Action — Controls system media playback.
"""

import pyautogui
from actions.base import Action, ActionRegistry

def media_player_action(parameters: dict, **kwargs) -> str:
    command = parameters.get("command", "").lower().strip()
    
    if command in ["play", "pause", "playpause", "play/pause"]:
        pyautogui.press("playpause")
        return "Toggled play/pause for media."
    elif command in ["next", "next track", "skip"]:
        pyautogui.press("nexttrack")
        return "Skipped to the next track."
    elif command in ["previous", "prev", "previous track", "back"]:
        pyautogui.press("prevtrack")
        return "Went back to the previous track."
    elif command in ["mute", "unmute"]:
        pyautogui.press("volumemute")
        return "Toggled system mute."
    else:
        return f"Unknown media command: '{command}'. Try 'play', 'pause', 'next', 'previous', or 'mute'."

class MediaPlayerAction(Action):
    @property
    def name(self) -> str:
        return "media_player"

    @property
    def description(self) -> str:
        return "Controls system media playback. Can play, pause, skip to next/previous tracks, or mute."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "Media command: 'play', 'pause', 'next', 'previous', or 'mute'."
                }
            },
            "required": ["command"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return media_player_action(parameters, **kwargs)

ActionRegistry.register(MediaPlayerAction)

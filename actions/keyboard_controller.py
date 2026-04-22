"""
Keyboard Controller Action — Simulate typing and hotkeys.
"""

import pyautogui
from actions.base import Action, ActionRegistry

def keyboard_controller_action(parameters: dict, **kwargs) -> str:
    command = parameters.get("command", "").lower().strip()
    
    try:
        if command == "type":
            text = parameters.get("text", "")
            interval = float(parameters.get("interval", 0.0))
            if not text:
                return "Text parameter is required for 'type' command."
            pyautogui.write(text, interval=interval)
            return f"Typed provided text."
            
        elif command == "hotkey":
            keys_str = parameters.get("keys", "")
            if not keys_str:
                return "Keys parameter is required for 'hotkey' command (e.g., 'ctrl,c')."
            keys = [k.strip() for k in keys_str.split(",")]
            pyautogui.hotkey(*keys)
            return f"Pressed hotkey: {' + '.join(keys)}"
            
        elif command == "press":
            key = parameters.get("key", "").lower().strip()
            if not key:
                return "Key parameter is required for 'press' command (e.g., 'enter')."
            pyautogui.press(key)
            return f"Pressed '{key}' key."
            
        else:
            return f"Unknown command: '{command}'. Use 'type', 'hotkey', or 'press'."
    except Exception as e:
        return f"Error performing keyboard action: {e}"

class KeyboardControllerAction(Action):
    @property
    def name(self) -> str:
        return "keyboard_controller"

    @property
    def description(self) -> str:
        return "Simulates keyboard input. Can type text, press individual keys, or trigger hotkeys."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "'type', 'hotkey', or 'press'."
                },
                "text": {
                    "type": "STRING",
                    "description": "Text to type out for 'type' command."
                },
                "interval": {
                    "type": "NUMBER",
                    "description": "Interval between keystrokes when typing (default 0.0)."
                },
                "keys": {
                    "type": "STRING",
                    "description": "Comma-separated keys for 'hotkey' (e.g. 'ctrl,alt,delete')."
                },
                "key": {
                    "type": "STRING",
                    "description": "A single key to press for 'press' command (e.g. 'enter', 'tab', 'esc')."
                }
            },
            "required": ["command"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return keyboard_controller_action(parameters, **kwargs)

ActionRegistry.register(KeyboardControllerAction)

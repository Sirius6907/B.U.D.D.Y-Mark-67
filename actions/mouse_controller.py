"""
Mouse Controller Action — Programmatic mouse control.
"""

import pyautogui
from actions.base import Action, ActionRegistry

def mouse_controller_action(parameters: dict, **kwargs) -> str:
    command = parameters.get("command", "").lower().strip()
    
    try:
        if command == "move":
            x = int(parameters.get("x", 0))
            y = int(parameters.get("y", 0))
            pyautogui.moveTo(x, y, duration=0.5)
            return f"Moved mouse to ({x}, {y})."
            
        elif command == "click":
            clicks = int(parameters.get("clicks", 1))
            button = parameters.get("button", "left").lower()
            if button not in ["left", "right", "middle"]:
                button = "left"
            pyautogui.click(clicks=clicks, button=button)
            return f"Performed {clicks} {button}-click(s)."
            
        elif command == "scroll":
            amount = int(parameters.get("amount", 0))
            pyautogui.scroll(amount)
            return f"Scrolled mouse by {amount} units."
            
        elif command == "position":
            x, y = pyautogui.position()
            return f"Current mouse position: ({x}, {y})"
            
        else:
            return f"Unknown command: '{command}'. Use 'move', 'click', 'scroll', or 'position'."
    except Exception as e:
        return f"Error performing mouse action: {e}"

class MouseControllerAction(Action):
    @property
    def name(self) -> str:
        return "mouse_controller"

    @property
    def description(self) -> str:
        return "Controls the mouse cursor. Can move, click, scroll, or get current coordinates."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "'move', 'click', 'scroll', or 'position'."
                },
                "x": {
                    "type": "INTEGER",
                    "description": "X coordinate for 'move'."
                },
                "y": {
                    "type": "INTEGER",
                    "description": "Y coordinate for 'move'."
                },
                "clicks": {
                    "type": "INTEGER",
                    "description": "Number of clicks for 'click' (default 1)."
                },
                "button": {
                    "type": "STRING",
                    "description": "Button to click: 'left', 'right', or 'middle'."
                },
                "amount": {
                    "type": "INTEGER",
                    "description": "Scroll amount (positive for up, negative for down)."
                }
            },
            "required": ["command"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return mouse_controller_action(parameters, **kwargs)

ActionRegistry.register(MouseControllerAction)

"""
Timer Manager Action — Sets simple background timers.
"""

import threading
import time
import ctypes
from actions.base import Action, ActionRegistry

def _timer_thread(seconds: int, message: str):
    time.sleep(seconds)
    # 0x40 is MB_ICONINFORMATION
    ctypes.windll.user32.MessageBoxW(0, message, "Buddy Timer", 0x40)

def timer_manager_action(parameters: dict, **kwargs) -> str:
    duration_str = parameters.get("duration", "60").strip()
    message = parameters.get("message", "Timer is up!").strip()
    
    try:
        duration = int(duration_str)
    except ValueError:
        return "Invalid duration. Please specify a number in seconds."
        
    if duration <= 0:
        return "Duration must be greater than zero."

    t = threading.Thread(target=_timer_thread, args=(duration, message), daemon=True)
    t.start()
    
    return f"Timer set for {duration} seconds. You will be notified when it's done."

class TimerManagerAction(Action):
    @property
    def name(self) -> str:
        return "timer_manager"

    @property
    def description(self) -> str:
        return "Sets a countdown timer that will pop up an alert when finished. Ideal for reminders and alarms."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "duration": {
                    "type": "STRING",
                    "description": "Duration of the timer in seconds (e.g. '300' for 5 minutes)."
                },
                "message": {
                    "type": "STRING",
                    "description": "Message to display when the timer is up."
                }
            },
            "required": ["duration"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return timer_manager_action(parameters, **kwargs)

ActionRegistry.register(TimerManagerAction)

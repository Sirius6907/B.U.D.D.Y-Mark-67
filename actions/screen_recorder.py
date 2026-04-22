import pyautogui
import time
import logging
from .base import Action

logger = logging.getLogger(__name__)

class ScreenRecorderAction(Action):
    """Controls NVIDIA ShadowPlay to record the screen."""
    
    name = "screen_recorder"
    description = "Controls NVIDIA ShadowPlay desktop recording (Alt+F9) and overlay (Alt+Z). Requires manual configuration for advanced settings."
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to perform: 'start', 'stop', or 'configure'.",
                "enum": ["start", "stop", "configure"]
            },
            "duration": {
                "type": "integer",
                "description": "Optional. If provided, starts recording, waits for duration (in seconds), then stops."
            },
            "resolution": {
                "type": "string",
                "description": "Optional. E.g., '1080p', '4k'. Only for 'configure' intent logging."
            },
            "fps": {
                "type": "integer",
                "description": "Optional. E.g., 60, 120. Only for 'configure' intent logging."
            },
            "bitrate": {
                "type": "integer",
                "description": "Optional. Only for 'configure' intent logging."
            },
            "audio_source": {
                "type": "string",
                "description": "Optional. 'system' or 'system_and_mic'."
            }
        },
        "required": ["action"]
    }
    
    def execute(self, action: str, duration: int = None, resolution: str = None, fps: int = None, bitrate: int = None, audio_source: str = None) -> str:
        try:
            if action == "configure":
                # Open the ShadowPlay overlay
                pyautogui.hotkey('alt', 'z')
                msg = "Triggered Alt+Z to open ShadowPlay overlay."
                if resolution or fps or bitrate or audio_source:
                    msg += f" Note: {resolution} {fps}fps {bitrate}kbps audio:{audio_source} must be set manually in the overlay menu."
                logger.info(msg)
                return msg
            elif duration is not None:
                # Start, Wait, Stop
                pyautogui.hotkey('alt', 'f9')
                logger.info(f"Triggered Alt+F9 to start ShadowPlay recording. Waiting {duration} seconds...")
                time.sleep(duration)
                pyautogui.hotkey('alt', 'f9')
                logger.info("Triggered Alt+F9 to stop ShadowPlay recording.")
                return f"Successfully triggered ShadowPlay recording for {duration} seconds."
            else:
                # Just press hotkey once
                pyautogui.hotkey('alt', 'f9')
                return f"Successfully triggered Alt+F9 to {action} ShadowPlay recording."
        except Exception as e:
            logger.error(f"ShadowPlay control failed: {e}")
            return f"Error controlling ShadowPlay: {str(e)}"

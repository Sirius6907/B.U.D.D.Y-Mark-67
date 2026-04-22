"""
Wallpaper Changer Action — Changes the Windows desktop wallpaper.
"""

import os
import ctypes
from actions.base import Action, ActionRegistry

def wallpaper_changer_action(parameters: dict, **kwargs) -> str:
    image_path = parameters.get("image_path", "").strip()
    
    if not image_path:
        return "Please provide the full path to an image file."
        
    if not os.path.exists(image_path):
        return f"Image file not found at: {image_path}"
        
    try:
        # SPI_SETDESKWALLPAPER = 20
        # SPIF_UPDATEINIFILE = 1
        # SPIF_SENDWININICHANGE = 2
        result = ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath(image_path), 3)
        if result:
            return f"Wallpaper successfully changed to {image_path}"
        else:
            return "Failed to change wallpaper. System API returned false."
    except Exception as e:
        return f"Error changing wallpaper: {e}"

class WallpaperChangerAction(Action):
    @property
    def name(self) -> str:
        return "wallpaper_changer"

    @property
    def description(self) -> str:
        return "Changes the Windows desktop background wallpaper to a specified local image."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "image_path": {
                    "type": "STRING",
                    "description": "Absolute path to the local image file to set as wallpaper."
                }
            },
            "required": ["image_path"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return wallpaper_changer_action(parameters, **kwargs)

ActionRegistry.register(WallpaperChangerAction)

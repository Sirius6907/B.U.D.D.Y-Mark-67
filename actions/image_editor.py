import os
import logging
from PIL import Image
from .base import Action

logger = logging.getLogger(__name__)

class ImageEditorAction(Action):
    """Resizes, crops, or rotates an image using Pillow."""
    
    name = "image_editor"
    description = "Edits an image file (resize, crop, rotate, or convert format)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Absolute path to the image file."
            },
            "output_path": {
                "type": "string",
                "description": "Absolute path to save the edited image."
            },
            "action": {
                "type": "string",
                "description": "The edit action to perform: 'resize', 'crop', 'rotate', or 'convert'.",
                "enum": ["resize", "crop", "rotate", "convert"]
            },
            "width": {
                "type": "integer",
                "description": "Width for resize or crop."
            },
            "height": {
                "type": "integer",
                "description": "Height for resize or crop."
            },
            "x": {
                "type": "integer",
                "description": "X coordinate for crop (top-left)."
            },
            "y": {
                "type": "integer",
                "description": "Y coordinate for crop (top-left)."
            },
            "degrees": {
                "type": "integer",
                "description": "Degrees to rotate (counter-clockwise)."
            }
        },
        "required": ["image_path", "output_path", "action"]
    }
    
    def execute(self, image_path: str, output_path: str, action: str, width: int = None, height: int = None, x: int = 0, y: int = 0, degrees: int = 0) -> str:
        if not os.path.exists(image_path):
            return f"Error: Image not found at {image_path}"
        try:
            with Image.open(image_path) as img:
                if action == "resize":
                    if not width or not height:
                        return "Error: Width and height must be provided for resize."
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                elif action == "crop":
                    if not width or not height:
                        return "Error: Width and height must be provided for crop."
                    img = img.crop((x, y, x + width, y + height))
                elif action == "rotate":
                    if degrees is None:
                        return "Error: Degrees must be provided for rotate."
                    img = img.rotate(degrees, expand=True)
                elif action == "convert":
                    if img.mode in ('RGBA', 'P') and output_path.lower().endswith('.jpg'):
                        img = img.convert('RGB')
                else:
                    return f"Error: Unknown action '{action}'"
                
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                img.save(output_path)
            return f"Successfully performed '{action}' on image. Saved to {output_path}."
        except Exception as e:
            logger.error(f"Image editing failed: {e}")
            return f"Error editing image: {str(e)}"

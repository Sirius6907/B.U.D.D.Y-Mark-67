import cv2
import os
import logging
from .base import Action

logger = logging.getLogger(__name__)

class CameraCaptureAction(Action):
    """Takes a photo using the default webcam."""
    
    name = "camera_capture"
    description = "Takes a picture using the default webcam and saves it to the specified path."
    parameters_schema = {
        "type": "object",
        "properties": {
            "output_path": {
                "type": "string",
                "description": "Absolute path to save the captured image (e.g., C:\\photo.jpg)."
            }
        },
        "required": ["output_path"]
    }
    
    def execute(self, output_path: str) -> str:
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Error: Could not open the default webcam."
                
            ret, frame = cap.read()
            if not ret:
                cap.release()
                return "Error: Failed to capture an image from the webcam."
                
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            cv2.imwrite(output_path, frame)
            cap.release()
            
            return f"Successfully captured photo and saved to {output_path}."
        except Exception as e:
            logger.error(f"Camera capture failed: {e}")
            return f"Error taking photo: {str(e)}"

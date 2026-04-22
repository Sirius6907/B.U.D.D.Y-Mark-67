import pyttsx3
import logging
from .base import Action

logger = logging.getLogger(__name__)

class TextToSpeechAction(Action):
    """Speaks the provided text using the system's text-to-speech engine."""
    
    name = "text_to_speech"
    description = "Speaks the provided text aloud using the system's text-to-speech engine."
    parameters_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to speak out loud."
            },
            "rate": {
                "type": "integer",
                "description": "Optional. The speed of the speech (default is usually 200).",
                "default": 200
            }
        },
        "required": ["text"]
    }
    
    def execute(self, text: str, rate: int = 200) -> str:
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', rate)
            engine.say(text)
            engine.runAndWait()
            return f"Successfully spoke the text."
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            return f"Error speaking text: {str(e)}"

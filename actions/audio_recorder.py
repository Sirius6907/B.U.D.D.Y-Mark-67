import sounddevice as sd
import wave
import os
import logging
from .base import Action

logger = logging.getLogger(__name__)

class AudioRecorderAction(Action):
    """Records audio from the default microphone."""
    
    name = "audio_recorder"
    description = "Records audio from the default microphone for a specified duration and saves it as a WAV file."
    parameters_schema = {
        "type": "object",
        "properties": {
            "output_path": {
                "type": "string",
                "description": "Absolute path to save the .wav file (e.g., C:\\recording.wav)."
            },
            "duration": {
                "type": "integer",
                "description": "Duration to record in seconds."
            },
            "sample_rate": {
                "type": "integer",
                "description": "Sample rate in Hz (default: 44100).",
                "default": 44100
            }
        },
        "required": ["output_path", "duration"]
    }
    
    def execute(self, output_path: str, duration: int, sample_rate: int = 44100) -> str:
        try:
            channels = 1  # Mono recording
            
            logger.info(f"Starting audio recording for {duration} seconds...")
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='int16')
            sd.wait()  # Wait until recording is finished
            
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2) # 2 bytes = 16 bit
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
                
            return f"Successfully recorded audio for {duration} seconds and saved to {output_path}."
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            return f"Error recording audio: {str(e)}"

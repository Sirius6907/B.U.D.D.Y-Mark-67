import { Audio } from 'expo-av';

const SARVAM_API_KEY = process.env.EXPO_PUBLIC_SARVAM_API_KEY || "";

export const speak = async (text: string) => {
  if (!SARVAM_API_KEY) {
    console.warn("Sarvam API key missing. Falling back to console.");
    return;
  }

  try {
    const response = await fetch("https://api.sarvam.ai/text-to-speech", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "api-subscription-key": SARVAM_API_KEY,
      },
      body: JSON.stringify({
        inputs: [text],
        target_language_code: "en-IN",
        speaker: "meera",
        pitch: 0,
        pace: 1.1,
        loudness: 1.5,
        model: "bulbul:v1",
      }),
    });

    const data = await response.json();
    if (data.audios && data.audios[0]) {
      const { sound } = await Audio.Sound.createAsync(
        { uri: `data:audio/wav;base64,${data.audios[0]}` },
        { shouldPlay: true }
      );
      return sound;
    }
  } catch (error) {
    console.error("TTS Error:", error);
  }
};

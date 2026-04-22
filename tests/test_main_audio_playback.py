import io
import wave

import numpy as np

import main


def _wav_bytes(samples: np.ndarray, samplerate: int = 24000, channels: int = 1) -> bytes:
    with io.BytesIO() as buffer:
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(samplerate)
            wav_file.writeframes(samples.astype(np.int16).tobytes())
        return buffer.getvalue()


def test_play_audio_bytes_uses_array_shape_instead_of_channels_kwarg(monkeypatch):
    captured = {}

    def fake_play(audio, samplerate, blocking, **kwargs):
        captured["audio"] = audio
        captured["samplerate"] = samplerate
        captured["blocking"] = blocking
        captured["kwargs"] = kwargs

    monkeypatch.setattr(main.sd, "play", fake_play)

    buddy = object.__new__(main.BuddyLive)
    wav_audio = _wav_bytes(np.array([1, -1, 2, -2], dtype=np.int16), channels=1)

    buddy._play_audio_bytes(wav_audio)

    assert captured["samplerate"] == 24000
    assert captured["blocking"] is True
    assert "channels" not in captured["kwargs"]


def test_play_audio_bytes_reshapes_multichannel_wav_before_playback(monkeypatch):
    captured = {}

    def fake_play(audio, samplerate, blocking, **kwargs):
        captured["audio"] = audio
        captured["samplerate"] = samplerate
        captured["blocking"] = blocking
        captured["kwargs"] = kwargs

    monkeypatch.setattr(main.sd, "play", fake_play)

    buddy = object.__new__(main.BuddyLive)
    stereo_samples = np.array([1, 10, -1, -10, 2, 20, -2, -20], dtype=np.int16)
    wav_audio = _wav_bytes(stereo_samples, channels=2)

    buddy._play_audio_bytes(wav_audio)

    assert captured["audio"].shape == (4, 2)
    assert captured["samplerate"] == 24000
    assert captured["blocking"] is True
    assert "channels" not in captured["kwargs"]

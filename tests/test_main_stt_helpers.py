import wave
from io import BytesIO

import main


def test_pcm16_to_wav_bytes_wraps_audio_in_wav_container():
    pcm_bytes = b"\x01\x00\xff\xff\x02\x00\xfe\xff"

    wav_bytes = main._pcm16_to_wav_bytes(pcm_bytes, samplerate=16000, channels=1)

    with wave.open(BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.readframes(wav_file.getnframes()) == pcm_bytes


def test_command_transcript_filter_rejects_noise_captions_and_hallucinated_essays():
    assert main._is_usable_command_transcript("[Panting]") is False
    assert (
        main._is_usable_command_transcript(
            "Okay, here is a transcript of a hypothetical speech. I'll imagine it's a keynote."
        )
        is False
    )


def test_command_transcript_filter_accepts_short_plain_command():
    assert main._is_usable_command_transcript("open youtube in chrome") is True

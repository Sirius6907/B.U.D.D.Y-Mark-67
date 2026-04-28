import asyncio
import io
import re
import threading
import sys
import time
import traceback
import wave
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import sounddevice as sd
import keyboard
from google import genai
from google.genai import types
from dashboard_v2.ui_facade import BuddyUI
from core.async_queues import enqueue_latest
from core.console import configure_console_output
from agent.kernel import kernel
from agent.personality import build_boot_greeting, build_shutdown_farewell, build_tool_error_reply
from agent.voice import VoiceOrchestrator
from agent.runtime import RuntimeCoordinator
from app_bootstrap import bootstrap_application
from buddy_logging import get_logger
from config import get_api_key
from memory.memory_manager import load_memory, format_memory_for_prompt, update_memory, search_local_files
from agent.planner import create_plan
from agent.telegram_bot import TelegramBot
from voice.config import load_voice_settings
from voice.providers.base import VoiceProviderError
from voice.providers.gemini_fallback import GeminiFallbackSpeechProvider
from voice.providers.sarvam import SarvamSpeechProvider
from voice.router import VoiceRouter

from actions import ActionRegistry


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR        = get_base_dir()
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"
LIVE_MODEL          = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS            = 1
SEND_SAMPLE_RATE    = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE          = 1024
MIC_ACTIVITY_THRESHOLD = 500
MIC_SILENCE_SECONDS = 0.8
MIC_MIN_SPEECH_SECONDS = 0.3
MIC_MAX_SPEECH_SECONDS = 15.0


def _get_api_key() -> str:
    return get_api_key(required=True)


logger = get_logger("buddy.main")


class _UnavailableSpeechProvider:
    def __init__(self, message: str):
        self.message = message

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        raise VoiceProviderError(self.message)

    def synthesize(self, text: str) -> bytes:
        raise VoiceProviderError(self.message)


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are BUDDY, Sirius's AI assistant. "
            "Be concise, direct, and always use the provided tools to complete tasks. "
            "Never simulate or guess results — always call the appropriate tool."
        )


# ── Transkripsiyon temizleyici ─────────────────────────────────────────────────
_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)
_NOISE_ONLY_RE = re.compile(r"^\s*(\[[^\]]+\]|\([^)]+\))(\s+(\[[^\]]+\]|\([^)]+\)))*\s*$")
_HALLUCINATION_MARKERS = (
    "here is a transcript",
    "hypothetical speech",
    "i'll imagine",
    "**[speaker:",
    "**(applause)",
    "---",
)

def _clean_transcript(text: str) -> str:
    """Gemini'nin ürettiği <ctrlXX> artefaktlarını ve kontrol karakterlerini temizler."""
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()


def _pcm16_to_wav_bytes(audio_bytes: bytes, samplerate: int, channels: int) -> bytes:
    with io.BytesIO() as buffer:
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(samplerate)
            wav_file.writeframes(audio_bytes)
        return buffer.getvalue()


def _is_usable_command_transcript(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    if _NOISE_ONLY_RE.fullmatch(normalized):
        return False
    if any(marker in lowered for marker in _HALLUCINATION_MARKERS):
        return False
    if normalized.count("\n") >= 2:
        return False
    if len(normalized) > 220:
        return False
    return True


# ── Tool declarations are now dynamically retrieved from ActionRegistry ──

class BuddyLive:

    def __init__(self, ui: BuddyUI):
        self.ui             = ui
        self._loop          = None
        self._is_speaking   = False
        self._speaking_lock = threading.Lock()
        self._tts_lock: asyncio.Lock | None = None
        self.mic_queue: asyncio.Queue[bytes] | None = None
        self.ui.on_text_command = self._on_text_command
        self._kernel_initialized = False
        self._startup_greeted = False
        self._online_logged = False
        self.voice_settings = load_voice_settings()
        self.speech_router = self._create_speech_router()
        self._is_awake = False
        self._last_awake_time = 0.0
        self.tts_muted = False
        
        # Phase 10: Elite Runtime Orchestrator
        self.orchestrator = VoiceOrchestrator(_get_api_key(), self.speak)
        self.orchestrator.runtime = RuntimeCoordinator(
            _get_api_key(),
            self.speak,
            approval_callback=self.ui.request_approval,
            status_callback=self.ui.update_runtime_status,
        )
        self.tg_bot = TelegramBot(
            on_text_received=self._on_tg_text,
            on_voice_received=self._on_tg_voice
        )

    def _on_text_command(self, text: str):
        if not self._loop:
            return
        # Route through the orchestrator for multi-step intelligence
        asyncio.run_coroutine_threadsafe(
            self.orchestrator.handle_user_command(text),
            self._loop
        )

    async def _on_tg_text(self, text: str):
        self.ui.write_log(f"TG Text: {text}")
        await self.orchestrator.handle_user_command(text)

    async def _on_tg_voice(self, audio_bytes: bytes):
        self.ui.write_log("TG Voice received")
        self.ui.set_state("THINKING")
        try:
            transcript = await asyncio.to_thread(
                self.speech_router.transcribe,
                audio_bytes,
                "audio/ogg",
            )
        except Exception as exc:
            logger.exception("TG Speech transcription failed")
            self.ui.write_log(f"ERR: TG speech trans failed — {exc}")
            return

        cleaned = _clean_transcript(transcript)
        if not _is_usable_command_transcript(cleaned):
            return
            
        self.ui.write_log(f"TG Voice: {cleaned}")
        await self.orchestrator.handle_user_command(cleaned)


    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")

    def _create_speech_router(self) -> VoiceRouter:
        primary_providers = [
            SarvamSpeechProvider(api_key=api_key, settings=self.voice_settings)
            for api_key in self.voice_settings.sarvam_api_keys
        ]
        gemini_key = get_api_key(required=False)
        if gemini_key:
            fallback_provider = GeminiFallbackSpeechProvider(api_key=gemini_key)
        else:
            fallback_provider = _UnavailableSpeechProvider(
                "Gemini fallback voice is unavailable because BUDDY_GEMINI_API_KEY is not configured."
            )
        return VoiceRouter(primary_providers=primary_providers, fallback_provider=fallback_provider)

    def speak(self, text: str):
        if not self._loop:
            return None
        future = asyncio.run_coroutine_threadsafe(
            self._speak_async(text),
            self._loop
        )
        future.add_done_callback(self._on_speak_done)
        return future

    @staticmethod
    def _on_speak_done(future):
        exc = future.exception()
        if exc:
            logger.error("speak() failed: %s", exc)

    async def _speak_async(self, text: str):
        if not text:
            return
        if self._tts_lock is None:
            self._tts_lock = asyncio.Lock()

        async with self._tts_lock:
            self.ui.write_log(f"Buddy: {text}")
            self.set_speaking(True)
            try:
                # Sync response back to Telegram if authenticated
                if getattr(self, "tg_bot", None) and getattr(self.tg_bot, "chat_id", None):
                    await self.tg_bot.send_text(text)
                if not getattr(self, "tts_muted", False):
                    audio_bytes = await asyncio.to_thread(self.speech_router.synthesize, text)
                    if getattr(self, "tg_bot", None) and getattr(self.tg_bot, "chat_id", None):
                        if self.tg_bot.tts_enabled and audio_bytes:
                            await self.tg_bot.send_audio(audio_bytes)
                    await asyncio.to_thread(self._play_audio_bytes, audio_bytes)
            except Exception as exc:
                logger.exception("Speech synthesis failed")
                self.ui.write_log(f"ERR: speech synthesis failed — {exc}")
            finally:
                self.set_speaking(False)

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.speak(build_tool_error_reply(tool_name, short))

    def _play_audio_bytes(self, audio_bytes: bytes) -> None:
        if not audio_bytes:
            raise VoiceProviderError("No audio returned from speech provider.")

        if audio_bytes[:4] == b"RIFF":
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                samplerate = wav_file.getframerate()
            if sample_width != 2:
                raise VoiceProviderError(f"Unsupported WAV sample width: {sample_width}")
            audio = np.frombuffer(frames, dtype=np.int16)
            if channels > 1:
                audio = audio.reshape(-1, channels)
            sd.play(audio, samplerate=samplerate, blocking=True)
            return

        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        sd.play(audio, samplerate=RECEIVE_SAMPLE_RATE, blocking=True)

    @staticmethod
    def _chunk_level(chunk: bytes) -> float:
        samples = np.frombuffer(chunk, dtype=np.int16)
        if samples.size == 0:
            return 0.0
        return float(np.abs(samples).max())

    async def _handle_voice_input(self, audio_bytes: bytes):
        self.ui.set_state("THINKING")
        wav_audio = _pcm16_to_wav_bytes(audio_bytes, samplerate=SEND_SAMPLE_RATE, channels=CHANNELS)
        try:
            transcript = await asyncio.to_thread(
                self.speech_router.transcribe,
                wav_audio,
                "audio/wav",
            )
        except Exception as exc:
            logger.exception("Speech transcription failed")
            self.ui.write_log(f"ERR: speech transcription failed — {exc}")
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            return

        cleaned = _clean_transcript(transcript)
        if not _is_usable_command_transcript(cleaned):
            logger.info("Dropped unusable transcript: %r", cleaned)
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            return

        lowered = cleaned.lower()
        wake_words = ["hey buddy", "ok buddy", "okay buddy", "hey, buddy", "ok, buddy", "okay, buddy"]
        
        current_time = time.time()
        if self._is_awake and (current_time - self._last_awake_time > 30.0):
            self._is_awake = False
            self.ui.write_log("SYS: Went back to sleep due to inactivity.")
            
        contains_wake_word = any(ww in lowered for ww in wake_words)

        if not self._is_awake:
            if not contains_wake_word:
                logger.info("Wake word not detected. Ignoring utterance: %r", cleaned)
                if not self.ui.muted:
                    self.ui.set_state("LISTENING")
                return
                
            self._is_awake = True
            self._last_awake_time = current_time
            self.ui.write_log("SYS: Buddy is AWAKE")
            
        else:
            self._last_awake_time = current_time

        # Strip wake word if present at the start of the sentence
        command = cleaned
        for ww in wake_words:
            if command.lower().startswith(ww):
                command = command[len(ww):].strip()
                # Also strip any leading punctuation like commas "Hey buddy, what's up" -> ", what's up"
                command = command.lstrip(" ,.!?").strip()
                break
                
        import string
        stripped_cmd = command.translate(str.maketrans('', '', string.punctuation)).strip()

        if not stripped_cmd:
            self.speak("Yes?")
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            return

        self.ui.write_log(f"You: {command}")
        await self.orchestrator.handle_user_command(command)

    async def _process_microphone(self):
        if self.mic_queue is None:
            return

        silence_limit = max(1, int(MIC_SILENCE_SECONDS * SEND_SAMPLE_RATE / CHUNK_SIZE))
        min_speech_chunks = max(1, int(MIC_MIN_SPEECH_SECONDS * SEND_SAMPLE_RATE / CHUNK_SIZE))
        max_speech_chunks = max(min_speech_chunks + 1, int(MIC_MAX_SPEECH_SECONDS * SEND_SAMPLE_RATE / CHUNK_SIZE))

        buffered_chunks: list[bytes] = []
        speech_chunks = 0
        silence_chunks = 0

        while True:
            chunk = await self.mic_queue.get()

            if self.ui.muted or self._is_speaking:
                buffered_chunks = []
                speech_chunks = 0
                silence_chunks = 0
                continue

            level = self._chunk_level(chunk)
            if level >= MIC_ACTIVITY_THRESHOLD:
                buffered_chunks.append(chunk)
                speech_chunks += 1
                silence_chunks = 0
            elif buffered_chunks:
                buffered_chunks.append(chunk)
                silence_chunks += 1

            utterance_complete = bool(buffered_chunks) and (
                silence_chunks >= silence_limit or len(buffered_chunks) >= max_speech_chunks
            )
            if not utterance_complete:
                continue

            captured_audio = b"".join(buffered_chunks)
            enough_speech = speech_chunks >= min_speech_chunks
            buffered_chunks = []
            speech_chunks = 0
            silence_chunks = 0

            if enough_speech:
                await self._handle_voice_input(captured_audio)

    def _build_config(self) -> types.LiveConnectConfig:
        from datetime import datetime

        memory     = load_memory()
        mem_str    = format_memory_for_prompt(memory)
        sys_prompt = _load_system_prompt()

        now      = datetime.now(ZoneInfo("Asia/Kolkata"))
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Timezone: Asia/Kolkata\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )

        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str)
        parts.append(sys_prompt)

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": ActionRegistry.get_all_declarations()}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Kore"
                    )
                )
            ),
        )

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})

        print(f"[BUDDY] 🔧 {name}  {args}")
        self.ui.set_state("THINKING")

        loop = asyncio.get_running_loop()
        result = "Done."

        async def run_action():
            return await loop.run_in_executor(
                None,
                lambda: ActionRegistry.execute(
                    name=name,
                    parameters=args,
                    player=self.ui,
                    speak=self.speak,
                    orchestrator=self.orchestrator
                )
            )

        try:
            # Phase 5: Execute via Kernel Task Engine with deterministic retries
            r = await kernel.tasks.execute_with_retry(run_action)
            result = r or "Done."

            # Update UI and log if save_memory returned ok silently
            if name == "save_memory":
                if not self.ui.muted:
                    self.ui.set_state("LISTENING")
                return types.FunctionResponse(
                    id=fc.id, name=name,
                    response={"result": result, "silent": True}
                )

        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            logger.exception(f"Tool '{name}' failed during execution")
            self.speak_error(name, e)

        if not self.ui.muted:
            self.ui.set_state("LISTENING")

        print(f"[BUDDY] 📤 {name} → {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )



    async def _listen_audio(self):
        print("[BUDDY] 🎤 Mic started")
        loop = asyncio.get_running_loop()

        def callback(indata, frames, time_info, status):
            with self._speaking_lock:
                buddy_speaking = self._is_speaking
            if not buddy_speaking and not self.ui.muted and self.mic_queue is not None:
                data = indata.tobytes()
                loop.call_soon_threadsafe(
                    enqueue_latest,
                    self.mic_queue,
                    data,
                )

        try:
            with sd.InputStream(
                samplerate=SEND_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=callback,
            ):
                print("[BUDDY] 🎤 Mic stream open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            logger.exception("Mic initialization or processing failed")
            print(f"[BUDDY] ❌ Mic: {e}")
            raise



    async def _run_telegram_bot_safe(self):
        """Fault-isolated wrapper — Telegram failures never crash the TaskGroup."""
        while True:
            try:
                await self.tg_bot.start()
            except asyncio.CancelledError:
                logger.info("Telegram bot task cancelled")
                raise  # Let TaskGroup teardown propagate cleanly
            except BaseException as e:
                logger.warning("Telegram bot crashed, will retry in 30s: %s", e)
                print(f"[BUDDY] ⚠️ Telegram bot error: {e}. Retrying in 30s...")
                try:
                    await asyncio.sleep(30)
                except asyncio.CancelledError:
                    raise

    async def run(self):
        # Phase 5: Initialize Local OS Kernel
        if not self._kernel_initialized:
            try:
                await kernel.initialize()
                self._kernel_initialized = True
            except Exception as e:
                logger.exception("Kernel OS initialization failed")
                print(f"[Kernel] ⚠️ Init failed: {e}")

        while True:
            try:
                print("[BUDDY] 🔌 Starting local voice pipeline...")
                self._loop = asyncio.get_running_loop()
                self.mic_queue = asyncio.Queue(maxsize=64)
                self._tts_lock = asyncio.Lock()

                async with asyncio.TaskGroup() as tg:
                    print("[BUDDY] ✅ Local voice pipeline ready.")
                    self.ui.set_state("LISTENING")
                    if not self._online_logged:
                        self._online_logged = True
                        self.ui.write_log("SYS: BUDDY online.")
                    if not self._startup_greeted:
                        if hasattr(self.ui, "wait_for_boot_sequence"):
                            try:
                                self.ui.wait_for_boot_sequence(timeout=12)
                            except Exception:
                                pass
                        self._startup_greeted = True
                        self.speak(build_boot_greeting())

                    tg.create_task(self._listen_audio())
                    tg.create_task(self._process_microphone())
                    tg.create_task(self._run_telegram_bot_safe())

            except Exception as e:
                logger.exception("Main loop voice pipeline failed")
                print(f"[BUDDY] ⚠️ {e}")
                
            self.set_speaking(False)
            self.ui.set_state("THINKING")
            print("[BUDDY] 🔄 Reconnecting in 3s...")
            await asyncio.sleep(3)


def main():
    configure_console_output()
    report = bootstrap_application()
    logger.info("Bootstrap complete. warnings=%s log_path=%s", len(report.warnings), report.log_path)
    ui = BuddyUI("face.png")

    def runner():
        ui.wait_for_api_key()
        buddy = BuddyLive(ui)
        ui.update_runtime_status(
            {
                "configReady": True,
                "setupRequired": False,
                "runtimeReady": True,
                "runtimeBooting": False,
            }
        )
        ui.set_state("LISTENING")
        
        # Global hotkeys
        def toggle_listening():
            if ui.muted:
                ui.set_muted(False)
                ui.set_state("LISTENING")
                logger.info("[BUDDY] Microphone ACTIVE via F4.")
                print("[BUDDY] Microphone ACTIVE.")
            else:
                ui.set_muted(True)
                ui.set_state("MUTED")
                logger.info("[BUDDY] Microphone MUTED via F4.")
                print("[BUDDY] Microphone MUTED.")
                buddy._is_awake = False

        def toggle_tts():
            buddy.tts_muted = not getattr(buddy, "tts_muted", False)
            state_str = "MUTED" if buddy.tts_muted else "ACTIVE"
            ui.write_log(f"SYS: TTS is now {state_str}")
            logger.info(f"[BUDDY] TTS {state_str} via F3.")
            print(f"[BUDDY] TTS {state_str}.")
            
        keyboard.add_hotkey('f4', toggle_listening)
        keyboard.add_hotkey('f3', toggle_tts)
        
        try:
            asyncio.run(buddy.run())
        except KeyboardInterrupt:
            buddy.speak(build_shutdown_farewell())
            logger.info("Shutting down from keyboard interrupt")

    threading.Thread(target=runner, daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    main()

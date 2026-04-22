import asyncio
import io
import logging
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config.runtime import load_config

logger = logging.getLogger(__name__)

def convert_to_ogg(input_bytes: bytes) -> bytes:
    """Uses FFmpeg to convert an audio byte stream to OGG Opus."""
    try:
        process = subprocess.Popen(
            ['ffmpeg', '-i', 'pipe:0', '-c:a', 'libopus', '-b:a', '32k', '-f', 'ogg', 'pipe:1'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = process.communicate(input=input_bytes)
        if process.returncode != 0:
            logger.error(f"FFmpeg conversion failed: {err.decode('utf-8', errors='ignore')}")
            return input_bytes # Fallback to original
        return out
    except FileNotFoundError:
        logger.warning("FFmpeg not found. Cannot convert to OGG Opus.")
        return input_bytes
    except Exception as e:
        logger.error(f"Error during audio conversion: {e}")
        return input_bytes


class TelegramBot:
    def __init__(self, on_text_received=None, on_voice_received=None):
        self.config = load_config()
        self.on_text_received = on_text_received
        self.on_voice_received = on_voice_received
        self.application = None
        self.tts_enabled = False
        self.chat_id = None  # To store the chat_id of the authorized user

    async def start(self):
        token = self.config.telegram_bot_token
        if not token:
            logger.info("Telegram bot token not provided. Bot will not start.")
            return

        self.application = Application.builder().token(token).build()

        self.application.add_handler(CommandHandler("start", self._start_cmd))
        self.application.add_handler(CommandHandler("tts", self._tts_cmd))
        self.application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self._handle_text))
        self.application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self._handle_voice))

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram bot started successfully.")

    async def stop(self):
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

    def _is_authorized(self, update: Update) -> bool:
        user = update.effective_user
        if not user:
            return False
        
        # Check against telegram_user_id or telegram_username
        if self.config.telegram_user_id and str(user.id) == self.config.telegram_user_id.strip():
            return True
        if self.config.telegram_username and user.username and user.username.lower() == self.config.telegram_username.strip().lower():
            return True
            
        logger.warning(f"Unauthorized access attempt from user: {user.username} (ID: {user.id})")
        return False

    async def _start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        self.chat_id = update.effective_chat.id
        await update.message.reply_text("SIRIUS Agent online. Awaiting commands. Use /tts on to enable voice responses.")

    async def _tts_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        self.chat_id = update.effective_chat.id
        
        args = context.args
        if not args:
            await update.message.reply_text(f"TTS is currently {'ON' if self.tts_enabled else 'OFF'}. Usage: /tts on | /tts off")
            return
            
        arg = args[0].lower()
        if arg == "on":
            self.tts_enabled = True
            await update.message.reply_text("TTS Audio responses enabled.")
        elif arg == "off":
            self.tts_enabled = False
            await update.message.reply_text("TTS Audio responses disabled.")
        else:
            await update.message.reply_text("Usage: /tts on | /tts off")

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        self.chat_id = update.effective_chat.id
        text = update.message.text
        
        if self.on_text_received:
            asyncio.create_task(self.on_text_received(text))

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        self.chat_id = update.effective_chat.id
        
        # Support both voice and audio attachments
        attachment = update.message.voice or update.message.audio
        if not attachment:
            return

        file = await attachment.get_file()
        media_bytes = await file.download_as_bytearray()
        
        if self.on_voice_received:
            asyncio.create_task(self.on_voice_received(bytes(media_bytes)))

    async def send_text(self, text: str):
        if self.application and self.chat_id:
            try:
                await self.application.bot.send_message(chat_id=self.chat_id, text=text)
            except Exception as e:
                logger.error(f"Failed to send Telegram text: {e}")

    async def send_audio(self, wav_bytes: bytes):
        if self.application and self.chat_id:
            try:
                # Convert WAV to OGG for native Telegram Voice playback if possible
                ogg_bytes = await asyncio.to_thread(convert_to_ogg, wav_bytes)
                
                # Send as voice message
                await self.application.bot.send_voice(chat_id=self.chat_id, voice=ogg_bytes)
            except Exception as e:
                logger.error(f"Failed to send Telegram voice: {e}")

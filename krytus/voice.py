import os
import tempfile
import edge_tts
import structlog
from telegram import Update
from telegram.ext import ContextTypes

from krytus.agent import agent
from krytus.memory import save_memory

logger = structlog.get_logger()

VOICE = "en-US-AriaNeural"


async def text_to_speech(text: str, output_path: str) -> bool:
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_path)
        return True
    except Exception as e:
        logger.error("tts_failed", error=str(e))
        return False


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != context.bot_data.get("my_chat_id"):
        await update.message.reply_text("❌ Unauthorized")
        return

    voice = update.message.voice
    if not voice:
        return

    logger.info("voice_received", file_id=voice.file_id, duration=voice.duration)

    try:
        voice_file = await context.bot.get_file(voice.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_in:
            await voice_file.download_to_drive(tmp_in.name)
            tmp_in_path = tmp_in.name

        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_ogg(tmp_in_path)
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                audio.export(tmp_wav.name, format="wav")
                tmp_wav_path = tmp_wav.name

            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.AudioFile(tmp_wav_path) as source:
                    audio_data = recognizer.record(source)
                    user_text = recognizer.recognize_google(audio_data)
                
                logger.info("stt_success", text=user_text[:100])
            except Exception as e:
                logger.error("stt_failed", error=str(e))
                await update.message.reply_text("🎤 Could not understand audio. Try again.")
                return
            finally:
                if os.path.exists(tmp_wav_path):
                    os.unlink(tmp_wav_path)
        finally:
            if os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)

        await update.message.reply_text(f"🎤 You said: {user_text}")

        response = await agent.process_message(user_text)
        save_memory("user", user_text)
        save_memory("assistant", response)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_out:
            if await text_to_speech(response, tmp_out.name):
                await update.message.reply_voice(voice=open(tmp_out.name, "rb"))
            else:
                await update.message.reply_text(response)
            os.unlink(tmp_out.name)

    except Exception as e:
        logger.error("voice_handler_error", error=str(e))
        await update.message.reply_text(f"⚠️ Voice processing error: {e!s}")


async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != context.bot_data.get("my_chat_id"):
        return

    if not context.args:
        await update.message.reply_text("Usage: `/voice <text to speak>`")
        return

    text = " ".join(context.args)
    
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        if await text_to_speech(text, tmp.name):
            await update.message.reply_voice(voice=open(tmp.name, "rb"))
            os.unlink(tmp.name)
        else:
            await update.message.reply_text("❌ TTS failed")
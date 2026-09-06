import os
import asyncio
import tempfile
import structlog
from typing import Optional

logger = structlog.get_logger()

_pytgcalls = None
_call_client = None
_call_active = False


def _is_linux():
    return os.name == "posix" and "linux" in os.uname().sysname.lower()


async def init_voice_call(bot_token: str, api_id: int, api_hash: str):
    global _pytgcalls, _call_client, _call_active
    
    if not _is_linux():
        logger.info("voice_call_skipped_not_linux")
        return False
    
    try:
        from pyrogram import Client
        from pytgcalls import PyTgCalls
        from pytgcalls.types.input_stream import InputAudioStream
        from pytgcalls.types.input_stream.quality import HighQualityAudio
        
        _call_client = Client(
            "krytus_voice",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
        )
        
        _pytgcalls = PyTgCalls(_call_client)
        await _pytgcalls.start()
        _call_active = True
        
        logger.info("voice_call_initialized")
        return True
    except Exception as e:
        logger.error("voice_call_init_failed", error=str(e))
        return False


async def join_voice_chat(chat_id: int) -> bool:
    global _call_active
    
    if not _call_active or not _pytgcalls:
        return False
    
    try:
        from pytgcalls.types.input_stream import InputAudioStream
        from pytgcalls.types.input_stream.quality import HighQualityAudio
        
        await _pytgcalls.join_group_call(
            chat_id,
            InputAudioStream(
                "silence.ogg",
                audio_quality=HighQualityAudio(),
            ),
        )
        logger.info("joined_voice_chat", chat_id=chat_id)
        return True
    except Exception as e:
        logger.error("join_voice_chat_failed", chat_id=chat_id, error=str(e))
        return False


async def leave_voice_chat(chat_id: int) -> bool:
    if not _call_active or not _pytgcalls:
        return False
    
    try:
        await _pytgcalls.leave_group_call(chat_id)
        logger.info("left_voice_chat", chat_id=chat_id)
        return True
    except Exception as e:
        logger.error("leave_voice_chat_failed", chat_id=chat_id, error=str(e))
        return False


async def speak_in_call(chat_id: int, text: str, voice: str = "en-US-AriaNeural") -> bool:
    if not _call_active or not _pytgcalls:
        return False
    
    try:
        import edge_tts
        
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            from pytgcalls.types.input_stream import InputAudioStream
            from pytgcalls.types.input_stream.quality import HighQualityAudio
            
            await _pytgcalls.change_stream(
                chat_id,
                InputAudioStream(tmp_path, audio_quality=HighQualityAudio())
            )
            
            await asyncio.sleep(2)
            
            return True
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        logger.error("speak_in_call_failed", error=str(e))
        return False


async def handle_call_command(chat_id: int, bot_token: str, api_id: int, api_hash: str):
    if not _is_linux():
        return "🔴 Live voice calls only work on Linux (Railway/WSL2). Deploy to Railway for live calls."
    
    if not await init_voice_call(bot_token, api_id, api_hash):
        return "❌ Failed to initialize voice call system"
    
    if await join_voice_chat(chat_id):
        await speak_in_call(chat_id, "Hello! I'm now in the voice chat. How can I help you?")
        return "✅ Joined voice chat! I'm now listening."
    else:
        return "❌ Failed to join voice chat. Make sure there's an active voice chat in this group."
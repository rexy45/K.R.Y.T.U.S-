import logging
import os
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib
import edge_tts
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from krytus.config import config
from krytus.memory import recall_memory, save_memory
from krytus.reminders import set_reminder

logger = logging.getLogger(__name__)

_bot_application = None


def set_bot_application(app):
    """Set the bot application for sending messages."""
    global _bot_application
    _bot_application = app


def _log_info(msg: str, **kwargs):
    logger.info(msg, extra=kwargs)


def _log_error(msg: str, **kwargs):
    logger.error(msg, extra=kwargs)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def send_email(recipient: str, subject: str, content: str) -> dict[str, Any]:
    try:
        msg = MIMEMultipart()
        msg["From"] = config.EMAIL_FROM
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(content, "plain"))

        await aiosmtplib.send(
            msg,
            hostname=config.SMTP_HOST,
            port=config.SMTP_PORT,
            username=config.SMTP_USERNAME,
            password=config.SMTP_PASSWORD,
            start_tls=True,
        )

        _log_info("email_sent", recipient=recipient, subject=subject)
        return {"success": True, "message": f"Email sent to {recipient}"}
    except Exception as e:
        _log_error("email_send_failed", recipient=recipient, error=str(e))
        return {"success": False, "error": str(e)}


async def _generate_tts_audio(text: str) -> bytes:
    """Generate TTS audio using Edge TTS."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=config.TTS_VOICE,
        rate=config.TTS_RATE,
        volume=config.TTS_VOLUME,
    )
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


async def send_telegram_voice(text: str) -> dict[str, Any]:
    """Generate TTS audio and send as Telegram voice message to MY_TELEGRAM_CHAT_ID."""
    try:
        if _bot_application is None:
            return {"success": False, "error": "Bot application not initialized"}

        # Generate TTS audio
        audio_data = await _generate_tts_audio(text)

        # Write to temp file and send
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                await _bot_application.bot.send_voice(
                    chat_id=config.MY_TELEGRAM_CHAT_ID,
                    voice=audio_file,
                    caption=text[:100] if len(text) > 100 else text,
                )

            _log_info("telegram_voice_sent", text_length=len(text))
            return {"success": True, "message": "Voice message sent to Telegram"}
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        _log_error("telegram_voice_failed", error=str(e))
        return {"success": False, "error": str(e)}


async def send_telegram_call_link() -> dict[str, Any]:
    """Send a Telegram VoIP call link to MY_TELEGRAM_CHAT_ID."""
    try:
        if _bot_application is None:
            return {"success": False, "error": "Bot application not initialized"}

        # Create a Telegram call link (tg://call)
        call_link = "tg://call?request_join=true"
        
        await _bot_application.bot.send_message(
            chat_id=config.MY_TELEGRAM_CHAT_ID,
            text=(
                "📞 **Incoming Call from Krytus**\n\n"
                "Tap the button below to start a live VoIP call:"
            ),
            parse_mode="Markdown",
            reply_markup={
                "inline_keyboard": [[
                    {"text": "📞 Answer Call", "url": call_link}
                ]]
            }
        )

        _log_info("telegram_call_link_sent")
        return {"success": True, "message": "Telegram call link sent", "call_link": call_link}

    except Exception as e:
        _log_error("telegram_call_link_failed", error=str(e))
        return {"success": False, "error": str(e)}


async def send_telegram_message(text: str) -> dict[str, Any]:
    """Send a plain text message to MY_TELEGRAM_CHAT_ID."""
    try:
        if _bot_application is None:
            return {"success": False, "error": "Bot application not initialized"}

        await _bot_application.bot.send_message(
            chat_id=config.MY_TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="Markdown"
        )

        _log_info("telegram_message_sent", text_length=len(text))
        return {"success": True, "message": "Telegram message sent"}

    except Exception as e:
        _log_error("telegram_message_failed", error=str(e))
        return {"success": False, "error": str(e)}


async def save_project_memory(topic: str, note: str) -> dict[str, Any]:
    try:
        result = save_memory(topic, note)
        return result
    except Exception as e:
        _log_error("save_memory_failed", topic=topic, error=str(e))
        return {"success": False, "error": str(e)}


async def recall_project_memory(query: str, n_results: int = 3) -> dict[str, Any]:
    try:
        result = recall_memory(query, n_results)
        return result
    except Exception as e:
        _log_error("recall_memory_failed", query=query, error=str(e))
        return {"success": False, "error": str(e)}


async def set_reminder_tool(minutes_from_now: int, message: str) -> dict[str, Any]:
    try:
        result = set_reminder(minutes_from_now, message)
        return result
    except Exception as e:
        _log_error("set_reminder_failed", error=str(e))
        return {"success": False, "error": str(e)}


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email via SMTP. Use for external communications. REQUIRES USER CONFIRMATION unless user explicitly said 'send it right now' or 'send immediately'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "content": {"type": "string", "description": "Email body content (plain text)"}
                },
                "required": ["recipient", "subject", "content"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram_voice",
            "description": "Generate speech using Edge TTS and send as a Telegram voice message to your chat. Use for speaking responses or alerts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to convert to speech and send as voice message"}
                },
                "required": ["text"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram_call_link",
            "description": "Send a Telegram VoIP call link to your chat. When you tap the link, a live VoIP call starts in Telegram. Use when user asks to 'call me' or 'call me now'.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram_message",
            "description": "Send a plain text message to your Telegram chat. Use for quick notifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Message text to send"}
                },
                "required": ["text"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_project_memory",
            "description": "Save architectural decisions, bug notes, project updates, or important context to long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic/category for this memory (e.g., 'architecture', 'bug-fix', 'decision')"},
                    "note": {"type": "string", "description": "Detailed note to save"}
                },
                "required": ["topic", "note"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_project_memory",
            "description": "Search long-term memory for relevant past context. Use when user asks about past decisions, bugs, or project history. ALWAYS USE THIS before answering questions about past context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Semantic search query"},
                    "n_results": {"type": "integer", "description": "Number of results to return", "default": 3}
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a timed reminder that will be delivered via Telegram at the specified time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "minutes_from_now": {"type": "integer", "description": "Minutes from now when reminder should trigger"},
                    "message": {"type": "string", "description": "Reminder message"}
                },
                "required": ["minutes_from_now", "message"],
                "additionalProperties": False
            }
        }
    }
]


TOOL_FUNCTIONS = {
    "send_email": send_email,
    "send_telegram_voice": send_telegram_voice,
    "send_telegram_call_link": send_telegram_call_link,
    "send_telegram_message": send_telegram_message,
    "save_project_memory": save_project_memory,
    "recall_project_memory": recall_project_memory,
    "set_reminder": set_reminder_tool,
}
import logging
import httpx

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

from krytus.agent import agent
from krytus.config import config
from krytus.memory import get_recent_memories
from krytus.reminders import (
    get_all_reminders,
    get_pending_reminders,
    init_database,
    mark_reminder_delivered,
)

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _log_info(msg: str, **kwargs):
    logger.info(msg, extra=kwargs)


def _log_error(msg: str, **kwargs):
    logger.error(msg, extra=kwargs)


def _log_warning(msg: str, **kwargs):
    logger.warning(msg, extra=kwargs)


async def check_reminders(bot_application: Application) -> None:
    pending = get_pending_reminders()
    for reminder in pending:
        try:
            delivered = mark_reminder_delivered(reminder["id"])
            if delivered:
                await bot_application.bot.send_message(
                    chat_id=config.MY_TELEGRAM_CHAT_ID,
                    text=f"⏰ **Reminder**: {reminder['message']}",
                    parse_mode="Markdown"
                )
                _log_info("reminder_delivered", reminder_id=reminder["id"])
        except Exception as e:
            _log_error("reminder_delivery_failed", reminder_id=reminder["id"], error=str(e))


def _is_authorized(update: Update) -> bool:
    if update.effective_chat is None:
        return False
    return update.effective_chat.id == config.MY_TELEGRAM_CHAT_ID


async def auth_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not _is_authorized(update):
        chat_id = update.effective_chat.id if update.effective_chat else "unknown"
        _log_warning("unauthorized_access", chat_id=chat_id)
        return False
    return True


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await auth_middleware(update, context):
        return
    await update.message.reply_text(
        "🤖 **Krytus Online**\n\n"
        "Your personal chief-of-staff is ready.\n\n"
        "**Commands:**\n"
        "• `/status` - System health check\n"
        "• `/memory` - View recent memories\n"
        "• `/reminders` - List pending reminders\n"
        "• `/health` - Detailed system status\n\n"
        "Just chat naturally - I'll use tools as needed."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await auth_middleware(update, context):
        return
    await update.message.reply_text("✅ Krytus operational. All systems nominal.")


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await auth_middleware(update, context):
        return
    
    from krytus.memory import get_recent_memories
    from krytus.reminders import get_all_reminders
    
    memories = get_recent_memories(1)
    reminders = get_all_reminders()
    pending = [r for r in reminders if not r["delivered"]]
    
    text = (
        "🏥 **System Health**\n\n"
        f"• **Memories stored**: {len(memories.get('memories', [])) if memories.get('success') else 'error'}\n"
        f"• **Total reminders**: {len(reminders)}\n"
        f"• **Pending reminders**: {len(pending)}\n"
        f"• **Scheduler**: {'Running' if scheduler.running else 'Stopped'}\n"
        f"• **OpenAI model**: {config.OPENAI_MODEL}\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await auth_middleware(update, context):
        return
    result = get_recent_memories(10)
    if result["success"] and result["memories"]:
        text = "🧠 **Recent Memories**:\n\n"
        for mem in result["memories"]:
            ts = mem['timestamp'][:19] if mem['timestamp'] != 'unknown' else 'unknown'
            text += f"• **{mem['topic']}** ({ts})\n  {mem['content'][:200]}...\n\n"
    else:
        text = "🧠 No memories stored yet."
    await update.message.reply_text(text, parse_mode="Markdown")


async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await auth_middleware(update, context):
        return
    reminders = get_all_reminders()
    if reminders:
        text = "⏰ **All Reminders**:\n\n"
        for r in reminders:
            status = "✅" if r["delivered"] else "⏳"
            text += f"{status} `{r['id']}`: {r['message']} (due: {r['due_at'][:19]})\n"
    else:
        text = "⏰ No reminders."
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await auth_middleware(update, context):
        return

    user_text = update.message.text
    _log_info("message_received", text=user_text[:100])

    try:
        response = await agent.process_message(user_text)
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        _log_error("agent_error", error=str(e))
        await update.message.reply_text(f"⚠️ Error processing request: {e!s}")


async def post_init(app: Application) -> None:
    config.ensure_data_dirs()
    init_database()
    
    scheduler.add_job(
        check_reminders,
        "interval",
        seconds=30,
        args=[app],
        id="reminder_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _log_info("krytus_started", scheduler_running=scheduler.running)


async def post_shutdown(app: Application) -> None:
    scheduler.shutdown(wait=False)
    _log_info("krytus_shutdown_complete")


def create_application() -> Application:
    # Custom HTTPX request with very long timeouts for slow networks
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=60.0,
        write_timeout=60.0,
        connect_timeout=60.0,
        pool_timeout=60.0,
    )
    
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .request(request)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("memory", memory_command))
    application.add_handler(CommandHandler("reminders", reminders_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Chat, Message, Update, User

from krytus.bot import (
    _is_authorized,
    auth_middleware,
    health_command,
    memory_command,
    reminders_command,
    start_command,
    status_command,
)


def make_update(chat_id: int, text: str = "/start") -> Update:
    user = MagicMock(spec=User)
    user.id = chat_id
    
    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    chat.type = "private"
    
    message = MagicMock(spec=Message)
    message.text = text
    message.chat = chat
    message.from_user = user
    message.reply_text = AsyncMock()
    
    update = MagicMock(spec=Update)
    update.effective_chat = chat
    update.message = message
    update.effective_user = user
    
    return update


@pytest.mark.asyncio
async def test_authorized_user():
    update = make_update(123456789)
    assert _is_authorized(update) is True


@pytest.mark.asyncio
async def test_unauthorized_user():
    update = make_update(999999999)
    assert _is_authorized(update) is False


@pytest.mark.asyncio
async def test_auth_middleware_authorized():
    update = make_update(123456789)
    context = MagicMock()
    result = await auth_middleware(update, context)
    assert result is True


@pytest.mark.asyncio
async def test_auth_middleware_unauthorized():
    update = make_update(999999999)
    context = MagicMock()
    result = await auth_middleware(update, context)
    assert result is False


@pytest.mark.asyncio
async def test_start_command(temp_dirs):
    update = make_update(123456789)
    context = MagicMock()
    await start_command(update, context)
    update.message.reply_text.assert_called_once()
    args = update.message.reply_text.call_args[0][0]
    assert "Krytus Online" in args


@pytest.mark.asyncio
async def test_status_command(temp_dirs):
    update = make_update(123456789)
    context = MagicMock()
    await status_command(update, context)
    update.message.reply_text.assert_called_once()
    args = update.message.reply_text.call_args[0][0]
    assert "operational" in args


@pytest.mark.asyncio
async def test_health_command(temp_dirs):
    update = make_update(123456789)
    context = MagicMock()
    await health_command(update, context)
    update.message.reply_text.assert_called_once()
    args = update.message.reply_text.call_args[0][0]
    assert "System Health" in args


@pytest.mark.asyncio
async def test_memory_command(temp_dirs):
    update = make_update(123456789)
    context = MagicMock()
    await memory_command(update, context)
    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_reminders_command(temp_dirs):
    update = make_update(123456789)
    context = MagicMock()
    await reminders_command(update, context)
    update.message.reply_text.assert_called_once()

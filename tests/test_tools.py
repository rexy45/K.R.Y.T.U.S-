
import pytest

from krytus.tools import (
    recall_project_memory,
    save_project_memory,
    send_email,
    send_telegram_call_link,
    send_telegram_message,
    send_telegram_voice,
    set_reminder_tool,
)


@pytest.mark.asyncio
async def test_send_email_success(mock_smtp):
    result = await send_email("test@example.com", "Subject", "Body")
    assert result["success"] is True
    mock_smtp.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_failure(mock_smtp):
    mock_smtp.side_effect = Exception("SMTP error")
    # The retry decorator catches and returns failed result after retries
    result = await send_email("test@example.com", "Subject", "Body")
    assert result["success"] is False
    assert "SMTP error" in result["error"]


@pytest.mark.asyncio
async def test_send_telegram_voice(mock_edge_tts, mock_bot_app, temp_dirs):
    result = await send_telegram_voice("Hello world")
    assert result["success"] is True
    assert "Voice message sent" in result["message"]
    mock_bot_app.bot.send_voice.assert_called_once()


@pytest.mark.asyncio
async def test_send_telegram_voice_no_bot_app(mock_edge_tts, temp_dirs):
    # Test when bot app is not initialized
    import krytus.tools
    krytus.tools._bot_application = None
    result = await send_telegram_voice("Hello world")
    assert result["success"] is False
    assert "Bot application not initialized" in result["error"]


@pytest.mark.asyncio
async def test_send_telegram_call_link(mock_bot_app, temp_dirs):
    result = await send_telegram_call_link()
    assert result["success"] is True
    assert "Telegram call link sent" in result["message"]
    assert result["call_link"] == "tg://call?request_join=true"
    mock_bot_app.bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_telegram_message(mock_bot_app, temp_dirs):
    result = await send_telegram_message("Test message")
    assert result["success"] is True
    assert "Telegram message sent" in result["message"]
    mock_bot_app.bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_save_project_memory(temp_dirs):
    result = await save_project_memory("test-topic", "test note")
    assert result["success"] is True


@pytest.mark.asyncio
async def test_recall_project_memory(temp_dirs):
    await save_project_memory("test", "saved note")
    result = await recall_project_memory("saved", n_results=1)
    assert result["success"] is True
    assert len(result["memories"]) == 1


@pytest.mark.asyncio
async def test_set_reminder_tool(temp_dirs):
    result = await set_reminder_tool(0, "Test reminder")
    assert result["success"] is True
    assert "reminder_id" in result
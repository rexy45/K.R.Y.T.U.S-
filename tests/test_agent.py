from unittest.mock import AsyncMock, patch

import pytest

from krytus.agent import KrytusAgent
from krytus.llm.base import ChatCompletion, ChatMessage, ToolCall


def _make_completion(content: str | None = None, tool_calls: list[ToolCall] | None = None) -> ChatCompletion:
    return ChatCompletion(message=ChatMessage(role="assistant", content=content, tool_calls=tool_calls))


@pytest.mark.asyncio
async def test_agent_no_tool_call():
    with patch.object(KrytusAgent, "_get_provider") as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.chat_completion.return_value = _make_completion("Hello! How can I help?")
        mock_get_provider.return_value = mock_provider
        
        agent = KrytusAgent()
        result = await agent.process_message("Hi")
        
        assert "Hello" in result


@pytest.mark.asyncio
async def test_agent_with_tool_call(temp_dirs):
    tool_call = ToolCall(id="call_123", name="set_reminder", arguments={"minutes_from_now": 5, "message": "Test"})
    
    with patch.object(KrytusAgent, "_get_provider") as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.chat_completion.side_effect = [
            _make_completion(None, [tool_call]),
            _make_completion("Reminder set for 5 minutes from now."),
        ]
        mock_get_provider.return_value = mock_provider
        
        agent = KrytusAgent()
        result = await agent.process_message("Remind me in 5 minutes to test")
        
        assert "Reminder set" in result


@pytest.mark.asyncio
async def test_agent_conversation_history(temp_dirs):
    with patch.object(KrytusAgent, "_get_provider") as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.chat_completion.return_value = _make_completion("Got it!")
        mock_get_provider.return_value = mock_provider
        
        agent = KrytusAgent()
        await agent.process_message("First message")
        await agent.process_message("Second message")
        
        assert len(agent.conversation_history) == 4
        assert agent.conversation_history[0]["content"] == "First message"
        assert agent.conversation_history[2]["content"] == "Second message"
from typing import Any

from openai import AsyncOpenAI

from krytus.llm.base import ChatCompletion, ChatMessage, LLMProvider, ToolCall


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = "auto",
        temperature: float = 0.3,
    ) -> ChatCompletion:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
        )

        msg = response.choices[0].message
        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments,
                )
                for tc in msg.tool_calls
            ]

        return ChatCompletion(
            message=ChatMessage(
                role="assistant",
                content=msg.content,
                tool_calls=tool_calls,
            )
        )

    async def close(self) -> None:
        await self.client.close()
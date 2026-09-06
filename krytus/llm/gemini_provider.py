import json
from typing import Any

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

from krytus.llm.base import ChatCompletion, ChatMessage, LLMProvider, ToolCall


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self._model = None

    def _get_model(self, tools: list[dict[str, Any]] | None = None):
        if self._model is None or tools is not None:
            gemini_tools = None
            if tools:
                function_declarations = []
                for tool in tools:
                    if tool.get("type") == "function":
                        func = tool["function"]
                        function_declarations.append(
                            FunctionDeclaration(
                                name=func["name"],
                                description=func.get("description", ""),
                                parameters=func.get("parameters", {}),
                            )
                        )
                if function_declarations:
                    gemini_tools = Tool(function_declarations=function_declarations)

            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=gemini_tools,
            )
        return self._model

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-format messages to Gemini format."""
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content")

            if role == "system":
                # Gemini uses system_instruction in model config, not messages
                continue
            elif role == "assistant" and msg.get("tool_calls"):
                # Assistant with tool calls
                parts = []
                if content:
                    parts.append({"text": content})
                for tc in msg["tool_calls"]:
                    parts.append({
                        "function_call": {
                            "name": tc["function"]["name"],
                            "args": json.loads(tc["function"]["arguments"]),
                        }
                    })
                gemini_messages.append({"role": "model", "parts": parts})
            elif role == "tool":
                # Tool result
                gemini_messages.append({
                    "role": "function",
                    "parts": [{
                        "function_response": {
                            "name": msg.get("name", "unknown"),
                            "response": {"result": msg.get("content", "")},
                        }
                    }]
                })
            else:
                # User or assistant without tool calls
                gemini_role = "user" if role == "user" else "model"
                gemini_messages.append({
                    "role": gemini_role,
                    "parts": [{"text": content or ""}],
                })
        return gemini_messages

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = "auto",
        temperature: float = 0.3,
    ) -> ChatCompletion:
        model = self._get_model(tools)
        gemini_messages = self._convert_messages(messages)

        # Extract system message if present
        system_instruction = None
        for msg in messages:
            if msg.get("role") == "system":
                system_instruction = msg.get("content")
                break

        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
                tools=model._tools if hasattr(model, '_tools') else None,
            )

        generation_config = genai.GenerationConfig(
            temperature=temperature,
        )

        response = await model.generate_content_async(
            gemini_messages,
            generation_config=generation_config,
        )

        # Parse response
        candidate = response.candidates[0]
        content = None
        tool_calls = None

        if candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    content = part.text
                elif hasattr(part, "function_call") and part.function_call:
                    if tool_calls is None:
                        tool_calls = []
                    fc = part.function_call
                    tool_calls.append(ToolCall(
                        id=f"call_{fc.name}",
                        name=fc.name,
                        arguments=json.dumps(dict(fc.args)),
                    ))

        return ChatCompletion(
            message=ChatMessage(
                role="assistant",
                content=content,
                tool_calls=tool_calls,
            )
        )

    async def close(self) -> None:
        # genai doesn't have explicit close
        pass
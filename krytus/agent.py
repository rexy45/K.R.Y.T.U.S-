import logging
from datetime import datetime
from typing import Any

from krytus.llm import ChatCompletion, LLMProvider, get_llm_provider
from krytus.tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

logger = logging.getLogger(__name__)

def _log_info(msg: str, **kwargs):
    logger.info(msg, extra=kwargs)

def _log_error(msg: str, **kwargs):
    logger.error(msg, extra=kwargs)


SYSTEM_PROMPT = """You are Krytus, an autonomous personal AI chief-of-staff. You operate with full tool access and long-term memory.

CORE PRINCIPLES:
1. TOOL USE: Always execute tools iteratively. Call a tool, receive the result, then decide the next action. Never assume tool results.
2. PROACTIVE RECALL: If the user asks about past tasks, architectural choices, project decisions, or anything that might be in memory, you MUST call recall_project_memory FIRST before responding.
3. HIGH-IMPACT CONFIRMATION: For sending external emails (send_email), you MUST format the draft cleanly and ask for explicit approval unless the user explicitly said "send it right now" or "send immediately".
4. GROUNDED CONTEXT: Current date/time will be injected into each conversation. Use it for scheduling and time-aware responses.
5. AUTONOMY: You can chain multiple tools in sequence to accomplish complex requests.

TOOL AVAILABILITY:
- send_email: External email (requires confirmation unless explicit "send it right now")
- send_telegram_voice: Generate speech (Edge TTS) and send as Telegram voice message
- send_telegram_call_link: Send a Telegram VoIP call link (tap to start live call)
- send_telegram_message: Send a plain text message to your Telegram chat
- save_project_memory: Persist decisions, bugs, architecture notes, updates
- recall_project_memory: Semantic search of past memories (USE PROACTIVELY)
- set_reminder: Schedule a future Telegram notification

MEMORY GUIDELINES:
- Save: Architectural choices, bug root causes, decisions, project milestones, meeting outcomes
- Recall: Before answering questions about "what did we decide", "how does X work", "what was that bug", etc.

COMMUNICATION STYLE:
- Concise, professional, action-oriented
- Confirm before high-impact actions
- Report tool results clearly
- Ask clarifying questions when ambiguous

Current date/time: {current_time}"""


class KrytusAgent:
    def __init__(self):
        self.conversation_history: list[dict[str, Any]] = []
        self.max_history = 20
        self._provider: LLMProvider | None = None

    def _get_provider(self) -> LLMProvider:
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    def _build_system_prompt(self) -> str:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        return SYSTEM_PROMPT.format(current_time=current_time)

    def _format_tool_result(self, function_name: str, result: dict[str, Any]) -> str:
        if not result.get("success"):
            return f"❌ {function_name} failed: {result.get('error', 'Unknown error')}"
        
        if function_name == "send_email":
            return f"✅ Email sent to {result.get('message', 'recipient')}"
        elif function_name == "send_telegram_voice":
            return "🔊 Voice message sent to Telegram"
        elif function_name == "send_telegram_call_link":
            return "📞 Telegram call link sent (tap to start live VoIP call)"
        elif function_name == "send_telegram_message":
            return "💬 Telegram message sent"
        elif function_name == "save_project_memory":
            return f"✅ Memory saved: {result.get('message', 'done')}"
        elif function_name == "recall_project_memory":
            memories = result.get("memories", [])
            if not memories:
                return "🔍 No relevant memories found."
            formatted = "🔍 Recalled memories:\n"
            for m in memories:
                formatted += f"  • [{m['topic']}] {m['content'][:150]}...\n"
            return formatted
        elif function_name == "set_reminder":
            return f"⏰ Reminder set for {result.get('due_at', 'unknown')}: {result.get('message', 'done')}"
        return f"✅ {function_name} completed"

    def _convert_to_provider_format(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert internal message format to provider format."""
        return messages

    def _convert_from_provider_response(self, response: ChatCompletion) -> dict[str, Any]:
        """Convert provider response to internal format."""
        msg = response.message
        result = {
            "role": "assistant",
            "content": msg.content,
        }
        if msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                }
                for tc in msg.tool_calls
            ]
        return result

    async def process_message(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})

        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ] + self.conversation_history

        provider = self._get_provider()

        while True:
            response = await provider.chat_completion(
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
            )

            message = response.message

            if message.tool_calls:
                # Convert to internal format for history
                internal_msg = self._convert_from_provider_response(response)
                messages.append(internal_msg)

                for tool_call in message.tool_calls:
                    function_name = tool_call.name
                    function_args = tool_call.arguments

                    _log_info("tool_executing", function=function_name, args=function_args)

                    if function_name in TOOL_FUNCTIONS:
                        try:
                            result = await TOOL_FUNCTIONS[function_name](**function_args)
                        except Exception as e:
                            _log_error("tool_exception", function=function_name, error=str(e))
                            result = {"success": False, "error": str(e)}
                    else:
                        result = {"success": False, "error": f"Unknown tool: {function_name}"}

                    formatted_result = self._format_tool_result(function_name, result)
                    _log_info("tool_result", function=function_name, result=result)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": formatted_result
                    })
            else:
                final_response = message.content or ""
                self.conversation_history.append({"role": "assistant", "content": final_response})
                return final_response


agent = KrytusAgent()
import sys
import asyncio
import httpx

import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    logger_factory=structlog.PrintLoggerFactory(sys.stdout),
    cache_logger_on_first_use=True,
)

BOT_TOKEN = "8678028258:AAHuDstYZ0qIr7osPuDEHYiujwzrrR7ckKs"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def send_message(chat_id: int, text: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

async def get_updates(offset: int = 0):
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{API_URL}/getUpdates", params={"offset": offset, "timeout": 30})
        return r.json()

async def main():
    print("Starting Krytus (minimal polling)...")
    
    # Test connection
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/getMe")
        print("Bot info:", r.json()["result"]["username"])
    
    offset = 0
    while True:
        try:
            result = await get_updates(offset)
            if result.get("ok") and result.get("result"):
                for update in result["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "")
                        
                        if chat_id == 6928539857:  # Only respond to authorized user
                            if text == "/start":
                                await send_message(chat_id, "🤖 Krytus Online!\n\nCommands:\n• /call - Get a call link\n• /voice <text> - Send voice message\n• /email <to> <subject> <body> - Send email\n• /remind <minutes> <msg> - Set reminder")
                            elif text == "/call":
                                await send_message(chat_id, "📞 [Tap for live call](tg://call?request_join=true)")
                            elif text.startswith("/voice "):
                                await send_message(chat_id, f"🔊 Voice: {text[7:]}")
                            elif text.startswith("/email "):
                                await send_message(chat_id, "📧 Email feature coming soon")
                            elif text.startswith("/remind "):
                                await send_message(chat_id, "⏰ Reminder feature coming soon")
                            else:
                                await send_message(chat_id, f"Echo: {text}")
                        else:
                            await send_message(chat_id, "❌ Unauthorized")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
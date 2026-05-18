import httpx
from app.core.config import settings

async def send_telegram_message(chat_id: str, text: str) -> None:
    if not settings.telegram_bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})

from fastapi import APIRouter, Request
from app.adapters.discord import handle_discord_event
router = APIRouter(prefix="/webhooks/discord", tags=["discord"])

@router.post("")
async def discord_webhook(request: Request):
    payload = await request.json()
    return await handle_discord_event(payload)

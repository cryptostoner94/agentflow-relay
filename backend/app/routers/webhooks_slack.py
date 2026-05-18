from fastapi import APIRouter, Request
from app.adapters.slack import handle_slack_event
router = APIRouter(prefix="/webhooks/slack", tags=["slack"])

@router.post("")
async def slack_webhook(request: Request):
    payload = await request.json()
    return await handle_slack_event(payload)

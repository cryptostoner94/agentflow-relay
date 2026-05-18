from fastapi import APIRouter, Request, Query, Response
from app.core.config import settings
from app.models.task import AgentTask
from app.services.orchestrator import route_task
from app.adapters.whatsapp import send_whatsapp_message

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])

@router.get("")
async def verify(mode: str = Query(None, alias="hub.mode"), token: str = Query(None, alias="hub.verify_token"), challenge: str = Query(None, alias="hub.challenge")):
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return Response(content=challenge or "", media_type="text/plain")
    return Response(status_code=403)

@router.post("")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        message = value.get("messages", [{}])[0]
        sender = message.get("from", "")
        text = message.get("text", {}).get("body", "")
    except Exception:
        return {"ok": True, "ignored": True}
    task = AgentTask(source_platform="whatsapp", user_ref=sender, text=text, metadata=payload)
    result = await route_task(task)
    await send_whatsapp_message(sender, result.output)
    return {"ok": True, "task_id": task.id, "status": result.status}

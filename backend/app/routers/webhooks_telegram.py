from fastapi import APIRouter, Request
from app.models.task import AgentTask
from app.services.orchestrator import route_task
from app.adapters.telegram import send_telegram_message

router = APIRouter(prefix="/webhooks/telegram", tags=["telegram"])

@router.post("")
async def telegram_webhook(request: Request):
    update = await request.json()
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat", {})
    text = msg.get("text", "")
    chat_id = str(chat.get("id", ""))
    task = AgentTask(source_platform="telegram", user_ref=chat_id, text=text, metadata=update)
    result = await route_task(task)
    await send_telegram_message(chat_id, result.output)
    return {"ok": True, "task_id": task.id, "status": result.status}

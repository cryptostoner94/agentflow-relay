from app.models.task import AgentTask, AgentResult, TaskStatus
from app.services.audit_log import log_event
from app.services.permission_engine import requires_approval
from app.core.config import settings
from app.adapters.webhook_agent import call_webhook_agent
from app.adapters.ollama_agent import call_ollama

async def route_task(task: AgentTask) -> AgentResult:
    log_event("task_received", task.model_dump(mode="json"))
    if requires_approval(task.text):
        log_event("approval_required", {"task_id": task.id, "text": task.text})
        return AgentResult(task_id=task.id, status=TaskStatus.needs_approval, output="Approval required before execution.")
    try:
        if settings.default_agent_webhook_url:
            result = await call_webhook_agent(settings.default_agent_webhook_url, task)
        else:
            result = await call_ollama(task)
        log_event("task_completed", result.model_dump(mode="json"))
        return result
    except Exception as exc:
        log_event("task_failed", {"task_id": task.id, "error": str(exc)})
        return AgentResult(task_id=task.id, status=TaskStatus.failed, output=f"Task failed: {exc}")

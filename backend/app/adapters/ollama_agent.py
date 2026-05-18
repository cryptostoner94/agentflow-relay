import httpx
from app.core.config import settings
from app.models.task import AgentTask, AgentResult, TaskStatus

async def call_ollama(task: AgentTask, model: str = "qwen2.5-coder:7b") -> AgentResult:
    payload = {"model": model, "prompt": task.text, "stream": False}
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{settings.ollama_base_url}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
    return AgentResult(task_id=task.id, status=TaskStatus.completed, output=data.get("response", ""), metadata={"model": model})

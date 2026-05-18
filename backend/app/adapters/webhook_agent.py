import httpx
from app.models.task import AgentTask, AgentResult, TaskStatus

async def call_webhook_agent(url: str, task: AgentTask) -> AgentResult:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=task.model_dump(mode="json"))
        r.raise_for_status()
        data = r.json()
    return AgentResult(task_id=task.id, status=TaskStatus.completed, output=data.get("output", str(data)), metadata=data)

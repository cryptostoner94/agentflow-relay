from fastapi import APIRouter
from app.models.task import AgentTask
from app.services.orchestrator import route_task

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("")
async def create_task(task: AgentTask):
    return await route_task(task)

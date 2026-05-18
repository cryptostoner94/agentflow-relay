from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.tasks import router as tasks_router
from app.routers.agents import router as agents_router
from app.routers.logs import router as logs_router
from app.routers.operator import router as operator_router

app = FastAPI(
    title="AgentFlow Relay",
    version="1.0.0",
    description="AI workforce infrastructure: agent relay, BYOA onboarding, SDK monetization, workflow templates, and enterprise orchestration."
)

app.include_router(operator_router)
app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(agents_router)
app.include_router(logs_router)

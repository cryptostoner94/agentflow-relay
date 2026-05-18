from fastapi import FastAPI
from app.routers.platform import router as platform_router

app = FastAPI(
    title="AgentFlow Relay Production Platform",
    version="3.0.0",
    description="AI workforce SaaS foundation with users, API keys, workflows, agents, revenue paths, SDK, audit logs, and execution ledger."
)

app.include_router(platform_router)

@app.get("/health")
def health():
    return {"ok": True, "service": "agentflow-relay", "version": "3.0.0"}

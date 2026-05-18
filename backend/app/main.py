from fastapi import FastAPI
from app.routers.platform import router as platform_router

app=FastAPI(title="AgentFlow Relay Complete Platform",version="5.0.0")
app.include_router(platform_router)

@app.get("/health")
def health():
    return {"ok":True,"service":"agentflow-relay","version":"5.0.0"}

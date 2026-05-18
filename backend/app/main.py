from fastapi import FastAPI
from app.routers.operator import router as operator_router

app = FastAPI(
    title="AgentFlow Enterprise",
    version="2.0"
)

app.include_router(operator_router)

@app.get("/health")
async def health():
    return {"ok": True}

from fastapi import FastAPI
from app.routers.ui import router as ui_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.health import router as health_router
from app.routers.tasks import router as tasks_router
from app.routers.agents import router as agents_router
from app.routers.logs import router as logs_router
from app.routers.webhooks_telegram import router as telegram_router
from app.routers.webhooks_whatsapp import router as whatsapp_router
from app.routers.webhooks_discord import router as discord_router
from app.routers.webhooks_slack import router as slack_router

app = FastAPI(title="AgentFlow Relay", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(agents_router)
app.include_router(logs_router)
app.include_router(telegram_router)
app.include_router(whatsapp_router)
app.include_router(discord_router)
app.include_router(slack_router)

app.include_router(ui_router)

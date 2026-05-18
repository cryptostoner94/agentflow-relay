from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/agentflowrelay"
    redis_url: str = "redis://redis:6379/0"
    public_base_url: str = "http://localhost:8000"
    telegram_bot_token: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_verify_token: str = "agentflow_verify_token"
    discord_bot_token: str | None = None
    discord_public_key: str | None = None
    slack_bot_token: str | None = None
    slack_signing_secret: str | None = None
    default_agent_webhook_url: str | None = None
    ollama_base_url: str = "http://host.docker.internal:11434"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

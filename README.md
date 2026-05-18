# AgentFlow Relay

Universal agent relay and orchestration infrastructure.

## Included

- FastAPI backend
- Next.js dashboard
- PostgreSQL
- Redis
- Docker Compose
- Telegram webhook adapter
- WhatsApp Cloud API adapter
- Discord webhook adapter
- Slack webhook adapter
- BYOA agent registration
- Capability discovery
- Permission/approval gates
- Execution audit logs
- Python SDK stub

## Run

```bash
cp .env.example .env
docker compose up -d --build
```

Backend: http://localhost:8000/docs  
Frontend: http://localhost:3000  
Health: http://localhost:8000/health

## Official API rule

All messaging integrations are adapters for official APIs only. No unofficial WhatsApp automation, scraping, telecom, satellite, blockchain, or hardware functions are included.

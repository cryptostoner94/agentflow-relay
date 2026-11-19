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

## Operator access

Every `/platform` route can rewrite the credential vault and spend the
operator's provider keys, so it requires the operator credential.

- `render.yaml` generates `AGENTFLOW_OPERATOR_TOKEN`; copy its value from the
  Render dashboard. Without it the admin routes answer 503 and stay closed.
- Send that value in the `X-Operator-Token` header, or as an
  `Authorization: Bearer <token>` header. The bundled dashboard asks for it
  once and keeps it in `localStorage`.
- `render.yaml` generates `AGENTFLOW_MASTER_SECRET` too. It must hold at least
  16 characters; the vault encrypts stored keys with it and refuses to store
  anything when it is absent.
- Telegram calls `/platform/telegram/update` with the secret that
  `POST /platform/telegram/webhook` registers through `secret_token`; the
  route accepts nothing else.

`/`, `/ui`, `/health` and `/demo/enterprise` stay public and hold no operator
data.

## Official API rule

All messaging integrations are adapters for official APIs only. No unofficial WhatsApp automation, scraping, telecom, satellite, blockchain, or hardware functions are included.

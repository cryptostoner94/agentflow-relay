# Deployment

1. Create `.env` from `.env.example`.
2. Add official platform credentials.
3. Run `docker compose up -d --build`.
4. Configure public HTTPS URL through a tunnel/reverse proxy.
5. Set platform webhooks:
   - Telegram: `/webhooks/telegram`
   - WhatsApp: `/webhooks/whatsapp`
   - Slack: `/webhooks/slack`
   - Discord: `/webhooks/discord`

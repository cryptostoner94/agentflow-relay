#!/bin/bash
cd ~/agentflow-relay-project
source .venv/bin/activate

pkill -f uvicorn || true
pkill -f cloudflared || true

PYTHONPATH=backend python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 5

echo "Local Product UI:"
echo "http://localhost:8000/ui"
echo ""
echo "API Docs:"
echo "http://localhost:8000/docs"
echo ""
echo "Starting Cloudflare tunnel..."
cloudflared tunnel --url http://localhost:8000

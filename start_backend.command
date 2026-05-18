#!/bin/bash
cd /Users/hsk/agentflow-relay-project
source /Users/hsk/agentflow-relay-project/.venv/bin/activate
export PYTHONPATH=/Users/hsk/agentflow-relay-project/backend
exec /Users/hsk/agentflow-relay-project/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

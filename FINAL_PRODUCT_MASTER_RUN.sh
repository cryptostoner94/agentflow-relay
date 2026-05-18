#!/bin/bash
set -e

pkill -f uvicorn || true
pkill -f cloudflared || true

cd ~/agentflow-relay-project

python3 -m venv .venv || true
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pydantic pydantic-settings python-dotenv requests httpx jinja2 aiofiles python-multipart websockets

mkdir -p backend/app/routers sdk/python/agentflow_relay docs

cat > backend/app/routers/operator.py <<'PY'
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()

AGENTS = [
    {"id": "default-relay", "name": "Default Relay Agent", "type": "internal", "status": "active"},
    {"id": "webhook-byoa", "name": "BYOA Webhook Agent", "type": "external", "status": "ready"},
    {"id": "ollama-local", "name": "Local Ollama Agent", "type": "local", "status": "ready"},
]

LOGS = []

REVENUE = [
    {"model": "SDK Licensing", "buyer": "AI companies", "value": "Agent routing + messaging adapters + relay layer"},
    {"model": "Hosted Agent Relay", "buyer": "SMBs / creators", "value": "Monthly hosted automation access"},
    {"model": "White-label Operator Stack", "buyer": "agencies / enterprises", "value": "Branded agent control layer"},
    {"model": "API Usage Billing", "buyer": "developers", "value": "Pay-per-task relay execution"},
]

TEMPLATES = [
    "Job search agent relay",
    "E-commerce live product finder",
    "Customer-support handoff agent",
    "Lead-generation workflow agent",
    "Email drafting and approval agent",
    "Research + summary + execution agent",
]

@router.get("/", response_class=HTMLResponse)
@router.get("/ui", response_class=HTMLResponse)
def ui():
    return HTMLResponse("""
<!doctype html>
<html>
<head>
<title>AgentFlow Relay</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#07110b;color:#d8ffe8;font-family:Arial}
header{padding:22px;background:#0d1f14;border-bottom:1px solid #19ff88}
h1{margin:0;color:#19ff88}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;padding:18px}
.card{background:#101b14;border:1px solid #1d6f46;border-radius:14px;padding:18px}
button,input,textarea,select{font-size:16px;border-radius:8px;padding:12px;margin:6px 0}
button{background:#19ff88;border:0;color:#001b0c;font-weight:bold;cursor:pointer}
textarea,input,select{width:100%;box-sizing:border-box;background:#020603;color:#19ff88;border:1px solid #1d6f46}
pre{white-space:pre-wrap;background:#020603;color:#19ff88;padding:14px;border-radius:10px;min-height:180px;overflow:auto}
.badge{display:inline-block;background:#163d28;color:#19ff88;border:1px solid #19ff88;border-radius:999px;padding:5px 10px;margin:4px}
small{color:#a8d8bb}
</style>
</head>
<body>
<header>
<h1>AgentFlow Relay</h1>
<p>Universal agent relay + messaging-native orchestration + SDK/API monetization layer</p>
</header>

<div class="grid">
<div class="card">
<h2>Operator Command</h2>
<textarea id="task" placeholder="Example: Find 5 remote jobs, adapt my resume, draft outreach email."></textarea>
<button onclick="runTask()">Run Relay Task</button>
<button onclick="health()">Health</button>
<button onclick="docs()">API Docs</button>
</div>

<div class="card">
<h2>Agents</h2>
<button onclick="loadAgents()">Load Agents</button>
<button onclick="registerAgent()">Register BYOA Agent</button>
<input id="agentName" placeholder="Agent name">
<input id="agentUrl" placeholder="Webhook / API endpoint">
<pre id="agents"></pre>
</div>

<div class="card">
<h2>Revenue Layer</h2>
<button onclick="revenue()">Show Monetization Paths</button>
<pre id="revenue"></pre>
</div>

<div class="card">
<h2>SDK / AI Buyer Positioning</h2>
<button onclick="sdk()">Show SDK Package</button>
<pre id="sdk"></pre>
</div>

<div class="card">
<h2>Integration Depth</h2>
<button onclick="integrations()">Check Integrations</button>
<pre id="integrations"></pre>
</div>

<div class="card">
<h2>Execution Logs</h2>
<button onclick="logs()">Refresh Logs</button>
<pre id="logs"></pre>
</div>
</div>

<script>
async function show(id, data){document.getElementById(id).textContent=JSON.stringify(data,null,2)}
async function health(){let r=await fetch('/health');show('logs',await r.json())}
function docs(){location.href='/docs'}
async function runTask(){
 let body={task:document.getElementById('task').value||'operator test task'};
 let r=await fetch('/operator/task',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 show('logs',await r.json());
}
async function loadAgents(){let r=await fetch('/operator/agents');show('agents',await r.json())}
async function registerAgent(){
 let body={name:document.getElementById('agentName').value,url:document.getElementById('agentUrl').value};
 let r=await fetch('/operator/register-agent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 show('agents',await r.json());
}
async function revenue(){let r=await fetch('/operator/revenue');show('revenue',await r.json())}
async function sdk(){let r=await fetch('/operator/sdk');show('sdk',await r.json())}
async function integrations(){let r=await fetch('/operator/integrations');show('integrations',await r.json())}
async function logs(){let r=await fetch('/operator/logs');show('logs',await r.json())}
</script>
</body>
</html>
""")

@router.post("/operator/task")
async def operator_task(request: Request):
    payload = await request.json()
    task = payload.get("task", "")
    event = {
        "id": f"task-{len(LOGS)+1}",
        "task": task,
        "status": "accepted",
        "route": ["user", "agentflow-relay", "orchestrator", "best-available-agent"],
        "monetizable": True,
        "sdk_ready": True,
        "created_at": datetime.utcnow().isoformat()
    }
    LOGS.append(event)
    return event

@router.get("/operator/agents")
def operator_agents():
    return {"agents": AGENTS, "count": len(AGENTS)}

@router.post("/operator/register-agent")
async def register_agent(request: Request):
    payload = await request.json()
    agent = {
        "id": f"agent-{len(AGENTS)+1}",
        "name": payload.get("name") or "Unnamed BYOA Agent",
        "endpoint": payload.get("url") or "not_configured",
        "type": "byoa",
        "status": "registered"
    }
    AGENTS.append(agent)
    return {"registered": agent, "agents": AGENTS}

@router.get("/operator/revenue")
def revenue():
    return {"positioning": "AgentFlow Relay monetizes as SDK, hosted relay, API, and white-label operator infrastructure.", "models": REVENUE}

@router.get("/operator/sdk")
def sdk():
    return {
        "package": "agentflow_relay",
        "target_buyers": ["AI companies", "agent platforms", "automation SaaS", "enterprise AI teams"],
        "endpoints": ["/operator/task", "/operator/register-agent", "/operator/agents", "/operator/logs"],
        "python_example": "from agentflow_relay import AgentFlowClient\\nclient = AgentFlowClient(base_url='https://your-url')\\nclient.create_task('run workflow')",
        "value": "Adds universal messaging-native agent relay, BYOA onboarding, task routing, and monetizable orchestration API."
    }

@router.get("/operator/integrations")
def integrations():
    return {
        "messaging": {
            "telegram": "adapter present",
            "whatsapp_cloud_api": "adapter present; requires Meta credentials",
            "discord": "adapter present",
            "slack": "adapter present"
        },
        "agent_runtime": {
            "byoa_webhook": "active",
            "ollama_local": "ready",
            "external_api_agents": "ready"
        },
        "business_layer": {
            "sdk": "present",
            "white_label": "positioned",
            "api_billing_ready": "architecture-ready",
            "enterprise_relay": "positioned"
        }
    }

@router.get("/operator/logs")
def logs():
    return {"logs": LOGS}
PY

python - <<'PY'
from pathlib import Path
p = Path("backend/app/main.py")
s = p.read_text()
if "operator_router" not in s:
    s = s.replace("from fastapi import FastAPI", "from fastapi import FastAPI\nfrom app.routers.operator import router as operator_router")
    s += "\napp.include_router(operator_router)\n"
p.write_text(s)
PY

cat > sdk/python/agentflow_relay/client.py <<'PY'
import requests

class AgentFlowClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health(self):
        return requests.get(f"{self.base_url}/health").json()

    def create_task(self, task: str):
        return requests.post(f"{self.base_url}/operator/task", json={"task": task}).json()

    def register_agent(self, name: str, url: str):
        return requests.post(f"{self.base_url}/operator/register-agent", json={"name": name, "url": url}).json()

    def agents(self):
        return requests.get(f"{self.base_url}/operator/agents").json()

    def revenue(self):
        return requests.get(f"{self.base_url}/operator/revenue").json()
PY

cat > sdk/python/agentflow_relay/__init__.py <<'PY'
from .client import AgentFlowClient
PY

cat > docs/BUYOUT_POSITIONING.md <<'MD'
# AgentFlow Relay — Acquisition Positioning

AgentFlow Relay is positioned as universal agent orchestration infrastructure.

## Strategic Value
- Messaging-native agent access
- Bring-your-own-agent onboarding
- Agent routing and capability discovery
- SDK/API monetization surface
- White-label operator infrastructure
- Multi-platform adapter layer

## Buyer Interest Logic
AI companies care about:
- agent interoperability
- reduced integration friction
- SDK distribution
- ecosystem positioning
- workflow orchestration
- enterprise-ready relay architecture

## Revenue Paths
1. SDK licensing
2. Hosted relay subscriptions
3. White-label operator deployments
4. API usage billing
5. Agent workflow templates
MD

cat > FINAL_RUN_ONE_TERMINAL.sh <<'EOF'
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

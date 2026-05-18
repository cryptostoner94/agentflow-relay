#!/bin/bash
set -e

cd ~/agentflow-relay-project

mkdir -p backend/app/routers sdk/python/agentflow_relay docs

cat > backend/app/routers/operator.py <<'PY'
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

LOGS = []
AGENTS = [
    {"id": "relay-core", "name": "AgentFlow Relay Core", "type": "orchestrator", "status": "active"},
    {"id": "byoa-webhook", "name": "Bring Your Own Agent", "type": "webhook", "status": "ready"},
    {"id": "messaging-hub", "name": "Messaging Agent Hub", "type": "telegram/slack/discord/whatsapp", "status": "ready"},
    {"id": "sdk-layer", "name": "Revenue SDK Layer", "type": "developer-platform", "status": "ready"}
]

@router.get("/", response_class=HTMLResponse)
@router.get("/ui", response_class=HTMLResponse)
def ui():
    return """
<!doctype html>
<html>
<head>
<title>AgentFlow Relay</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#173b28,#050705 60%);color:#fff;font-family:Inter,Arial,sans-serif}
header{padding:48px 28px;border-bottom:1px solid rgba(0,255,140,.25)}
h1{font-size:52px;margin:0;color:#32ff9a}h2{color:#32ff9a}p{color:#c6d6cc}
.container{max-width:1200px;margin:auto}.hero{display:grid;grid-template-columns:1.2fr .8fr;gap:24px}
.badge{display:inline-block;border:1px solid #32ff9a;color:#32ff9a;border-radius:999px;padding:8px 14px;margin:6px 6px 6px 0}
.card{background:rgba(5,15,10,.82);border:1px solid rgba(50,255,154,.25);border-radius:22px;padding:24px;box-shadow:0 0 40px rgba(0,255,140,.08)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;padding:24px}
button{background:#32ff9a;color:#00190b;border:0;border-radius:12px;padding:14px 18px;font-weight:800;margin:6px;cursor:pointer}
button.secondary{background:#111;color:#32ff9a;border:1px solid #32ff9a}
textarea,input{width:100%;background:#020503;color:#32ff9a;border:1px solid rgba(50,255,154,.45);border-radius:14px;padding:14px;font-size:15px}
pre{background:#020503;color:#32ff9a;border:1px solid rgba(50,255,154,.35);border-radius:16px;padding:16px;min-height:260px;overflow:auto}
.kpi{font-size:34px;color:#32ff9a;font-weight:900}.small{font-size:13px;color:#9fb5a8}
footer{padding:30px;text-align:center;color:#8ea999}
@media(max-width:800px){.hero{grid-template-columns:1fr}h1{font-size:38px}}
</style>
</head>
<body>
<header>
<div class="container hero">
<div>
<div class="badge">LIVE CLOUD DEPLOYED</div><div class="badge">SDK/API READY</div><div class="badge">AI BUYOUT POSITIONING</div>
<h1>AgentFlow Relay</h1>
<p>Universal agent relay infrastructure for messaging-native AI operators, BYOA onboarding, SDK monetization, workflow templates, and enterprise orchestration.</p>
<button onclick="runTask()">Run Demo Task</button>
<button class="secondary" onclick="location.href='/docs'">Open API Docs</button>
</div>
<div class="card">
<h2>Acquisition Thesis</h2>
<p>AI companies need interoperability, orchestration, workflow routing, and messaging-native access. AgentFlow Relay packages that as infrastructure.</p>
<div class="kpi">4</div><div class="small">Revenue surfaces: SDK, API, hosted agents, white-label</div>
</div>
</div>
</header>

<div class="grid">
<div class="card"><h2>Operator Command</h2><textarea id="task" rows="6">Find 5 remote jobs, select best match, rewrite resume angle, draft outreach email.</textarea><button onclick="runTask()">Execute Relay</button><pre id="out"></pre></div>
<div class="card"><h2>Agents</h2><button onclick="agents()">Load Agents</button><button onclick="registerAgent()">Register BYOA</button><input id="agentName" placeholder="Agent name"><input id="agentUrl" placeholder="Webhook/API URL"><pre id="agents"></pre></div>
<div class="card"><h2>Revenue Engine</h2><button onclick="revenue()">Show Revenue Paths</button><pre id="revenue"></pre></div>
<div class="card"><h2>SDK / Corporate Buyer Layer</h2><button onclick="sdk()">Show SDK</button><pre id="sdk"></pre></div>
<div class="card"><h2>Workflow Marketplace</h2><button onclick="templates()">Show Templates</button><pre id="templates"></pre></div>
<div class="card"><h2>Platform Status</h2><button onclick="health()">Health</button><button onclick="logs()">Logs</button><pre id="status"></pre></div>
</div>

<footer>AgentFlow Relay — AI workforce infrastructure, not a chatbot.</footer>

<script>
async function j(path, opts={}){let r=await fetch(path,opts);return await r.json()}
function show(id,data){document.getElementById(id).textContent=JSON.stringify(data,null,2)}
async function health(){show('status',await j('/health'))}
async function logs(){show('status',await j('/operator/logs'))}
async function agents(){show('agents',await j('/operator/agents'))}
async function revenue(){show('revenue',await j('/operator/revenue'))}
async function sdk(){show('sdk',await j('/operator/sdk'))}
async function templates(){show('templates',await j('/operator/templates'))}
async function runTask(){show('out',await j('/operator/task',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:document.getElementById('task').value})}))}
async function registerAgent(){show('agents',await j('/operator/register-agent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('agentName').value,url:document.getElementById('agentUrl').value})}))}
</script>
</body>
</html>
"""

@router.post("/operator/task")
async def task(request: Request):
    body = await request.json()
    item = {
        "id": f"task-{len(LOGS)+1}",
        "task": body.get("task",""),
        "status": "accepted",
        "route": ["user", "agentflow-relay", "capability-discovery", "best-agent", "approval-gate", "execution-log"],
        "business_value": "Demonstrates monetizable AI task relay infrastructure.",
        "created_at": datetime.utcnow().isoformat()
    }
    LOGS.append(item)
    return item

@router.get("/operator/agents")
def agents():
    return {"agents": AGENTS}

@router.post("/operator/register-agent")
async def register_agent(request: Request):
    body = await request.json()
    agent = {"id": f"agent-{len(AGENTS)+1}", "name": body.get("name") or "BYOA Agent", "endpoint": body.get("url") or "not_configured", "status": "registered"}
    AGENTS.append(agent)
    return {"registered": agent, "agents": AGENTS}

@router.get("/operator/revenue")
def revenue():
    return {
        "models": [
            {"name": "SDK Licensing", "buyer": "AI companies", "why": "Embed agent relay into existing AI products."},
            {"name": "Hosted Agent Relay", "buyer": "SMBs / creators", "why": "Monthly subscription for AI workflows."},
            {"name": "API Usage Billing", "buyer": "developers", "why": "Pay-per-task orchestration endpoint."},
            {"name": "White-label Operator Stack", "buyer": "agencies / enterprise", "why": "Deploy branded AI workforce portals."}
        ]
    }

@router.get("/operator/sdk")
def sdk():
    return {
        "package": "agentflow_relay",
        "python_example": "from agentflow_relay import AgentFlowClient\\nclient=AgentFlowClient('https://agentflow-relay.onrender.com')\\nclient.create_task('run workflow')",
        "endpoints": ["/operator/task", "/operator/agents", "/operator/register-agent", "/operator/revenue", "/operator/templates"],
        "buyer_interest": ["interoperability", "messaging-native access", "agent routing", "BYOA onboarding", "workflow monetization"]
    }

@router.get("/operator/templates")
def templates():
    return {
        "templates": [
            "Job Search + Resume + Outreach Agent",
            "E-commerce Product Finder Agent",
            "Customer Support Escalation Agent",
            "Lead Generation Agent",
            "Research + Report Agent",
            "Email Draft + Approval Agent",
            "Business Ops Workflow Agent"
        ]
    }

@router.get("/operator/logs")
def logs():
    return {"logs": LOGS}
PY

python - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
if "operator_router" not in s:
    s=s.replace("from fastapi import FastAPI","from fastapi import FastAPI\nfrom app.routers.operator import router as operator_router")
    s += "\napp.include_router(operator_router)\n"
p.write_text(s)
PY

cat > sdk/python/agentflow_relay/client.py <<'PY'
import requests
class AgentFlowClient:
    def __init__(self, base_url): self.base_url=base_url.rstrip("/")
    def health(self): return requests.get(self.base_url+"/health").json()
    def create_task(self, task): return requests.post(self.base_url+"/operator/task", json={"task":task}).json()
    def agents(self): return requests.get(self.base_url+"/operator/agents").json()
    def revenue(self): return requests.get(self.base_url+"/operator/revenue").json()
PY

cat > sdk/python/agentflow_relay/__init__.py <<'PY'
from .client import AgentFlowClient
PY

cat > docs/BUYOUT_AND_REVENUE_POSITIONING.md <<'MD'
# AgentFlow Relay — Revenue and Buyout Positioning

AgentFlow Relay is positioned as AI workforce infrastructure.

## What it sells
- SDK licensing
- Hosted agent relay subscriptions
- White-label AI operator portals
- API usage billing
- Workflow template marketplace

## Why AI companies may care
- Agent interoperability
- Messaging-native access
- BYOA onboarding
- Capability discovery
- Task routing
- Workflow monetization
- Enterprise operator layer

## Product wedge
Start with high-value workflows:
1. Job search + resume + outreach
2. Lead generation
3. E-commerce intelligence
4. Support escalation
5. Research automation
MD

git add .
git commit -m "Final premium product operator revenue SDK upgrade" || true
git push origin main

render services deploy srv-d8511brbc2fs73etqt8g --confirm || true

echo ""
echo "FINAL URLS:"
echo "https://agentflow-relay.onrender.com/ui"
echo "https://agentflow-relay.onrender.com/docs"
echo "https://agentflow-relay.onrender.com/operator/revenue"
echo "https://agentflow-relay.onrender.com/operator/sdk"
echo "https://agentflow-relay.onrender.com/operator/templates"

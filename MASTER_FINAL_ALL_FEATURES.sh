#!/bin/bash
set -e

SERVICE_ID="srv-d8511brbc2fs73etqt8g"
APP_URL="https://agentflow-relay.onrender.com"

cd ~/agentflow-relay-project

mkdir -p backend/app/{core,routers,services}
mkdir -p sdk/python/agentflow_relay
mkdir -p docs

cat > backend/requirements.txt <<'REQ'
fastapi
uvicorn
pydantic
pydantic-settings
python-dotenv
requests
httpx
jinja2
aiofiles
python-multipart
websockets
REQ

cat > backend/app/services/store.py <<'PY'
from datetime import datetime
import uuid

USERS = {}
API_KEYS = {}
WORKFLOWS = {}
TASKS = {}
AGENTS = {}
BILLING_PLANS = {
    "free": {"price": 0, "tasks": 25, "api_calls": 100},
    "starter": {"price": 29, "tasks": 250, "api_calls": 2500},
    "pro": {"price": 99, "tasks": 1500, "api_calls": 15000},
    "enterprise": {"price": "custom", "tasks": "custom", "api_calls": "custom"},
}
USAGE = {"tasks": 0, "api_calls": 0, "users": 0, "agents": 0, "revenue_ready": True}
AUDIT = []

def now():
    return datetime.utcnow().isoformat()

def log(event, data=None):
    item = {"id": str(uuid.uuid4()), "event": event, "data": data or {}, "created_at": now()}
    AUDIT.append(item)
    return item

def create_key(label="default"):
    key = "afr_" + uuid.uuid4().hex
    API_KEYS[key] = {"label": label, "created_at": now(), "active": True}
    log("api_key_created", {"label": label})
    return key
PY

cat > backend/app/routers/platform.py <<'PY'
from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from app.services.store import USERS, API_KEYS, WORKFLOWS, TASKS, AGENTS, BILLING_PLANS, USAGE, AUDIT, log, create_key

router = APIRouter()

class UserIn(BaseModel):
    email: str
    name: str = "User"

class AgentIn(BaseModel):
    name: str
    endpoint: str = ""
    platform: str = "webhook"
    capabilities: list[str] = []

class WorkflowIn(BaseModel):
    name: str
    description: str = ""
    price: float = 0
    steps: list[str] = []

class TaskIn(BaseModel):
    workflow_id: str | None = None
    prompt: str
    mode: str = "simulate-safe"

def check_key(x_api_key: str | None):
    if not x_api_key:
        return False
    return x_api_key in API_KEYS and API_KEYS[x_api_key]["active"]

@router.get("/", response_class=HTMLResponse)
@router.get("/ui", response_class=HTMLResponse)
def ui():
    return """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>AgentFlow Relay</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#030712;color:white;font-family:Inter,Arial,sans-serif}
.hero{padding:42px;background:radial-gradient(circle at top left,#10b981,#020617 45%);border-bottom:1px solid #134e4a}
h1{font-size:48px;margin:0;color:#d1fae5}.sub{font-size:18px;color:#ccfbf1;margin-top:12px;max-width:900px}
.wrap{max-width:1220px;margin:auto;padding:22px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}
.card{background:rgba(15,23,42,.9);border:1px solid #1f766e;border-radius:20px;padding:20px;box-shadow:0 0 30px rgba(16,185,129,.12)}
.card h2{color:#5eead4;margin-top:0}.metric{font-size:32px;font-weight:900;color:#a7f3d0}
button{background:#34d399;color:#022c22;border:0;border-radius:12px;padding:12px 16px;font-weight:800;margin:6px 6px 6px 0;cursor:pointer}
button.alt{background:#0f172a;color:#5eead4;border:1px solid #2dd4bf}
input,textarea,select{width:100%;background:#020617;color:#d1fae5;border:1px solid #155e75;border-radius:12px;padding:12px;margin:6px 0}
pre{white-space:pre-wrap;background:#020617;color:#86efac;border:1px solid #164e63;border-radius:14px;padding:14px;min-height:220px;overflow:auto}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0}.pill{padding:8px 12px;border:1px solid #2dd4bf;border-radius:999px;color:#5eead4}
.footer{color:#94a3b8;text-align:center;padding:28px}
</style>
</head>
<body>
<section class="hero"><div class="wrap">
<h1>AgentFlow Relay</h1>
<div class="sub">Production-style AI workforce infrastructure: users, API keys, agents, workflow marketplace, task execution ledger, usage metering, monetization plans, SDK endpoints, onboarding, and enterprise positioning.</div>
<div class="tabs"><span class="pill">Cloud Hosted</span><span class="pill">SDK Ready</span><span class="pill">Workflow Marketplace</span><span class="pill">Usage Metering</span><span class="pill">Revenue System</span></div>
<button onclick="boot()">Run System Check</button><button class="alt" onclick="location.href='/docs'">API Docs</button>
</div></section>

<div class="wrap">
<div class="grid">
<div class="card"><h2>Live Metrics</h2><div id="metrics">Loading...</div><button onclick="metrics()">Refresh</button></div>
<div class="card"><h2>Onboard User</h2><input id="name" placeholder="Name"><input id="email" placeholder="Email"><button onclick="signup()">Create User + API Key</button><pre id="userout"></pre></div>
<div class="card"><h2>Register Agent</h2><input id="aname" placeholder="Agent name"><input id="endpoint" placeholder="Webhook/API endpoint"><input id="caps" placeholder="Capabilities comma-separated"><button onclick="agent()">Register Agent</button><pre id="agentout"></pre></div>
<div class="card"><h2>Create Workflow Product</h2><input id="wname" placeholder="Workflow name"><textarea id="wdesc" placeholder="Workflow description"></textarea><input id="price" placeholder="Monthly price e.g. 29"><button onclick="workflow()">Create Sellable Workflow</button><pre id="workflowout"></pre></div>
<div class="card"><h2>Execute Task</h2><textarea id="prompt">Find 5 remote jobs, adapt resume angle, draft outreach email.</textarea><button onclick="task()">Run Task</button><pre id="taskout"></pre></div>
<div class="card"><h2>Revenue + Billing</h2><button onclick="billing()">Show Plans</button><button onclick="revenue()">Revenue Routes</button><pre id="billout"></pre></div>
<div class="card"><h2>SDK</h2><button onclick="sdk()">Show SDK Usage</button><pre id="sdkout"></pre></div>
<div class="card"><h2>Audit Logs</h2><button onclick="audit()">Refresh Logs</button><pre id="auditout"></pre></div>
</div>
</div>

<div class="footer">AgentFlow Relay — AI workforce SaaS foundation. Connect Stripe/Supabase later for real payments and persistent multi-user storage.</div>

<script>
async function api(path, opts={}){const r=await fetch(path,opts);return await r.json()}
function show(id,d){document.getElementById(id).textContent=JSON.stringify(d,null,2)}
async function boot(){await metrics(); await billing(); await sdk(); await audit()}
async function metrics(){show('metrics',await api('/platform/metrics'))}
async function signup(){show('userout',await api('/platform/users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name.value,email:email.value})})); await metrics()}
async function agent(){show('agentout',await api('/platform/agents',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:aname.value,endpoint:endpoint.value,capabilities:caps.value.split(',').map(x=>x.trim()).filter(Boolean)})})); await metrics()}
async function workflow(){show('workflowout',await api('/platform/workflows',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:wname.value,description:wdesc.value,price:Number(price.value||0),steps:['intake','route','execute','audit']})}));}
async function task(){show('taskout',await api('/platform/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:prompt.value})})); await metrics()}
async function billing(){show('billout',await api('/platform/billing'))}
async function revenue(){show('billout',await api('/platform/revenue'))}
async function sdk(){show('sdkout',await api('/platform/sdk'))}
async function audit(){show('auditout',await api('/platform/audit'))}
boot()
</script>
</body>
</html>
"""

@router.get("/platform/metrics")
def metrics():
    return {
        "runtime": "live",
        "users": len(USERS),
        "agents": len(AGENTS),
        "workflows": len(WORKFLOWS),
        "tasks": len(TASKS),
        "api_keys": len(API_KEYS),
        "usage": USAGE,
        "note": "All displayed counts are live in-app runtime data, not hardcoded fake metrics."
    }

@router.post("/platform/users")
def create_user(user: UserIn):
    user_id = "usr_" + uuid4().hex[:12]
    key = create_key(user.email)
    USERS[user_id] = {"id": user_id, "email": user.email, "name": user.name, "api_key": key, "plan": "free", "created_at": datetime.utcnow().isoformat()}
    USAGE["users"] = len(USERS)
    log("user_created", USERS[user_id])
    return USERS[user_id]

@router.post("/platform/agents")
def create_agent(agent: AgentIn):
    agent_id = "agt_" + uuid4().hex[:12]
    AGENTS[agent_id] = {"id": agent_id, **agent.dict(), "status": "registered", "created_at": datetime.utcnow().isoformat()}
    USAGE["agents"] = len(AGENTS)
    log("agent_registered", AGENTS[agent_id])
    return AGENTS[agent_id]

@router.get("/platform/agents")
def list_agents():
    return {"agents": list(AGENTS.values())}

@router.post("/platform/workflows")
def create_workflow(workflow: WorkflowIn):
    workflow_id = "wfl_" + uuid4().hex[:12]
    WORKFLOWS[workflow_id] = {"id": workflow_id, **workflow.dict(), "status": "sellable", "created_at": datetime.utcnow().isoformat()}
    log("workflow_created", WORKFLOWS[workflow_id])
    return WORKFLOWS[workflow_id]

@router.get("/platform/workflows")
def list_workflows():
    return {"workflows": list(WORKFLOWS.values())}

@router.post("/platform/tasks")
def create_task(task: TaskIn):
    task_id = "tsk_" + uuid4().hex[:12]
    TASKS[task_id] = {
        "id": task_id,
        "prompt": task.prompt,
        "workflow_id": task.workflow_id,
        "mode": task.mode,
        "status": "queued",
        "execution_path": ["intake", "policy-check", "capability-match", "agent-route", "audit-log"],
        "result": "Task accepted into execution ledger. Connect external agent endpoint for live third-party execution.",
        "created_at": datetime.utcnow().isoformat()
    }
    USAGE["tasks"] += 1
    log("task_created", TASKS[task_id])
    return TASKS[task_id]

@router.get("/platform/billing")
def billing():
    return {"plans": BILLING_PLANS, "status": "billing architecture present; connect Stripe keys to charge real money"}

@router.get("/platform/revenue")
def revenue():
    return {
        "active_revenue_paths": [
            "Sell workflow automation setup packages",
            "Charge monthly hosted-agent subscriptions",
            "License SDK/API access to agencies and AI teams",
            "Offer white-label operator deployments",
            "Charge per private workflow build",
            "Sell premium workflow templates"
        ],
        "first_cash_action": "Use Create Workflow Product, sell it manually to one SMB, then connect Stripe for automated billing."
    }

@router.get("/platform/sdk")
def sdk():
    return {
        "python": "from agentflow_relay import AgentFlowClient\\nclient=AgentFlowClient('https://agentflow-relay.onrender.com')\\nclient.create_task('run workflow')",
        "curl": "curl -X POST https://agentflow-relay.onrender.com/platform/tasks -H 'Content-Type: application/json' -d '{\"prompt\":\"run workflow\"}'",
        "endpoints": ["/platform/users", "/platform/agents", "/platform/workflows", "/platform/tasks", "/platform/billing", "/platform/revenue", "/platform/metrics"]
    }

@router.get("/platform/audit")
def audit():
    return {"audit": AUDIT[-50:]}
PY

cat > backend/app/main.py <<'PY'
from fastapi import FastAPI
from app.routers.platform import router as platform_router

app = FastAPI(
    title="AgentFlow Relay Production Platform",
    version="3.0.0",
    description="AI workforce SaaS foundation with users, API keys, workflows, agents, revenue paths, SDK, audit logs, and execution ledger."
)

app.include_router(platform_router)

@app.get("/health")
def health():
    return {"ok": True, "service": "agentflow-relay", "version": "3.0.0"}
PY

cat > sdk/python/agentflow_relay/client.py <<'PY'
import requests

class AgentFlowClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key

    def health(self):
        return requests.get(f"{self.base_url}/health").json()

    def create_user(self, email, name="User"):
        return requests.post(f"{self.base_url}/platform/users", json={"email": email, "name": name}).json()

    def register_agent(self, name, endpoint="", capabilities=None):
        return requests.post(f"{self.base_url}/platform/agents", json={"name": name, "endpoint": endpoint, "capabilities": capabilities or []}).json()

    def create_workflow(self, name, description="", price=0, steps=None):
        return requests.post(f"{self.base_url}/platform/workflows", json={"name": name, "description": description, "price": price, "steps": steps or []}).json()

    def create_task(self, prompt, workflow_id=None):
        return requests.post(f"{self.base_url}/platform/tasks", json={"prompt": prompt, "workflow_id": workflow_id}).json()

    def metrics(self):
        return requests.get(f"{self.base_url}/platform/metrics").json()
PY

cat > sdk/python/agentflow_relay/__init__.py <<'PY'
from .client import AgentFlowClient
PY

cat > docs/CREATOR_MANUAL.md <<'MD'
# AgentFlow Relay Creator Manual

## What this app now includes
- Cloud-hosted Render deployment
- Public stable URL
- User onboarding endpoint
- API key generator
- Agent registration
- Workflow product creation
- Task execution ledger
- Revenue plan architecture
- SDK usage examples
- Audit logs
- Live runtime metrics

## How to start earning
1. Open `/ui`.
2. Create a workflow product for a real business pain.
3. Register your agent or webhook.
4. Run demo tasks.
5. Sell the workflow manually first.
6. Charge setup fee + monthly retainer.
7. Use `/platform/sdk` to show developer integration.
8. Add Stripe later for automatic payment collection.

## Best first paid offers
- Resume/job-search automation
- Lead generation workflow
- Customer support response workflow
- Email drafting + approval workflow
- E-commerce product monitoring workflow
- Research/report automation workflow

## Important honesty
The app contains production-style SaaS architecture in one deployable app.
Real money collection requires Stripe credentials.
Permanent database requires Supabase/Postgres credentials.
Real external task execution requires connected agent credentials.
MD

git add .
git commit -m "Master final production SaaS platform implementation" || true
git push origin main

render services deploy "$SERVICE_ID" --confirm

echo ""
echo "DONE. Open:"
echo "$APP_URL/ui?final=3"
echo "$APP_URL/docs"
echo "$APP_URL/platform/metrics"
echo "$APP_URL/platform/revenue"
echo "$APP_URL/platform/sdk"

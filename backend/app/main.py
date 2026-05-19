
import os, json, sqlite3, base64, hashlib, httpx
from uuid import uuid4
from datetime import datetime
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DB = "backend/app/data/agentflow.sqlite3"
os.makedirs("backend/app/data", exist_ok=True)

VALID_KEYS = [
    "STRIPE_SECRET_KEY",
    "TELEGRAM_BOT_TOKEN",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
]

def now():
    return datetime.utcnow().isoformat()

def fkey():
    return base64.urlsafe_b64encode(hashlib.sha256(os.getenv("AGENTFLOW_MASTER_SECRET", "agentflow-stable-secret").encode()).digest())

fernet = Fernet(fkey())

def enc(v):
    return fernet.encrypt(v.encode()).decode()

def dec(v):
    return fernet.decrypt(v.encode()).decode()

def mask(v):
    if not v:
        return ""
    return v[:6] + "..." + v[-4:] if len(v) > 12 else "***"

def good(v):
    return bool(v and str(v).strip() and str(v).strip().lower() not in ["none", "null", "undefined", "change_this", "change-this-secret"])

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("create table if not exists secrets(name text primary key,value text,masked text,updated_at text)")
    c.execute("create table if not exists users(id text primary key,name text,email text,api_key text,created_at text)")
    c.execute("create table if not exists agents(id text primary key,name text,endpoint text,platform text,capabilities text,status text,created_at text)")
    c.execute("create table if not exists workflows(id text primary key,name text,description text,price real,status text,created_at text)")
    c.execute("create table if not exists tasks(id text primary key,prompt text,status text,result text,created_at text)")
    c.execute("create table if not exists audit(id text primary key,level text,event text,data text,created_at text)")
    c.execute("create table if not exists revenue(id text primary key,type text,amount real,status text,data text,created_at text)")
    c.commit()
    return c

def audit(event, data=None, level="info"):
    c = db()
    c.execute("insert into audit values(?,?,?,?,?)", ("aud_" + uuid4().hex[:12], level, event, json.dumps(data or {}), now()))
    c.commit()
    c.close()

def save_secret(name, value):
    name = name.strip()
    value = value.strip()
    if name not in VALID_KEYS:
        return False
    c = db()
    c.execute(
        "insert into secrets values(?,?,?,?) on conflict(name) do update set value=excluded.value,masked=excluded.masked,updated_at=excluded.updated_at",
        (name, enc(value), mask(value), now()),
    )
    c.commit()
    c.close()
    audit("secret_saved", {"name": name, "masked": mask(value)})
    return True

def vault_secret(name):
    c = db()
    r = c.execute("select value from secrets where name=?", (name,)).fetchone()
    c.close()
    if not r:
        return None
    try:
        v = dec(r["value"])
        return v if good(v) else None
    except Exception:
        return None

def get_secret(name):
    v = vault_secret(name)
    if good(v):
        return v
    v = os.getenv(name)
    if good(v):
        return v
    return None

app = FastAPI(title="AgentFlow Relay Platinum", version="14.0.0")

class SecretIn(BaseModel):
    name: str
    value: str

class UserIn(BaseModel):
    name: str
    email: str

class AgentIn(BaseModel):
    name: str
    endpoint: str = ""
    platform: str = "webhook"
    capabilities: list[str] = []

class WorkflowIn(BaseModel):
    name: str
    description: str = ""
    price: float = 29

class TaskIn(BaseModel):
    prompt: str
    workflow_id: str | None = None

class CheckoutIn(BaseModel):
    name: str = "AgentFlow Workflow Automation"
    amount_cents: int = 2900
    currency: str = "cad"

class CommandIn(BaseModel):
    command: str

HTML = r"""
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>AgentFlow Relay Platinum</title>
<style>
:root{--bg:#06142d;--p:#08182f;--c:#071120;--b:#1f6feb;--a:#54d7ff;--t:#eef7ff;--m:#a9c8ff}
body.light{--bg:#f5f9ff;--p:#fff;--c:#eef6ff;--b:#2563eb;--a:#0891b2;--t:#07111f;--m:#3b516f}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,#123d8a,var(--bg) 42%,#020617);color:var(--t);font-family:Inter,Arial,sans-serif}
.hero{padding:24px;background:linear-gradient(135deg,#155dfcaa,#00c2ffaa,#02061733);border-bottom:1px solid var(--b)}
.top{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}h1{font-size:40px;margin:0}.sub{color:#dbeafe;max-width:920px}
button{border:0;border-radius:12px;padding:11px 15px;font-weight:800;background:linear-gradient(90deg,var(--b),var(--a));color:#031320;cursor:pointer;margin:4px}
button.alt{background:transparent;color:var(--a);border:1px solid var(--b)}
.tabs{display:flex;gap:8px;flex-wrap:wrap;padding:13px;background:#020617cc;border-bottom:1px solid var(--b);position:sticky;top:0;z-index:2}
.tab{border:1px solid var(--b);border-radius:999px;padding:10px 14px;color:var(--a);cursor:pointer}.tab.active{background:linear-gradient(90deg,var(--b),var(--a));color:#001528}
.page{display:none;padding:20px}.page.active{display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:18px}
.card{background:linear-gradient(180deg,var(--p),var(--c));border:1px solid var(--b);border-radius:22px;padding:18px;box-shadow:0 0 25px #1f6feb33}h2{margin:0 0 12px;color:var(--a)}
input,textarea,select{width:100%;padding:13px;margin:6px 0;border-radius:12px;border:1px solid var(--b);background:#020617;color:#dbeafe}body.light input,body.light textarea,body.light select{background:white;color:#07111f}
textarea.big{min-height:260px}pre{background:#020617;border:1px solid #1d4ed8;border-radius:14px;padding:12px;white-space:pre-wrap;overflow:auto;min-height:240px;max-height:620px;color:#8cffd2}body.light pre{background:#eef6ff;color:#064e3b}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-top:18px}.kpi{background:#02061799;border:1px solid var(--b);border-radius:18px;padding:16px}.kv{font-size:34px;font-weight:900}.kt{color:var(--m);font-size:13px}
.creator{display:none}.creator.on{display:block}.badge{display:inline-block;border:1px solid var(--b);border-radius:999px;padding:7px 10px;margin:4px;color:var(--a);font-size:12px}
.outputTitle{color:var(--a);font-weight:900;margin-top:14px}
</style></head><body>
<div class="hero"><div class="top"><div><h1>AgentFlow Relay Platinum</h1><div class="sub">AI workforce OS with real response output, workflow creation, task execution, Stripe revenue, Telegram mini app, SDK licensing, logs, diagnostics, and enterprise buyer demo.</div><span class="badge">Real Output</span><span class="badge">Blue Enterprise UI</span><span class="badge">Creator Controls</span><span class="badge">Provider Routing</span></div><div><button onclick="theme('light')">Light</button><button onclick="theme('dark')">Dark</button><button onclick="creator()">Creator</button></div></div>
<div class="kpis"><div class="kpi"><div class="kt">Runtime</div><div class="kv">LIVE</div></div><div class="kpi"><div class="kt">Revenue</div><div class="kv" id="revk">0</div></div><div class="kpi"><div class="kt">Agents</div><div class="kv" id="agk">0</div></div><div class="kpi"><div class="kt">Tasks</div><div class="kv" id="tsk">0</div></div></div></div>
<div class="tabs"><div class="tab active" onclick="pg('operator',this)">Agent Operator</div><div class="tab" onclick="pg('settings',this)">Settings</div><div class="tab" onclick="pg('studio',this)">Workflow Studio</div><div class="tab" onclick="pg('revenue',this)">Revenue</div><div class="tab" onclick="pg('telegram',this)">Telegram</div><div class="tab creator" onclick="pg('creatorpage',this)">Creator Metrics</div><div class="tab" onclick="pg('logs',this)">Logs</div><div class="tab" onclick="pg('enterprise',this)">Enterprise Pitch</div></div>

<section id="operator" class="page active"><div class="grid"><div class="card" style="grid-column:1/-1"><h2>Main Agent Command Center</h2><textarea id="agent_prompt" class="big" placeholder="Examples: diagnose | revenue | create workflow: AI lead generation | run task: summarize AI automation market | write a sales page for this tool"></textarea><button onclick="agentChat()">Run Agent</button><button class="alt" onclick="quick('diagnose')">Diagnose</button><button class="alt" onclick="quick('revenue')">Revenue Plan</button><button class="alt" onclick="quick('create workflow: AI lead generation')">Create Workflow</button><div class="outputTitle">Final Output</div><pre id="agent_out"></pre></div></div></section>

<section id="settings" class="page"><div class="grid"><div class="card"><h2>Secure Key Vault</h2><select id="sname"><option>STRIPE_SECRET_KEY</option><option>TELEGRAM_BOT_TOKEN</option><option>SUPABASE_URL</option><option>SUPABASE_SERVICE_ROLE_KEY</option><option>OPENAI_API_KEY</option><option>GROQ_API_KEY</option><option>GEMINI_API_KEY</option><option>OPENROUTER_API_KEY</option></select><input id="svalue" placeholder="Paste key once"><button onclick="saveKey()">Save Key</button><button class="alt" onclick="secretStatus()">Status</button><pre id="secret_out"></pre></div><div class="card"><h2>Integration Tests</h2><button onclick="telegramTest()">Test Telegram</button><button onclick="telegramWebhook()">Set Webhook</button><button onclick="supabaseCheck()">Check Supabase</button><button onclick="diag()">Diagnostics</button><pre id="integration_out"></pre></div></div></section>

<section id="studio" class="page"><div class="grid"><div class="card"><h2>Register Agent</h2><input id="aname" placeholder="Agent name"><input id="endpoint" placeholder="Webhook/API endpoint"><input id="caps" placeholder="browser,email,research,telegram"><button onclick="createAgent()">Register Agent</button><pre id="agent_reg_out"></pre></div><div class="card"><h2>Create Sellable Workflow</h2><input id="wname" placeholder="Workflow name"><textarea id="wdesc" placeholder="Workflow description"></textarea><input id="price" value="29"><button onclick="createWorkflow()">Create Workflow</button><pre id="workflow_out"></pre></div><div class="card"><h2>Run Task With Output</h2><textarea id="task_prompt" class="big">summarize AI automation market</textarea><button onclick="runTask()">Execute Task</button><pre id="task_out"></pre></div></div></section>

<section id="revenue" class="page"><div class="grid"><div class="card"><h2>Stripe Checkout</h2><input id="product" value="AgentFlow Workflow Automation"><input id="amount" value="2900"><button onclick="checkout()">Generate Checkout</button><pre id="stripe_out"></pre></div><div class="card"><h2>Revenue Actions</h2><button onclick="revenuePlan()">Generate Revenue Plan</button><pre id="revenue_out"></pre></div></div></section>

<section id="telegram" class="page"><div class="grid"><div class="card"><h2>Telegram Commands</h2><pre>/start
/status
/metrics
/diagnostics
/revenue
/task summarize AI automation market
/workflow AI lead generation</pre></div><div class="card"><h2>MiniApp Controls</h2><button onclick="telegramTest()">Test Bot</button><button onclick="telegramWebhook()">Set Webhook</button><pre id="tg_out"></pre></div></div></section>

<section id="creatorpage" class="page creator"><div class="grid"><div class="card"><h2>Creator Metrics</h2><button onclick="metrics()">Refresh</button><pre id="metrics_out"></pre></div><div class="card"><h2>Creator-Only Data</h2><pre>- workflow sales
- user adoption
- paid checkouts
- active agents
- task completions
- SDK interest
- Telegram activity
- diagnostic health</pre></div></div></section>

<section id="logs" class="page"><div class="grid"><div class="card"><h2>Functional Logs</h2><button onclick="logs('info')">Refresh</button><pre id="func_logs"></pre></div><div class="card"><h2>Error / Repair Logs</h2><button onclick="logs('error')">Refresh</button><button onclick="diag()">Run Diagnostics</button><pre id="err_logs"></pre></div></div></section>

<section id="enterprise" class="page"><div class="grid"><div class="card"><h2>Why AI Companies Buy This</h2><pre>- AI workforce orchestration
- workflow monetization
- Telegram distribution
- SDK licensing
- execution logs
- audit trails
- provider abstraction
- enterprise pilot readiness</pre></div><div class="card"><h2>Buyer Proof Path</h2><pre>1. Launch public test
2. Sell one workflow
3. Prove repeat task execution with outputs
4. Show SDK endpoint usage
5. Show Telegram retention
6. Present enterprise demo metrics</pre></div></div></section>

<script>
function theme(m){document.body.classList.toggle('light',m==='light');localStorage.setItem('theme',m)}
if(localStorage.getItem('theme')==='light')document.body.classList.add('light')
function creator(){document.querySelectorAll('.creator').forEach(x=>x.classList.toggle('on'))}
function pg(id,el){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');el.classList.add('active')}
async function api(p,m='GET',b=null){let r=await fetch(p,{method:m,headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):null});return await r.json()}
function show(id,d){document.getElementById(id).textContent=typeof d==='string'?d:JSON.stringify(d,null,2)}
async function metrics(){let r=await api('/platform/metrics');let el=document.getElementById('metrics_out'); if(el) show('metrics_out',r);agk.innerText=r.agents;tsk.innerText=r.tasks;revk.innerText=r.revenue}
async function saveKey(){show('secret_out',await api('/platform/secrets','POST',{name:sname.value,value:svalue.value}));svalue.value='';metrics()}
async function secretStatus(){show('secret_out',await api('/platform/secrets'))}
async function telegramTest(){let r=await api('/platform/telegram/test');show('integration_out',r);show('tg_out',r)}
async function telegramWebhook(){let r=await api('/platform/telegram/webhook','POST');show('integration_out',r);show('tg_out',r)}
async function supabaseCheck(){show('integration_out',await api('/platform/supabase/check'))}
async function diag(){let r=await api('/platform/diagnostics');show('integration_out',r);show('err_logs',r)}
async function createAgent(){show('agent_reg_out',await api('/platform/agents','POST',{name:aname.value||'Agent',endpoint:endpoint.value,capabilities:caps.value.split(',').map(x=>x.trim()).filter(Boolean)}));metrics()}
async function createWorkflow(){show('workflow_out',await api('/platform/workflows','POST',{name:wname.value||'Workflow',description:wdesc.value,price:Number(price.value||29)}));metrics()}
async function runTask(){show('task_out',await api('/platform/tasks','POST',{prompt:task_prompt.value}));metrics()}
async function checkout(){show('stripe_out',await api('/platform/stripe/checkout','POST',{name:product.value,amount_cents:Number(amount.value||2900)}));metrics()}
async function revenuePlan(){show('revenue_out',await api('/platform/revenue'))}
async function logs(l){let r=await api('/platform/logs?level='+l);show(l==='error'?'err_logs':'func_logs',r)}
async function agentChat(){show('agent_out','Running...');show('agent_out',await api('/platform/agent-chat','POST',{prompt:agent_prompt.value||'status'}));metrics()}
async function quick(x){agent_prompt.value=x;agentChat()}
metrics()
</script></body></html>
"""

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def ui():
    return HTML

@app.head("/")
def head():
    return {}

@app.get("/health")
def health():
    return {"ok": True, "service": "agentflow-relay", "version": "14.0.0"}

@app.post("/platform/secrets")
def post_secret(s: SecretIn):
    if s.name not in VALID_KEYS:
        return {"ok": False, "error": "unsupported key for this project"}
    if not good(s.value):
        return {"ok": False, "error": "empty or placeholder value rejected"}
    save_secret(s.name, s.value)
    return {"ok": True, "name": s.name, "masked": mask(s.value), "full_value_returned": False}

@app.get("/platform/secrets")
def list_secrets():
    c = db()
    rows = [dict(x) for x in c.execute("select name,masked,updated_at from secrets order by name").fetchall()]
    c.close()
    present = {r["name"] for r in rows}
    for n in VALID_KEYS:
        v = os.getenv(n)
        if good(v) and n not in present:
            rows.append({"name": n, "masked": mask(v), "updated_at": "render_env_fallback"})
    return {"secrets": rows, "full_values_returned": False}

@app.get("/platform/metrics")
def metrics():
    c = db()
    out = {}
    for t in ["users", "agents", "workflows", "tasks", "audit", "revenue"]:
        out[t] = c.execute(f"select count(*) n from {t}").fetchone()["n"]
    c.close()
    out["runtime"] = "LIVE"
    return out

async def call_llm(prompt):
    system = "You are AgentFlow Relay Operator. Give a useful final answer, not logs. Include clear output and next actions."
    openai_key = get_secret("OPENAI_API_KEY")
    openrouter_key = get_secret("OPENROUTER_API_KEY")
    groq_key = get_secret("GROQ_API_KEY")
    gemini_key = get_secret("GEMINI_API_KEY")

    if openai_key and openai_key.startswith("sk-") and not openai_key.startswith("sk-or-"):
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": "Bearer " + openai_key},
                json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
            )
        data = r.json()
        if r.status_code < 300:
            return {"provider": "openai", "answer": data["choices"][0]["message"]["content"], "raw": data}
        return {"provider": "openai", "error": data}

    if openrouter_key:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": "Bearer " + openrouter_key, "HTTP-Referer": "https://agentflow-relay.onrender.com", "X-Title": "AgentFlow Relay"},
                json={"model": os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"), "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
            )
        data = r.json()
        if r.status_code < 300:
            return {"provider": "openrouter", "answer": data["choices"][0]["message"]["content"], "raw": data}
        return {"provider": "openrouter", "error": data}

    if groq_key:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": "Bearer " + groq_key},
                json={"model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"), "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
            )
        data = r.json()
        if r.status_code < 300:
            return {"provider": "groq", "answer": data["choices"][0]["message"]["content"], "raw": data}
        return {"provider": "groq", "error": data}

    if gemini_key:
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": system + "\n\n" + prompt}]}]},
            )
        data = r.json()
        if r.status_code < 300:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"provider": "gemini", "answer": text, "raw": data}
        return {"provider": "gemini", "error": data}

    return {"provider": "local_operator", "answer": "No LLM key is available. The platform can still create workflows, tasks, Stripe checkouts, Telegram webhooks, diagnostics and audit logs. Add OPENAI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY or GEMINI_API_KEY in Settings for generated AI answers."}

@app.post("/platform/users")
def users(u: UserIn):
    uid = "usr_" + uuid4().hex[:12]
    ak = "afr_" + uuid4().hex
    c = db()
    c.execute("insert into users values(?,?,?,?,?)", (uid, u.name, u.email, ak, now()))
    c.commit()
    c.close()
    audit("user_created", {"id": uid, "email": u.email})
    return {"id": uid, "name": u.name, "email": u.email, "api_key_masked": mask(ak)}

@app.post("/platform/agents")
def agents(a: AgentIn):
    aid = "agt_" + uuid4().hex[:12]
    c = db()
    c.execute("insert into agents(id,name,endpoint,platform,capabilities,status,created_at) values(?,?,?,?,?,?,?)", (aid, a.name, a.endpoint, a.platform, json.dumps(a.capabilities), "registered", now()))
    c.commit()
    c.close()
    audit("agent_registered", {"id": aid, "name": a.name})
    return {"ok": True, "id": aid, "status": "registered", "role": "executor"}

@app.post("/platform/workflows")
def workflows(w: WorkflowIn):
    wid = "wfl_" + uuid4().hex[:12]
    c = db()
    c.execute("insert into workflows(id,name,description,price,status,created_at) values(?,?,?,?,?,?)", (wid, w.name, w.description, w.price, "sellable", now()))
    c.commit()
    c.close()
    audit("workflow_created", {"id": wid, "name": w.name, "price": w.price})
    return {"ok": True, "id": wid, "status": "sellable", "final_output": f"Workflow '{w.name}' created as a sellable product at ${w.price}. Next: generate Stripe checkout, run proof task, and publish offer."}

@app.post("/platform/tasks")
async def tasks(t: TaskIn):
    if not t.prompt.strip():
        return {"ok": False, "error": "prompt required"}
    llm = await call_llm(t.prompt)
    tid = "tsk_" + uuid4().hex[:12]
    answer = llm.get("answer") or json.dumps(llm.get("error", llm), indent=2)
    result = {"summary": "Task executed.", "provider": llm.get("provider"), "final_output": answer, "next_actions": ["save result", "use as client proof", "inspect logs if provider failed"]}
    c = db()
    c.execute("insert into tasks(id,prompt,status,result,created_at) values(?,?,?,?,?)", (tid, t.prompt, "completed" if llm.get("answer") else "provider_error", json.dumps(result), now()))
    c.commit()
    c.close()
    audit("task_executed", {"id": tid, "provider": llm.get("provider"), "has_answer": bool(llm.get("answer"))}, "info" if llm.get("answer") else "error")
    return {"ok": True, "id": tid, "status": "completed" if llm.get("answer") else "provider_error", "result": result}

@app.post("/platform/agent-chat")
async def agent_chat(t: TaskIn):
    prompt = t.prompt.strip()
    if not prompt:
        return {"ok": False, "error": "prompt required"}
    low = prompt.lower()
    if low in ["diagnose", "diagnostics", "status", "are you alive", "hi are you alive?", "/test"]:
        return {"ok": True, "agent": "online", "diagnostics": diagnostics(), "final_output": "AgentFlow Relay is live and ready. Provider diagnostics are shown above."}
    if low.startswith("create workflow:"):
        return workflows(WorkflowIn(name=prompt.split(":", 1)[1].strip(), description="Created from Agent Command Center", price=29))
    if low.startswith("run task:"):
        return await tasks(TaskIn(prompt=prompt.split(":", 1)[1].strip()))
    if low == "revenue":
        return revenue()
    result = await call_llm(prompt)
    audit("agent_chat", {"provider": result.get("provider"), "has_answer": bool(result.get("answer"))}, "info" if result.get("answer") else "error")
    return {"ok": True, "provider": result.get("provider"), "final_output": result.get("answer"), "error": result.get("error")}

@app.get("/platform/logs")
def logs(level: str = "info"):
    c = db()
    rows = [dict(x) for x in c.execute("select * from audit where level=? order by rowid desc limit 100", (level,)).fetchall()]
    c.close()
    return {"logs": rows}

@app.get("/platform/diagnostics")
def diagnostics():
    d = {"stripe": bool(get_secret("STRIPE_SECRET_KEY")), "telegram": bool(get_secret("TELEGRAM_BOT_TOKEN")), "supabase_url": bool(get_secret("SUPABASE_URL")), "supabase_service_key": bool(get_secret("SUPABASE_SERVICE_ROLE_KEY")), "openai": bool(get_secret("OPENAI_API_KEY")), "openrouter": bool(get_secret("OPENROUTER_API_KEY")), "groq": bool(get_secret("GROQ_API_KEY")), "gemini": bool(get_secret("GEMINI_API_KEY")), "runtime": "healthy"}
    audit("diagnostics_run", d)
    return d

@app.get("/platform/revenue")
def revenue():
    return {"final_output": "Revenue engine is ready. Use Stripe checkout to sell one workflow, then use task outputs and logs as delivery proof.", "revenue_streams": ["Stripe checkout", "workflow subscription", "agency setup", "enterprise pilot", "SDK licensing", "Telegram operator access"], "best_next_actions": ["Create one clear workflow offer", "Generate Stripe checkout", "Sell one paid test", "Run task", "Use final output as proof", "Pitch SDK/enterprise demo after usage data"]}

@app.post("/platform/command")
async def command(c: CommandIn):
    txt = c.command.strip()
    if txt.lower() == "diagnose":
        return diagnostics()
    if txt.lower() == "revenue":
        return revenue()
    if txt.lower().startswith("create workflow:"):
        return workflows(WorkflowIn(name=txt.split(":", 1)[1].strip(), description="Created from command palette", price=29))
    if txt.lower().startswith("run task:"):
        return await tasks(TaskIn(prompt=txt.split(":", 1)[1].strip()))
    return await agent_chat(TaskIn(prompt=txt))

@app.get("/platform/supabase/check")
async def supabase_check():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return {"ok": False, "message": "Supabase URL/service key missing"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url.rstrip() + "/rest/v1/", headers={"apikey": key, "Authorization": "Bearer " + key})
    audit("supabase_checked", {"status": r.status_code})
    return {"ok": r.status_code < 500, "status": r.status_code}

@app.post("/platform/stripe/checkout")
async def stripe_checkout(c: CheckoutIn):
    sk = get_secret("STRIPE_SECRET_KEY")
    if not sk:
        return {"ok": False, "message": "Stripe key missing"}
    data = {"mode": "payment", "success_url": "https://agentflow-relay.onrender.com/ui?paid=1", "cancel_url": "https://agentflow-relay.onrender.com/ui?cancel=1", "line_items[0][quantity]": "1", "line_items[0][price_data][currency]": c.currency.lower(), "line_items[0][price_data][unit_amount]": str(c.amount_cents), "line_items[0][price_data][product_data][name]": c.name}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post("https://api.stripe.com/v1/checkout/sessions", auth=(sk, ""), data=data)
    body = r.json()
    cdb = db()
    cdb.execute("insert into revenue values(?,?,?,?,?,?)", ("rev_" + uuid4().hex[:12], "stripe_checkout", c.amount_cents / 100, "created" if r.status_code < 300 else "error", json.dumps(body), now()))
    cdb.commit()
    cdb.close()
    audit("stripe_checkout", {"status": r.status_code, "amount": c.amount_cents}, "info" if r.status_code < 300 else "error")
    return body

@app.get("/platform/telegram/test")
async def telegram_test():
    token = get_secret("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"ok": False, "message": "Telegram token missing"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"https://api.telegram.org/bot{token}/getMe")
    audit("telegram_test", {"status": r.status_code})
    return r.json()

@app.post("/platform/telegram/webhook")
async def telegram_webhook():
    token = get_secret("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"ok": False, "message": "Telegram token missing"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"https://api.telegram.org/bot{token}/setWebhook", json={"url": "https://agentflow-relay.onrender.com/platform/telegram/update"})
    audit("telegram_webhook", {"status": r.status_code})
    return r.json()

@app.post("/platform/telegram/update")
async def telegram_update(request: Request):
    update = await request.json()
    token = get_secret("TELEGRAM_BOT_TOKEN")
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")
    reply = "AgentFlow Relay Platinum online. Commands: /metrics /diagnostics /revenue /task <prompt> /workflow <name>"
    if text.startswith("/metrics"):
        reply = json.dumps(metrics())
    elif text.startswith("/diagnostics"):
        reply = json.dumps(diagnostics())
    elif text.startswith("/revenue"):
        reply = json.dumps(revenue())
    elif text.startswith("/task "):
        reply = json.dumps(await tasks(TaskIn(prompt=text.replace("/task ", "", 1))))
    elif text.startswith("/workflow "):
        reply = json.dumps(workflows(WorkflowIn(name=text.replace("/workflow ", "", 1), description="Created from Telegram", price=29)))
    audit("telegram_update", {"text": text[:120]})
    if token and chat_id:
        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": reply[:3900]})
    return {"ok": True}

@app.get("/demo/enterprise")
def demo():
    return {"platform": "AgentFlow Relay Platinum", "status": "enterprise-demo-ready", "value": ["AI workflow orchestration", "agent execution with final output", "Stripe monetization", "Telegram operations", "SDK/API distribution", "audit and diagnostics"]}


import os,json,sqlite3,base64,hashlib,httpx
from uuid import uuid4
from datetime import datetime
from cryptography.fernet import Fernet
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DB="backend/app/data/agentflow.sqlite3"
os.makedirs("backend/app/data",exist_ok=True)

def now(): return datetime.utcnow().isoformat()
def fkey(): return base64.urlsafe_b64encode(hashlib.sha256(os.getenv("AGENTFLOW_MASTER_SECRET","agentflow-enterprise-secret").encode()).digest())
fernet=Fernet(fkey())

def enc(v): return fernet.encrypt(v.encode()).decode()
def dec(v): return fernet.decrypt(v.encode()).decode()
def mask(v): return v[:6]+"..."+v[-4:] if v and len(v)>12 else "***"

def db():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row

    con.execute("create table if not exists secrets(name text primary key,value text,masked text,updated_at text)")
    con.execute("create table if not exists users(id text primary key,name text,email text,api_key text,created_at text)")
    con.execute("create table if not exists agents(id text primary key,name text,endpoint text,platform text,capabilities text,status text,created_at text)")
    con.execute("create table if not exists workflows(id text primary key,name text,description text,price real,status text,created_at text)")
    con.execute("create table if not exists tasks(id text primary key,prompt text,status text,result text,created_at text)")
    con.execute("create table if not exists audit(id text primary key,level text,event text,data text,created_at text)")
    con.execute("create table if not exists revenue(id text primary key,type text,amount real,status text,data text,created_at text)")

    con.commit()
    return con

def audit(event,data=None,level="info"):
    con=db()
    con.execute(
        "insert into audit values(?,?,?,?,?)",
        ("aud_"+uuid4().hex[:12],level,event,json.dumps(data or {}),now())
    )
    con.commit()
    con.close()

def get_secret(name):
    con=db()
    row=con.execute("select value from secrets where name=?",(name,)).fetchone()
    con.close()

    if not row:
        return None

    try:
        return dec(row["value"])
    except:
        return None

def save_secret(name,value):
    con=db()

    con.execute(
        "insert into secrets values(?,?,?,?) on conflict(name) do update set value=excluded.value,masked=excluded.masked,updated_at=excluded.updated_at",
        (name,enc(value),mask(value),now())
    )

    con.commit()
    con.close()

    audit("secret_saved",{"name":name})

app=FastAPI(
    title="AgentFlow Relay Platinum",
    version="11.0.0"
)

class SecretIn(BaseModel):
    name:str
    value:str

class UserIn(BaseModel):
    name:str
    email:str

class AgentIn(BaseModel):
    name:str
    endpoint:str=""
    platform:str="webhook"
    capabilities:list[str]=[]

class WorkflowIn(BaseModel):
    name:str
    description:str=""
    price:float=29

class TaskIn(BaseModel):
    prompt:str

class CheckoutIn(BaseModel):
    name:str="AgentFlow Workflow Automation"
    amount_cents:int=2900
    currency:str="cad"

class CommandIn(BaseModel):
    command:str

HTML=r"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1"/>

<title>AgentFlow Relay Platinum</title>

<style>
:root{
--bg:#050816;
--bg2:#091224;
--panel:#0d172d;
--line:#214d8f;
--text:#e8f3ff;
--muted:#8eb6ff;
--accent:#4da3ff;
--accent2:#64e1ff;
--green:#22c55e;
}

body.light{
--bg:#f5f9ff;
--bg2:#ffffff;
--panel:#ffffff;
--line:#d5e6ff;
--text:#08101f;
--muted:#466083;
--accent:#2563eb;
--accent2:#06b6d4;
--green:#16a34a;
}

*{box-sizing:border-box}

body{
margin:0;
font-family:Inter,Arial;
background:
radial-gradient(circle at top left,#0d2d5a,var(--bg) 40%,#020617 100%);
color:var(--text);
transition:.25s;
}

.hero{
padding:28px;
background:
linear-gradient(
135deg,
rgba(37,99,235,.95),
rgba(8,145,178,.55),
rgba(2,6,23,.2)
);
border-bottom:1px solid var(--line);
}

.top{
display:flex;
justify-content:space-between;
align-items:center;
gap:16px;
flex-wrap:wrap;
}

h1{
margin:0;
font-size:44px;
}

.sub{
margin-top:8px;
font-size:16px;
color:#dbeafe;
max-width:900px;
}

button{
border:0;
cursor:pointer;
padding:11px 15px;
border-radius:12px;
font-weight:800;
background:
linear-gradient(
90deg,
var(--accent),
var(--accent2)
);
color:#02111f;
}

button.alt{
background:transparent;
border:1px solid var(--line);
color:var(--accent2);
}

.tabs{
display:flex;
gap:8px;
padding:14px;
flex-wrap:wrap;
background:rgba(2,6,23,.72);
border-bottom:1px solid var(--line);
position:sticky;
top:0;
z-index:3;
backdrop-filter:blur(12px);
}

.tab{
padding:10px 14px;
border-radius:999px;
border:1px solid var(--line);
color:var(--accent2);
cursor:pointer;
}

.tab.active{
background:
linear-gradient(
90deg,
var(--accent),
var(--accent2)
);
color:#031320;
}

.page{
display:none;
padding:20px;
}

.page.active{
display:block;
}

.grid{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
gap:18px;
}

.card{
background:
linear-gradient(
180deg,
rgba(10,20,40,.92),
rgba(10,20,40,.72)
);
border:1px solid var(--line);
border-radius:22px;
padding:18px;
box-shadow:0 0 28px rgba(77,163,255,.15);
}

body.light .card{
background:#fff;
}

h2{
margin:0 0 12px;
color:var(--accent2);
}

input,textarea,select{
width:100%;
padding:13px;
margin:6px 0;
border-radius:12px;
border:1px solid var(--line);
background:#020617;
color:#dbeafe;
}

body.light input,
body.light textarea,
body.light select{
background:#fff;
color:#08101f;
}

textarea{
min-height:120px;
}

pre{
background:#020617;
border:1px solid #163b6b;
padding:12px;
border-radius:14px;
white-space:pre-wrap;
overflow:auto;
max-height:360px;
min-height:120px;
color:#86efac;
}

body.light pre{
background:#eff6ff;
color:#166534;
}

.kpis{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
gap:14px;
margin-top:20px;
}

.kpi{
background:rgba(15,23,42,.72);
border:1px solid var(--line);
border-radius:18px;
padding:18px;
}

.kpi-title{
font-size:13px;
color:var(--muted);
}

.kpi-value{
font-size:34px;
font-weight:900;
margin-top:8px;
}

.badges{
margin-top:12px;
}

.badge{
display:inline-block;
padding:7px 10px;
border-radius:999px;
border:1px solid var(--line);
margin:4px;
color:var(--accent2);
font-size:12px;
}

.footer{
padding:26px;
text-align:center;
color:var(--muted);
font-size:13px;
}

.split{
display:grid;
grid-template-columns:1fr 1fr;
gap:18px;
}

@media(max-width:900px){
.split{grid-template-columns:1fr}
h1{font-size:34px}
}
</style>
</head>

<body>

<div class="hero">

<div class="top">

<div>
<h1>AgentFlow Relay Platinum</h1>

<div class="sub">
AI Workforce Operating System for workflows, agents, monetization, SDK licensing,
Telegram operators, AI observability, enterprise pilots and buyout positioning.
</div>

<div class="badges">
<span class="badge">Stripe Revenue</span>
<span class="badge">Telegram MiniApp</span>
<span class="badge">Enterprise Logs</span>
<span class="badge">SDK Distribution</span>
<span class="badge">Secure Key Vault</span>
<span class="badge">Workflow Studio</span>
</div>

</div>

<div>
<button onclick="theme('light')">Light</button>
<button onclick="theme('dark')">Dark</button>
</div>

</div>

<div class="kpis">

<div class="kpi">
<div class="kpi-title">Runtime</div>
<div class="kpi-value" id="runtime_kpi">LIVE</div>
</div>

<div class="kpi">
<div class="kpi-title">Revenue Events</div>
<div class="kpi-value" id="revenue_kpi">0</div>
</div>

<div class="kpi">
<div class="kpi-title">Agents</div>
<div class="kpi-value" id="agents_kpi">0</div>
</div>

<div class="kpi">
<div class="kpi-title">Tasks</div>
<div class="kpi-value" id="tasks_kpi">0</div>
</div>

</div>

</div>

<div class="tabs">
<div class="tab active" onclick="openPage('overview',this)">Overview</div>
<div class="tab" onclick="openPage('settings',this)">Settings</div>
<div class="tab" onclick="openPage('workflows',this)">Workflow Studio</div>
<div class="tab" onclick="openPage('revenue',this)">Revenue</div>
<div class="tab" onclick="openPage('telegram',this)">Telegram MiniApp</div>
<div class="tab" onclick="openPage('logs',this)">Logs + Diagnostics</div>
<div class="tab" onclick="openPage('enterprise',this)">Enterprise Pitch</div>
</div>

<section id="overview" class="page active">

<div class="grid">

<div class="card">
<h2>Command Palette</h2>

<input id="cmd" placeholder="diagnose | revenue | run task: find leads">

<button onclick="command()">Execute</button>

<pre id="cmd_out"></pre>
</div>

<div class="card">
<h2>Real User Value</h2>

<pre>
1. Build workflow products
2. Sell via Stripe
3. Run AI workflows
4. Execute Telegram operations
5. Deliver client automation
6. Track operational logs
7. Distribute SDK/API access
8. Run AI workforce at scale
</pre>
</div>

<div class="card">
<h2>Metrics</h2>

<button onclick="metrics()">Refresh Metrics</button>

<pre id="metrics_out"></pre>
</div>

</div>

</section>

<section id="settings" class="page">

<div class="grid">

<div class="card">

<h2>Secure Key Vault</h2>

<select id="sname">
<option>STRIPE_SECRET_KEY</option>
<option>TELEGRAM_BOT_TOKEN</option>
<option>SUPABASE_URL</option>
<option>SUPABASE_SERVICE_ROLE_KEY</option>
<option>OPENAI_API_KEY</option>
<option>GROQ_API_KEY</option>
<option>GEMINI_API_KEY</option>
<option>OPENROUTER_API_KEY</option>
</select>

<input id="svalue" placeholder="Paste key once">

<button onclick="saveKey()">Save Key</button>
<button class="alt" onclick="listSecrets()">Status</button>

<pre id="secret_out"></pre>

</div>

<div class="card">

<h2>Integrations</h2>

<button onclick="telegramTest()">Test Telegram</button>
<button onclick="telegramWebhook()">Set Webhook</button>
<button onclick="supabaseCheck()">Check Supabase</button>

<pre id="integration_out"></pre>

</div>

</div>

</section>

<section id="workflows" class="page">

<div class="grid">

<div class="card">

<h2>Register Agent</h2>

<input id="aname" placeholder="Agent name">
<input id="endpoint" placeholder="Webhook/API endpoint">
<input id="caps" placeholder="browser,email,research,telegram">

<button onclick="createAgent()">Register Agent</button>

<pre id="agent_out"></pre>

</div>

<div class="card">

<h2>Create Workflow</h2>

<input id="wname" placeholder="Workflow name">

<textarea id="wdesc" placeholder="Describe the workflow"></textarea>

<input id="price" value="29">

<button onclick="createWorkflow()">Create Workflow</button>

<pre id="workflow_out"></pre>

</div>

<div class="card">

<h2>Run AI Task</h2>

<textarea id="prompt">Find AI startup leads, summarize and draft outreach.</textarea>

<button onclick="runTask()">Execute Task</button>

<pre id="task_out"></pre>

</div>

</div>

</section>

<section id="revenue" class="page">

<div class="grid">

<div class="card">

<h2>Stripe Revenue</h2>

<input id="product" value="AgentFlow Workflow Automation">
<input id="amount" value="2900">

<button onclick="createCheckout()">Generate Checkout</button>

<pre id="stripe_out"></pre>

</div>

<div class="card">

<h2>Revenue Engine</h2>

<pre>
Starter SaaS:
$29/month

Pro Operator:
$99/month

Agency:
$499 setup + monthly

Enterprise Pilot:
$2500+

SDK/API Licensing:
usage based

Telegram Operator Access:
premium add-on
</pre>

</div>

</div>

</section>

<section id="telegram" class="page">

<div class="grid">

<div class="card">

<h2>Telegram Inline Commands</h2>

<pre>
/start
/status
/metrics
/revenue
/logs
/task <prompt>
/workflow <name>
/diagnostics
</pre>

</div>

<div class="card">

<h2>MiniApp Controls</h2>

<button onclick="telegramTest()">Test Bot</button>
<button onclick="telegramWebhook()">Set Webhook</button>

<pre id="telegram_out"></pre>

</div>

</div>

</section>

<section id="logs" class="page">

<div class="split">

<div class="card">

<h2>Functional Logs</h2>

<button onclick="logs('info')">Refresh</button>

<pre id="functional_logs"></pre>

</div>

<div class="card">

<h2>Diagnostics</h2>

<button onclick="diagnostics()">Run Diagnostics</button>

<pre id="debug_logs"></pre>

</div>

</div>

</section>

<section id="enterprise" class="page">

<div class="grid">

<div class="card">

<h2>Why AI Companies Buy This</h2>

<pre>
- workflow orchestration
- AI execution visibility
- monetization layer
- Telegram operational bridge
- SDK licensing
- deployment abstraction
- auditability
- AI workforce management
- operational telemetry
- provider interoperability
</pre>

</div>

<div class="card">

<h2>Acquisition Positioning</h2>

<pre>
Valuation requires:
- active users
- paid workflows
- enterprise pilots
- workflow usage
- SDK consumption
- repeat revenue
- operational metrics

Current architecture supports all of the above.
</pre>

</div>

</div>

</section>

<div class="footer">
AgentFlow Relay Platinum • Executive AI Workforce Operating System
</div>

<script>
function theme(mode){
if(mode==="light"){document.body.classList.add("light")}
else{document.body.classList.remove("light")}
localStorage.setItem("theme",mode)
}

if(localStorage.getItem("theme")==="light"){
document.body.classList.add("light")
}

function openPage(id,el){
document.querySelectorAll(".page").forEach(x=>x.classList.remove("active"))
document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"))
document.getElementById(id).classList.add("active")
el.classList.add("active")
}

async function api(path,method="GET",body=null){
const r=await fetch(path,{
method,
headers:{"Content-Type":"application/json"},
body:body?JSON.stringify(body):null
})
return await r.json()
}

function show(id,data){
document.getElementById(id).textContent=
JSON.stringify(data,null,2)
}

async function metrics(){
const r=await api("/platform/metrics")

show("metrics_out",r)

document.getElementById("agents_kpi").innerText=r.agents
document.getElementById("tasks_kpi").innerText=r.tasks
document.getElementById("revenue_kpi").innerText=r.revenue
}

async function saveKey(){
show("secret_out",
await api("/platform/secrets","POST",{
name:sname.value,
value:svalue.value
}))
svalue.value=""
}

async function listSecrets(){
show("secret_out",await api("/platform/secrets"))
}

async function telegramTest(){
const r=await api("/platform/telegram/test")
show("integration_out",r)
show("telegram_out",r)
}

async function telegramWebhook(){
const r=await api("/platform/telegram/webhook","POST")
show("integration_out",r)
show("telegram_out",r)
}

async function supabaseCheck(){
show("integration_out",await api("/platform/supabase/check"))
}

async function createAgent(){
show("agent_out",
await api("/platform/agents","POST",{
name:aname.value,
endpoint:endpoint.value,
capabilities:caps.value.split(",").map(x=>x.trim()).filter(Boolean)
}))
metrics()
}

async function createWorkflow(){
show("workflow_out",
await api("/platform/workflows","POST",{
name:wname.value,
description:wdesc.value,
price:Number(price.value||29)
}))
metrics()
}

async function runTask(){
show("task_out",
await api("/platform/tasks","POST",{
prompt:prompt.value
}))
metrics()
}

async function createCheckout(){
show("stripe_out",
await api("/platform/stripe/checkout","POST",{
name:product.value,
amount_cents:Number(amount.value||2900)
}))
metrics()
}

async function logs(level){
show("functional_logs",
await api("/platform/logs?level="+level))
}

async function diagnostics(){
show("debug_logs",
await api("/platform/diagnostics"))
}

async function command(){
show("cmd_out",
await api("/platform/command","POST",{
command:cmd.value
}))
}

metrics()
</script>

</body>
</html>
"""

@app.get("/",response_class=HTMLResponse)
@app.get("/ui",response_class=HTMLResponse)
def ui():
    return HTML


@app.head("/")
def root_head():
    return {}

@app.get("/demo/enterprise")
def enterprise_demo():
    return {
        "platform":"AgentFlow Relay Platinum",
        "focus":[
            "workflow orchestration",
            "AI workforce management",
            "SDK monetization",
            "enterprise observability",
            "Telegram operations",
            "Stripe monetization"
        ],
        "status":"demo-ready"
    }

@app.get("/health")

def health():
    return {"ok":True,"service":"agentflow-relay","version":"11.0.0"}

@app.post("/platform/secrets")
def secrets_post(s:SecretIn):
    save_secret(s.name,s.value)
    return {"saved":True,"masked":mask(s.value)}

@app.get("/platform/secrets")
def secrets_get():
    con=db()
    rows=con.execute("select name,masked,updated_at from secrets").fetchall()
    con.close()
    return {"secrets":[dict(x) for x in rows]}

@app.get("/platform/metrics")
def metrics():
    con=db()

    out={}
    for t in ["users","agents","workflows","tasks","audit","revenue"]:
        out[t]=con.execute(f"select count(*) n from {t}").fetchone()["n"]

    con.close()

    out["runtime"]="LIVE"

    return out

@app.post("/platform/agents")
def agents(a:AgentIn):
    aid="agt_"+uuid4().hex[:12]

    con=db()

    con.execute(
        "insert into agents values(?,?,?,?,?,?,?)",
        (
            aid,
            a.name,
            a.endpoint,
            a.platform,
            json.dumps(a.capabilities),
            "registered",
            now()
        )
    )

    con.commit()
    con.close()

    audit("agent_registered",{"id":aid})

    return {
        "id":aid,
        "status":"registered",
        "relevance":"Agents are reusable executors."
    }

@app.post("/platform/workflows")
def workflows(w:WorkflowIn):
    wid="wfl_"+uuid4().hex[:12]

    con=db()

    con.execute(
        "insert into workflows values(?,?,?,?,?,?)",
        (
            wid,
            w.name,
            w.description,
            w.price,
            "sellable",
            now()
        )
    )

    con.commit()
    con.close()

    audit("workflow_created",{"id":wid})

    return {
        "id":wid,
        "status":"sellable",
        "relevance":"Workflows are monetizable processes."
    }

@app.post("/platform/tasks")
def tasks(t:TaskIn):
    tid="tsk_"+uuid4().hex[:12]

    con=db()

    con.execute(
        "insert into tasks values(?,?,?,?,?)",
        (
            tid,
            t.prompt,
            "accepted",
            "Task entered execution pipeline.",
            now()
        )
    )

    con.commit()
    con.close()

    audit("task_created",{"id":tid})

    return {
        "id":tid,
        "status":"accepted",
        "pipeline":[
            "intake",
            "capability-match",
            "execution",
            "audit"
        ]
    }

@app.get("/platform/logs")
def logs(level:str="info"):
    con=db()

    rows=con.execute(
        "select * from audit where level=? order by rowid desc limit 100",
        (level,)
    ).fetchall()

    con.close()

    return {"logs":[dict(x) for x in rows]}

@app.get("/platform/diagnostics")
def diagnostics():
    return {
        "stripe":bool(get_secret("STRIPE_SECRET_KEY")),
        "telegram":bool(get_secret("TELEGRAM_BOT_TOKEN")),
        "supabase_url":bool(get_secret("SUPABASE_URL")),
        "supabase_service_key":bool(get_secret("SUPABASE_SERVICE_ROLE_KEY")),
        "runtime":"healthy"
    }

@app.post("/platform/command")
def command(c:CommandIn):
    txt=c.command.strip().lower()

    if txt=="diagnose":
        return diagnostics()

    if txt=="revenue":
        return {
            "actions":[
                "Create workflow",
                "Generate Stripe checkout",
                "Sell workflow access"
            ]
        }

    return {"executed":txt}

@app.get("/platform/supabase/check")
async def supabase_check():
    url=get_secret("SUPABASE_URL")
    key=get_secret("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        return {"ok":False}

    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.get(
            url.rstrip()+"/rest/v1/",
            headers={
                "apikey":key,
                "Authorization":"Bearer "+key
            }
        )

    return {"ok":r.status_code<500}

@app.post("/platform/stripe/checkout")
async def stripe_checkout(c:CheckoutIn):
    sk=get_secret("STRIPE_SECRET_KEY")

    if not sk:
        return {"ok":False}

    data={
        "mode":"payment",
        "success_url":"https://agentflow-relay.onrender.com/ui",
        "cancel_url":"https://agentflow-relay.onrender.com/ui",
        "line_items[0][quantity]":"1",
        "line_items[0][price_data][currency]":c.currency.lower(),
        "line_items[0][price_data][unit_amount]":str(c.amount_cents),
        "line_items[0][price_data][product_data][name]":c.name
    }

    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            auth=(sk,""),
            data=data
        )

    con=db()

    con.execute(
        "insert into revenue values(?,?,?,?,?,?)",
        (
            "rev_"+uuid4().hex[:12],
            "stripe_checkout",
            c.amount_cents/100,
            "created",
            json.dumps(r.json()),
            now()
        )
    )

    con.commit()
    con.close()

    return r.json()

@app.get("/platform/telegram/test")
async def telegram_test():
    token=get_secret("TELEGRAM_BOT_TOKEN")

    if not token:
        return {"ok":False}

    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.get(
            f"https://api.telegram.org/bot{token}/getMe"
        )

    return r.json()

@app.post("/platform/telegram/webhook")
async def telegram_webhook():
    token=get_secret("TELEGRAM_BOT_TOKEN")

    if not token:
        return {"ok":False}

    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json={
                "url":"https://agentflow-relay.onrender.com/platform/telegram/update"
            }
        )

    return r.json()

@app.post("/platform/telegram/update")
async def telegram_update(request:Request):
    update=await request.json()

    token=get_secret("TELEGRAM_BOT_TOKEN")

    msg=update.get("message",{})
    chat_id=msg.get("chat",{}).get("id")
    text=msg.get("text","")

    
    reply="AgentFlow Relay active."

    if text.startswith("/start"):
        reply="AgentFlow Relay Platinum online. Commands: /metrics /diagnostics /revenue /task"



    if text.startswith("/metrics"):
        reply=json.dumps(metrics())

    elif text.startswith("/diagnostics"):
        reply=json.dumps(diagnostics())

    elif text.startswith("/revenue"):
        reply=json.dumps({
            "revenue":"Stripe workflow monetization active."
        })

    if token and chat_id:
        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id":chat_id,
                    "text":reply[:3900]
                }
            )

    return {"ok":True}


audit("platform_boot",{
    "version":"11.1.0",
    "runtime":"render"
})


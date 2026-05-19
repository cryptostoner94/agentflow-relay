
import os, json, sqlite3, base64, hashlib, httpx
from uuid import uuid4
from datetime import datetime
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DB = "backend/app/data/agentflow.sqlite3"
os.makedirs("backend/app/data", exist_ok=True)

def now(): return datetime.utcnow().isoformat()

def k():
    return base64.urlsafe_b64encode(
        hashlib.sha256(os.getenv("AGENTFLOW_MASTER_SECRET", "agentflow-final-secret").encode()).digest()
    )

fernet = Fernet(k())

def enc(v): return fernet.encrypt(v.encode()).decode()
def dec(v): return fernet.decrypt(v.encode()).decode()
def mask(v): return v[:6] + "..." + v[-4:] if v and len(v) > 12 else "***"

def con():
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
    c = con()
    c.execute("insert into audit values(?,?,?,?,?)", ("aud_" + uuid4().hex[:12], level, event, json.dumps(data or {}), now()))
    c.commit()
    c.close()

def save_secret(name, value):
    c = con()
    c.execute(
        "insert into secrets values(?,?,?,?) on conflict(name) do update set value=excluded.value,masked=excluded.masked,updated_at=excluded.updated_at",
        (name, enc(value), mask(value), now())
    )
    c.commit()
    c.close()
    audit("secret_saved", {"name": name, "masked": mask(value)})

def get_secret(name):
    if os.getenv(name):
        return os.getenv(name)
    c = con()
    r = c.execute("select value from secrets where name=?", (name,)).fetchone()
    c.close()
    if not r:
        return None
    try:
        return dec(r["value"])
    except Exception:
        return None

app = FastAPI(title="AgentFlow Relay Platinum", version="12.0.0")

class SecretIn(BaseModel): name: str; value: str
class UserIn(BaseModel): name: str; email: str
class AgentIn(BaseModel): name: str; endpoint: str = ""; platform: str = "webhook"; capabilities: list[str] = []
class WorkflowIn(BaseModel): name: str; description: str = ""; price: float = 29
class TaskIn(BaseModel): prompt: str; workflow_id: str | None = None
class CheckoutIn(BaseModel): name: str = "AgentFlow Workflow Automation"; amount_cents: int = 2900; currency: str = "cad"
class CommandIn(BaseModel): command: str

HTML = r'''
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>AgentFlow Relay Platinum</title>
<style>
:root{--bg:#06142d;--p:#08182f;--c:#071120;--b:#1f6feb;--a:#54d7ff;--t:#eef7ff;--m:#a9c8ff}
body.light{--bg:#f5f9ff;--p:#fff;--c:#eef6ff;--b:#2563eb;--a:#0891b2;--t:#07111f;--m:#3b516f}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,#123d8a,var(--bg) 42%,#020617);color:var(--t);font-family:Inter,Arial,sans-serif}
.hero{padding:26px;background:linear-gradient(135deg,#155dfcaa,#00c2ffaa,#02061733);border-bottom:1px solid var(--b)}
.top{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}h1{font-size:42px;margin:0}.sub{color:#dbeafe;max-width:900px}
button{border:0;border-radius:12px;padding:11px 15px;font-weight:800;background:linear-gradient(90deg,var(--b),var(--a));color:#031320;cursor:pointer;margin:4px}
button.alt{background:transparent;color:var(--a);border:1px solid var(--b)}
.tabs{display:flex;gap:8px;flex-wrap:wrap;padding:13px;background:#020617cc;border-bottom:1px solid var(--b);position:sticky;top:0;z-index:2}
.tab{border:1px solid var(--b);border-radius:999px;padding:10px 14px;color:var(--a);cursor:pointer}.tab.active{background:linear-gradient(90deg,var(--b),var(--a));color:#001528}
.page{display:none;padding:20px}.page.active{display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}
.card{background:linear-gradient(180deg,var(--p),var(--c));border:1px solid var(--b);border-radius:22px;padding:18px;box-shadow:0 0 25px #1f6feb33}h2{margin:0 0 12px;color:var(--a)}
input,textarea,select{width:100%;padding:13px;margin:6px 0;border-radius:12px;border:1px solid var(--b);background:#020617;color:#dbeafe}body.light input,body.light textarea,body.light select{background:white;color:#07111f}
textarea.big{min-height:220px}pre{background:#020617;border:1px solid #1d4ed8;border-radius:14px;padding:12px;white-space:pre-wrap;overflow:auto;min-height:160px;max-height:460px;color:#8cffd2}body.light pre{background:#eef6ff;color:#064e3b}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-top:18px}.kpi{background:#02061799;border:1px solid var(--b);border-radius:18px;padding:16px}.kv{font-size:34px;font-weight:900}.kt{color:var(--m);font-size:13px}
.creator{display:none}.creator.on{display:block}.badge{display:inline-block;border:1px solid var(--b);border-radius:999px;padding:7px 10px;margin:4px;color:var(--a);font-size:12px}
</style></head><body>
<div class="hero"><div class="top"><div><h1>AgentFlow Relay Platinum</h1><div class="sub">AI workforce OS: workflow studio, agent execution, Stripe revenue, Telegram mini app, SDK licensing, logs, diagnostics, enterprise buyer demo.</div><span class="badge">Blue Enterprise UI</span><span class="badge">Light/Dark</span><span class="badge">Creator Controls</span><span class="badge">Real Integrations</span></div><div><button onclick="theme('light')">Light</button><button onclick="theme('dark')">Dark</button><button onclick="creator()">Creator</button></div></div>
<div class="kpis"><div class="kpi"><div class="kt">Runtime</div><div class="kv">LIVE</div></div><div class="kpi"><div class="kt">Revenue</div><div class="kv" id="revk">0</div></div><div class="kpi"><div class="kt">Agents</div><div class="kv" id="agk">0</div></div><div class="kpi"><div class="kt">Tasks</div><div class="kv" id="tsk">0</div></div></div></div>
<div class="tabs"><div class="tab active" onclick="pg('operator',this)">Agent Operator</div><div class="tab" onclick="pg('settings',this)">Settings</div><div class="tab" onclick="pg('studio',this)">Workflow Studio</div><div class="tab" onclick="pg('revenue',this)">Revenue</div><div class="tab" onclick="pg('telegram',this)">Telegram</div><div class="tab creator" onclick="pg('creatorpage',this)">Creator Metrics</div><div class="tab" onclick="pg('logs',this)">Logs</div><div class="tab" onclick="pg('enterprise',this)">Enterprise Pitch</div></div>

<section id="operator" class="page active"><div class="grid"><div class="card" style="grid-column:1/-1"><h2>Main Agent Command Center</h2><textarea id="agent_prompt" class="big" placeholder="Ask the agent to create workflows, run tasks, diagnose, generate revenue actions, draft outreach, create SDK plan..."></textarea><button onclick="agentChat()">Run Agent</button><button class="alt" onclick="quick('diagnose')">Diagnose</button><button class="alt" onclick="quick('revenue')">Revenue Plan</button><button class="alt" onclick="quick('create workflow: AI lead generation')">Create Workflow</button><pre id="agent_out"></pre></div></div></section>

<section id="settings" class="page"><div class="grid"><div class="card"><h2>Secure Key Vault</h2><select id="sname"><option>STRIPE_SECRET_KEY</option><option>TELEGRAM_BOT_TOKEN</option><option>SUPABASE_URL</option><option>SUPABASE_SERVICE_ROLE_KEY</option><option>OPENAI_API_KEY</option><option>GROQ_API_KEY</option><option>GEMINI_API_KEY</option><option>OPENROUTER_API_KEY</option></select><input id="svalue" placeholder="Paste key once"><button onclick="saveKey()">Save Key</button><button class="alt" onclick="secretStatus()">Status</button><pre id="secret_out"></pre></div><div class="card"><h2>Integration Tests</h2><button onclick="telegramTest()">Test Telegram</button><button onclick="telegramWebhook()">Set Webhook</button><button onclick="supabaseCheck()">Check Supabase</button><button onclick="diag()">Diagnostics</button><pre id="integration_out"></pre></div></div></section>

<section id="studio" class="page"><div class="grid"><div class="card"><h2>Register Agent</h2><input id="aname" placeholder="Agent name"><input id="endpoint" placeholder="Webhook/API endpoint"><input id="caps" placeholder="browser,email,research,telegram"><button onclick="createAgent()">Register Agent</button><pre id="agent_reg_out"></pre></div><div class="card"><h2>Create Sellable Workflow</h2><input id="wname" placeholder="Workflow name"><textarea id="wdesc" placeholder="Workflow description"></textarea><input id="price" value="29"><button onclick="createWorkflow()">Create Workflow</button><pre id="workflow_out"></pre></div><div class="card"><h2>Run Task</h2><textarea id="task_prompt" class="big">Find AI startup leads, summarize, and draft outreach.</textarea><button onclick="runTask()">Execute Task</button><pre id="task_out"></pre></div></div></section>

<section id="revenue" class="page"><div class="grid"><div class="card"><h2>Stripe Checkout</h2><input id="product" value="AgentFlow Workflow Automation"><input id="amount" value="2900"><button onclick="checkout()">Generate Checkout</button><pre id="stripe_out"></pre></div><div class="card"><h2>Revenue Actions</h2><button onclick="revenuePlan()">Generate Revenue Plan</button><pre id="revenue_out"></pre></div></div></section>

<section id="telegram" class="page"><div class="grid"><div class="card"><h2>Telegram Commands</h2><pre>/start
/status
/metrics
/diagnostics
/revenue
/task your task
/workflow workflow name</pre></div><div class="card"><h2>MiniApp Controls</h2><button onclick="telegramTest()">Test Bot</button><button onclick="telegramWebhook()">Set Webhook</button><pre id="tg_out"></pre></div></div></section>

<section id="creatorpage" class="page creator"><div class="grid"><div class="card"><h2>Creator Metrics</h2><button onclick="metrics()">Refresh</button><pre id="metrics_out"></pre></div><div class="card"><h2>Real User Value</h2><pre>Creator-only:
- workflow sales
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
3. Prove repeat task execution
4. Show SDK endpoint usage
5. Show Telegram retention
6. Present enterprise demo metrics</pre></div></div></section>

<script>
function theme(m){document.body.classList.toggle('light',m==='light');localStorage.setItem('theme',m)}
if(localStorage.getItem('theme')==='light')document.body.classList.add('light')
function creator(){document.querySelectorAll('.creator').forEach(x=>x.classList.toggle('on'))}
function pg(id,el){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');el.classList.add('active')}
async function api(p,m='GET',b=null){let r=await fetch(p,{method:m,headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):null});return await r.json()}
function show(id,d){document.getElementById(id).textContent=JSON.stringify(d,null,2)}
async function metrics(){let r=await api('/platform/metrics');show('metrics_out',r);agk.innerText=r.agents;tsk.innerText=r.tasks;revk.innerText=r.revenue}
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
async function agentChat(){show('agent_out',await api('/platform/agent-chat','POST',{prompt:agent_prompt.value||'status'}));metrics()}
async function quick(x){agent_prompt.value=x;agentChat()}
metrics()
</script></body></html>
'''

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def ui(): return HTML

@app.head("/")
def head(): return {}

@app.get("/health")
def health(): return {"ok": True, "service": "agentflow-relay", "version": "12.0.0"}

@app.post("/platform/secrets")
def post_secret(s: SecretIn):
    if not s.name or not s.value:
        return {"ok": False, "error": "name and value required"}
    save_secret(s.name, s.value)
    return {"ok": True, "name": s.name, "masked": mask(s.value), "full_value_returned": False}

@app.get("/platform/secrets")
def list_secrets():
    env_names = ["STRIPE_SECRET_KEY","TELEGRAM_BOT_TOKEN","SUPABASE_URL","SUPABASE_SERVICE_ROLE_KEY","OPENAI_API_KEY","GROQ_API_KEY","GEMINI_API_KEY","OPENROUTER_API_KEY"]
    c = con()
    rows = [dict(x) for x in c.execute("select name,masked,updated_at from secrets order by name").fetchall()]
    c.close()
    present = {r["name"] for r in rows}
    for n in env_names:
        if os.getenv(n) and n not in present:
            rows.append({"name": n, "masked": mask(os.getenv(n)), "updated_at": "render_env"})
    return {"secrets": rows, "full_values_returned": False}

@app.get("/platform/metrics")
def metrics():
    c = con()
    out = {}
    for t in ["users","agents","workflows","tasks","audit","revenue"]:
        out[t] = c.execute(f"select count(*) n from {t}").fetchone()["n"]
    c.close()
    out["runtime"] = "LIVE"
    return out

@app.post("/platform/users")
def users(u: UserIn):
    uid="usr_"+uuid4().hex[:12]; ak="afr_"+uuid4().hex
    c=con(); c.execute("insert into users values(?,?,?,?,?)",(uid,u.name,u.email,ak,now())); c.commit(); c.close()
    audit("user_created",{"id":uid,"email":u.email})
    return {"id":uid,"name":u.name,"email":u.email,"api_key_masked":mask(ak)}

@app.post("/platform/agents")
def agents(a: AgentIn):
    aid="agt_"+uuid4().hex[:12]
    c=con()
    c.execute("insert into agents(id,name,endpoint,platform,capabilities,status,created_at) values(?,?,?,?,?,?,?)",(aid,a.name,a.endpoint,a.platform,json.dumps(a.capabilities),"registered",now()))
    c.commit(); c.close()
    audit("agent_registered",{"id":aid,"name":a.name})
    return {"ok":True,"id":aid,"status":"registered","role":"executor"}

@app.post("/platform/workflows")
def workflows(w: WorkflowIn):
    wid="wfl_"+uuid4().hex[:12]
    c=con()
    c.execute("insert into workflows(id,name,description,price,status,created_at) values(?,?,?,?,?,?)",(wid,w.name,w.description,w.price,"sellable",now()))
    c.commit(); c.close()
    audit("workflow_created",{"id":wid,"name":w.name,"price":w.price})
    return {"ok":True,"id":wid,"status":"sellable","role":"monetizable process"}

@app.post("/platform/tasks")
def tasks(t: TaskIn):
    if not t.prompt.strip(): return {"ok":False,"error":"prompt required"}
    tid="tsk_"+uuid4().hex[:12]
    result={"summary":"Task accepted into execution pipeline.","next_actions":["match capability","route to agent","execute","audit result"]}
    c=con()
    c.execute("insert into tasks(id,prompt,status,result,created_at) values(?,?,?,?,?)",(tid,t.prompt,"accepted",json.dumps(result),now()))
    c.commit(); c.close()
    audit("task_created",{"id":tid,"prompt":t.prompt[:120]})
    return {"ok":True,"id":tid,"status":"accepted","result":result}

@app.post("/platform/agent-chat")
async def agent_chat(t: TaskIn):
    prompt=t.prompt.strip()
    if not prompt: return {"ok":False,"error":"prompt required"}
    low=prompt.lower()
    if low in ["diagnose","diagnostics","status","are you alive","hi are you alive?"]:
        return {"ok":True,"agent":"online","diagnostics":diagnostics(),"message":"AgentFlow Relay is live and ready."}
    if low.startswith("create workflow:"):
        return workflows(WorkflowIn(name=prompt.split(":",1)[1].strip(),description="Created from Agent Command Center",price=29))
    if low.startswith("run task:"):
        return tasks(TaskIn(prompt=prompt.split(":",1)[1].strip()))
    if low=="revenue":
        return revenue()
    key=get_secret("OPENAI_API_KEY")
    if key:
        async with httpx.AsyncClient(timeout=30) as client:
            r=await client.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":"Bearer "+key},json={"model":"gpt-4o-mini","messages":[{"role":"system","content":"You are AgentFlow Relay operator. Return concise execution plan and next actions."},{"role":"user","content":prompt}]})
        audit("agent_ai_response",{"status":r.status_code})
        return r.json()
    return {"ok":True,"mode":"local_operator","response":{"interpretation":prompt,"next_actions":["Create workflow if sellable","Register agent if execution endpoint exists","Generate checkout if customer-ready","Run task and inspect logs"],"command_examples":["create workflow: Lead generation","run task: Find 10 prospects","diagnose","revenue"]}}

@app.get("/platform/logs")
def logs(level: str = "info"):
    c=con()
    rows=[dict(x) for x in c.execute("select * from audit where level=? order by rowid desc limit 100",(level,)).fetchall()]
    c.close()
    return {"logs":rows}

@app.get("/platform/diagnostics")
def diagnostics():
    d={"stripe":bool(get_secret("STRIPE_SECRET_KEY")),"telegram":bool(get_secret("TELEGRAM_BOT_TOKEN")),"supabase_url":bool(get_secret("SUPABASE_URL")),"supabase_service_key":bool(get_secret("SUPABASE_SERVICE_ROLE_KEY")),"openai":bool(get_secret("OPENAI_API_KEY")),"runtime":"healthy"}
    audit("diagnostics_run",d)
    return d

@app.get("/platform/revenue")
def revenue():
    return {"revenue_streams":["Stripe checkout","workflow subscription","agency setup","enterprise pilot","SDK licensing","Telegram operator access"],"best_next_actions":["Create one clear workflow offer","Generate Stripe checkout","Sell one paid test","Run task","Use logs as proof","Pitch SDK/enterprise demo after usage data"]}

@app.post("/platform/command")
def command(c: CommandIn):
    txt=c.command.strip()
    if txt.lower()=="diagnose": return diagnostics()
    if txt.lower()=="revenue": return revenue()
    if txt.lower().startswith("create workflow:"):
        return workflows(WorkflowIn(name=txt.split(":",1)[1].strip(),description="Created from command palette",price=29))
    if txt.lower().startswith("run task:"):
        return tasks(TaskIn(prompt=txt.split(":",1)[1].strip()))
    return {"ok":True,"executed":txt,"available":["diagnose","revenue","create workflow: <name>","run task: <prompt>"]}

@app.get("/platform/supabase/check")
async def supabase_check():
    url=get_secret("SUPABASE_URL"); key=get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key: return {"ok":False,"message":"Supabase URL/service key missing"}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.get(url.rstrip()+"/rest/v1/",headers={"apikey":key,"Authorization":"Bearer "+key})
    audit("supabase_checked",{"status":r.status_code})
    return {"ok":r.status_code<500,"status":r.status_code}

@app.post("/platform/stripe/checkout")
async def stripe_checkout(c: CheckoutIn):
    sk=get_secret("STRIPE_SECRET_KEY")
    if not sk: return {"ok":False,"message":"Stripe key missing"}
    data={"mode":"payment","success_url":"https://agentflow-relay.onrender.com/ui?paid=1","cancel_url":"https://agentflow-relay.onrender.com/ui?cancel=1","line_items[0][quantity]":"1","line_items[0][price_data][currency]":c.currency.lower(),"line_items[0][price_data][unit_amount]":str(c.amount_cents),"line_items[0][price_data][product_data][name]":c.name}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post("https://api.stripe.com/v1/checkout/sessions",auth=(sk,""),data=data)
    body=r.json()
    cdb=con(); cdb.execute("insert into revenue values(?,?,?,?,?,?)",("rev_"+uuid4().hex[:12],"stripe_checkout",c.amount_cents/100,"created" if r.status_code<300 else "error",json.dumps(body),now())); cdb.commit(); cdb.close()
    audit("stripe_checkout",{"status":r.status_code,"amount":c.amount_cents})
    return body

@app.get("/platform/telegram/test")
async def telegram_test():
    token=get_secret("TELEGRAM_BOT_TOKEN")
    if not token: return {"ok":False,"message":"Telegram token missing"}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.get(f"https://api.telegram.org/bot{token}/getMe")
    audit("telegram_test",{"status":r.status_code})
    return r.json()

@app.post("/platform/telegram/webhook")
async def telegram_webhook():
    token=get_secret("TELEGRAM_BOT_TOKEN")
    if not token: return {"ok":False,"message":"Telegram token missing"}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post(f"https://api.telegram.org/bot{token}/setWebhook",json={"url":"https://agentflow-relay.onrender.com/platform/telegram/update"})
    audit("telegram_webhook",{"status":r.status_code})
    return r.json()

@app.post("/platform/telegram/update")
async def telegram_update(request: Request):
    update=await request.json()
    token=get_secret("TELEGRAM_BOT_TOKEN")
    msg=update.get("message",{})
    chat_id=msg.get("chat",{}).get("id")
    text=msg.get("text","")
    reply="AgentFlow Relay Platinum online. Commands: /metrics /diagnostics /revenue /task <prompt> /workflow <name>"
    if text.startswith("/metrics"): reply=json.dumps(metrics())
    elif text.startswith("/diagnostics"): reply=json.dumps(diagnostics())
    elif text.startswith("/revenue"): reply=json.dumps(revenue())
    elif text.startswith("/task "): reply=json.dumps(tasks(TaskIn(prompt=text.replace("/task ","",1))))
    elif text.startswith("/workflow "): reply=json.dumps(workflows(WorkflowIn(name=text.replace("/workflow ","",1),description="Created from Telegram",price=29)))
    audit("telegram_update",{"text":text[:120]})
    if token and chat_id:
        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(f"https://api.telegram.org/bot{token}/sendMessage",json={"chat_id":chat_id,"text":reply[:3900]})
    return {"ok":True}

@app.get("/demo/enterprise")
def demo():
    return {"platform":"AgentFlow Relay Platinum","status":"enterprise-demo-ready","value":["AI workflow orchestration","agent execution","Stripe monetization","Telegram operations","SDK/API distribution","audit and diagnostics"]}


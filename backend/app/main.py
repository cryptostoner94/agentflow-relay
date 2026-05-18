import os, json, sqlite3, base64, hashlib, httpx
from uuid import uuid4
from datetime import datetime
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DB="backend/app/data/agentflow.sqlite3"
os.makedirs("backend/app/data", exist_ok=True)

def now(): return datetime.utcnow().isoformat()
def key():
    return base64.urlsafe_b64encode(hashlib.sha256(os.getenv("AGENTFLOW_MASTER_SECRET","agentflow-secret").encode()).digest())
fernet=Fernet(key())
def enc(v): return fernet.encrypt(v.encode()).decode()
def dec(v): return fernet.decrypt(v.encode()).decode()
def mask(v): return v[:6]+"..."+v[-4:] if v and len(v)>12 else "***"

def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    con.execute("create table if not exists secrets(name text primary key,value text,masked text,updated_at text)")
    con.execute("create table if not exists users(id text primary key,name text,email text,api_key text,created_at text)")
    con.execute("create table if not exists agents(id text primary key,name text,endpoint text,capabilities text,status text,created_at text)")
    con.execute("create table if not exists workflows(id text primary key,name text,description text,price real,status text,created_at text)")
    con.execute("create table if not exists tasks(id text primary key,prompt text,status text,result text,created_at text)")
    con.execute("create table if not exists audit(id text primary key,event text,data text,created_at text)")
    con.commit(); return con

def audit(event,data=None):
    con=db()
    con.execute("insert into audit values(?,?,?,?)",("aud_"+uuid4().hex[:12],event,json.dumps(data or {}),now()))
    con.commit(); con.close()

def get_secret(name):
    con=db(); row=con.execute("select value from secrets where name=?",(name,)).fetchone(); con.close()
    return dec(row["value"]) if row else None

app=FastAPI(title="AgentFlow Relay Platinum",version="8.0.0")

class SecretIn(BaseModel): name:str; value:str
class UserIn(BaseModel): name:str; email:str
class AgentIn(BaseModel): name:str; endpoint:str=""; capabilities:list[str]=[]
class WorkflowIn(BaseModel): name:str; description:str=""; price:float=0
class TaskIn(BaseModel): prompt:str
class CheckoutIn(BaseModel): name:str="AgentFlow Workflow"; amount_cents:int=2900; currency:str="cad"

HTML="""
<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>AgentFlow Relay Platinum</title>
<style>
body{margin:0;background:#020617;color:white;font-family:Arial}
.hero{padding:42px;background:linear-gradient(135deg,#10b981,#0891b2,#020617)}h1{font-size:46px;margin:0}.sub{font-size:18px;color:#d1fae5}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px;padding:24px}
.card{background:#0f172a;border:1px solid #2dd4bf;border-radius:22px;padding:20px;box-shadow:0 0 30px rgba(45,212,191,.15)}
h2{color:#5eead4}button{background:#5eead4;color:#022c22;border:0;border-radius:12px;padding:12px 16px;font-weight:bold;margin:6px;cursor:pointer}
input,textarea,select{width:100%;background:#020617;color:#d1fae5;border:1px solid #155e75;border-radius:12px;padding:12px;margin:6px 0}
pre{background:#020617;color:#86efac;border:1px solid #164e63;border-radius:14px;padding:14px;min-height:170px;white-space:pre-wrap;overflow:auto}
</style></head><body>
<div class='hero'><h1>AgentFlow Relay Platinum</h1><div class='sub'>Secure key vault, Stripe checkout, Telegram webhook, Supabase check, workflows, agents, SDK, audit logs.</div></div>
<div class='grid'>
<div class='card'><h2>Secure Key Vault</h2><select id='sname'><option>STRIPE_SECRET_KEY</option><option>SUPABASE_URL</option><option>SUPABASE_SERVICE_ROLE_KEY</option><option>TELEGRAM_BOT_TOKEN</option><option>OPENAI_API_KEY</option><option>GROQ_API_KEY</option><option>GEMINI_API_KEY</option></select><input id='svalue' placeholder='Paste key once'><button onclick='secret()'>Save Key</button><button onclick='secrets()'>Status</button><pre id='secretout'></pre></div>
<div class='card'><h2>Stripe</h2><input id='product' value='AgentFlow Workflow Automation'><input id='amount' value='2900'><button onclick='checkout()'>Create Checkout Link</button><pre id='stripeout'></pre></div>
<div class='card'><h2>Telegram</h2><button onclick='tgtest()'>Test Bot</button><button onclick='tgwebhook()'>Set Webhook</button><pre id='tgout'></pre></div>
<div class='card'><h2>Supabase</h2><button onclick='supabase()'>Check Connection</button><pre id='dbout'></pre></div>
<div class='card'><h2>User</h2><input id='name' placeholder='Name'><input id='email' placeholder='Email'><button onclick='user()'>Create User</button><pre id='userout'></pre></div>
<div class='card'><h2>Agent</h2><input id='aname' placeholder='Agent name'><input id='endpoint' placeholder='Endpoint'><button onclick='agent()'>Register Agent</button><pre id='agentout'></pre></div>
<div class='card'><h2>Workflow</h2><input id='wname' placeholder='Workflow name'><textarea id='wdesc' placeholder='Description'></textarea><input id='price' value='29'><button onclick='workflow()'>Create Workflow</button><pre id='workflowout'></pre></div>
<div class='card'><h2>Task</h2><textarea id='prompt'>Find 5 remote jobs, adapt resume angle, draft outreach email.</textarea><button onclick='task()'>Run Task</button><pre id='taskout'></pre></div>
<div class='card'><h2>Metrics</h2><button onclick='metrics()'>Refresh</button><pre id='metrics'></pre></div>
<div class='card'><h2>Revenue Manual</h2><button onclick='revenue()'>Show</button><pre id='revout'></pre></div>
<div class='card'><h2>SDK</h2><button onclick='sdk()'>Show</button><pre id='sdkout'></pre></div>
<div class='card'><h2>Audit</h2><button onclick='auditlog()'>Show</button><pre id='auditout'></pre></div>
</div>
<script>
async function api(p,o={}){let r=await fetch(p,o);return await r.json()}function show(i,d){document.getElementById(i).textContent=JSON.stringify(d,null,2)}
async function secret(){show('secretout',await api('/platform/secrets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:sname.value,value:svalue.value})}));svalue.value=''}
async function secrets(){show('secretout',await api('/platform/secrets'))}
async function checkout(){show('stripeout',await api('/platform/stripe/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:product.value,amount_cents:Number(amount.value||2900)})}))}
async function tgtest(){show('tgout',await api('/platform/telegram/test'))}
async function tgwebhook(){show('tgout',await api('/platform/telegram/webhook',{method:'POST'}))}
async function supabase(){show('dbout',await api('/platform/supabase/check'))}
async function user(){show('userout',await api('/platform/users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name.value||'Creator',email:email.value||'creator@example.com'})}))}
async function agent(){show('agentout',await api('/platform/agents',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:aname.value||'Agent',endpoint:endpoint.value})}))}
async function workflow(){show('workflowout',await api('/platform/workflows',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:wname.value||'Workflow',description:wdesc.value||'Automation workflow',price:Number(price.value||29)})}))}
async function task(){show('taskout',await api('/platform/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:prompt.value})}))}
async function metrics(){show('metrics',await api('/platform/metrics'))}
async function revenue(){show('revout',await api('/platform/revenue'))}
async function sdk(){show('sdkout',await api('/platform/sdk'))}
async function auditlog(){show('auditout',await api('/platform/audit'))}
metrics();secrets()
</script></body></html>
"""

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def ui(): return HTML

@app.head("/")
def head_root(): return {}

@app.get("/health")
def health(): return {"ok":True,"service":"agentflow-relay","version":"8.0.0"}

@app.post("/platform/secrets")
def save_secret(s:SecretIn):
    con=db(); con.execute("insert into secrets values(?,?,?,?) on conflict(name) do update set value=excluded.value,masked=excluded.masked,updated_at=excluded.updated_at",(s.name,enc(s.value),mask(s.value),now())); con.commit(); con.close()
    audit("secret_saved",{"name":s.name,"masked":mask(s.value)})
    return {"saved":True,"name":s.name,"masked":mask(s.value),"full_value_returned":False}

@app.get("/platform/secrets")
def secrets():
    con=db(); rows=con.execute("select name,masked,updated_at from secrets order by name").fetchall(); con.close()
    return {"secrets":[dict(r) for r in rows],"full_values_returned":False}

@app.get("/platform/metrics")
def metrics():
    con=db(); out={}
    for t in ["users","agents","workflows","tasks","audit","secrets"]:
        out[t]=con.execute(f"select count(*) n from {t}").fetchone()["n"]
    con.close(); out["runtime"]="live"; out["fake_metrics"]=False
    return out

@app.post("/platform/users")
def users(u:UserIn):
    uid="usr_"+uuid4().hex[:12]; key="afr_"+uuid4().hex
    con=db(); con.execute("insert into users values(?,?,?,?,?)",(uid,u.name,u.email,key,now())); con.commit(); con.close()
    audit("user_created",{"id":uid,"email":u.email})
    return {"id":uid,"name":u.name,"email":u.email,"api_key_masked":mask(key)}

@app.post("/platform/agents")
def agents(a:AgentIn):
    aid="agt_"+uuid4().hex[:12]
    con=db(); con.execute("insert into agents values(?,?,?,?,?,?)",(aid,a.name,a.endpoint,json.dumps(a.capabilities),"registered",now())); con.commit(); con.close()
    audit("agent_registered",{"id":aid,"name":a.name})
    return {"id":aid,"name":a.name,"status":"registered"}

@app.post("/platform/workflows")
def workflows(w:WorkflowIn):
    wid="wfl_"+uuid4().hex[:12]
    con=db(); con.execute("insert into workflows values(?,?,?,?,?,?)",(wid,w.name,w.description,w.price,"sellable",now())); con.commit(); con.close()
    audit("workflow_created",{"id":wid,"name":w.name})
    return {"id":wid,"name":w.name,"price":w.price,"status":"sellable"}

@app.post("/platform/tasks")
def tasks(t:TaskIn):
    tid="tsk_"+uuid4().hex[:12]
    con=db(); con.execute("insert into tasks values(?,?,?,?,?)",(tid,t.prompt,"accepted","Task accepted into execution ledger.",now())); con.commit(); con.close()
    audit("task_created",{"id":tid})
    return {"id":tid,"status":"accepted","execution_path":["intake","route","execute","audit"],"prompt":t.prompt}

@app.get("/platform/audit")
def audit_view():
    con=db(); rows=con.execute("select * from audit order by rowid desc limit 80").fetchall(); con.close()
    return {"audit":[dict(r) for r in rows]}

@app.get("/platform/revenue")
def revenue():
    return {"revenue_streams":["Stripe workflow checkout","monthly automation retainer","SDK/API licensing","white-label deployments","Telegram operator access"],"first_money_path":["Save Stripe key","Create workflow","Create checkout link","Sell one customer","Run task","Use audit as proof"]}


@app.get("/platform/sdk")
def sdk():
    return {
        "python": "from agentflow_relay import AgentFlowClient\nclient = AgentFlowClient('https://agentflow-relay.onrender.com')\nclient.create_task('run workflow')",
        "curl": "curl -X POST https://agentflow-relay.onrender.com/platform/tasks -H 'Content-Type: application/json' -d '{\"prompt\":\"run workflow\"}'",
        "base_url": "https://agentflow-relay.onrender.com",
        "endpoints": [
            "/health",
            "/ui",
            "/platform/secrets",
            "/platform/stripe/checkout",
            "/platform/telegram/test",
            "/platform/telegram/webhook",
            "/platform/supabase/check",
            "/platform/users",
            "/platform/agents",
            "/platform/workflows",
            "/platform/tasks",
            "/platform/metrics",
            "/platform/audit"
        ]
    }

@app.get("/platform/supabase/check")
async def supabase_check():
    url=get_secret("SUPABASE_URL"); key=get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key: return {"ok":False,"message":"Save SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first."}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.get(url.rstrip()+"/rest/v1/",headers={"apikey":key,"Authorization":"Bearer "+key})
    return {"ok":r.status_code<500,"status":r.status_code}

@app.post("/platform/stripe/checkout")
async def stripe_checkout(c:CheckoutIn):
    sk=get_secret("STRIPE_SECRET_KEY")
    if not sk: return {"ok":False,"message":"Save STRIPE_SECRET_KEY first."}
    data={"mode":"payment","success_url":"https://agentflow-relay.onrender.com/ui?paid=1","cancel_url":"https://agentflow-relay.onrender.com/ui?cancel=1","line_items[0][quantity]":"1","line_items[0][price_data][currency]":c.currency,"line_items[0][price_data][unit_amount]":str(c.amount_cents),"line_items[0][price_data][product_data][name]":c.name}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post("https://api.stripe.com/v1/checkout/sessions",auth=(sk,""),data=data)
    return r.json()

@app.get("/platform/telegram/test")
async def telegram_test():
    token=get_secret("TELEGRAM_BOT_TOKEN")
    if not token: return {"ok":False,"message":"Save TELEGRAM_BOT_TOKEN first."}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.get(f"https://api.telegram.org/bot{token}/getMe")
    return r.json()

@app.post("/platform/telegram/webhook")
async def telegram_webhook():
    token=get_secret("TELEGRAM_BOT_TOKEN")
    if not token: return {"ok":False,"message":"Save TELEGRAM_BOT_TOKEN first."}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post(f"https://api.telegram.org/bot{token}/setWebhook",json={"url":"https://agentflow-relay.onrender.com/platform/telegram/update"})
    return r.json()

@app.post("/platform/telegram/update")
async def telegram_update(request:Request):
    update=await request.json(); audit("telegram_update",update); return {"ok":True}

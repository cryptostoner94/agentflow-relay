from datetime import datetime
from uuid import uuid4
from cryptography.fernet import Fernet
import base64, hashlib, os, httpx

USERS={}
AGENTS={}
WORKFLOWS={}
TASKS={}
AUDIT=[]
LOCAL_SECRETS={}
LOCAL_SECRET_KEY=Fernet.generate_key()
FERNET=Fernet(LOCAL_SECRET_KEY)

def now():
    return datetime.utcnow().isoformat()

def audit(event, data=None):
    item={"id":"aud_"+uuid4().hex[:12],"event":event,"data":data or {},"created_at":now()}
    AUDIT.append(item)
    return item

def mask(v):
    if not v:
        return None
    return v[:6]+"..." + v[-4:] if len(v) > 12 else "***"

def enc(v):
    return FERNET.encrypt(v.encode()).decode()

def dec(v):
    return FERNET.decrypt(v.encode()).decode()

def supabase_headers(url,key):
    return {"apikey":key,"Authorization":f"Bearer {key}","Content-Type":"application/json","Prefer":"return=representation"}

async def supabase_request(method, url, key, path, json=None):
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.request(method, f"{url.rstrip('/')}/rest/v1/{path}", headers=supabase_headers(url,key), json=json)
        return {"status":r.status_code,"ok":r.status_code<300,"text":r.text}

async def save_secret(name,value):
    LOCAL_SECRETS[name]=enc(value)
    audit("secret_saved",{"name":name,"masked":mask(value)})
    sb_url = get_secret_plain("SUPABASE_URL")
    sb_key = get_secret_plain("SUPABASE_SERVICE_ROLE_KEY")
    if sb_url and sb_key and name not in ["SUPABASE_URL","SUPABASE_SERVICE_ROLE_KEY"]:
        row={"name":name,"value_encrypted":LOCAL_SECRETS[name],"masked_value":mask(value),"updated_at":now()}
        await supabase_request("POST",sb_url,sb_key,"agentflow_secrets",row)
    return {"name":name,"masked":mask(value),"saved":True}

def get_secret_plain(name):
    v=LOCAL_SECRETS.get(name)
    if not v:
        return None
    try:
        return dec(v)
    except Exception:
        return None

def secret_status():
    return {k:{"configured":True,"masked":mask(get_secret_plain(k))} for k in LOCAL_SECRETS.keys()}

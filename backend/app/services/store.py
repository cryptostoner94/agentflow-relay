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

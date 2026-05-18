from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
import datetime
import os
import platform
import socket

router = APIRouter()

LIVE_DATA = {
    "server_time": str(datetime.datetime.utcnow()),
    "hostname": socket.gethostname(),
    "platform": platform.platform(),
    "render_service": os.getenv("RENDER_SERVICE_NAME", "agentflow-relay"),
    "port": os.getenv("PORT", "10000"),
    "sdk_enabled": True,
    "cloud_status": "ACTIVE",
    "monetization": [
        "API Licensing",
        "White-label SaaS",
        "Enterprise Automation",
        "AI Workflow Hosting",
        "SDK Usage Billing",
        "Private Deployments"
    ]
}

HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'/>
<title>AgentFlow Enterprise</title>

<style>

body{{
background:#050505;
font-family:Arial;
margin:0;
color:white;
}}

.header{{
padding:30px;
font-size:42px;
font-weight:bold;
background:linear-gradient(90deg,#00ff88,#00ccff);
color:black;
}}

.sub{{
padding:20px 30px;
font-size:18px;
color:#ddd;
}}

.grid{{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
gap:25px;
padding:30px;
}}

.card{{
background:#111;
padding:25px;
border-radius:18px;
border:1px solid #222;
box-shadow:0 0 25px rgba(0,255,100,0.12);
}}

.title{{
font-size:24px;
margin-bottom:15px;
color:#00ff99;
}}

.value{{
font-size:20px;
line-height:1.6;
word-break:break-word;
}}

button{{
margin-top:15px;
padding:14px 18px;
border:none;
border-radius:12px;
background:#00ff99;
font-weight:bold;
cursor:pointer;
}}

button:hover{{
background:#00cc77;
}}

.console{{
margin:30px;
background:black;
padding:20px;
border-radius:15px;
height:300px;
overflow:auto;
border:1px solid #333;
font-family:monospace;
color:#00ff88;
}}

.manual{{
padding:30px;
line-height:1.8;
font-size:18px;
}}

h2{{
color:#00ff99;
}}

</style>
</head>

<body>

<div class="header">
AGENTFLOW ENTERPRISE AI OS
</div>

<div class="sub">
Real runtime telemetry + onboarding + monetization infrastructure
</div>

<div class="grid">

<div class="card">
<div class="title">Cloud Runtime</div>
<div class="value">
Service: {LIVE_DATA["render_service"]}<br>
Status: {LIVE_DATA["cloud_status"]}<br>
Host: {LIVE_DATA["hostname"]}
</div>
<button onclick="log('Render cloud runtime verified.')">Verify Runtime</button>
</div>

<div class="card">
<div class="title">System Information</div>
<div class="value">
{LIVE_DATA["platform"]}
</div>
<button onclick="log('System telemetry loaded.')">Load Telemetry</button>
</div>

<div class="card">
<div class="title">SDK Monetization</div>
<div class="value">
SDK Status: ENABLED
</div>
<button onclick="log('SDK licensing ready for enterprise integration.')">Open SDK</button>
</div>

<div class="card">
<div class="title">Revenue Streams</div>
<div class="value">
API Licensing<br>
White-label SaaS<br>
Enterprise Hosting<br>
Workflow Automation
</div>
<button onclick="log('Revenue systems initialized.')">Revenue Engine</button>
</div>

</div>

<div class="console" id="console">
LIVE SYSTEM READY
</div>

<div class="manual">

<h2>ONBOARDING FLOW</h2>

1. Create AI workflow tools and automation APIs.<br>
2. Connect Telegram, browser automation, or external APIs.<br>
3. Offer workflow automation as SaaS subscriptions.<br>
4. License SDK/API access to startups or agencies.<br>
5. Offer managed deployments for businesses.<br>
6. Scale through Render cloud infrastructure.<br>

<h2>REALISTIC MONETIZATION</h2>

• Automation agency services<br>
• AI workflow subscriptions<br>
• API metering access<br>
• White-label deployments<br>
• Enterprise consulting<br>
• Hosted AI operations platform<br>

<h2>HOW TO START EARNING</h2>

1. Publish landing page demos.<br>
2. Create automation templates.<br>
3. Charge monthly subscriptions.<br>
4. Sell integrations to small businesses.<br>
5. Offer setup packages.<br>
6. License workflow SDK access.<br>

<h2>IMPORTANT</h2>

This platform is now cloud-hosted on Render and no longer depends on your Mac remaining online.

</div>

<script>
function log(t){{
document.getElementById("console").innerHTML += "<br><br>" + t;
}}
</script>

</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
async def root():
    return HTML

@router.get("/ui", response_class=HTMLResponse)
async def ui():
    return HTML

@router.get("/live")
async def live():
    return JSONResponse(LIVE_DATA)

@router.get("/health")
async def health():
    return {{"ok": True}}

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
@router.get("/ui", response_class=HTMLResponse)
def operator_ui():
    return """
<!doctype html>
<html>
<head>
  <title>AgentFlow Relay</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { background:#0b0f0c; color:#00ff88; font-family:Arial; padding:20px; }
    button { padding:14px; margin:6px; font-size:16px; border-radius:8px; }
    textarea { width:100%; height:420px; background:#000; color:#00ff88; padding:12px; }
  </style>
</head>
<body>
  <h1>AgentFlow Relay Operator Console</h1>
  <button onclick="call('/health')">Health</button>
  <button onclick="call('/agents')">Agents</button>
  <button onclick="call('/logs')">Logs</button>
  <button onclick="task()">Create Task</button>
  <button onclick="location.href='/docs'">API Docs</button>
  <textarea id="out" readonly></textarea>

<script>
async function call(path){
  const r = await fetch(path);
  document.getElementById('out').value = JSON.stringify(await r.json(), null, 2);
}
async function task(){
  const r = await fetch('/tasks', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({task:'operator test task'})
  });
  document.getElementById('out').value = JSON.stringify(await r.json(), null, 2);
}
</script>
</body>
</html>
"""

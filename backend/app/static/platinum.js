async function api(path, method="GET", body=null){
  const r = await fetch(path,{
    method,
    headers:{"Content-Type":"application/json"},
    body: body ? JSON.stringify(body):null
  });
  return await r.json();
}

document.body.innerHTML = `
<div style="background:#050816;color:#dff;padding:20px;font-family:Arial;min-height:100vh">
<h1 style="font-size:52px;margin-bottom:10px;background:linear-gradient(90deg,#7cf,#7f7);-webkit-background-clip:text;color:transparent">
AGENTFLOW RELAY PLATINUM
</h1>

<p style="font-size:18px;color:#9fe">
Production AI orchestration + monetization + enterprise workflow platform
</p>

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px;margin-top:30px">

<div style="border:1px solid #2ff;padding:20px;border-radius:18px;background:#0a1228">
<h2>Stripe</h2>
<input id="stripe" placeholder="sk_live or sk_test key"
style="width:100%;padding:14px;margin-top:10px;background:black;color:#0f0;border:1px solid #2ff;border-radius:10px">
<button onclick="saveKey('STRIPE_SECRET_KEY','stripe')" style="margin-top:15px;padding:12px 20px">Save Stripe Key</button>
<div id="stripe_result"></div>
</div>

<div style="border:1px solid #2ff;padding:20px;border-radius:18px;background:#0a1228">
<h2>Telegram</h2>
<input id="telegram" placeholder="Telegram Bot Token"
style="width:100%;padding:14px;margin-top:10px;background:black;color:#0f0;border:1px solid #2ff;border-radius:10px">
<button onclick="saveKey('TELEGRAM_BOT_TOKEN','telegram')" style="margin-top:15px;padding:12px 20px">Save Telegram Token</button>
<button onclick="testTelegram()" style="margin-top:15px;padding:12px 20px">Test Telegram</button>
<div id="telegram_result"></div>
</div>

<div style="border:1px solid #2ff;padding:20px;border-radius:18px;background:#0a1228">
<h2>Supabase</h2>
<input id="supabase_url" placeholder="Supabase URL"
style="width:100%;padding:14px;margin-top:10px;background:black;color:#0f0;border:1px solid #2ff;border-radius:10px">

<input id="supabase_key" placeholder="Supabase Service Key"
style="width:100%;padding:14px;margin-top:10px;background:black;color:#0f0;border:1px solid #2ff;border-radius:10px">

<button onclick="saveSupabase()" style="margin-top:15px;padding:12px 20px">Save Supabase</button>
<div id="supabase_result"></div>
</div>

<div style="border:1px solid #2ff;padding:20px;border-radius:18px;background:#0a1228">
<h2>Create Workflow</h2>

<input id="workflow_name" placeholder="Workflow name"
style="width:100%;padding:14px;margin-top:10px;background:black;color:#0f0;border:1px solid #2ff;border-radius:10px">

<textarea id="workflow_desc"
placeholder="Describe workflow"
style="width:100%;height:120px;padding:14px;margin-top:10px;background:black;color:#0f0;border:1px solid #2ff;border-radius:10px"></textarea>

<button onclick="createWorkflow()" style="margin-top:15px;padding:12px 20px">Create Workflow</button>
<div id="workflow_result"></div>
</div>

<div style="border:1px solid #2ff;padding:20px;border-radius:18px;background:#0a1228">
<h2>Run AI Task</h2>

<textarea id="task_prompt"
placeholder="Find leads, generate workflow, summarize docs, etc"
style="width:100%;height:140px;padding:14px;margin-top:10px;background:black;color:#0f0;border:1px solid #2ff;border-radius:10px"></textarea>

<button onclick="runTask()" style="margin-top:15px;padding:12px 20px">Execute Task</button>

<pre id="task_result" style="margin-top:15px;color:#7f7;white-space:pre-wrap"></pre>
</div>

<div style="border:1px solid #2ff;padding:20px;border-radius:18px;background:#0a1228">
<h2>Revenue Engine</h2>

<button onclick="metrics()" style="padding:12px 20px">Refresh Metrics</button>

<pre id="metrics_result" style="margin-top:15px;color:#7f7;white-space:pre-wrap"></pre>
</div>

</div>
</div>
`;

async function saveKey(name,id){
  const value=document.getElementById(id).value;

  const r=await api("/platform/secrets","POST",{
    key:name,
    value:value
  });

  document.getElementById(id+"_result").innerText=
    JSON.stringify(r,null,2);
}

async function saveSupabase(){
  const url=document.getElementById("supabase_url").value;
  const key=document.getElementById("supabase_key").value;

  const r1=await api("/platform/secrets","POST",{
    key:"SUPABASE_URL",
    value:url
  });

  const r2=await api("/platform/secrets","POST",{
    key:"SUPABASE_SERVICE_KEY",
    value:key
  });

  document.getElementById("supabase_result").innerText=
    JSON.stringify({r1,r2},null,2);
}

async function testTelegram(){
  const r=await api("/platform/telegram/test");
  document.getElementById("telegram_result").innerText=
    JSON.stringify(r,null,2);
}

async function createWorkflow(){
  const r=await api("/platform/workflows","POST",{
    name:document.getElementById("workflow_name").value,
    description:document.getElementById("workflow_desc").value
  });

  document.getElementById("workflow_result").innerText=
    JSON.stringify(r,null,2);
}

async function runTask(){
  const r=await api("/platform/tasks","POST",{
    prompt:document.getElementById("task_prompt").value
  });

  document.getElementById("task_result").innerText=
    JSON.stringify(r,null,2);
}

async function metrics(){
  const r=await api("/platform/metrics");
  document.getElementById("metrics_result").innerText=
    JSON.stringify(r,null,2);
}

metrics();

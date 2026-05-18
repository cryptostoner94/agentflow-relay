#!/bin/bash

set -e

echo "======================================"
echo "AGENTFLOW RELAY OPERATOR STACK"
echo "======================================"

cd ~/agentflow-relay-project

# -----------------------------
# PYTHON ENV
# -----------------------------
python3 -m venv .venv || true

source .venv/bin/activate

# -----------------------------
# INSTALL BACKEND DEPENDENCIES
# -----------------------------
pip install --upgrade pip

pip install \
fastapi \
uvicorn \
pydantic \
pydantic-settings \
python-dotenv \
requests \
httpx \
redis \
pytest \
python-multipart \
jinja2 \
aiofiles \
websockets

# -----------------------------
# NODE CHECK
# -----------------------------
if ! command -v npm >/dev/null 2>&1; then
    echo ""
    echo "NodeJS missing."
    echo "Install from:"
    echo "https://nodejs.org"
    exit 1
fi

# -----------------------------
# FRONTEND INSTALL
# -----------------------------
cd frontend

npm install

cd ..

# -----------------------------
# SIMPLE CONTROL PANEL
# -----------------------------
cat > frontend/app/page.tsx <<'FRONTEND'
"use client";

import { useState } from "react";

export default function Home() {
  const [output, setOutput] = useState("");

  async function call(path: string, method = "GET") {
    const res = await fetch(`http://localhost:8000${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      body:
        method === "POST"
          ? JSON.stringify({ task: "operator test task" })
          : undefined,
    });

    const data = await res.json();

    setOutput(JSON.stringify(data, null, 2));
  }

  return (
    <main style={{
      padding: 30,
      fontFamily: "Arial",
      background: "#111",
      color: "#0f0",
      minHeight: "100vh"
    }}>
      <h1>AgentFlow Relay Operator Console</h1>

      <div style={{
        display: "flex",
        gap: 10,
        flexWrap: "wrap",
        marginTop: 20
      }}>
        <button onClick={() => call("/health")}>Health</button>
        <button onClick={() => call("/agents")}>Agents</button>
        <button onClick={() => call("/logs")}>Logs</button>
        <button onClick={() => call("/tasks", "POST")}>Create Task</button>
      </div>

      <textarea
        value={output}
        readOnly
        style={{
          width: "100%",
          height: "500px",
          marginTop: "20px",
          background: "#000",
          color: "#0f0",
          border: "1px solid #0f0",
          padding: "15px",
          fontSize: "14px"
        }}
      />
    </main>
  );
}
FRONTEND

# -----------------------------
# START BACKEND
# -----------------------------
echo ""
echo "Starting backend..."

env PYTHONPATH=backend \
python -m uvicorn app.main:app \
--host 0.0.0.0 \
--port 8000 \
> backend.log 2>&1 &

BACKEND_PID=$!

sleep 5

# -----------------------------
# START FRONTEND
# -----------------------------
echo ""
echo "Starting frontend..."

cd frontend

npm run dev > ../frontend.log 2>&1 &

FRONTEND_PID=$!

cd ..

sleep 10

# -----------------------------
# INSTALL CLOUDFLARE
# -----------------------------
if ! command -v cloudflared >/dev/null 2>&1; then
    brew install cloudflared
fi

# -----------------------------
# START TUNNEL
# -----------------------------
echo ""
echo "Starting secure tunnel..."

cloudflared tunnel --url http://localhost:3000 | tee cloudflare.log

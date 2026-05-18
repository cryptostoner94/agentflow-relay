from fastapi import APIRouter
from app.services.capability_discovery import discover_capabilities

router = APIRouter(prefix="/agents", tags=["agents"])
AGENTS: dict[str, dict] = {}

@router.post("")
async def register_agent(agent: dict):
    agent_id = agent.get("id") or f"agent_{len(AGENTS)+1}"
    agent["id"] = agent_id
    agent["capabilities"] = discover_capabilities(agent)
    AGENTS[agent_id] = agent
    return agent

@router.get("")
async def list_agents():
    return list(AGENTS.values())

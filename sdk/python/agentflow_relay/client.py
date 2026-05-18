import httpx

class AgentFlowClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
    async def create_task(self, source_platform: str, user_ref: str, text: str):
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}/tasks", json={"source_platform": source_platform, "user_ref": user_ref, "text": text})
            r.raise_for_status()
            return r.json()

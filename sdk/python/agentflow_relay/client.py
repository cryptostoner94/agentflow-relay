import requests

class AgentFlowClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health(self):
        return requests.get(f"{self.base_url}/health").json()

    def create_task(self, task: str):
        return requests.post(f"{self.base_url}/operator/task", json={"task": task}).json()

    def register_agent(self, name: str, url: str):
        return requests.post(f"{self.base_url}/operator/register-agent", json={"name": name, "url": url}).json()

    def agents(self):
        return requests.get(f"{self.base_url}/operator/agents").json()

    def revenue(self):
        return requests.get(f"{self.base_url}/operator/revenue").json()

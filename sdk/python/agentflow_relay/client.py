import requests
class AgentFlowClient:
    def __init__(self, base_url): self.base_url=base_url.rstrip("/")
    def health(self): return requests.get(self.base_url+"/health").json()
    def create_task(self, task): return requests.post(self.base_url+"/operator/task", json={"task":task}).json()
    def agents(self): return requests.get(self.base_url+"/operator/agents").json()
    def revenue(self): return requests.get(self.base_url+"/operator/revenue").json()

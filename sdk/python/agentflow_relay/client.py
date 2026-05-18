import requests
class AgentFlowClient:
    def __init__(self, base_url): self.base_url=base_url.rstrip("/")
    def health(self): return requests.get(self.base_url+"/health").json()
    def create_task(self,prompt): return requests.post(self.base_url+"/platform/tasks",json={"prompt":prompt}).json()

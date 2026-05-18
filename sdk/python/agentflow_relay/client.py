import requests
class AgentFlowClient:
    def __init__(self, base_url, api_key=None):
        self.base_url=base_url.rstrip("/")
        self.headers={"Content-Type":"application/json"}
        if api_key: self.headers["X-API-Key"]=api_key
    def health(self): return requests.get(f"{self.base_url}/health").json()
    def create_task(self,prompt): return requests.post(f"{self.base_url}/platform/tasks",json={"prompt":prompt}).json()
    def register_agent(self,name,endpoint="",capabilities=None): return requests.post(f"{self.base_url}/platform/agents",json={"name":name,"endpoint":endpoint,"capabilities":capabilities or []}).json()
    def create_workflow(self,name,description="",price=0): return requests.post(f"{self.base_url}/platform/workflows",json={"name":name,"description":description,"price":price}).json()

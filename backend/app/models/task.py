from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
import uuid

class TaskStatus(str, Enum):
    received = "received"
    approved = "approved"
    running = "running"
    completed = "completed"
    failed = "failed"
    needs_approval = "needs_approval"

class AgentTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_platform: str
    user_ref: str
    text: str
    status: TaskStatus = TaskStatus.received
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentResult(BaseModel):
    task_id: str
    status: TaskStatus
    output: str
    metadata: dict[str, Any] = Field(default_factory=dict)

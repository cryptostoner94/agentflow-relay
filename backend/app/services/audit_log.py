from datetime import datetime
from typing import Any

_AUDIT_LOGS: list[dict[str, Any]] = []

def log_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    item = {"ts": datetime.utcnow().isoformat(), "event_type": event_type, "payload": payload}
    _AUDIT_LOGS.append(item)
    return item

def list_logs() -> list[dict[str, Any]]:
    return list(reversed(_AUDIT_LOGS[-500:]))

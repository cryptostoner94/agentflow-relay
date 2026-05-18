from typing import Any

def discover_capabilities(agent_config: dict[str, Any]) -> dict[str, Any]:
    kind = agent_config.get("kind", "webhook")
    caps = {"kind": kind, "supports_text": True, "supports_tools": False, "supports_streaming": False}
    if kind in {"webhook", "openai_compatible", "ollama"}:
        caps["supports_tools"] = True
    return caps

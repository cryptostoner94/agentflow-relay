SENSITIVE_KEYWORDS = ["send email", "purchase", "buy", "delete", "pay", "apply", "book", "submit"]

def requires_approval(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in SENSITIVE_KEYWORDS)

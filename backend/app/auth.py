"""Operator authentication for the admin API of AgentFlow Relay.

Every /platform route can rewrite the credential vault, spend the operator's
provider keys, or call the operator's Stripe and Telegram accounts. This guard
rejects a caller that does not hold the operator credential before the route
runs, and it fails closed when the deployment holds no credential at all, so a
missing environment variable never turns the admin API public.
"""

import base64
import hashlib
import hmac
import json
import os

ADMIN_PATH_PREFIX = "/platform"
TELEGRAM_UPDATE_PATH = ADMIN_PATH_PREFIX + "/telegram/update"

# The dashboard shell and the health probe carry no operator data, so they stay
# reachable. Everything else is default-deny.
PUBLIC_PATHS = frozenset({"/", "/ui", "/health", "/demo/enterprise"})

OPERATOR_TOKEN_ENV = "AGENTFLOW_OPERATOR_TOKEN"
MASTER_SECRET_ENV = "AGENTFLOW_MASTER_SECRET"

OPERATOR_TOKEN_HEADER = "x-operator-token"
TELEGRAM_SECRET_HEADER = "x-telegram-bot-api-secret-token"

MIN_MASTER_SECRET_LENGTH = 16

_PLACEHOLDERS = frozenset(
    {"none", "null", "undefined", "change_me", "change-me", "changeme", "secret", "password"}
)

# The literal earlier versions derived the vault key from. It is in this public
# repository, so a vault under it is readable by everybody and it is refused.
_LEGACY_DEFAULT_SECRETS = frozenset({"agentflow-stable-secret"})


class VaultKeyUnavailable(RuntimeError):
    """The deployment holds no master secret strong enough to protect the vault."""


def _configured(name):
    value = (os.getenv(name) or "").strip()
    if not value or value.lower() in _PLACEHOLDERS:
        return ""
    return value


def master_secret():
    """The operator's vault key, or None when the deployment does not hold one."""
    value = _configured(MASTER_SECRET_ENV)
    if len(value) < MIN_MASTER_SECRET_LENGTH or value.lower() in _LEGACY_DEFAULT_SECRETS:
        return None
    return value


def telegram_webhook_secret():
    """The value Telegram must echo in X-Telegram-Bot-Api-Secret-Token.

    Derived from the master secret with an HMAC label so that the deployment
    needs no second value to type, and so that the result uses only the
    characters Telegram accepts: A-Z, a-z, 0-9, underscore and hyphen.
    """
    master = master_secret()
    if master is None:
        return None
    digest = hmac.new(master.encode(), b"agentflow-relay telegram webhook", hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")[:48]


def _normalize(path):
    return path.rstrip("/") or "/"


def _is_admin_path(path):
    if path in PUBLIC_PATHS:
        return False
    return path == ADMIN_PATH_PREFIX or path.startswith(ADMIN_PATH_PREFIX + "/")


def _header(scope, name):
    for key, value in scope.get("headers") or ():
        if key.decode("latin-1").lower() == name:
            return value.decode("latin-1").strip()
    return ""


def operator_credential(scope):
    presented = _header(scope, OPERATOR_TOKEN_HEADER)
    if presented:
        return presented
    scheme, _, value = _header(scope, "authorization").partition(" ")
    if scheme.lower() == "bearer" and value:
        return value.strip()
    return ""


def _matches(presented, expected):
    if not presented or not expected:
        return False
    return hmac.compare_digest(presented.encode(), expected.encode())


async def _refuse(send, status, message):
    body = json.dumps({"ok": False, "error": message}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})


class OperatorAuthMiddleware:
    """Default-deny ASGI guard for the operator routes."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = _normalize(scope.get("path", ""))
        if not _is_admin_path(path):
            await self.app(scope, receive, send)
            return

        if path == TELEGRAM_UPDATE_PATH:
            expected = telegram_webhook_secret()
            if not expected:
                await _refuse(send, 503, f"{MASTER_SECRET_ENV} is not configured; Telegram updates are disabled")
                return
            if not _matches(_header(scope, TELEGRAM_SECRET_HEADER), expected):
                await _refuse(send, 401, "missing or invalid Telegram webhook secret")
                return
            await self.app(scope, receive, send)
            return

        expected = _configured(OPERATOR_TOKEN_ENV)
        if not expected:
            await _refuse(send, 503, f"{OPERATOR_TOKEN_ENV} is not configured; operator routes are disabled")
            return
        if not _matches(operator_credential(scope), expected):
            await _refuse(send, 401, "missing or invalid operator token")
            return
        await self.app(scope, receive, send)

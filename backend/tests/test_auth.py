import importlib

import pytest
from fastapi.testclient import TestClient

OPERATOR_TOKEN = "test-operator-token-abc123"
MASTER_SECRET = "test-master-secret-0123456789"
OPERATOR = {"X-Operator-Token": OPERATOR_TOKEN}


@pytest.fixture()
def main(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTFLOW_OPERATOR_TOKEN", OPERATOR_TOKEN)
    monkeypatch.setenv("AGENTFLOW_MASTER_SECRET", MASTER_SECRET)
    module = importlib.reload(importlib.import_module("app.main"))
    monkeypatch.setattr(module, "DB", str(tmp_path / "agentflow.sqlite3"))
    return module


@pytest.fixture()
def client(main):
    return TestClient(main.app)


def test_health_stays_public(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_dashboard_shell_stays_public(client):
    assert client.get("/ui").status_code == 200


def test_anonymous_caller_cannot_write_the_vault(client):
    r = client.post("/platform/secrets", json={"name": "OPENAI_API_KEY", "value": "sk-attacker-supplied-key"})
    assert r.status_code == 401
    listed = client.get("/platform/secrets", headers=OPERATOR).json()
    assert "OPENAI_API_KEY" not in [row["name"] for row in listed["secrets"]]


def test_every_platform_data_route_rejects_an_anonymous_caller(client):
    for path in [
        "/platform/secrets",
        "/platform/metrics",
        "/platform/logs",
        "/platform/diagnostics",
        "/platform/revenue",
        "/platform/supabase/check",
        "/platform/telegram/test",
    ]:
        assert client.get(path).status_code == 401, path
    for path in ["/platform/tasks", "/platform/agent-chat", "/platform/command", "/platform/stripe/checkout", "/platform/secrets"]:
        assert client.post(path, json={}).status_code == 401, path


def test_wrong_operator_token_is_rejected(client):
    assert client.get("/platform/metrics", headers={"X-Operator-Token": "wrong-token"}).status_code == 401


def test_operator_token_authorizes_the_vault_write(client):
    saved = client.post("/platform/secrets", json={"name": "OPENAI_API_KEY", "value": "sk-operator-key-123456"}, headers=OPERATOR)
    assert saved.status_code == 200
    assert saved.json()["ok"] is True
    assert saved.json()["masked"].endswith("3456")
    metrics = client.get("/platform/metrics", headers=OPERATOR)
    assert metrics.status_code == 200
    assert metrics.json()["runtime"] == "LIVE"


def test_bearer_token_is_accepted(client):
    assert client.get("/platform/metrics", headers={"Authorization": f"Bearer {OPERATOR_TOKEN}"}).status_code == 200


def test_platform_routes_fail_closed_without_an_operator_token(main, monkeypatch):
    monkeypatch.delenv("AGENTFLOW_OPERATOR_TOKEN")
    client = TestClient(main.app)
    assert client.get("/platform/metrics").status_code == 503
    assert client.get("/health").status_code == 200


def test_telegram_update_rejects_a_forged_body(client):
    r = client.post("/platform/telegram/update", json={"message": {"chat": {"id": 1}, "text": "/workflow pwned"}})
    assert r.status_code == 401
    assert client.get("/platform/metrics", headers=OPERATOR).json()["workflows"] == 0


def test_telegram_update_accepts_the_registered_secret(main, client):
    secret = main.telegram_webhook_secret()
    assert secret and set(secret) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
    r = client.post(
        "/platform/telegram/update",
        json={"message": {"chat": {"id": 1}, "text": "/workflow genuine"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": secret},
    )
    assert r.status_code == 200
    assert client.get("/platform/metrics", headers=OPERATOR).json()["workflows"] == 1


def test_telegram_update_refuses_the_operator_token(client):
    r = client.post("/platform/telegram/update", json={"message": {"text": "/status"}}, headers=OPERATOR)
    assert r.status_code == 401


def test_vault_refuses_the_published_default_master_secret(main, monkeypatch):
    monkeypatch.setenv("AGENTFLOW_MASTER_SECRET", "agentflow-stable-secret")
    client = TestClient(main.app)
    r = client.post("/platform/secrets", json={"name": "OPENAI_API_KEY", "value": "sk-live-key-123456"}, headers=OPERATOR)
    assert r.status_code == 503
    with pytest.raises(main.VaultKeyUnavailable):
        main.fkey()
    assert client.get("/platform/diagnostics", headers=OPERATOR).json()["vault_key"] is False


def test_vault_refuses_a_missing_master_secret(main, monkeypatch):
    monkeypatch.delenv("AGENTFLOW_MASTER_SECRET")
    client = TestClient(main.app)
    assert client.post("/platform/secrets", json={"name": "OPENAI_API_KEY", "value": "sk-live-key-123456"}, headers=OPERATOR).status_code == 503
    assert main.master_secret() is None
    assert main.telegram_webhook_secret() is None


def _store_under_legacy_key(main, name, value):
    import base64
    import hashlib
    from cryptography.fernet import Fernet

    key = base64.urlsafe_b64encode(hashlib.sha256(b"agentflow-stable-secret").digest())
    c = main.db()
    c.execute("insert into secrets values(?,?,?,?)", (name, Fernet(key).encrypt(value.encode()).decode(), main.mask(value), main.now()))
    c.commit()
    c.close()


def test_row_stored_under_the_old_key_is_reported_not_hidden(main, monkeypatch):
    client = TestClient(main.app)
    _store_under_legacy_key(main, "OPENAI_API_KEY", "sk-stored-under-the-old-literal")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-render-env-1234")

    d = client.get("/platform/diagnostics", headers=OPERATOR).json()
    assert d["vault_key"] is True
    assert d["vault_unreadable"] == ["OPENAI_API_KEY"]
    assert d["openai"] is True

    listed = client.get("/platform/secrets", headers=OPERATOR).json()["secrets"]
    row = [r for r in listed if r["name"] == "OPENAI_API_KEY"][0]
    assert row["readable"] is False

    events = [l["event"] for l in client.get("/platform/logs?level=error", headers=OPERATOR).json()["logs"]]
    assert "secret_undecryptable" in events

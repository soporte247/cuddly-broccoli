import os
import shutil

# Use a temporary sqlite DB for tests
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_database.db")

from fastapi.testclient import TestClient

import openai

from app.main import app


def setup_module(module):
    # ensure no leftover DB
    try:
        os.remove("test_database.db")
    except Exception:
        pass


def teardown_module(module):
    try:
        os.remove("test_database.db")
    except Exception:
        pass


def test_register_login_chat(monkeypatch):
    client = TestClient(app)

    # Mock moderation to return not flagged
    def mock_moderation_create(model, input):
        return {"results": [{"flagged": False}]}

    # Mock chat completion
    def mock_chat_create(model, messages, max_tokens):
        return {"choices": [{"message": {"content": "Respuesta de prueba desde el mock"}}]}

    monkeypatch.setattr(openai.Moderation, "create", mock_moderation_create)
    monkeypatch.setattr(openai.ChatCompletion, "create", mock_chat_create)

    # Register user
    r = client.post("/auth/register", params={"username": "testuser", "password": "secret"})
    assert r.status_code == 201

    # Get token
    r = client.post("/auth/token", data={"username": "testuser", "password": "secret"})
    assert r.status_code == 200
    token = r.json().get("access_token")
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # Send chat
    r = client.post("/chat", json={"message": "Explícame XSS con ejemplo"}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "reply" in body
    assert "Respuesta de prueba" in body["reply"]

    # History should contain user and assistant messages
    r = client.get("/history", headers=headers)
    assert r.status_code == 200
    hist = r.json()
    roles = [m["role"] for m in hist]
    assert "user" in roles
    assert "assistant" in roles

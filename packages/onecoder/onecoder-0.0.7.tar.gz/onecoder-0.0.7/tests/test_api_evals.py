import pytest
from fastapi.testclient import TestClient
from onecoder.api import app
from onecoder.ipc_auth import TOKEN_STORE
import os
from pathlib import Path

@pytest.fixture
def client():
    # Inject a test token
    token = "test-evals-token"
    TOKEN_STORE._tokens[token] = 9999999999.0 # Far future expiry
    
    # Mock some environment variables
    os.environ["ACTIVE_SPRINT_ID"] = "092-mvw-and-dynamic-workers"
    os.environ["ACTIVE_SESSION_ID"] = "test-session-123"
    
    with TestClient(app) as c:
        yield c, token

def test_get_evals_summary(client):
    c, token = client
    response = c.get("/evals/summary", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "total_cost" in data
    assert "tool_usage" in data
    assert "sprint_id" in data

def test_get_evals_performance(client):
    c, token = client
    response = c.get("/evals/performance", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "recommendations" in data

def test_get_evals_unauthorized(client):
    c, _ = client
    response = c.get("/evals/summary", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401

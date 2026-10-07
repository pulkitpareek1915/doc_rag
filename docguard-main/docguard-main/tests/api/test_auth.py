from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from docguard.api.main import app
from docguard.config import settings

client = TestClient(app)

@pytest.fixture
def mock_auth_settings(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "api_auth_token", "test-secret-token")
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_requests", 5)

@pytest.fixture
def mock_cache():
    with patch("docguard.api.auth._cache") as mock:
        mock.enabled = True
        mock.redis = MagicMock()
        # Setup pipeline mock
        pipe_mock = MagicMock()
        mock.redis.pipeline.return_value = pipe_mock
        pipe_mock.execute.return_value = [1]  # request_count = 1
        yield mock

def test_missing_token_returns_401(mock_auth_settings):
    response = client.post("/query", json={"query": "test"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_invalid_token_returns_401(mock_auth_settings):
    headers = {"Authorization": "Bearer wrong-token"}
    response = client.post("/query", headers=headers, json={"query": "test"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"

def test_valid_token_allows_request(mock_auth_settings, mock_cache):
    with patch("docguard.api.routes.query.execute_query") as mock_exec:
        mock_exec.return_value = {"answer": "test", "citations": [], "refusal_reason": None}
        headers = {"Authorization": "Bearer test-secret-token"}
        response = client.post("/query", headers=headers, json={"query": "test"})
        assert response.status_code == 200

def test_auth_disabled_allows_request(monkeypatch, mock_cache):
    monkeypatch.setattr(settings, "auth_enabled", False)
    with patch("docguard.api.routes.query.execute_query") as mock_exec:
        mock_exec.return_value = {"answer": "test", "citations": [], "refusal_reason": None}
        response = client.post("/query", json={"query": "test"})
        assert response.status_code == 200

def test_health_does_not_require_auth(mock_auth_settings):
    response = client.get("/health")
    assert response.status_code == 200

def test_ready_does_not_require_auth(mock_auth_settings):
    with patch("docguard.api.routes.health.psycopg.connect"), patch("docguard.services.query._cache"):
        response = client.get("/health/ready")
        assert response.status_code in [200, 503]  # Just verifying it doesn't return 401

def test_rate_limit_rejects_over_threshold(mock_auth_settings, mock_cache):
    # Set request_count > rate_limit_requests (which is 5)
    mock_cache.redis.pipeline.return_value.execute.return_value = [6]
    headers = {"Authorization": "Bearer test-secret-token"}
    response = client.post("/query", headers=headers, json={"query": "test"})
    assert response.status_code == 429
    assert response.json()["detail"] == "Too Many Requests"
    assert "Retry-After" in response.headers

def test_redis_failure_policy_allows_request(mock_auth_settings, mock_cache):
    # Simulate redis failure
    mock_cache.redis.pipeline.side_effect = Exception("Redis down")
    with patch("docguard.api.routes.query.execute_query") as mock_exec:
        mock_exec.return_value = {"answer": "test", "citations": [], "refusal_reason": None}
        headers = {"Authorization": "Bearer test-secret-token"}
        response = client.post("/query", headers=headers, json={"query": "test"})
        assert response.status_code == 200

def test_openapi_contains_auth_scheme():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]

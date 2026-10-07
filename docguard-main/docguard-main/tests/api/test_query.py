from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from docguard.api.main import app
from docguard.config import settings


@pytest.fixture(autouse=True)
def disable_auth():
    settings.auth_enabled = False
    yield
    settings.auth_enabled = True

client = TestClient(app, raise_server_exceptions=False)


@patch("docguard.api.routes.query.execute_query")
def test_valid_query_returns_answer(mock_execute: MagicMock) -> None:
    mock_execute.return_value = {
        "answer": "This is the answer.",
        "citations": ["doc-1"],
        "refusal_reason": None,
    }
    response = client.post("/query", json={"query": "Hello?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is the answer."


def test_empty_query_rejected() -> None:
    response = client.post("/query", json={"query": ""})
    assert response.status_code == 422  # Pydantic validation error


def test_query_too_long_rejected() -> None:
    long_query = "a" * (settings.max_query_length + 1)
    response = client.post("/query", json={"query": long_query})
    assert response.status_code == 422


@patch("docguard.api.routes.query.execute_query")
def test_graph_refusal_returns_properly(mock_execute: MagicMock) -> None:
    mock_execute.return_value = {
        "answer": None,
        "citations": [],
        "refusal_reason": "insufficient_context",
    }

    response = client.post("/query", json={"query": "A question"})

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] is None
    assert data["refusal_reason"] == "insufficient_context"


@patch("docguard.api.routes.query.execute_query")
def test_internal_exception_sanitized(mock_execute: MagicMock) -> None:
    mock_execute.side_effect = Exception("DB connection lost")

    response = client.post("/query", json={"query": "Trigger error"})

    assert response.status_code == 500
    # Detail should not contain the secret trace
    assert response.json()["detail"] == "An unexpected error occurred"


def test_cors_configuration() -> None:
    response = client.options(
        "/query",
        headers={"Origin": "http://evil.com", "Access-Control-Request-Method": "POST"},
    )
    # Testing that CORS middleware is active and correctly responds to OPTIONS
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    # With allow_credentials=True and allow_origins=["*"], Starlette echoes the Origin
    assert response.headers["access-control-allow-origin"] == "http://evil.com"

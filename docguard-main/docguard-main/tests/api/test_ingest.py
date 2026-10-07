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


@patch("docguard.api.routes.ingest.embed_text", return_value=[0.1] * 1536)
@patch("docguard.api.routes.ingest.store.add", return_value="doc-123")
def test_document_ingestion_validates_size(
    mock_add: MagicMock, mock_embed: MagicMock
) -> None:
    response = client.post(
        "/documents/ingest", json={"content": "Hello", "metadata": {}}
    )
    assert response.status_code == 200
    assert response.json()["document_id"] == "doc-123"


@patch("docguard.api.routes.ingest.settings.max_document_size_mb", 0.000001)
def test_document_ingestion_too_large() -> None:
    response = client.post(
        "/documents/ingest",
        json={"content": "This is way too large" * 10, "metadata": {}},
    )
    assert response.status_code == 413
    assert "exceeds maximum size" in response.json()["detail"]


@patch(
    "docguard.api.routes.ingest.store.add",
    side_effect=Exception("DB Error"),
)
@patch("docguard.api.routes.ingest.embed_text", return_value=[0.1] * 1536)
def test_internal_exception_sanitized(
    mock_embed: MagicMock, mock_add: MagicMock
) -> None:
    response = client.post(
        "/documents/ingest", json={"content": "Hello", "metadata": {}}
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal ingestion error"

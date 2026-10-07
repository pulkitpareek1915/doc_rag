from unittest.mock import patch

from fastapi.testclient import TestClient

from docguard.api.main import app

client = TestClient(app)


def test_liveness_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "docguard"


@patch("docguard.api.routes.health.psycopg.connect")
@patch("docguard.services.query._cache")
def test_readiness_check(mock_cache, mock_connect) -> None:
    # Set up the mock to succeed without raising exception
    mock_conn = mock_connect.return_value.__enter__.return_value
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    mock_cur.execute.return_value = None

    mock_cache.enabled = True
    mock_cache.redis.ping.return_value = True

    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "postgres" in data["dependencies"]
    assert "redis" in data["dependencies"]

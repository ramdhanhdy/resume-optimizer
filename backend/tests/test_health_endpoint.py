"""Tests for deployment healthcheck endpoint."""

from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import server


def test_health_endpoint_returns_lightweight_status():
    response = TestClient(server.app).get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["database"] in {"supabase", "sqlite"}
    assert isinstance(body["timestamp"], int)

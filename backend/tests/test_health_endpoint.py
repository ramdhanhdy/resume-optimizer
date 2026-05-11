"""Tests for deployment healthcheck endpoint."""

from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest


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


def test_runtime_config_error_explains_missing_supabase_env(monkeypatch):
    monkeypatch.setenv("USE_SUPABASE_DB", "true")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    try:
        server._validate_runtime_config()
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected missing Supabase config to fail validation")

    assert "Supabase is the default database backend" in message
    assert "SUPABASE_URL" in message
    assert "SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY" in message
    assert "USE_SUPABASE_DB=false" in message


def test_startup_fails_fast_when_supabase_env_is_missing(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    with pytest.raises(RuntimeError, match="Supabase is the default database backend"):
        with TestClient(server.app):
            pass

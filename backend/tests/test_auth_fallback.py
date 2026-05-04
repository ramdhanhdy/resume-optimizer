from pathlib import Path
import sys

from starlette.requests import Request


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.middleware.auth import get_user_id_from_request


def make_request(headers=None):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in (headers or {}).items()
            ],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
        }
    )


def test_client_id_fallback_disabled_when_dev_mode_false(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "false")

    user_id = get_user_id_from_request(make_request({"X-Client-Id": "local-client"}))

    assert user_id is None


def test_client_id_fallback_enabled_when_dev_mode_true(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "true")

    user_id = get_user_id_from_request(make_request({"X-Client-Id": "local-client"}))

    assert user_id == "client:local-client"

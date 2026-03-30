from __future__ import annotations

from src import dashboard_server as dashboard_server_module


def test_allowed_dashboard_origin_loopback_defaults():
    assert dashboard_server_module._is_allowed_dashboard_origin("http://127.0.0.1:8091")
    assert dashboard_server_module._is_allowed_dashboard_origin("http://localhost:5173")
    assert dashboard_server_module._is_allowed_dashboard_origin("http://[::1]:8091")


def test_allowed_dashboard_origin_rejects_external_by_default():
    assert dashboard_server_module._is_allowed_dashboard_origin("https://evil.example") is False


def test_allowed_dashboard_origin_accepts_allowlist_env(monkeypatch):
    monkeypatch.setenv("DASHBOARD_ALLOWED_ORIGINS", "https://ops.example.com,https://admin.example.com")
    assert dashboard_server_module._is_allowed_dashboard_origin("https://ops.example.com")
    assert dashboard_server_module._is_allowed_dashboard_origin("https://admin.example.com")
    assert dashboard_server_module._is_allowed_dashboard_origin("https://evil.example") is False


def test_api_request_access_blocks_untrusted_origin_for_write(monkeypatch):
    monkeypatch.delenv("DASHBOARD_API_TOKEN", raising=False)
    ok, status, code = dashboard_server_module._check_api_request_access(
        method="POST",
        path="/api/reset-database",
        origin="https://evil.example",
        headers={},
    )
    assert ok is False
    assert status == 403
    assert code == "FORBIDDEN_ORIGIN"


def test_api_request_access_requires_token_when_configured(monkeypatch):
    monkeypatch.setenv("DASHBOARD_API_TOKEN", "local-secret")
    ok, status, code = dashboard_server_module._check_api_request_access(
        method="POST",
        path="/api/module/control",
        origin="http://127.0.0.1:8091",
        headers={"X-Dashboard-Token": "wrong"},
    )
    assert ok is False
    assert status == 401
    assert code == "UNAUTHORIZED"


def test_api_request_access_allows_get_from_non_browser_clients(monkeypatch):
    monkeypatch.delenv("DASHBOARD_API_TOKEN", raising=False)
    ok, status, code = dashboard_server_module._check_api_request_access(
        method="GET",
        path="/api/status",
        origin="",
        headers={},
    )
    assert ok is True
    assert status == 200
    assert code is None

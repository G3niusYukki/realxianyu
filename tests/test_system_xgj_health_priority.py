from __future__ import annotations

from src.dashboard.routes import system as system_routes


def test_check_xgj_health_prefers_env_over_system_config(monkeypatch):
    monkeypatch.setattr(
        system_routes,
        "_read_system_config",
        lambda: {
            "xianguanjia": {
                "app_key": "json-key",
                "app_secret": "json-secret",
                "base_url": "https://json.example",
                "mode": "self_developed",
                "seller_id": "",
            }
        },
    )
    monkeypatch.setenv("XGJ_APP_KEY", "env-key")
    monkeypatch.setenv("XGJ_APP_SECRET", "env-secret")
    monkeypatch.setenv("XGJ_BASE_URL", "https://env.example")
    monkeypatch.setenv("XGJ_MODE", "business")
    monkeypatch.setenv("XGJ_SELLER_ID", "seller-1")

    captured: dict[str, str] = {}

    def _fake_test_xgj_connection(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "message": "ok"}

    monkeypatch.setattr("src.dashboard.mimic_ops._test_xgj_connection", _fake_test_xgj_connection)

    result = system_routes._check_xgj_health()
    assert result["ok"] is True
    assert captured["app_key"] == "env-key"
    assert captured["app_secret"] == "env-secret"
    assert captured["base_url"] == "https://env.example"
    assert captured["mode"] == "business"
    assert captured["seller_id"] == "seller-1"


def test_check_xgj_health_uses_system_config_when_env_missing(monkeypatch):
    monkeypatch.setattr(
        system_routes,
        "_read_system_config",
        lambda: {
            "xianguanjia": {
                "app_key": "json-key",
                "app_secret": "json-secret",
                "base_url": "https://json.example",
                "mode": "self_developed",
                "seller_id": "seller-json",
            }
        },
    )
    monkeypatch.delenv("XGJ_APP_KEY", raising=False)
    monkeypatch.delenv("XGJ_APP_SECRET", raising=False)
    monkeypatch.delenv("XGJ_BASE_URL", raising=False)
    monkeypatch.delenv("XGJ_MODE", raising=False)
    monkeypatch.delenv("XGJ_SELLER_ID", raising=False)
    monkeypatch.delenv("XIANGUANJIA_APP_KEY", raising=False)
    monkeypatch.delenv("XIANGUANJIA_APP_SECRET", raising=False)
    monkeypatch.delenv("XIANGUANJIA_BASE_URL", raising=False)
    monkeypatch.delenv("XIANGUANJIA_MODE", raising=False)
    monkeypatch.delenv("XIANGUANJIA_SELLER_ID", raising=False)

    captured: dict[str, str] = {}

    def _fake_test_xgj_connection(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "message": "ok"}

    monkeypatch.setattr("src.dashboard.mimic_ops._test_xgj_connection", _fake_test_xgj_connection)

    result = system_routes._check_xgj_health()
    assert result["ok"] is True
    assert captured["app_key"] == "json-key"
    assert captured["app_secret"] == "json-secret"
    assert captured["base_url"] == "https://json.example"
    assert captured["mode"] == "self_developed"
    assert captured["seller_id"] == "seller-json"

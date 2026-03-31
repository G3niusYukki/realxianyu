from __future__ import annotations

from src.dashboard.routes import orders as orders_routes
from src.dashboard.services import xgj_service as xgj_service_module
from src.dashboard.services.xgj_service import XGJService


def test_xgj_service_reads_repo_root_env_file(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    service_dir = repo_root / "src" / "dashboard" / "services"
    service_dir.mkdir(parents=True)

    # Correct source of truth: <repo>/.env
    (repo_root / ".env").write_text("XGJ_APP_KEY=repo-root-key\n", encoding="utf-8")

    # A misleading local .env under src/dashboard should be ignored.
    dashboard_env = repo_root / "src" / "dashboard" / ".env"
    dashboard_env.parent.mkdir(parents=True, exist_ok=True)
    dashboard_env.write_text("XGJ_APP_KEY=dashboard-key\n", encoding="utf-8")

    fake_service_file = service_dir / "xgj_service.py"
    monkeypatch.setattr(xgj_service_module, "__file__", str(fake_service_file))
    monkeypatch.delenv("XGJ_APP_KEY", raising=False)

    assert XGJService._get_env_value("XGJ_APP_KEY") == "repo-root-key"


def test_xgj_creds_prefers_env_over_system_config(monkeypatch):
    monkeypatch.setattr(
        "src.dashboard.config_service.read_system_config",
        lambda: {"xianguanjia": {"app_key": "json-key", "app_secret": "json-secret"}},
    )
    monkeypatch.setenv("XGJ_APP_KEY", "env-key")
    monkeypatch.setenv("XGJ_APP_SECRET", "env-secret")
    monkeypatch.delenv("XIANGUANJIA_APP_KEY", raising=False)
    monkeypatch.delenv("XIANGUANJIA_APP_SECRET", raising=False)

    assert orders_routes._xgj_creds() == ("env-key", "env-secret")


def test_xgj_creds_reads_canonical_xgj_env_names(monkeypatch):
    monkeypatch.setattr("src.dashboard.config_service.read_system_config", lambda: {"xianguanjia": {}})
    monkeypatch.setenv("XGJ_APP_KEY", "canonical-key")
    monkeypatch.setenv("XGJ_APP_SECRET", "canonical-secret")
    monkeypatch.delenv("XIANGUANJIA_APP_KEY", raising=False)
    monkeypatch.delenv("XIANGUANJIA_APP_SECRET", raising=False)

    assert orders_routes._xgj_creds() == ("canonical-key", "canonical-secret")


def test_xgj_setting_prefers_env_over_config(monkeypatch):
    monkeypatch.setenv("XGJ_BASE_URL", "https://open.goofish.pro")
    monkeypatch.delenv("XIANGUANJIA_BASE_URL", raising=False)
    assert (
        orders_routes._xgj_setting(
            {"base_url": "https://json.example"},
            field="base_url",
            env_key="XGJ_BASE_URL",
            default="https://default.example",
        )
        == "https://open.goofish.pro"
    )


def test_xgj_setting_legacy_env_fallback_and_default(monkeypatch):
    monkeypatch.delenv("XGJ_MODE", raising=False)
    monkeypatch.setenv("XIANGUANJIA_MODE", "business")
    assert (
        orders_routes._xgj_setting(
            {},
            field="mode",
            env_key="XGJ_MODE",
            legacy_env_key="XIANGUANJIA_MODE",
            default="self_developed",
        )
        == "business"
    )

    monkeypatch.delenv("XIANGUANJIA_MODE", raising=False)
    assert (
        orders_routes._xgj_setting(
            {},
            field="mode",
            env_key="XGJ_MODE",
            legacy_env_key="XIANGUANJIA_MODE",
            default="self_developed",
        )
        == "self_developed"
    )

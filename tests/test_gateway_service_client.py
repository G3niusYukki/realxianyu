from __future__ import annotations

import json

import pytest
from app.client import XianGuanJiaClient, XianyuConfig


def test_xianyu_config_falls_back_to_legacy_xgj_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XIANYU_APP_KEY", raising=False)
    monkeypatch.delenv("XIANYU_APP_SECRET", raising=False)
    monkeypatch.delenv("XIANYU_BASE_URL", raising=False)
    monkeypatch.setenv("XGJ_APP_KEY", "legacy-key")
    monkeypatch.setenv("XGJ_APP_SECRET", "legacy-secret")
    monkeypatch.setenv("XGJ_BASE_URL", "https://open.goofish.pro")

    config = XianyuConfig()

    assert config.app_key == "legacy-key"
    assert config.app_secret == "legacy-secret"
    assert config.base_url == "https://open.goofish.pro"
    assert config.is_configured is True


@pytest.mark.asyncio
async def test_gateway_client_posts_open_platform_requests_with_query_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}

    async def fake_request(self, method: str, url: str, **kwargs):
        calls["method"] = method
        calls["url"] = url
        calls["params"] = kwargs["params"]
        calls["content"] = kwargs["content"]
        calls["headers"] = kwargs["headers"]

        class _Response:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict[str, object]:
                return {"code": 0, "data": {"ok": True}}

        return _Response()

    monkeypatch.setattr("app.client.sign_request", lambda *args, **kwargs: "sig")
    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    config = XianyuConfig()
    config.app_key = "key"
    config.app_secret = "secret"
    config.base_url = "https://example.test"
    client = XianGuanJiaClient(config)

    result = await client.list_products(page=2, page_size=50)

    assert result == {"code": 0, "data": {"ok": True}}
    assert calls["method"] == "POST"
    assert calls["url"] == "/api/open/product/list"
    assert calls["headers"] == {"Content-Type": "application/json"}
    assert calls["params"]["appid"] == "key"
    assert calls["params"]["sign"] == "sig"
    assert "timestamp" in calls["params"]
    assert json.loads(calls["content"].decode("utf-8")) == {"page": 2, "pageSize": 50}

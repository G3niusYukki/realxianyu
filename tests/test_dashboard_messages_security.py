from __future__ import annotations

from unittest.mock import MagicMock

from src.dashboard.routes import messages as messages_routes


def _make_ctx(body: dict):
    ctx = MagicMock()
    ctx.json_body.return_value = body
    return ctx


def test_notifications_test_rejects_non_https_url():
    ctx = _make_ctx({"channel": "feishu", "webhook_url": "http://127.0.0.1:8080/hook"})
    messages_routes.handle_notifications_test(ctx)
    ctx.send_json.assert_called_once()
    payload = ctx.send_json.call_args.args[0]
    status = ctx.send_json.call_args.kwargs.get("status")
    assert payload["ok"] is False
    assert status == 400


def test_notifications_test_rejects_private_host():
    ctx = _make_ctx({"channel": "wechat", "webhook_url": "https://127.0.0.1/webhook"})
    messages_routes.handle_notifications_test(ctx)
    payload = ctx.send_json.call_args.args[0]
    status = ctx.send_json.call_args.kwargs.get("status")
    assert payload["ok"] is False
    assert status == 400


def test_ai_test_rejects_private_host():
    ctx = _make_ctx({"api_key": "k", "base_url": "https://127.0.0.1:8443/v1", "model": "qwen-plus"})
    messages_routes.handle_ai_test(ctx)
    payload = ctx.send_json.call_args.args[0]
    status = ctx.send_json.call_args.kwargs.get("status")
    assert payload["ok"] is False
    assert status == 400


def test_ai_test_allows_known_provider_host(monkeypatch):
    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {}

    class _Client:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, *args, **kwargs):
            return _Resp()

    monkeypatch.setattr("httpx.Client", _Client)
    ctx = _make_ctx(
        {"api_key": "k", "base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"}
    )
    messages_routes.handle_ai_test(ctx)
    payload = ctx.send_json.call_args.args[0]
    assert payload["ok"] is True


def test_notifications_test_rejects_unknown_public_host():
    ctx = _make_ctx({"channel": "feishu", "webhook_url": "https://evil.example/hook"})
    messages_routes.handle_notifications_test(ctx)
    payload = ctx.send_json.call_args.args[0]
    status = ctx.send_json.call_args.kwargs.get("status")
    assert payload["ok"] is False
    assert status == 400

from __future__ import annotations

import base64
import json

import pytest

from src.core.error_handler import BrowserError
from src.modules.messages.ws_live import GoofishWsTransport, MessagePackDecoder, decode_sync_payload, extract_chat_event


@pytest.fixture
def ws_enabled(monkeypatch):
    monkeypatch.setattr("src.modules.messages.ws_live.websockets", object())


def _transport():
    return GoofishWsTransport(
        cookie_text="unb=10001; _m_h5_tk=token_a_123; cookie2=a; _tb_token_=t; sgcookie=s",
        config={"queue_wait_seconds": 0.01, "message_expire_ms": 1000},
    )


def test_messagepack_basic_decode():
    out = MessagePackDecoder(bytes([0x81, 0xA1, 0x61, 0x01])).decode()
    assert out == {"a": 1}


def test_decode_sync_payload_fallback_messagepack():
    raw = bytes([0x81, 0xA1, 0x61, 0x01])
    txt = base64.b64encode(raw).decode()
    assert decode_sync_payload(txt) == {"a": 1}
    assert decode_sync_payload("@@@@") is None


def test_extract_chat_event_invalid_returns_none():
    assert extract_chat_event(None) is None
    assert extract_chat_event({"1": {"2": "cid"}}) is None


@pytest.mark.asyncio
async def test_push_event_dedupe_and_queue(ws_enabled):
    t = _transport()
    t.my_user_id = "mine"
    event = {"chat_id": "c1", "sender_user_id": "u1", "sender_name": "n", "text": "hi", "create_time": 9999999999999}

    await t._push_event(event)
    await t._push_event(event)
    assert t._queue.qsize() == 1
    row = t._queue.get_nowait()
    assert row["session_id"] == "c1"


@pytest.mark.asyncio
async def test_handle_sync_calls_push(ws_enabled, monkeypatch):
    t = _transport()
    pushed = []

    async def fake_push(e):
        pushed.append(e)

    monkeypatch.setattr(t, "_push_event", fake_push)

    payload = {
        "body": {
            "syncPushPackage": {
                "data": [
                    {
                        "data": (
                            "eyIxIjp7IjIiOiJjMUBnb29maXNoIiwiNSI6MSwiMTAiOnsiY29udGVudCI6ImhpIiwiZnJvbVVzZXJJ"
                            "ZCI6InUxIiwic2VuZGVyTmljayI6Im4ifX19"
                        )
                    }
                ]
            }
        }
    }
    await t._handle_sync(payload)
    assert pushed and pushed[0]["chat_id"] == "c1"


@pytest.mark.asyncio
async def test_send_text_ready_and_missing_peer(ws_enabled):
    t = _transport()

    async def _noop_start():
        return None

    class _WS:
        async def send(self, _x):
            return None

    t.start = _noop_start
    t._ready.set()
    t._ws = _WS()

    assert await t.send_text("missing", "x") is False
    t._session_peer["s1"] = "u2"
    assert await t.send_text("s1", "hello") is True


@pytest.mark.asyncio
async def test_wait_cookie_update_and_auth_markers(ws_enabled):
    t = _transport()
    assert t._next_reconnect_delay(auth_error=True) >= 5.0
    assert GoofishWsTransport._is_auth_related_error(Exception("HTTP 401 forbidden")) is True
    assert GoofishWsTransport._is_auth_related_error(Exception("network")) is False

    calls = {"n": 0}

    def supplier():
        calls["n"] += 1
        if calls["n"] > 1:
            return "unb=10001; _m_h5_tk=token_b_123; cookie2=a"
        return "unb=10001; _m_h5_tk=token_a_123; cookie2=a"

    t.cookie_supplier = supplier
    assert await t._wait_for_cookie_update(timeout_seconds=2) is True


def test_cookie_apply_raises_without_unb(ws_enabled):
    with pytest.raises(BrowserError):
        GoofishWsTransport(cookie_text="a=1", config={})


@pytest.mark.asyncio
async def test_fetch_token_rgv587_recovers_with_im_refresh(ws_enabled, monkeypatch):
    t = _transport()
    t.config["token_max_attempts"] = 2

    async def _no_preflight():
        return True

    monkeypatch.setattr(t, "_preflight_has_login", _no_preflight)
    monkeypatch.setattr(t, "_maybe_reload_cookie", lambda reason="": False)

    refresh_calls = {"n": 0}

    async def _im_refresh(urgent=False):
        refresh_calls["n"] += 1
        return True

    monkeypatch.setattr(t, "_try_goofish_im_refresh", _im_refresh)

    call_idx = {"n": 0}

    class _Resp:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200
            self.cookies = {}

        def json(self):
            return self._payload

    class _Client:
        def __init__(self, *args, **kwargs):
            self.cookies = type("Jar", (), {"jar": []})()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            call_idx["n"] += 1
            if call_idx["n"] == 1:
                return _Resp({"ret": ["RGV587::被挤爆"]})
            return _Resp({"ret": ["SUCCESS::调用成功"], "data": {"accessToken": "token-after-refresh"}})

    monkeypatch.setattr("src.modules.messages.ws_live.httpx.AsyncClient", _Client)

    token = await t._fetch_token()
    assert token == "token-after-refresh"
    assert refresh_calls["n"] == 1
    assert call_idx["n"] == 2


@pytest.mark.asyncio
async def test_fetch_token_uses_app_key_fallback_when_mtop_secret_missing(ws_enabled, monkeypatch):
    monkeypatch.setattr("src.modules.messages.ws_live._MTOP_APP_SECRET", "")
    monkeypatch.setattr("src.modules.messages.ws_live._MTOP_APP_KEY", "34839810")

    t = GoofishWsTransport(
        cookie_text="unb=10001; _m_h5_tk=token_a_123; cookie2=a; _tb_token_=t; sgcookie=s",
        config={"queue_wait_seconds": 0.01, "message_expire_ms": 1000},
    )
    t.config["token_max_attempts"] = 1

    async def _no_preflight():
        return True

    monkeypatch.setattr(t, "_preflight_has_login", _no_preflight)
    monkeypatch.setattr(t, "_maybe_reload_cookie", lambda reason="": False)

    posted = {"payload_app_key": ""}

    class _Resp:
        def __init__(self):
            self.status_code = 200
            self.cookies = {}

        def json(self):
            return {"ret": ["SUCCESS::调用成功"], "data": {"accessToken": "token-ok"}}

    class _Client:
        def __init__(self, *args, **kwargs):
            self.cookies = type("Jar", (), {"jar": []})()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            data_payload = json.loads(kwargs.get("data", {}).get("data", "{}"))
            posted["payload_app_key"] = str(data_payload.get("appKey", ""))
            return _Resp()

    monkeypatch.setattr("src.modules.messages.ws_live.httpx.AsyncClient", _Client)

    token = await t._fetch_token()
    assert token == "token-ok"
    assert posted["payload_app_key"] == "34839810"


@pytest.mark.asyncio
async def test_send_text_via_mtop_rejects_risk_control_marker(ws_enabled, monkeypatch):
    t = _transport()
    recorded: list[tuple[str, str]] = []

    def _record(chat_id: str, text: str) -> None:
        recorded.append((chat_id, text))

    async def _mtop_call(api: str, version: str, data_dict: dict):
        return {"ret": [], "data": {"accepted": True}, "_mtop_error_type": "risk_control"}

    monkeypatch.setattr(t, "_record_bot_sig", _record)
    monkeypatch.setattr(t, "_mtop_call", _mtop_call)

    ok = await t._send_text_via_mtop("chat-1", "hello")

    assert ok is False
    assert recorded == []


@pytest.mark.asyncio
async def test_mtop_call_marks_rgv587_response(ws_enabled, monkeypatch):
    t = _transport()

    class _Resp:
        def __init__(self):
            self.status_code = 200
            self.cookies = {}

        def json(self):
            return {"ret": ["RGV587::被挤爆"], "data": {}}

    class _Client:
        def __init__(self, *args, **kwargs):
            self.cookies = type("Jar", (), {"jar": []})()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return _Resp()

    monkeypatch.setattr("src.modules.messages.ws_live.httpx.AsyncClient", _Client)

    payload = await t._mtop_call("mtop.taobao.idle.pc.im.msg.send", "1.0", {"cid": "chat-1@goofish"})
    assert payload.get("_mtop_error_type") == "risk_control"

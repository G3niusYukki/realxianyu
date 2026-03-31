from __future__ import annotations

import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.modules.messages.service import MessagesService


class _Logger:
    """Minimal logger stub that collects messages for assertions."""

    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.debugs: list[str] = []

    def info(self, msg: str, *args) -> None:
        if args:
            msg = msg % args
        self.infos.append(str(msg))

    def warning(self, msg: str, *args) -> None:
        if args:
            msg = msg % args
        self.warnings.append(str(msg))

    def debug(self, msg: str, *args) -> None:
        if args:
            msg = msg % args
        self.debugs.append(str(msg))


@pytest.fixture
def cfg(monkeypatch, tmp_path):
    c = SimpleNamespace(
        browser={"delay": {"min": 0.0, "max": 0.0}},
        accounts=[{"enabled": True, "cookie": "acc_cookie=v"}],
    )

    def get_section(name, default=None):
        if name == "messages":
            return {}
        if name == "quote":
            return {}
        if name == "content":
            return {"templates": {"path": str(tmp_path)}}
        return default or {}

    c.get_section = get_section
    monkeypatch.setattr("src.modules.messages.service.get_config", lambda: c)
    monkeypatch.setattr("src.modules.messages.service.get_compliance_guard", lambda: object())


def test_transport_mode_and_safe_float(cfg):
    assert MessagesService._normalized_transport_mode("X") == "ws"
    assert MessagesService._safe_float("1.2") == 1.2
    assert MessagesService._safe_float(None) == 0.0


def test_load_templates_and_select(cfg, tmp_path):
    p = tmp_path / "reply_templates.json"
    p.write_text(json.dumps({"weight_template": "W", "volume_template": "V"}), encoding="utf-8")

    s = MessagesService(controller=None, config={})
    tpl = s._load_reply_templates()
    assert tpl["weight_template"] == "W"
    assert s._select_quote_reply_template({"actual_weight_kg": 1, "billing_weight_kg": 2}) == "V"
    assert s._select_quote_reply_template({"actual_weight_kg": 2, "billing_weight_kg": 2}) == "W"


def test_resolve_ws_cookie_fallbacks(monkeypatch, cfg):
    s = MessagesService(controller=None, config={"cookie": "cfg_cookie=v"})
    monkeypatch.delenv("XIANYU_COOKIE_1", raising=False)
    assert s._resolve_ws_cookie() == "cfg_cookie=v"

    monkeypatch.setenv("XIANYU_COOKIE_1", "env_cookie=v")
    assert s._resolve_ws_cookie() == "env_cookie=v"


class _Logger:
    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.debugs: list[str] = []

    def info(self, msg: str, *args) -> None:
        if args:
            msg = msg % args
        self.infos.append(str(msg))

    def warning(self, msg: str, *args) -> None:
        if args:
            msg = msg % args
        self.warnings.append(str(msg))

    def debug(self, msg: str, *args) -> None:
        if args:
            msg = msg % args
        self.debugs.append(str(msg))


class _Transport:
    def __init__(self, unread: list[dict], *, ready: bool = True, resync_requested: bool = False) -> None:
        self._unread = unread
        self._ready = ready
        self._resync_requested = resync_requested

    async def get_unread_sessions(self, limit: int = 20) -> list[dict]:
        return self._unread[:limit]

    def is_ready(self) -> bool:
        return self._ready

    def consume_unread_resync_flag(self) -> bool:
        requested = self._resync_requested
        self._resync_requested = False
        return requested


@pytest.mark.asyncio
async def test_get_unread_sessions_falls_back_to_dom_when_ws_queue_empty(cfg, monkeypatch):
    svc = MessagesService(controller=object(), config={})
    svc.logger = _Logger()
    transport = _Transport([])
    dom_sessions = [{"session_id": "dom-1", "last_message": "在吗"}]

    monkeypatch.setattr(svc, "_ensure_ws_transport", AsyncMock(return_value=transport))
    monkeypatch.setattr(svc, "_get_unread_sessions_dom", AsyncMock(return_value=dom_sessions))

    result = await svc.get_unread_sessions(limit=5)

    assert result == dom_sessions
    assert any("dom fallback" in msg and "queue_empty" in msg for msg in svc.logger.debugs)


@pytest.mark.asyncio
async def test_get_unread_sessions_skips_dom_fallback_during_cooldown_without_resync(cfg, monkeypatch):
    svc = MessagesService(controller=object(), config={})
    svc.logger = _Logger()
    svc._last_ws_empty_fallback_scan_ts = time.monotonic()
    transport = _Transport([])

    dom_scan = AsyncMock(return_value=[{"session_id": "dom-2"}])
    monkeypatch.setattr(svc, "_ensure_ws_transport", AsyncMock(return_value=transport))
    monkeypatch.setattr(svc, "_get_unread_sessions_dom", dom_scan)

    result = await svc.get_unread_sessions(limit=5)

    assert result == []
    assert dom_scan.await_count == 0
    assert any("fallback skipped" in msg and "cooldown" in msg for msg in svc.logger.debugs)


@pytest.mark.asyncio
async def test_get_unread_sessions_reconnect_resync_bypasses_dom_fallback_cooldown(cfg, monkeypatch):
    svc = MessagesService(controller=object(), config={})
    svc.logger = _Logger()
    svc._last_ws_empty_fallback_scan_ts = time.monotonic()
    transport = _Transport([], resync_requested=True)
    dom_sessions = [{"session_id": "dom-3", "last_message": "补扫命中"}]

    monkeypatch.setattr(svc, "_ensure_ws_transport", AsyncMock(return_value=transport))
    monkeypatch.setattr(svc, "_get_unread_sessions_dom", AsyncMock(return_value=dom_sessions))

    result = await svc.get_unread_sessions(limit=3)

    assert result == dom_sessions
    assert any("reason=reconnect_resync" in msg for msg in svc.logger.debugs)


class _Dedup:
    """In-memory dedup stub for testing."""

    def __init__(self) -> None:
        self._replied: set[str] = set()
        self._sent: list[tuple[str, str]] = []

    @staticmethod
    def _key(cid: str, ct: int, msg: str) -> str:
        return f"{cid}:{ct}:{msg}"

    def is_duplicate(self, cid: str, ct: int, msg: str) -> bool:
        return self._key(cid, ct, msg) in self._replied

    def is_content_duplicate(self, cid: str, msg: str, window_seconds: int = 600) -> bool:
        return False

    def mark_replied(self, cid: str, ct: int, msg: str, reply: str = "") -> None:
        self._replied.add(self._key(cid, ct, msg))

    def mark_reply_sent(self, cid: str, reply: str) -> None:
        self._sent.append((cid, reply))


@pytest.mark.asyncio
async def test_process_session_does_not_mark_dedup_when_send_fails(cfg, monkeypatch):
    """Regression: mark_replied must NOT be called before the reply send attempt.
    If the send fails, the dedup tables must stay clean so the next poll can retry.
    """
    svc = MessagesService(controller=object(), config={})
    svc.logger = _Logger()
    dedup = _Dedup()
    monkeypatch.setattr(svc, "_get_dedup", lambda: dedup)

    monkeypatch.setattr(
        svc,
        "_generate_reply_with_quote",
        AsyncMock(return_value=("测试回复", {})),
    )
    monkeypatch.setattr(
        svc,
        "compliance_center",
        SimpleNamespace(evaluate_before_send=lambda *a, **kw: SimpleNamespace(blocked=False, reason="", policy_scope="")),
    )
    monkeypatch.setattr(svc, "reply_to_session", AsyncMock(return_value=False))

    session = {
        "session_id": "sess-dedup-test",
        "last_message": "你好",
        "create_time": int(time.time() * 1000),
    }
    result = await svc.process_session(session)

    # Send failed → dedup must NOT be poisoned
    assert result["sent"] is False
    assert not dedup._replied, f"dedup was marked before send — bug! keys={dedup._replied}"


@pytest.mark.asyncio
async def test_process_session_marks_dedup_after_successful_send(cfg, monkeypatch):
    """When the send succeeds, dedup should be recorded so the message is not reprocessed."""
    svc = MessagesService(controller=object(), config={})
    svc.logger = _Logger()
    dedup = _Dedup()
    monkeypatch.setattr(svc, "_get_dedup", lambda: dedup)

    monkeypatch.setattr(
        svc,
        "_generate_reply_with_quote",
        AsyncMock(return_value=("好的", {})),
    )
    monkeypatch.setattr(
        svc,
        "compliance_center",
        SimpleNamespace(evaluate_before_send=lambda *a, **kw: SimpleNamespace(blocked=False, reason="", policy_scope="")),
    )
    monkeypatch.setattr(svc, "reply_to_session", AsyncMock(return_value=True))

    ct = int(time.time() * 1000)
    session = {
        "session_id": "sess-ok",
        "last_message": "在吗",
        "create_time": ct,
    }
    result = await svc.process_session(session)

    assert result["sent"] is True
    assert dedup._key("sess-ok", ct, "在吗") in dedup._replied


@pytest.mark.asyncio
async def test_process_session_marks_dedup_on_skipped_message(cfg, monkeypatch):
    """System notifications (skipped) should be deduped — no point retrying."""
    svc = MessagesService(controller=object(), config={})
    svc.logger = _Logger()
    dedup = _Dedup()
    monkeypatch.setattr(svc, "_get_dedup", lambda: dedup)

    monkeypatch.setattr(
        svc,
        "_generate_reply_with_quote",
        AsyncMock(return_value=("", {"skipped": True, "reason": "system_notification"})),
    )
    monkeypatch.setattr(
        svc,
        "compliance_center",
        SimpleNamespace(evaluate_before_send=lambda *a, **kw: SimpleNamespace(blocked=False, reason="", policy_scope="")),
    )

    ct = int(time.time() * 1000)
    session = {
        "session_id": "sess-skip",
        "last_message": "买家已付款",
        "create_time": ct,
    }
    await svc.process_session(session)

    assert dedup._key("sess-skip", ct, "买家已付款") in dedup._replied


@pytest.mark.asyncio
async def test_process_session_retry_succeeds_after_initial_send_failure(cfg, monkeypatch):
    """End-to-end: first send fails (dedup NOT marked), second attempt succeeds."""
    svc = MessagesService(controller=object(), config={})
    svc.logger = _Logger()
    dedup = _Dedup()
    monkeypatch.setattr(svc, "_get_dedup", lambda: dedup)
    monkeypatch.setattr(
        svc,
        "_generate_reply_with_quote",
        AsyncMock(return_value=("重试回复", {})),
    )
    monkeypatch.setattr(
        svc,
        "compliance_center",
        SimpleNamespace(evaluate_before_send=lambda *a, **kw: SimpleNamespace(blocked=False, reason="", policy_scope="")),
    )

    ct = int(time.time() * 1000)
    session = {
        "session_id": "sess-retry",
        "last_message": "多少钱",
        "create_time": ct,
    }

    # First attempt: send fails
    monkeypatch.setattr(svc, "reply_to_session", AsyncMock(return_value=False))
    r1 = await svc.process_session(session)
    assert r1["sent"] is False

    # Second attempt: dedup should NOT block, send succeeds
    monkeypatch.setattr(svc, "reply_to_session", AsyncMock(return_value=True))
    r2 = await svc.process_session(session)
    assert r2["sent"] is True

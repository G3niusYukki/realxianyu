"""Dashboard reply test service — sandbox reply testing."""

from __future__ import annotations

import time
from typing import Any

from src.core.config import get_config
from src.modules.messages.service import MessagesService


class ReplyTestService:
    """Provides sandboxed reply generation for the test-reply dashboard endpoint."""

    def __init__(self, project_root: Any) -> None:
        # project_root kept for API symmetry, not directly used
        self._project_root = project_root

    _sandbox_services: dict[str, tuple[float, MessagesService]] = {}
    _SANDBOX_TTL = 1800

    def _get_sandbox_service(self, session_id: str) -> MessagesService:
        now = time.time()
        stale = [k for k, (ts, _) in self._sandbox_services.items() if now - ts > self._SANDBOX_TTL]
        for k in stale:
            self._sandbox_services.pop(k, None)
        entry = self._sandbox_services.get(session_id)
        if entry is not None:
            self._sandbox_services[session_id] = (now, entry[1])
            return entry[1]
        msg_cfg = get_config().get_section("messages", {})
        svc = MessagesService(controller=None, config=msg_cfg)
        self._sandbox_services[session_id] = (now, svc)
        return svc

    def test_reply(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.dashboard.mimic_ops import _run_async

        started = time.perf_counter()
        message = str(payload.get("message") or payload.get("user_message") or payload.get("user_msg") or "").strip()
        item_title = str(payload.get("item_title") or payload.get("item") or payload.get("item_desc") or "").strip()
        session_id = str(payload.get("session_id") or "").strip()
        origin = str(payload.get("origin") or "").strip()
        destination = str(payload.get("destination") or "").strip()
        weight_val = payload.get("weight")

        message_eval = message
        if origin and destination and weight_val not in {None, ""}:
            extras: list[str] = []
            length = payload.get("length")
            width = payload.get("width")
            height = payload.get("height")
            volume_weight = payload.get("volume_weight")
            courier = str(payload.get("courier") or "").strip()
            if length not in {None, ""} and width not in {None, ""} and height not in {None, ""}:
                extras.append(f"{length}x{width}x{height}cm")
            if volume_weight not in {None, ""}:
                extras.append(f"体积重{volume_weight}kg")
            if courier and courier.lower() != "auto":
                extras.append(courier)
            structured = f"从{origin}寄到{destination} {weight_val}kg"
            if extras:
                structured = f"{structured} {' '.join(extras)}"
            message_eval = f"{message} {structured}".strip() if message else structured

        if session_id:
            service = self._get_sandbox_service(session_id)
        else:
            msg_cfg = get_config().get_section("messages", {})
            service = MessagesService(controller=None, config=msg_cfg)
        reply, detail = _run_async(
            service._generate_reply_with_quote(message_eval, item_title=item_title, session_id=session_id)
        )

        quote_part: dict[str, Any] | None = None
        if isinstance(detail, dict) and bool(detail.get("is_quote")):
            quote_result = detail.get("quote_result")
            all_couriers = detail.get("quote_all_couriers")
            if isinstance(quote_result, dict):
                quote_part = quote_result
            if isinstance(all_couriers, list):
                quote_part = {"best": quote_part or {}, "all_couriers": all_couriers}

        intent = "quote" if bool(detail.get("is_quote")) else "general"
        agent = (
            "MessagesService+AutoQuoteEngine"
            if quote_part is not None
            else ("MessagesService+RuleBasedReplyStrategy" if intent == "general" else "MessagesService")
        )
        response_time_ms = (time.perf_counter() - started) * 1000
        return {
            "success": True,
            "reply": reply,
            "quote": quote_part,
            "intent": intent,
            "agent": agent,
            "detail": detail,
            "response_time_ms": response_time_ms,
            "response_time": response_time_ms,
        }

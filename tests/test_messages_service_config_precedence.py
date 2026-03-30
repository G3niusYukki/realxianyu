from __future__ import annotations

import json
from types import SimpleNamespace

from src.modules.messages.service import MessagesService


def test_messages_service_uses_merged_runtime_config(monkeypatch, tmp_path):
    # Simulate merged runtime config where env overrides dashboard JSON.
    merged_messages = {
        "enabled": False,
        "first_reply_delay_seconds": [1.1, 1.2],
        "inter_reply_delay_seconds": [2.1, 2.2],
        "ai": {"task_switches": {"quote_extract": False, "express_reply": False}, "api_key": ""},
    }
    merged_ai = {"task_switches": {"quote_extract": False, "express_reply": False}, "api_key": ""}

    app_cfg = SimpleNamespace(
        browser={"delay": {"min": 0.0, "max": 0.0}},
        get_section=lambda name, default=None: (
            merged_messages
            if name == "messages"
            else ({} if name == "quote" else ({"templates": {"path": str(tmp_path)}} if name == "content" else (default or {})))
        ),
    )

    # Write conflicting system_config values that should NOT override merged runtime config.
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "system_config.json").write_text(
        json.dumps(
            {
                "auto_reply": {
                    "enabled": True,
                    "first_reply_delay": "0.1-0.2",
                    "inter_reply_delay": "0.3-0.4",
                },
                "ai": {"api_key": "json-ai-key"},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("src.modules.messages.service.get_config", lambda: app_cfg)
    monkeypatch.setattr("src.modules.messages.service.get_compliance_guard", lambda: object())

    svc = MessagesService(controller=None, config=None)

    assert svc.config.get("enabled") is False
    assert svc.first_reply_delay_seconds == (1.1, 1.2)
    assert svc.inter_reply_delay_seconds == (2.1, 2.2)
    assert svc._ai_extract_enabled is False
    assert svc._ai_reply_enabled is False
    assert svc._sys_ai_config == merged_ai

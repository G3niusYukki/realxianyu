"""System config YAML sync service extracted from MimicOps."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_YAML_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "config.yaml"
_YAML_EXAMPLE_PATH = Path(__file__).resolve().parents[2] / "config" / "config.example.yaml"

_AUTO_REPLY_TO_YAML_KEYS = {
    "default_reply": "default_reply",
    "virtual_default_reply": "virtual_default_reply",
    "enabled": "enabled",
    "ai_intent_enabled": "ai_intent_enabled",
    "quote_missing_template": "quote_missing_template",
    "strict_format_reply_enabled": "strict_format_reply_enabled",
    "force_non_empty_reply": "force_non_empty_reply",
    "non_empty_reply_fallback": "non_empty_reply_fallback",
    "quote_failed_template": "quote_failed_template",
    "quote_reply_max_couriers": "quote_reply_max_couriers",
    "first_reply_delay": "first_reply_delay_seconds",
    "inter_reply_delay": "inter_reply_delay_seconds",
}


def sync_system_config_to_yaml(sys_config: dict[str, Any]) -> None:
    """Write relevant system_config fields back to config.yaml so the runtime picks them up."""
    yaml_path = _YAML_CONFIG_PATH if _YAML_CONFIG_PATH.exists() else _YAML_EXAMPLE_PATH
    if not yaml_path.exists():
        return
    try:
        raw = yaml_path.read_text(encoding="utf-8")
        cfg = yaml.safe_load(raw) or {}
    except Exception:
        return

    changed = False

    ar = sys_config.get("auto_reply")
    if isinstance(ar, dict):
        msgs = cfg.setdefault("messages", {})
        _RANGE_KEYS = {"first_reply_delay", "inter_reply_delay"}
        for src_key, dst_key in _AUTO_REPLY_TO_YAML_KEYS.items():
            if src_key in ar:
                val = ar[src_key]
                if src_key in _RANGE_KEYS and isinstance(val, str) and "-" in val:
                    try:
                        parts = val.split("-", 1)
                        val = [float(parts[0].strip()), float(parts[1].strip())]
                    except (ValueError, IndexError):
                        pass
                msgs[dst_key] = val
                changed = True
        kw_text = ar.get("keyword_replies_text")
        if isinstance(kw_text, str) and kw_text.strip():
            kw_dict: dict[str, str] = {}
            for line in kw_text.strip().splitlines():
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k and v:
                        kw_dict[k] = v
            if kw_dict:
                msgs["keyword_replies"] = kw_dict
                changed = True
        custom_rules = ar.get("custom_intent_rules")
        if isinstance(custom_rules, list):
            msgs["intent_rules"] = [
                {
                    k: v
                    for k, v in r.items()
                    if k
                    in (
                        "name",
                        "keywords",
                        "reply",
                        "patterns",
                        "priority",
                        "categories",
                        "needs_human",
                        "human_reason",
                        "phase",
                        "skip_reply",
                    )
                }
                for r in custom_rules
                if isinstance(r, dict) and r.get("name")
            ]
            changed = True

    for section_key in ("pricing", "delivery"):
        sec = sys_config.get(section_key)
        if isinstance(sec, dict):
            cfg.setdefault(section_key, {}).update(sec)
            changed = True

    store = sys_config.get("store")
    if isinstance(store, dict) and "category" in store:
        cfg.setdefault("store", {})["category"] = store["category"]
        changed = True

    slider = sys_config.get("slider_auto_solve")
    if isinstance(slider, dict):
        ws_cfg = cfg.setdefault("messages", {}).setdefault("ws", {})
        slider_dict = {
            "enabled": bool(slider.get("enabled", False)),
            "max_attempts": int(slider.get("max_attempts", 2)),
            "cooldown_seconds": int(slider.get("cooldown_seconds", 300)),
            "headless": bool(slider.get("headless", False)),
        }
        fp = slider.get("fingerprint_browser")
        if isinstance(fp, dict):
            slider_dict["fingerprint_browser"] = {
                "enabled": bool(fp.get("enabled", False)),
                "api_url": str(fp.get("api_url", "http://127.0.0.1:54345")),
                "browser_id": str(fp.get("browser_id", "")),
            }
        ws_cfg["slider_auto_solve"] = slider_dict
        changed = True

    if changed:
        try:
            tmp = yaml_path.with_suffix(".tmp")
            tmp.write_text(
                yaml.dump(cfg, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8"
            )
            tmp.rename(yaml_path)
        except Exception as exc:
            logger.warning("Failed to sync config to YAML: %s", exc)


class ConfigSyncService:
    """Facade for config sync operations."""

    def __init__(self) -> None:
        pass

    def sync_system_config_to_yaml(self, sys_config: dict[str, Any]) -> None:
        sync_system_config_to_yaml(sys_config)

from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.core.utils import now_iso, run_async, safe_int

logger = logging.getLogger(__name__)

_product_image_cache: dict[str, tuple[str, float]] = {}
_PRODUCT_IMAGE_CACHE_TTL = 1800  # 30 minutes


def _safe_int(value: str | None, default: int, min_value: int, max_value: int) -> int:
    return safe_int(value, default=default, min_value=min_value, max_value=max_value)


def _error_payload(message: str, code: str = "INTERNAL_ERROR", details: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": False,
        "error": str(message),
        "error_code": str(code),
        "error_message": str(message),
    }
    if details is not None:
        payload["details"] = details
    return payload


def _extract_json_payload(text: str) -> Any | None:
    raw = str(text or "").strip()
    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    for lch, rch in (("{", "}"), ("[", "]")):
        start = raw.find(lch)
        end = raw.rfind(rch)
        if start != -1 and end != -1 and end > start:
            candidate = raw[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return None


def _test_xgj_connection(
    *,
    app_key: str,
    app_secret: str,
    base_url: str,
    mode: str = "self_developed",
    seller_id: str = "",
) -> dict[str, Any]:
    from src.integrations.xianguanjia.open_platform_client import OpenPlatformClient

    client = OpenPlatformClient(
        base_url=base_url,
        app_key=app_key,
        app_secret=app_secret,
        mode=mode,
        seller_id=seller_id,
        timeout=8.0,
    )
    t0 = time.time()
    resp = client.list_authorized_users()
    latency = int((time.time() - t0) * 1000)
    if resp.ok:
        return {"ok": True, "message": "连通", "latency_ms": latency}
    return {"ok": False, "message": resp.error_message or "连接失败", "latency_ms": latency}


DEFAULT_WEIGHT_TEMPLATE = (
    "{origin_province}到{dest_province} {billing_weight}kg 参考价格\n"
    "{courier}: {price} 元\n"
    "预计时效：{eta_days}\n"
    "重要提示：\n"
    "体积重大于实际重量时按体积计费！"
)
DEFAULT_VOLUME_TEMPLATE = (
    "{origin_province}到{dest_province} {billing_weight}kg 参考价格\n"
    "体积重规则：{volume_formula}\n"
    "{courier}: {price} 元\n"
    "预计时效：{eta_days}\n"
    "重要提示：\n"
    "体积重大于实际重量时按体积计费！"
)


def _run_async(coro: Any) -> Any:
    return run_async(coro)


def _now_iso() -> str:
    return now_iso()

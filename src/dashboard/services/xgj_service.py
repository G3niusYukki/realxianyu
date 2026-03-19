"""Xianyu Guan Jia (闲管家) integration service extracted from MimicOps."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from src.dashboard.config_service import (
    read_system_config as _read_system_config,
)

logger = logging.getLogger(__name__)


class XGJService:
    """Service for 闲管家 (Xianyu Guan Jia) order and product callbacks."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    # ------------------------------------------------------------------
    # Static env helpers (shared logic; no self state needed)
    # ------------------------------------------------------------------

    @staticmethod
    def _to_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        text = str(value or "").strip().lower()
        if not text:
            return default
        return text in {"1", "true", "yes", "on", "enabled"}

    @staticmethod
    def _get_env_bool(key: str, default: bool = False) -> bool:
        raw = os.getenv(key, "")
        return XGJService._to_bool(raw, default=default)

    @staticmethod
    def _get_env_value(key: str) -> str:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            key_norm = f"{key}="
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith(key_norm):
                    return line[len(key_norm) :]
        return os.getenv(key, "")

    @staticmethod
    def _mask_secret(value: str) -> str:
        text = str(value or "").strip()
        if len(text) <= 6:
            return "*" * len(text)
        return text[:3] + "*" * (len(text) - 6) + text[-3:]

    # ------------------------------------------------------------------
    # Class-level config helpers
    # ------------------------------------------------------------------

    @classmethod
    def _get_xianguanjia_settings(cls) -> dict[str, Any]:
        app_key = cls._get_env_value("XGJ_APP_KEY").strip()
        app_secret = cls._get_env_value("XGJ_APP_SECRET").strip()
        merchant_id = cls._get_env_value("XGJ_MERCHANT_ID").strip()
        base_url = cls._get_env_value("XGJ_BASE_URL").strip() or "https://open.goofish.pro"
        auto_price_enabled = cls._get_env_bool("XGJ_AUTO_PRICE_ENABLED", default=True)
        auto_ship_enabled = cls._get_env_bool("XGJ_AUTO_SHIP_ENABLED", default=True)
        auto_ship_on_paid = cls._get_env_bool("XGJ_AUTO_SHIP_ON_PAID", default=True)
        return {
            "configured": bool(app_key and app_secret),
            "app_key": app_key,
            "app_secret": app_secret,
            "merchant_id": merchant_id,
            "base_url": base_url,
            "auto_price_enabled": auto_price_enabled,
            "auto_ship_enabled": auto_ship_enabled,
            "auto_ship_on_paid": auto_ship_on_paid,
        }

    @classmethod
    def _xianguanjia_service_config(cls) -> dict[str, Any]:
        settings = cls._get_xianguanjia_settings()
        sys_cfg = _read_system_config()
        xgj_sys = sys_cfg.get("xianguanjia", {}) if isinstance(sys_cfg.get("xianguanjia"), dict) else {}

        # Fallback to system_config when env is empty
        app_key = (settings["app_key"] or "").strip() or str(xgj_sys.get("app_key", "")).strip()
        app_secret = (settings["app_secret"] or "").strip() or str(xgj_sys.get("app_secret", "")).strip()
        base_url = (
            (settings["base_url"] or "").strip()
            or str(xgj_sys.get("base_url", "")).strip()
            or "https://open.goofish.pro"
        )
        merchant_id = (settings["merchant_id"] or "").strip() or str(xgj_sys.get("merchant_id", "")).strip() or None

        merged_xgj = dict(xgj_sys)
        merged_xgj.update(
            {
                "enabled": bool(app_key and app_secret),
                "app_key": app_key,
                "app_secret": app_secret,
                "merchant_id": merchant_id or None,
                "base_url": base_url,
            }
        )

        result: dict[str, Any] = {"xianguanjia": merged_xgj}
        oss_cfg = sys_cfg.get("oss")
        if isinstance(oss_cfg, dict) and oss_cfg:
            clean_oss = {k: v for k, v in oss_cfg.items() if v and not str(v).endswith("****")}
            if clean_oss:
                result["oss"] = clean_oss
        return result

    # ------------------------------------------------------------------
    # Public API (instance methods, require project_root)
    # ------------------------------------------------------------------

    def get_xianguanjia_settings(self) -> dict[str, Any]:
        settings = XGJService._get_xianguanjia_settings()
        return {
            "success": True,
            "configured": settings["configured"],
            "app_key": settings["app_key"],
            "app_secret_masked": XGJService._mask_secret(settings["app_secret"]),
            "merchant_id": settings["merchant_id"],
            "base_url": settings["base_url"],
            "auto_price_enabled": settings["auto_price_enabled"],
            "auto_ship_enabled": settings["auto_ship_enabled"],
            "auto_ship_on_paid": settings["auto_ship_on_paid"],
            "callback_url": "/api/orders/callback",
        }

    def save_xianguanjia_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = dict(payload or {})
        updates = {
            "XGJ_APP_KEY": str(data.get("app_key") or XGJService._get_env_value("XGJ_APP_KEY")).strip(),
            "XGJ_APP_SECRET": str(data.get("app_secret") or XGJService._get_env_value("XGJ_APP_SECRET")).strip(),
            "XGJ_MERCHANT_ID": str(data.get("merchant_id") or XGJService._get_env_value("XGJ_MERCHANT_ID")).strip(),
            "XGJ_BASE_URL": str(data.get("base_url") or XGJService._get_env_value("XGJ_BASE_URL")).strip()
            or "https://open.goofish.pro",
            "XGJ_AUTO_PRICE_ENABLED": "1"
            if XGJService._to_bool(
                data.get("auto_price_enabled"),
                default=XGJService._get_env_bool("XGJ_AUTO_PRICE_ENABLED", True),
            )
            else "0",
            "XGJ_AUTO_SHIP_ENABLED": "1"
            if XGJService._to_bool(
                data.get("auto_ship_enabled"),
                default=XGJService._get_env_bool("XGJ_AUTO_SHIP_ENABLED", True),
            )
            else "0",
            "XGJ_AUTO_SHIP_ON_PAID": "1"
            if XGJService._to_bool(
                data.get("auto_ship_on_paid"),
                default=XGJService._get_env_bool("XGJ_AUTO_SHIP_ON_PAID", True),
            )
            else "0",
        }
        for key, value in updates.items():
            self._set_env_value(key, value)

        saved = self.get_xianguanjia_settings()
        saved["message"] = "闲管家设置已更新"
        return saved

    def _set_env_value(self, key: str, value: str) -> None:
        """Write a key=value line to .env file."""
        env_path = self.project_root / ".env"
        key_norm = f"{key}="
        lines = []
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        updated = False
        for idx, line in enumerate(lines):
            if line.startswith(key_norm):
                lines[idx] = f"{key}={value}"
                updated = True
                break
        if not updated:
            lines.append(f"{key}={value}")
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        os.environ[key] = value

    def retry_xianguanjia_delivery(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.modules.orders.service import OrderFulfillmentService
        from src.dashboard.mimic_ops import _error_payload

        svc_cfg = XGJService._xianguanjia_service_config()
        if not (svc_cfg.get("xianguanjia", {}).get("enabled", False)):
            return _error_payload("闲管家凭证未配置", code="XGJ_NOT_CONFIGURED")

        data = dict(payload or {})
        shipping_info = data.get("shipping_info")
        if not isinstance(shipping_info, dict):
            shipping_info = {}

        for field in (
            "order_no",
            "waybill_no",
            "express_code",
            "express_name",
            "ship_name",
            "ship_mobile",
            "ship_province",
            "ship_city",
            "ship_area",
            "ship_address",
        ):
            if field in data and data.get(field) not in (None, ""):
                shipping_info[field] = data.get(field)

        order_id = str(data.get("order_id") or data.get("order_no") or "").strip()
        if not order_id:
            return _error_payload("缺少订单号", code="MISSING_ORDER_ID")

        service = OrderFulfillmentService(
            db_path=str(self.project_root / "data" / "orders.db"),
            config=XGJService._xianguanjia_service_config(),
        )
        try:
            result = service.deliver(
                order_id=order_id,
                dry_run=XGJService._to_bool(data.get("dry_run"), default=False),
                shipping_info=shipping_info or None,
            )
        except Exception as exc:
            return _error_payload(f"发货重试失败: {exc}", code="XGJ_RETRY_SHIP_FAILED")
        return {"success": True, **result}

    def retry_xianguanjia_price(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.modules.operations.service import OperationsService
        from src.dashboard.mimic_ops import _error_payload, _run_async

        svc_cfg = XGJService._xianguanjia_service_config()
        if not (svc_cfg.get("xianguanjia", {}).get("enabled", False)):
            return _error_payload("闲管家凭证未配置", code="XGJ_NOT_CONFIGURED")

        data = dict(payload or {})
        product_id = str(data.get("product_id") or data.get("productId") or "").strip()
        if not product_id:
            return _error_payload("缺少商品 ID", code="MISSING_PRODUCT_ID")

        try:
            new_price = float(data.get("new_price"))
        except Exception:
            return _error_payload("缺少有效的新价格", code="INVALID_NEW_PRICE")

        original_price_raw = data.get("original_price")
        original_price = None
        if original_price_raw not in (None, ""):
            try:
                original_price = float(original_price_raw)
            except Exception:
                return _error_payload("原价格式无效", code="INVALID_ORIGINAL_PRICE")

        service = OperationsService(config=XGJService._xianguanjia_service_config())
        try:
            result = _run_async(service.update_price(product_id, new_price, original_price))
        except Exception as exc:
            return _error_payload(f"改价重试失败: {exc}", code="XGJ_RETRY_PRICE_FAILED")
        return {"success": bool(result.get("success")), **result}

    def handle_order_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.modules.orders.service import OrderFulfillmentService
        from src.dashboard.mimic_ops import _error_payload

        data = dict(payload or {})
        svc_cfg = XGJService._xianguanjia_service_config()
        xgj_enabled = bool(svc_cfg.get("xianguanjia", {}).get("enabled", False))
        service = OrderFulfillmentService(
            db_path=str(self.project_root / "data" / "orders.db"),
            config=svc_cfg,
        )

        sys_cfg = _read_system_config()
        delivery_cfg = sys_cfg.get("delivery", {})
        settings = XGJService._get_xianguanjia_settings()
        auto_delivery_override = delivery_cfg.get("auto_delivery")
        if auto_delivery_override is not None:
            use_auto = bool(auto_delivery_override) and xgj_enabled
        else:
            use_auto = bool(xgj_enabled and settings["auto_ship_enabled"] and settings["auto_ship_on_paid"])

        try:
            result = service.process_callback(
                data,
                dry_run=XGJService._to_bool(data.get("dry_run"), default=False),
                auto_deliver=use_auto,
            )
        except Exception as exc:
            return _error_payload(f"回调处理失败: {exc}", code="XGJ_CALLBACK_FAILED")

        result["settings"] = {
            "configured": settings["configured"],
            "auto_ship_enabled": settings["auto_ship_enabled"],
            "auto_ship_on_paid": settings["auto_ship_on_paid"],
            "auto_delivery_source": "system_config" if auto_delivery_override is not None else "env",
        }
        return result

    def handle_order_push(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle order push notification from Xianyu.

        Processes order callback AND triggers auto-price-modify for
        status 11 (pending payment) orders asynchronously.
        """
        order_status = payload.get("order_status")
        order_no = str(payload.get("order_no", ""))

        callback_result = self.handle_order_callback(payload)

        if order_status == 11 and order_no:
            sys_cfg = _read_system_config()
            apm_cfg = sys_cfg.get("auto_price_modify", {})
            if apm_cfg.get("enabled"):
                import threading

                t = threading.Thread(
                    target=self._auto_modify_price_sync,
                    args=(order_no, payload, apm_cfg),
                    daemon=True,
                )
                t.start()
                callback_result["auto_price_modify_triggered"] = True

        return callback_result

    def _auto_modify_price_sync(self, order_no: str, push_payload: dict[str, Any], apm_cfg: dict[str, Any]) -> None:
        """Background thread: look up quote and modify order price."""
        try:
            from src.integrations.xianguanjia.open_platform_client import OpenPlatformClient
            from src.modules.quote.ledger import get_quote_ledger

            settings = XGJService._get_xianguanjia_settings()
            if not settings["configured"]:
                logger.warning("Auto-price-modify: xianguanjia not configured")
                return

            xgj_cfg = XGJService._xianguanjia_service_config().get("xianguanjia", {})
            client_fields = {"base_url", "app_key", "app_secret", "timeout", "mode", "seller_id"}
            client_kwargs = {k: v for k, v in xgj_cfg.items() if k in client_fields and v}
            client = OpenPlatformClient(**client_kwargs)

            detail_resp = client.get_order_detail({"order_no": order_no})
            if not detail_resp.ok:
                logger.warning("Auto-price-modify: failed to get order detail for %s", order_no)
                return

            detail = detail_resp.data or {}
            buyer_nick = str(detail.get("buyer_nick", ""))
            buyer_eid = str(detail.get("buyer_eid", "")).strip()
            goods = detail.get("goods") or {}
            item_id = str(goods.get("item_id", ""))
            total_amount = int(detail.get("total_amount", 0))

            if not buyer_nick and not buyer_eid:
                logger.info("Auto-price-modify: no buyer_nick/buyer_eid in order %s", order_no)
                return

            max_age = int(apm_cfg.get("max_quote_age_seconds", 7200))
            ledger = get_quote_ledger()
            quote = ledger.find_by_buyer(
                buyer_nick,
                item_id=item_id,
                max_age_seconds=max_age,
                sender_user_id=buyer_eid,
            )

            if not quote:
                fallback = apm_cfg.get("fallback_action", "skip")
                if fallback == "use_listing_price":
                    logger.info(
                        "Auto-price-modify: no quote for buyer=%s order=%s, "
                        "fallback=use_listing_price — accepting at current price",
                        buyer_nick,
                        order_no,
                    )
                    return
                logger.info(
                    "Auto-price-modify: no matching quote for buyer=%s order=%s, fallback=%s",
                    buyer_nick,
                    order_no,
                    fallback,
                )
                return

            quote_rows = quote.get("quote_rows", [])
            courier_choice = quote.get("courier_choice", "")

            target_fee = None
            if courier_choice:
                for row in quote_rows:
                    if str(row.get("courier", "")).strip() == courier_choice.strip():
                        target_fee = row.get("total_fee")
                        break
            if target_fee is None and quote_rows:
                target_fee = min(r.get("total_fee", 0) for r in quote_rows if r.get("total_fee"))

            if target_fee is None:
                logger.info("Auto-price-modify: no valid fee in quote for order=%s", order_no)
                return

            target_price_cents = round(float(target_fee) * 100)
            express_fee_cents = int(float(apm_cfg.get("default_express_fee", 0)) * 100)

            if target_price_cents == total_amount:
                logger.info("Auto-price-modify: price already correct for order=%s", order_no)
                return

            import time as _time

            retry_delays = (2, 4, 8)
            last_exc = None
            modify_resp = None
            for attempt in range(1 + len(retry_delays)):
                try:
                    modify_resp = client.modify_order_price(
                        {
                            "order_no": order_no,
                            "order_price": target_price_cents,
                            "express_fee": express_fee_cents,
                        }
                    )
                    if modify_resp.ok:
                        logger.info(
                            "Auto-price-modify: SUCCESS order=%s from=%d to=%d (express=%d)",
                            order_no,
                            total_amount,
                            target_price_cents,
                            express_fee_cents,
                        )
                        self._mark_order_processed_in_poller(order_no)
                        return
                    last_exc = None
                    if not getattr(modify_resp, "retryable", False) or attempt >= len(retry_delays):
                        break
                    delay = retry_delays[attempt]
                    logger.info(
                        "Auto-price-modify: retry in %ds (attempt %d) order=%s error=%s",
                        delay,
                        attempt + 1,
                        order_no,
                        modify_resp.error_message,
                    )
                    _time.sleep(delay)
                except Exception as exc:
                    last_exc = exc
                    if attempt >= len(retry_delays):
                        break
                    from src.integrations.xianguanjia.errors import is_retryable_error

                    if not is_retryable_error(exc):
                        raise
                    delay = retry_delays[attempt]
                    logger.info(
                        "Auto-price-modify: retry in %ds (attempt %d) order=%s exc=%s",
                        delay,
                        attempt + 1,
                        order_no,
                        type(exc).__name__,
                    )
                    _time.sleep(delay)

            if modify_resp is not None and not modify_resp.ok:
                logger.warning(
                    "Auto-price-modify: FAILED order=%s error=%s",
                    order_no,
                    modify_resp.error_message,
                )
            if last_exc is not None:
                raise last_exc

        except Exception:
            logger.error("Auto-price-modify: unexpected error for order=%s", order_no, exc_info=True)

    @staticmethod
    def _mark_order_processed_in_poller(order_no: str) -> None:
        """Notify the poller that this order was already handled by the push callback."""
        try:
            from src.modules.orders.auto_price_poller import get_price_poller

            poller = get_price_poller()
            if poller is not None:
                poller._processed[order_no] = __import__("time").time()
        except Exception:
            pass

    def _resolve_session_id_for_order(self, order_no: str) -> str:
        """Try to find the chat session_id for a given order.

        Priority: local orders DB > QuoteLedger (via buyer_nick) > ws_live reverse map.
        """
        from src.integrations.xianguanjia.open_platform_client import OpenPlatformClient
        from src.modules.messages.ws_live import get_session_by_buyer_nick
        from src.modules.orders.service import OrderFulfillmentService
        from src.modules.quote.ledger import get_quote_ledger

        # 1. Check local orders DB
        try:
            ofs = OrderFulfillmentService(config=XGJService._xianguanjia_service_config())
            order = ofs.get_order(order_no)
            if order and str(order.get("session_id", "")).strip():
                return str(order["session_id"]).strip()
        except Exception:
            pass

        # 2. Get buyer_nick via Xianyu API, then check QuoteLedger
        buyer_nick = ""
        try:
            xgj_cfg = XGJService._xianguanjia_service_config().get("xianguanjia", {})
            client_fields = {"base_url", "app_key", "app_secret", "timeout", "mode", "seller_id"}
            client_kwargs = {k: v for k, v in xgj_cfg.items() if k in client_fields and v}
            if client_kwargs.get("app_key") and client_kwargs.get("app_secret"):
                client = OpenPlatformClient(**client_kwargs)
                detail_resp = client.get_order_detail({"order_no": order_no})
                if detail_resp.ok and isinstance(detail_resp.data, dict):
                    buyer_nick = str(detail_resp.data.get("buyer_nick", "")).strip()
        except Exception:
            pass

        if buyer_nick:
            try:
                quote = get_quote_ledger().find_by_buyer(buyer_nick)
                if quote and str(quote.get("session_id", "")).strip():
                    return str(quote["session_id"]).strip()
            except Exception:
                pass

        # 3. ws_live reverse map
        try:
            sid = get_session_by_buyer_nick(buyer_nick) if buyer_nick else ""
            if sid:
                return sid
        except Exception:
            pass

        return ""

    def handle_product_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle product callback notification (async publish result)."""
        product_id = payload.get("product_id")
        task_type = payload.get("task_type")
        task_result = payload.get("task_result")
        err_code = payload.get("err_code", "")
        err_msg = payload.get("err_msg", "")

        logger.info(
            "Product callback: product_id=%s task_type=%s result=%s err=%s/%s",
            product_id,
            task_type,
            task_result,
            err_code,
            err_msg,
        )

        if product_id and task_type in (10, 11):
            try:
                from src.modules.listing.publish_queue import PublishQueue

                queue = PublishQueue(project_root=self.project_root)
                for item in queue.get_queue():
                    pid = (
                        item.get("published_product_id")
                        if isinstance(item, dict)
                        else getattr(item, "published_product_id", None)
                    )
                    status = item.get("status") if isinstance(item, dict) else getattr(item, "status", None)
                    item_id_val = item.get("id") if isinstance(item, dict) else getattr(item, "id", None)
                    if pid == product_id and status == "publishing":
                        if task_result == 1:
                            queue.update_item(
                                item_id_val,
                                {
                                    "status": "published",
                                    "error": None,
                                },
                            )
                            logger.info("Product callback: marked queue item %s as published", item_id_val)
                        elif task_result == 2:
                            queue.update_item(
                                item_id_val,
                                {
                                    "status": "failed",
                                    "error": f"上架失败: [{err_code}] {err_msg}",
                                },
                            )
                            logger.warning("Product callback: marked queue item %s as failed: %s", item_id_val, err_msg)
                        break
            except Exception:
                logger.error("Product callback: failed to update publish queue", exc_info=True)

        return {"success": True, "product_id": product_id, "task_result": task_result}

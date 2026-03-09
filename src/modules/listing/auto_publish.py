"""自动上架编排器。

完整流程:
1. AI 生成标题/描述 (ContentService)
2. 选择模板 + 生成商品图片 (image_generator)
3. 合规检查 (ComplianceGuard)
4. 上传图片到 OSS (OSSUploader)
5. 获取 user_name (OpenPlatformClient.list_authorized_users)
6. 调用闲管家 API 创建商品 (OpenPlatformClient.create_product)
7. 调用闲管家 API 上架商品 (OpenPlatformClient.publish_product)

上架为异步操作，最终结果通过商品回调通知确认。
"""

from __future__ import annotations

import time
from typing import Any

from src.core.compliance import get_compliance_guard
from src.core.logger import get_logger
from src.integrations.xianguanjia.open_platform_client import OpenPlatformClient
from src.modules.content.service import ContentService

from .brand_assets import BrandAssetManager
from .image_generator import generate_frame_images, generate_product_images, get_available_categories
from .oss_uploader import OSSUploader

logger = get_logger()

_XGJ_CLIENT_FIELDS = {"base_url", "app_key", "app_secret", "timeout", "mode", "seller_id"}


class AutoPublishService:
    """自动上架服务。"""

    def __init__(
        self,
        *,
        api_client: OpenPlatformClient | None = None,
        content_service: ContentService | None = None,
        oss_uploader: OSSUploader | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.config = config or {}
        if api_client is not None:
            self.api_client = api_client
        elif self.config.get("xianguanjia"):
            try:
                xgj_raw = self.config["xianguanjia"]
                client_kwargs = {k: v for k, v in xgj_raw.items() if k in _XGJ_CLIENT_FIELDS and v}
                self.api_client = OpenPlatformClient(**client_kwargs)
                logger.info("AutoPublishService: auto-constructed OpenPlatformClient from config")
            except Exception as exc:
                logger.warning("AutoPublishService: failed to construct OpenPlatformClient: %s", exc)
                self.api_client = None
        else:
            self.api_client = None
        self.content_service = content_service or ContentService()
        self.oss_uploader = oss_uploader or OSSUploader(self.config.get("oss"))
        self.compliance = get_compliance_guard()
        self._publish_defaults = self.config.get("xianguanjia", {}) if self.config else {}

    async def generate_preview(self, product_config: dict[str, Any]) -> dict[str, Any]:
        """生成上架预览（不实际发布），返回预览数据供前端展示或人工确认。

        支持 frame_id + brand_asset_ids 使用新 Frame 模板系统，
        也兼容旧模板系统（无 frame_id 时 fallback）。
        """
        category = str(product_config.get("category", "exchange")).strip()
        product_name = str(product_config.get("name", "")).strip()
        features = product_config.get("features") or []
        price = product_config.get("price")
        extra_params = product_config.get("template_params") or {}
        frame_id = product_config.get("frame_id")
        brand_asset_ids = product_config.get("brand_asset_ids") or []

        content = self.content_service.generate_listing_content({
            "name": product_name or category,
            "features": features,
            "category": category,
            "condition": product_config.get("condition", "全新"),
            "reason": product_config.get("reason", "闲置出"),
            "tags": product_config.get("tags", []),
            "extra_info": product_config.get("extra_info"),
        })

        title = product_config.get("title") or content.get("title", product_name)
        description = product_config.get("description") or content.get("description", "")

        compliance_result = content.get("compliance", {})
        if compliance_result.get("blocked"):
            return {
                "ok": False,
                "step": "compliance",
                "error": compliance_result.get("message", "内容合规检查未通过"),
                "compliance": compliance_result,
            }

        local_images: list[str] = []

        if frame_id:
            brand_items = self._load_brand_items(brand_asset_ids, category)
            frame_params = {
                "headline": extra_params.get("headline", title),
                "sub_headline": extra_params.get("sub_headline", ""),
                "labels": extra_params.get("labels", ""),
                "tagline": extra_params.get("tagline", ""),
                "brand_items": brand_items,
            }
            local_images = await generate_frame_images(
                frame_id=frame_id,
                category=category,
                params=frame_params,
            )
        else:
            image_params = [{
                "title": title,
                "desc": description[:80] if description else "",
                "badge": extra_params.get("badge", ""),
                "features": features[:6],
                "price": price,
                "footer": extra_params.get("footer", ""),
                **extra_params,
            }]
            local_images = await generate_product_images(
                category=category,
                params_list=image_params,
            )

        return {
            "ok": True,
            "step": "preview",
            "title": title,
            "description": description,
            "category": category,
            "price": price,
            "frame_id": frame_id,
            "brand_asset_ids": brand_asset_ids,
            "local_images": local_images,
            "compliance": compliance_result,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _load_brand_items(
        self, brand_asset_ids: list[str], category: str
    ) -> list[dict[str, str]]:
        """加载品牌图片为模板可用的 brand_items 列表。"""
        mgr = BrandAssetManager()

        if brand_asset_ids:
            ids_to_load = brand_asset_ids
        else:
            assets = mgr.list_assets(category=category)
            ids_to_load = [a["id"] for a in assets]

        items: list[dict[str, str]] = []
        for aid in ids_to_load:
            entry = None
            for a in mgr.list_assets():
                if a["id"] == aid:
                    entry = a
                    break
            if entry is None:
                continue
            path = mgr.get_asset_path(aid)
            if path is None:
                continue
            from .brand_assets import file_to_data_uri
            items.append({
                "name": entry["name"],
                "src": file_to_data_uri(path),
            })
        return items

    async def publish(self, product_config: dict[str, Any]) -> dict[str, Any]:
        """执行完整自动上架流程：创建商品 -> 上架商品。"""
        if not self.api_client:
            return {"ok": False, "step": "init", "error": "api_client_not_configured"}

        preview = await self.generate_preview(product_config)
        if not preview.get("ok"):
            return preview

        rate_check = await self.compliance.evaluate_publish_rate(
            f"auto_publish:{product_config.get('account_id', 'global')}"
        )
        if rate_check.get("blocked"):
            return {
                "ok": False,
                "step": "rate_limit",
                "error": rate_check.get("message", "发布频率限制"),
            }

        local_images = preview.get("local_images", [])
        if not local_images:
            return {"ok": False, "step": "image_gen", "error": "没有生成图片"}

        if not self.oss_uploader.configured:
            return {"ok": False, "step": "oss_upload", "error": "OSS 未配置"}

        image_urls = self.oss_uploader.upload_batch(local_images)
        if not image_urls:
            return {"ok": False, "step": "oss_upload", "error": "图片上传失败"}

        user_name = self._get_user_name()

        payload = self._build_create_payload(
            title=preview["title"],
            description=preview["description"],
            price=preview.get("price"),
            image_urls=image_urls,
            user_name=user_name,
            defaults=self._publish_defaults,
            extra=product_config.get("api_payload"),
        )

        create_resp = self.api_client.create_product(payload)
        if not create_resp.ok:
            return {
                "ok": False,
                "step": "api_create",
                "error": create_resp.error_message or "商品创建失败",
                "api_response": create_resp.to_dict() if hasattr(create_resp, "to_dict") else str(create_resp),
            }

        product_data = create_resp.data or {}
        product_id = product_data.get("product_id")
        if not product_id:
            return {"ok": False, "step": "api_create", "error": "创建成功但未返回 product_id"}

        publish_result = self._publish_product(
            product_id=product_id,
            user_name=user_name,
            scheduled_time=product_config.get("scheduled_time"),
        )
        if not publish_result["ok"]:
            return publish_result

        return {
            "ok": True,
            "step": "publishing",
            "product_id": product_id,
            "title": preview["title"],
            "image_urls": image_urls,
            "publish_async": True,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    async def publish_from_preview(self, preview_data: dict[str, Any]) -> dict[str, Any]:
        """从预览数据直接发布（人工确认后调用）。"""
        if not self.api_client:
            return {"ok": False, "step": "init", "error": "api_client_not_configured"}

        local_images = preview_data.get("local_images", [])
        if not local_images:
            return {"ok": False, "step": "image_gen", "error": "预览数据中没有图片"}

        if not self.oss_uploader.configured:
            return {"ok": False, "step": "oss_upload", "error": "OSS 未配置"}

        image_urls = self.oss_uploader.upload_batch(local_images)
        if not image_urls:
            return {"ok": False, "step": "oss_upload", "error": "图片上传失败"}

        user_name = self._get_user_name()

        payload = self._build_create_payload(
            title=preview_data.get("title", ""),
            description=preview_data.get("description", ""),
            price=preview_data.get("price"),
            image_urls=image_urls,
            user_name=user_name,
            defaults=self._publish_defaults,
            extra=preview_data.get("api_payload"),
        )

        create_resp = self.api_client.create_product(payload)
        if not create_resp.ok:
            return {
                "ok": False,
                "step": "api_create",
                "error": create_resp.error_message or "商品创建失败",
            }

        product_data = create_resp.data or {}
        product_id = product_data.get("product_id")
        if not product_id:
            return {"ok": False, "step": "api_create", "error": "创建成功但未返回 product_id"}

        publish_result = self._publish_product(
            product_id=product_id,
            user_name=user_name,
            scheduled_time=preview_data.get("scheduled_time"),
        )
        if not publish_result["ok"]:
            return publish_result

        return {
            "ok": True,
            "step": "publishing",
            "product_id": product_id,
            "title": preview_data.get("title"),
            "image_urls": image_urls,
            "publish_async": True,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _publish_product(
        self,
        *,
        product_id: int,
        user_name: str,
        scheduled_time: int | None = None,
    ) -> dict[str, Any]:
        """调用 publish_product API 将草稿商品上架（异步操作）。"""
        if not self.api_client:
            return {"ok": False, "step": "api_publish", "error": "api_client_not_configured"}

        publish_payload: dict[str, Any] = {
            "product_id": product_id,
            "user_name": user_name,
        }
        if scheduled_time:
            publish_payload["specify_publish_time"] = int(scheduled_time)

        resp = self.api_client.publish_product(publish_payload)
        if not resp.ok:
            return {
                "ok": False,
                "step": "api_publish",
                "error": resp.error_message or "商品上架请求失败",
                "product_id": product_id,
            }
        return {"ok": True, "step": "api_publish", "product_id": product_id}

    def _get_user_name(self) -> str:
        """从闲管家获取授权用户名。"""
        if not self.api_client:
            return ""
        try:
            resp = self.api_client.list_authorized_users()
            if resp.ok and isinstance(resp.data, list) and resp.data:
                first_user = resp.data[0]
                if isinstance(first_user, dict):
                    return str(first_user.get("user_name") or first_user.get("nick_name") or "")
        except Exception as e:
            logger.warning(f"Failed to get authorized user name: {e}")
        return ""

    @staticmethod
    def _build_create_payload(
        *,
        title: str,
        description: str,
        price: float | int | None,
        image_urls: list[str],
        user_name: str = "",
        defaults: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """构建符合闲管家 create_product API 规范的请求体。

        必填字段：title, content, images, item_biz_type, sp_biz_type,
        channel_cat_id, express_fee, stock, stuff_status, province, city, district。
        user_name 通过 publish_shop 数组传入。
        """
        d = defaults or {}

        payload: dict[str, Any] = {
            "title": title,
            "content": description,
            "images": image_urls[:9],
            "item_biz_type": int(d.get("default_item_biz_type", 2)),
            "sp_biz_type": int(d.get("default_sp_biz_type", 2)),
            "channel_cat_id": str(d.get("default_channel_cat_id", "")),
            "stuff_status": str(d.get("default_stuff_status", "1")),
            "stock": int(d.get("default_stock", 1)),
            "express_fee": int(d.get("default_express_fee", 0)),
            "province": str(d.get("default_province", "")),
            "city": str(d.get("default_city", "")),
            "district": str(d.get("default_district", "")),
        }

        if price is not None:
            payload["price"] = int(float(price) * 100)

        if user_name:
            payload["publish_shop"] = [{"user_name": user_name}]

        if extra and isinstance(extra, dict):
            payload.update(extra)

        return payload

    @staticmethod
    def list_categories() -> list[dict[str, str]]:
        return get_available_categories()

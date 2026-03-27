import json
import os
from typing import Any

import httpx

from app.signing import sign_request


class XianyuConfig:
    """闲管家配置类"""

    def __init__(self):
        self.app_key = os.getenv("XIANYU_APP_KEY", "")
        self.app_secret = os.getenv("XIANYU_APP_SECRET", "")
        self.base_url = os.getenv("XIANYU_BASE_URL", "https://api.xianyu.com")

    @property
    def is_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)


class XianGuanJiaClient:
    """闲管家 HTTP 客户端"""

    def __init__(self, config: XianyuConfig):
        self.config = config
        self.client = httpx.AsyncClient(base_url=config.base_url, timeout=30.0)

    async def _request(
        self, method: str, path: str, payload: dict | None = None
    ) -> dict:
        """
        发送带签名的请求

        Args:
            method: HTTP 方法
            path: API 路径
            payload: 请求体数据

        Returns:
            API 响应数据
        """
        import time

        payload = payload or {}
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        timestamp = str(int(time.time() * 1000))

        # 生成签名
        signature = sign_request(
            self.config.app_key, self.config.app_secret, body, timestamp
        )

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "X-App-Key": self.config.app_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
        }

        # 发送请求
        response = await self.client.request(
            method=method.upper(),
            url=path,
            content=body.encode("utf-8"),
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def list_authorized_users(self) -> dict:
        """获取已授权用户列表"""
        return await self._request("POST", "/openapi/users/authorized")

    async def list_products(self, page: int = 1, page_size: int = 20) -> dict:
        """
        获取商品列表

        Args:
            page: 页码
            page_size: 每页数量
        """
        payload = {"page": page, "pageSize": page_size}
        return await self._request("POST", "/openapi/products/list", payload)

    async def create_product(self, product: dict) -> dict:
        """
        创建商品

        Args:
            product: 商品数据
        """
        return await self._request("POST", "/openapi/products/create", product)

    async def list_orders(
        self, status: str | None = None, page: int = 1, page_size: int = 20
    ) -> dict:
        """
        获取订单列表

        Args:
            status: 订单状态
            page: 页码
            page_size: 每页数量
        """
        payload = {"page": page, "pageSize": page_size}
        if status:
            payload["status"] = status
        return await self._request("POST", "/openapi/orders/list", payload)

    async def modify_order_price(self, order_id: str, price: float) -> dict:
        """
        修改订单价格

        Args:
            order_id: 订单 ID
            price: 新价格
        """
        payload = {"orderId": order_id, "price": price}
        return await self._request("POST", "/openapi/orders/modifyPrice", payload)

    async def ship_order(self, order_id: str, shipping: dict) -> dict:
        """
        订单发货

        Args:
            order_id: 订单 ID
            shipping: 物流信息
        """
        payload = {"orderId": order_id, **shipping}
        return await self._request("POST", "/openapi/orders/ship", payload)

from fastapi import APIRouter, Depends, HTTPException, status

from app.client import XianGuanJiaClient, XianyuConfig
from app.routes import get_client, get_config

router = APIRouter()


@router.get("/orders")
async def list_orders(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    client: XianGuanJiaClient = Depends(get_client),
):
    """获取订单列表"""
    return await client.list_orders(status, page, page_size)


@router.post("/orders/{order_id}/price")
async def modify_order_price(
    order_id: str,
    data: dict,
    client: XianGuanJiaClient = Depends(get_client),
):
    """修改订单价格"""
    price = data.get("price")
    if price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="price is required",
        )
    return await client.modify_order_price(order_id, price)


@router.post("/orders/{order_id}/ship")
async def ship_order(
    order_id: str,
    shipping: dict,
    client: XianGuanJiaClient = Depends(get_client),
):
    """订单发货"""
    return await client.ship_order(order_id, shipping)

from fastapi import APIRouter, Depends

from app.client import XianGuanJiaClient, XianyuConfig
from app.routes import get_client, get_config

router = APIRouter()


@router.get("/products")
async def list_products(
    page: int = 1,
    page_size: int = 20,
    client: XianGuanJiaClient = Depends(get_client),
):
    """获取商品列表"""
    return await client.list_products(page, page_size)


@router.post("/products")
async def create_product(
    product: dict,
    client: XianGuanJiaClient = Depends(get_client),
):
    """创建商品"""
    return await client.create_product(product)

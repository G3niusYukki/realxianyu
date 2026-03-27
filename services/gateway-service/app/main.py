import os
from typing import Annotated

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse, Response

from app.client import XianGuanJiaClient
from app.routes import get_client
from app.routes.orders import router as orders_router
from app.routes.products import router as products_router

app = FastAPI(
    title="Gateway Service",
    description="Gateway Service for Xianyu API integration",
    version="0.1.0",
)


@app.get("/")
async def root():
    """根路径元数据，避免浏览器直开时误判服务未启动。"""
    return JSONResponse(
        content={
            "service": "gateway-service",
            "status": "healthy",
            "health": "/health",
            "docs": "/docs",
        },
        status_code=status.HTTP_200_OK,
    )


@app.get("/favicon.ico")
async def favicon():
    """避免浏览器自动请求 favicon 产生 404 噪音。"""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse(
        content={"status": "healthy", "service": "gateway-service"},
        status_code=status.HTTP_200_OK,
    )


@app.get("/api/v1/users/authorized")
async def get_authorized_users(client: Annotated[XianGuanJiaClient, Depends(get_client)]):
    """获取已授权用户列表"""
    return await client.list_authorized_users()


# 注册路由
app.include_router(products_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)

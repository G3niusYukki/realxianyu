from fastapi import Depends, HTTPException, status

from app.client import XianGuanJiaClient, XianyuConfig


def get_config() -> XianyuConfig:
    """从环境变量加载配置"""
    config = XianyuConfig()
    if not config.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Xianyu API not configured",
        )
    return config


def get_client(config: XianyuConfig = Depends(get_config)) -> XianGuanJiaClient:
    """获取客户端实例"""
    return XianGuanJiaClient(config)

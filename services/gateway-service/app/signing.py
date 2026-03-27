import hashlib


def sign_request(app_key: str, app_secret: str, body: str, timestamp: str) -> str:
    """
    闲管家 API 签名算法

    Args:
        app_key: 应用 key
        app_secret: 应用密钥
        body: 请求体字符串
        timestamp: 时间戳字符串

    Returns:
        签名字符串
    """
    # 计算 body 的 md5
    body_md5 = hashlib.md5(body.encode("utf-8")).hexdigest()

    # 拼接签名字符串: appKey,bodyMd5,timestamp,appSecret
    sign_str = f"{app_key},{body_md5},{timestamp},{app_secret}"

    # 计算最终签名
    signature = hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    return signature

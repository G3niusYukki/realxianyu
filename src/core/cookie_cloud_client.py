"""CookieCloud 客户端 — 统一凭证管理与 AES-CBC 解密。

将原先分散在 cookie_grabber.py、dashboard_server.py、CookieService 中
重复的凭证读取 / 密钥派生 / AES 解密逻辑收归此处。
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from src.core.logger import get_logger

logger = get_logger()


class CookieCloudClient:
    """CookieCloud 凭证读取与数据解密。"""

    def __init__(self, uuid: str = "", password: str = "", server: str = "") -> None:
        self.uuid = uuid.strip()
        self.password = password.strip()
        self.server = server.strip()

    # ------------------------------------------------------------------
    # 工厂方法
    # ------------------------------------------------------------------

    @classmethod
    def from_env_and_config(cls) -> CookieCloudClient:
        """从环境变量 → data/system_config.json 降级读取凭证。

        与原 cookie_grabber.py / dashboard_server.py 中的读取逻辑保持完全一致。
        """
        uuid_val = os.environ.get("COOKIE_CLOUD_UUID", "").strip()
        pwd = os.environ.get("COOKIE_CLOUD_PASSWORD", "").strip()
        host = os.environ.get("COOKIE_CLOUD_HOST", "").strip()

        if not uuid_val or not pwd:
            try:
                cfg_path = Path("data/system_config.json")
                if cfg_path.exists():
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                    cc = cfg.get("cookie_cloud", {}) if isinstance(cfg.get("cookie_cloud"), dict) else {}
                    uuid_val = uuid_val or str(cc.get("cookie_cloud_uuid") or cfg.get("cookie_cloud_uuid", "")).strip()
                    pwd = pwd or str(cc.get("cookie_cloud_password") or cfg.get("cookie_cloud_password", "")).strip()
                    host = host or str(cc.get("cookie_cloud_host") or cfg.get("cookie_cloud_host", "")).strip()
            except Exception:
                pass

        return cls(uuid=uuid_val, password=pwd, server=host)

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        return bool(self.uuid and self.password)

    def get_api_url(self) -> str:
        """获取完整的 CookieCloud API URL。"""
        server = self.server or "https://cookiecloud.czy.rs"
        return f"{server.rstrip('/')}/get/{self.uuid}"

    def derive_key(self) -> str:
        """根据 uuid + password 派生 16 字符 AES 密钥。"""
        key_raw = f"{self.uuid}-{self.password}"
        return hashlib.md5(key_raw.encode("utf-8")).hexdigest()[:16]

    # ------------------------------------------------------------------
    # AES-CBC 解密
    # ------------------------------------------------------------------

    @staticmethod
    def decrypt(encrypted: str, key: str) -> dict[str, Any]:
        """解密 CookieCloud AES-CBC 加密数据。

        支持两种模式:
        - legacy (CryptoJS passphrase mode, Salted__ header, EVP_BytesToKey)
        - aes-128-cbc-fixed (zero IV, direct key)

        Copy of the exact logic from cookie_grabber._decrypt_cookiecloud.
        """
        try:
            import base64
            from hashlib import md5 as _md5

            from cryptography.hazmat.primitives import padding as sym_padding
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

            raw = base64.b64decode(encrypted)

            if raw[:8] == b"Salted__":
                salt = raw[8:16]
                ct = raw[16:]
                passphrase = key.encode("utf-8")

                d = b""
                last = b""
                while len(d) < 48:
                    last = _md5(last + passphrase + salt).digest()
                    d += last
                derived_key, iv = d[:32], d[32:48]
            else:
                ct = raw
                derived_key = key.encode("utf-8")[:16]
                iv = b"\x00" * 16

            cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded = decryptor.update(ct) + decryptor.finalize()

            unpadder = sym_padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded) + unpadder.finalize()

            return json.loads(plaintext.decode("utf-8"))
        except Exception as exc:
            logger.debug(f"CookieCloud 解密失败: {exc}")
            return {}

"""Thread-safe Cookie 持久化存储。

所有对 XIANYU_COOKIE_1 的 os.environ 写入和 .env 文件写入
都应通过本模块进行，保证并发安全和文件原子性。
"""

from __future__ import annotations

import os
import re
import tempfile
import threading
from pathlib import Path

from src.core.logger import get_logger

logger = get_logger()

_lock = threading.Lock()
_ENV_KEY = "XIANYU_COOKIE_1"


def save_cookie(cookie_str: str, *, persist: bool = True, source: str = "") -> None:
    """Thread-safe: 写入 os.environ 并可选持久化到 .env 文件。

    persist=True 时使用原子写（先写临时文件再 rename）避免文件损坏。
    """
    with _lock:
        os.environ[_ENV_KEY] = cookie_str
        if persist:
            _atomic_save_to_env(cookie_str)
        if source:
            logger.info(f"Cookie saved (source={source}, length={len(cookie_str)})")


def load_cookie() -> str:
    """Thread-safe: 从 os.environ 读取当前 Cookie。"""
    return os.environ.get(_ENV_KEY, "")


def _atomic_save_to_env(cookie_str: str) -> None:
    """原子写 .env 文件：先写临时文件，再 rename 替换。"""
    env_path = Path(".env")
    try:
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            if f"{_ENV_KEY}=" in content:
                content = re.sub(
                    rf"{_ENV_KEY}=.*",
                    f"{_ENV_KEY}={cookie_str}",
                    content,
                )
            else:
                content += f"\n{_ENV_KEY}={cookie_str}\n"
        else:
            content = f"{_ENV_KEY}={cookie_str}\n"

        dir_path = env_path.parent
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), prefix=".env.", suffix=".tmp")
        closed = False
        try:
            os.write(fd, content.encode("utf-8"))
            os.fsync(fd)
            os.close(fd)
            closed = True
            os.replace(tmp_path, str(env_path))
        except Exception:
            if not closed:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception as exc:
        logger.error(f"Cookie 原子写入 .env 失败: {exc}")

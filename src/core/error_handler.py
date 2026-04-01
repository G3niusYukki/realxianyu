"""
统一异常处理模块
Unified Error Handling

提供异常装饰器和工具函数
"""

from __future__ import annotations

import asyncio
import inspect
import random
from collections.abc import Callable
from functools import wraps
from typing import Any

import httpx

from src.core.logger import get_logger


def safe_execute(
    logger=None,
    default_return: Any = None,
    raise_on_error: bool = False,
    log_level: str = "debug",
    catch: tuple = (Exception,),
    http_aware: bool = False,
):
    """Unified safe execution decorator.

    Args:
        logger: 日志记录器，不指定则使用全局logger
        default_return: 发生异常时返回的默认值
        raise_on_error: 是否在异常时重新抛出
        log_level: "debug" | "warning" | "error"
        catch: Exception types to catch
        http_aware: If True, handle httpx errors specifically with detailed messages
    """

    log_level_ = log_level.lower()

    def _log(logger_instance, msg, *args, **kwargs):
        if log_level_ == "warning":
            logger_instance.warning(msg, *args, **kwargs)
        elif log_level_ == "error":
            logger_instance.error(msg, *args, **kwargs)
        else:
            logger_instance.debug(msg, *args, **kwargs)

    def decorator(func: Callable) -> Callable:
        if http_aware:
            # HTTP-aware wrapper: uses self.logger, handles httpx errors specially.
            # Network/timeout use configured log_level; HTTP status/errors and
            # unexpected exceptions always log at error level (matching original
            # handle_controller_errors behavior).
            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                logger_ = logger or self.logger
                try:
                    return await func(self, *args, **kwargs)
                except (ConnectionError, httpx.ConnectError, httpx.NetworkError) as e:
                    _log(logger_, f"Network connection error in {func.__name__}: {e}")
                    if raise_on_error:
                        raise
                    return default_return
                except httpx.TimeoutException as e:
                    _log(logger_, f"Timeout in {func.__name__}: {e}")
                    if raise_on_error:
                        raise
                    return default_return
                except httpx.HTTPStatusError as e:
                    logger_.error(f"HTTP error in {func.__name__}: {e.response.status_code}")
                    if raise_on_error:
                        raise
                    return default_return
                except httpx.HTTPError as e:
                    logger_.error(f"HTTP request error in {func.__name__}: {e}")
                    if raise_on_error:
                        raise
                    return default_return
                except asyncio.CancelledError:
                    logger_.debug(f"Task cancelled in {func.__name__}")
                    raise
                except catch as e:
                    logger_.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                    if raise_on_error:
                        raise
                    return default_return

            return async_wrapper

        else:
            # Standard wrapper: supports both sync and async
            logger_ = logger or get_logger()

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except catch as e:
                    use_exc_info = log_level_ == "error"
                    _log(logger_, f"Error in {func.__name__}: {e}", exc_info=use_exc_info)
                    if raise_on_error:
                        raise
                    return default_return

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except catch as e:
                    use_exc_info = log_level_ == "error"
                    _log(logger_, f"Error in {func.__name__}: {e}", exc_info=use_exc_info)
                    if raise_on_error:
                        raise
                    return default_return

            return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


# ---------------------------------------------------------------------------
# Backward-compatible aliases (deprecated, will be removed in future version)
# ---------------------------------------------------------------------------


def handle_controller_errors(default_return: Any = None, raise_on_error: bool = False):
    """控制器操作异常处理装饰器 (deprecated: use safe_execute with http_aware=True)."""
    return safe_execute(
        default_return=default_return,
        raise_on_error=raise_on_error,
        log_level="warning",
        http_aware=True,
    )


def handle_operation_errors(default_return: Any = False, raise_on_error: bool = False):
    """操作异常处理装饰器 (deprecated: use safe_execute)."""
    return safe_execute(
        default_return=default_return,
        raise_on_error=raise_on_error,
        log_level="debug",
    )


def handle_errors(
    exceptions: tuple | None = None,
    default_return: Any = None,
    logger=None,
    raise_on_error: bool = False,
):
    """通用异常处理装饰器 (deprecated: use safe_execute with log_level='error')."""
    return safe_execute(
        logger=logger,
        default_return=default_return,
        raise_on_error=raise_on_error,
        log_level="error",
        catch=exceptions or (Exception,),
    )


# ---------------------------------------------------------------------------
# Keep retry and log_execution_time completely unchanged
# ---------------------------------------------------------------------------


def retry(max_attempts: int = 3, delay: float = 1.0, backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """
    重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = kwargs.pop("logger", None) or get_logger()

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except KeyboardInterrupt:
                    raise
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"Final attempt failed for {func.__name__}: {e}")
                        raise

                    wait_time = delay * (backoff_factor**attempt) * random.uniform(0.5, 1.5)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = kwargs.pop("logger", None) or get_logger()

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except KeyboardInterrupt:
                    raise
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"Final attempt failed for {func.__name__}: {e}")
                        raise

                    wait_time = delay * (backoff_factor**attempt) * random.uniform(0.5, 1.5)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time:.1f}s..."
                    )
                    import time

                    time.sleep(wait_time)

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


def log_execution_time(logger=None):
    """
    记录执行时间装饰器

    Args:
        logger: 日志记录器
    """
    if logger is None:
        logger = get_logger()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} executed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}", exc_info=True)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} executed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}", exc_info=True)
                raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class XianyuError(Exception):
    """基础异常类"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {"type": self.__class__.__name__, "message": self.message, "details": self.details}


class ConfigError(XianyuError):
    """配置错误"""

    pass


class BrowserError(XianyuError):
    """浏览器操作错误"""

    pass


class AIError(XianyuError):
    """AI服务错误"""

    pass


class MediaError(XianyuError):
    """媒体处理错误"""

    pass


class AccountError(XianyuError):
    """账号错误"""

    pass


class DatabaseError(XianyuError):
    """数据库错误"""

    pass

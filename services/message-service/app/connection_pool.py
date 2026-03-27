"""
WebSocket Connection Pool - Optimized for high concurrency
Phase 4: Performance optimization
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger()


class ConnectionState(Enum):
    """连接状态"""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


@dataclass
class ConnectionMetrics:
    """连接指标"""
    created_at: float = field(default_factory=time.time)
    connected_at: Optional[float] = None
    messages_sent: int = 0
    messages_received: int = 0
    reconnect_count: int = 0
    last_activity: float = field(default_factory=time.time)
    latency_ms: deque = field(default_factory=lambda: deque(maxlen=100))

    @property
    def uptime_seconds(self) -> float:
        """连接正常运行时间"""
        if self.connected_at:
            return time.time() - self.connected_at
        return 0.0

    @property
    def avg_latency_ms(self) -> float:
        """平均延迟"""
        if not self.latency_ms:
            return 0.0
        return sum(self.latency_ms) / len(self.latency_ms)


@dataclass
class PooledConnection:
    """池化连接"""
    account_id: str
    connection: Any  # WebSocket connection object
    state: ConnectionState = ConnectionState.IDLE
    metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _last_used: float = field(default_factory=time.time)

    async def acquire(self) -> bool:
        """获取连接使用权"""
        if self.state == ConnectionState.CONNECTED:
            self._last_used = time.time()
            return True
        return False

    def release(self) -> None:
        """释放连接"""
        pass

    def is_expired(self, max_idle_seconds: float = 300) -> bool:
        """检查连接是否过期"""
        return time.time() - self._last_used > max_idle_seconds


class WebSocketConnectionPool:
    """
    优化的 WebSocket 连接池

    特性：
    - 连接复用，减少重复建立连接开销
    - 自动健康检查和重连
    - 连接池大小动态调整
    - 性能指标收集
    """

    def __init__(
        self,
        max_connections: int = 100,
        min_connections: int = 10,
        max_idle_time: float = 300,
        health_check_interval: float = 30,
        connection_timeout: float = 10,
    ):
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval
        self.connection_timeout = connection_timeout

        # 连接存储
        self._connections: dict[str, PooledConnection] = {}
        self._connection_queue: deque[str] = deque(maxlen=max_connections)
        self._waiting_queue: deque[asyncio.Future] = deque()

        # 锁和事件
        self._lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()

        # 后台任务
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        # 指标收集
        self._metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "avg_latency_ms": 0.0,
        }

    async def initialize(self) -> None:
        """初始化连接池"""
        logger.info("Initializing WebSocket connection pool", max_connections=self.max_connections)
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._metrics_task = asyncio.create_task(self._metrics_collection_loop())

    async def shutdown(self) -> None:
        """关闭连接池"""
        logger.info("Shutting down connection pool")
        self._shutdown_event.set()

        # 取消后台任务
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._metrics_task:
            self._metrics_task.cancel()

        # 关闭所有连接
        async with self._lock:
            for conn in self._connections.values():
                await self._close_connection(conn)
            self._connections.clear()

        logger.info("Connection pool shutdown complete")

    async def get_connection(self, account_id: str) -> Optional[PooledConnection]:
        """
        获取连接（带等待队列）

        如果连接池已满，会等待直到有可用连接或超时
        """
        start_time = time.time()

        async with self._lock:
            # 检查是否已有连接
            if account_id in self._connections:
                conn = self._connections[account_id]
                if conn.state == ConnectionState.CONNECTED:
                    conn._last_used = time.time()
                    return conn
                # 连接断开，需要重连
                await self._reconnect(conn)
                return conn

            # 检查池是否已满
            if len(self._connections) >= self.max_connections:
                # 等待可用连接
                future = asyncio.get_event_loop().create_future()
                self._waiting_queue.append(future)

        # 在锁外等待
        try:
            await asyncio.wait_for(future, timeout=self.connection_timeout)
            async with self._lock:
                if account_id in self._connections:
                    return self._connections[account_id]
        except asyncio.TimeoutError:
            logger.warning("Connection pool full, timeout waiting", account_id=account_id)
            return None

        # 创建新连接
        return await self._create_connection(account_id)

    async def release_connection(self, account_id: str) -> None:
        """释放连接回池"""
        async with self._lock:
            # 检查等待队列
            while self._waiting_queue:
                future = self._waiting_queue.popleft()
                if not future.done():
                    future.set_result(True)
                    break

    async def send_message(self, account_id: str, message: dict) -> bool:
        """发送消息"""
        conn = await self.get_connection(account_id)
        if not conn:
            return False

        try:
            start_time = time.time()
            # 实际发送逻辑
            await self._send_via_connection(conn, message)

            # 记录指标
            latency = (time.time() - start_time) * 1000
            conn.metrics.latency_ms.append(latency)
            conn.metrics.messages_sent += 1
            self._metrics["messages_sent"] += 1

            return True
        except Exception as e:
            logger.error("Failed to send message", account_id=account_id, error=str(e))
            return False
        finally:
            await self.release_connection(account_id)

    async def _create_connection(self, account_id: str) -> Optional[PooledConnection]:
        """创建新连接"""
        async with self._lock:
            conn = PooledConnection(
                account_id=account_id,
                connection=None,  # 实际 WebSocket 连接对象
                state=ConnectionState.CONNECTING,
            )
            self._connections[account_id] = conn

        try:
            # 实际连接逻辑
            conn.connection = await self._establish_websocket(account_id)
            conn.state = ConnectionState.CONNECTED
            conn.metrics.connected_at = time.time()
            self._metrics["total_connections"] += 1
            self._metrics["active_connections"] += 1

            logger.info("Connection established", account_id=account_id)
            return conn
        except Exception as e:
            logger.error("Failed to create connection", account_id=account_id, error=str(e))
            conn.state = ConnectionState.CLOSED
            self._metrics["failed_connections"] += 1
            return None

    async def _reconnect(self, conn: PooledConnection) -> bool:
        """重连"""
        conn.state = ConnectionState.RECONNECTING
        conn.metrics.reconnect_count += 1

        # 指数退避
        backoff = min(2 ** conn.metrics.reconnect_count, 60)
        await asyncio.sleep(backoff)

        try:
            if conn.connection:
                await self._close_connection(conn)
            conn.connection = await self._establish_websocket(conn.account_id)
            conn.state = ConnectionState.CONNECTED
            conn.metrics.connected_at = time.time()
            logger.info("Connection reestablished", account_id=conn.account_id)
            return True
        except Exception as e:
            logger.error("Reconnection failed", account_id=conn.account_id, error=str(e))
            return False

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.health_check_interval
                )
            except asyncio.TimeoutError:
                await self._perform_health_check()

    async def _perform_health_check(self) -> None:
        """执行健康检查"""
        async with self._lock:
            expired_accounts = []
            for account_id, conn in self._connections.items():
                # 检查连接是否过期
                if conn.is_expired(self.max_idle_time):
                    expired_accounts.append(account_id)
                    continue

                # 检查连接状态
                if conn.state == ConnectionState.CONNECTED:
                    is_healthy = await self._ping_connection(conn)
                    if not is_healthy:
                        asyncio.create_task(self._reconnect(conn))

            # 清理过期连接
            for account_id in expired_accounts:
                conn = self._connections.pop(account_id)
                await self._close_connection(conn)
                self._metrics["active_connections"] -= 1

            logger.debug(
                "Health check complete",
                active=len(self._connections),
                expired=len(expired_accounts),
            )

    async def _metrics_collection_loop(self) -> None:
        """指标收集循环"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=60  # 每分钟收集一次
                )
            except asyncio.TimeoutError:
                await self._collect_metrics()

    async def _collect_metrics(self) -> None:
        """收集性能指标"""
        async with self._lock:
            total_latency = 0
            latency_count = 0

            for conn in self._connections.values():
                if conn.metrics.latency_ms:
                    total_latency += sum(conn.metrics.latency_ms)
                    latency_count += len(conn.metrics.latency_ms)

            if latency_count > 0:
                self._metrics["avg_latency_ms"] = total_latency / latency_count

        logger.info(
            "Pool metrics",
            total=self._metrics["total_connections"],
            active=self._metrics["active_connections"],
            failed=self._metrics["failed_connections"],
            avg_latency_ms=round(self._metrics["avg_latency_ms"], 2),
        )

    # Stub methods for actual implementation
    async def _establish_websocket(self, account_id: str) -> Any:
        """建立 WebSocket 连接（实际实现）"""
        # 这里接入实际的 WebSocket 连接逻辑
        raise NotImplementedError()

    async def _close_connection(self, conn: PooledConnection) -> None:
        """关闭连接（实际实现）"""
        if conn.connection:
            # 实际关闭逻辑
            pass

    async def _send_via_connection(self, conn: PooledConnection, message: dict) -> None:
        """通过连接发送消息（实际实现）"""
        # 实际发送逻辑
        pass

    async def _ping_connection(self, conn: PooledConnection) -> bool:
        """Ping 连接检查健康（实际实现）"""
        # 实际 ping 逻辑
        return True

    def get_metrics(self) -> dict:
        """获取当前指标"""
        return self._metrics.copy()

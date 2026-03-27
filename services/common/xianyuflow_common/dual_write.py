"""
Dual-write transition layer
Phase 5: Migration with zero downtime

This module provides a transition layer that writes to both SQLite (old) and
PostgreSQL (new) databases during the migration period.

Usage:
    1. Enable dual-write mode
    2. Run data migration in background
    3. Gradually shift read traffic to PostgreSQL
    4. Disable SQLite writes once migration is complete
"""

import asyncio
import re
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Optional

import aiosqlite
import asyncpg
import structlog

logger = structlog.get_logger()

_VALID_TABLE_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


class WriteMode(Enum):
    """写入模式"""
    SQLITE_ONLY = "sqlite_only"      # 仅写入 SQLite（迁移前）
    DUAL_WRITE = "dual_write"        # 双写（迁移中）
    PG_ONLY = "pg_only"              # 仅写入 PostgreSQL（迁移后）
    PG_PRIMARY = "pg_primary"        # PG 主写，SQLite 备份（过渡）


class ReadMode(Enum):
    """读取模式"""
    SQLITE_ONLY = "sqlite_only"      # 仅从 SQLite 读
    PG_ONLY = "pg_only"              # 仅从 PostgreSQL 读
    SQLITE_FALLBACK = "sqlite_fallback"  # PG 优先，失败回退 SQLite
    PG_FALLBACK = "pg_fallback"      # SQLite 优先，失败回退 PG


class DualWriteManager:
    """双写管理器"""

    def __init__(
        self,
        sqlite_path: str,
        pg_dsn: str,
        write_mode: WriteMode = WriteMode.DUAL_WRITE,
        read_mode: ReadMode = ReadMode.SQLITE_FALLBACK,
    ):
        self.sqlite_path = sqlite_path
        self.pg_dsn = pg_dsn
        self.write_mode = write_mode
        self.read_mode = read_mode

        self._lock = asyncio.Lock()
        self._sqlite_pool: Optional[aiosqlite.Connection] = None
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._migration_progress = 0.0  # 0.0 - 1.0

    async def initialize(self) -> None:
        """初始化连接池"""
        if self.write_mode in (WriteMode.SQLITE_ONLY, WriteMode.DUAL_WRITE, WriteMode.PG_PRIMARY):
            self._sqlite_pool = await aiosqlite.connect(self.sqlite_path)
            self._sqlite_pool.row_factory = aiosqlite.Row

        if self.write_mode in (WriteMode.PG_ONLY, WriteMode.DUAL_WRITE, WriteMode.PG_PRIMARY):
            self._pg_pool = await asyncpg.create_pool(self.pg_dsn, min_size=5, max_size=20)

        logger.info(
            "DualWriteManager initialized",
            write_mode=self.write_mode.value,
            read_mode=self.read_mode.value,
        )

    async def close(self) -> None:
        """关闭连接"""
        if self._sqlite_pool:
            await self._sqlite_pool.close()
        if self._pg_pool:
            await self._pg_pool.close()

    async def execute(
        self,
        sql: str,
        params: tuple = (),
        table: str = "",
    ) -> dict[str, Any]:
        """
        执行写入操作（根据 write_mode 决定写入目标）

        Returns:
            dict with results from each database
        """
        results = {
            "sqlite": None,
            "postgresql": None,
            "errors": [],
        }

        # SQLite 写入
        if self.write_mode in (WriteMode.SQLITE_ONLY, WriteMode.DUAL_WRITE, WriteMode.PG_PRIMARY):
            try:
                async with self._sqlite_lock():
                    cursor = await self._sqlite_pool.execute(sql, params)
                    await self._sqlite_pool.commit()
                    results["sqlite"] = cursor.lastrowid
            except Exception as e:
                logger.error("SQLite write failed", error=str(e), sql=sql)
                results["errors"].append(("sqlite", str(e)))

        # PostgreSQL 写入
        if self.write_mode in (WriteMode.PG_ONLY, WriteMode.DUAL_WRITE, WriteMode.PG_PRIMARY):
            try:
                async with self._pg_pool.acquire() as conn:
                    result = await conn.fetchval(sql + " RETURNING id", *params)
                    results["postgresql"] = result
            except Exception as e:
                logger.error("PostgreSQL write failed", error=str(e), sql=sql)
                results["errors"].append(("postgresql", str(e)))

        return results

    async def fetchone(
        self,
        sql: str,
        params: tuple = (),
    ) -> Optional[dict[str, Any]]:
        """
        执行读取操作（根据 read_mode 决定读取来源）
        """
        # 尝试 PostgreSQL（优先或仅 PG）
        if self.read_mode in (ReadMode.PG_ONLY, ReadMode.SQLITE_FALLBACK):
            try:
                if self._pg_pool:
                    async with self._pg_pool.acquire() as conn:
                        row = await conn.fetchrow(sql, *params)
                        if row:
                            return dict(row)
            except Exception as e:
                logger.warning("PostgreSQL read failed, trying fallback", error=str(e))
                if self.read_mode == ReadMode.PG_ONLY:
                    return None

        # 尝试 SQLite
        if self.read_mode in (ReadMode.SQLITE_ONLY, ReadMode.SQLITE_FALLBACK, ReadMode.PG_FALLBACK):
            try:
                if self._sqlite_pool:
                    async with self._sqlite_lock():
                        cursor = await self._sqlite_pool.execute(sql, params)
                        row = await cursor.fetchone()
                        if row:
                            return dict(row)
            except Exception as e:
                logger.error("SQLite read failed", error=str(e))

        return None

    async def fetchall(
        self,
        sql: str,
        params: tuple = (),
    ) -> list[dict[str, Any]]:
        """执行读取操作，返回多条记录"""
        # 尝试 PostgreSQL
        if self.read_mode in (ReadMode.PG_ONLY, ReadMode.SQLITE_FALLBACK):
            try:
                if self._pg_pool:
                    async with self._pg_pool.acquire() as conn:
                        rows = await conn.fetch(sql, *params)
                        return [dict(row) for row in rows]
            except Exception as e:
                logger.warning("PostgreSQL read failed, trying fallback", error=str(e))
                if self.read_mode == ReadMode.PG_ONLY:
                    return []

        # 尝试 SQLite
        if self.read_mode in (ReadMode.SQLITE_ONLY, ReadMode.SQLITE_FALLBACK, ReadMode.PG_FALLBACK):
            try:
                if self._sqlite_pool:
                    async with self._sqlite_lock():
                        cursor = await self._sqlite_pool.execute(sql, params)
                        rows = await cursor.fetchall()
                        return [dict(row) for row in rows]
            except Exception as e:
                logger.error("SQLite read failed", error=str(e))

        return []

    async def compare_data(
        self,
        table: str,
        limit: int = 100,
    ) -> dict[str, Any]:
        """比较 SQLite 和 PostgreSQL 中的数据一致性"""
        # Input validation
        if not isinstance(table, str) or not _VALID_TABLE_RE.match(table):
            raise ValueError(f"Invalid table name: {table!r}")
        limit = max(1, min(int(limit), 10000))

        results = {
            "table": table,
            "sqlite_count": 0,
            "pg_count": 0,
            "mismatch_count": 0,
            "sample_mismatches": [],
        }

        # 获取 SQLite 数据
        sqlite_data = []
        if self._sqlite_pool:
            async with self._sqlite_lock():
                cursor = await self._sqlite_pool.execute(
                    f"SELECT * FROM {table} ORDER BY id LIMIT ?",
                    (limit,),
                )
                sqlite_data = [dict(row) for row in await cursor.fetchall()]

        # 获取 PostgreSQL 数据
        pg_data = []
        if self._pg_pool:
            async with self._pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"SELECT * FROM {table} ORDER BY id LIMIT $1",
                    limit,
                )
                pg_data = [dict(row) for row in rows]

        results["sqlite_count"] = len(sqlite_data)
        results["pg_count"] = len(pg_data)

        # 比较数据
        for i, (sqlite_row, pg_row) in enumerate(zip(sqlite_data, pg_data)):
            if sqlite_row != pg_row:
                results["mismatch_count"] += 1
                if len(results["sample_mismatches"]) < 5:
                    results["sample_mismatches"].append({
                        "row": i,
                        "sqlite": sqlite_row,
                        "pg": pg_row,
                    })

        return results

    def set_migration_progress(self, progress: float) -> None:
        """设置迁移进度（0.0 - 1.0）"""
        self._migration_progress = max(0.0, min(1.0, progress))

        # 根据进度自动调整模式
        if self._migration_progress >= 1.0:
            logger.info("Migration complete, switching to PG_ONLY mode")
            self.write_mode = WriteMode.PG_ONLY
            self.read_mode = ReadMode.PG_ONLY

    def get_stats(self) -> dict[str, Any]:
        """获取双写统计信息"""
        return {
            "write_mode": self.write_mode.value,
            "read_mode": self.read_mode.value,
            "migration_progress": self._migration_progress,
            "sqlite_connected": self._sqlite_pool is not None,
            "pg_connected": self._pg_pool is not None,
        }

    @asynccontextmanager
    async def _sqlite_lock(self):
        """SQLite 操作锁（防止并发问题）"""
        # SQLite 不支持高并发写入，需要序列化
        async with self._lock:
            yield


class DualWriteMiddleware:
    """FastAPI 中间件：自动双写"""

    def __init__(self, dual_write_manager: DualWriteManager):
        self.manager = dual_write_manager

    async def __call__(self, request, call_next):
        # 在请求上下文中注入双写管理器
        request.state.db = self.manager
        response = await call_next(request)
        return response


# 配置示例和迁移脚本
MIGRATION_STAGES = [
    {
        "name": "stage_1_initial",
        "description": "初始双写阶段",
        "write_mode": WriteMode.DUAL_WRITE,
        "read_mode": ReadMode.SQLITE_ONLY,
        "duration_hours": 24,
    },
    {
        "name": "stage_2_validation",
        "description": "验证阶段，开始从 PG 读取",
        "write_mode": WriteMode.DUAL_WRITE,
        "read_mode": ReadMode.SQLITE_FALLBACK,
        "duration_hours": 48,
    },
    {
        "name": "stage_3_cutover",
        "description": "切换阶段，PG 主读",
        "write_mode": WriteMode.DUAL_WRITE,
        "read_mode": ReadMode.PG_FALLBACK,
        "duration_hours": 24,
    },
    {
        "name": "stage_4_final",
        "description": "最终阶段，仅使用 PG",
        "write_mode": WriteMode.PG_ONLY,
        "read_mode": ReadMode.PG_ONLY,
        "duration_hours": None,
    },
]

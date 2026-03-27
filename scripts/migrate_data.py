#!/usr/bin/env python3
"""
XianyuFlow v10 Phase 5: Data Migration Script
SQLite → PostgreSQL

Usage:
    python migrate_data.py --source sqlite:///data/orders.db --target postgresql://user:pass@localhost/xianyuflow
    python migrate_data.py --validate  # 验证迁移结果
    python migrate_data.py --rollback  # 紧急回滚
"""

import argparse
import asyncio
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

import asyncpg
import structlog
from tqdm import tqdm

logger = structlog.get_logger()


@dataclass
class MigrationConfig:
    """迁移配置"""
    source_sqlite_path: str
    target_pg_dsn: str
    batch_size: int = 1000
    dry_run: bool = False
    skip_validation: bool = False


class MigrationError(Exception):
    """迁移错误"""
    pass


class DataMigrator:
    """数据迁移器"""

    # 表映射关系
    TABLE_MAPPINGS = {
        "orders": {
            "sqlite_sql": """
                SELECT id, xianyu_order_id, buyer_id, status, amount,
                       created_at, updated_at
                FROM orders
            """,
            "pg_insert": """
                INSERT INTO orders (id, xianyu_order_id, buyer_id, status, amount, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO NOTHING
            """,
        },
        "virtual_goods_codes": {
            "sqlite_sql": """
                SELECT id, order_id, code, used, used_at, created_at
                FROM virtual_goods_codes
            """,
            "pg_insert": """
                INSERT INTO virtual_goods_codes (id, order_id, code, used, used_at, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO NOTHING
            """,
        },
        "user_profiles": {
            "sqlite_sql": """
                SELECT user_id, xianyu_user_id, preferences, common_routes,
                       preferred_couriers, price_sensitivity, communication_style,
                       total_orders, total_spent_cents, avg_order_value_cents,
                       credit_score, risk_level, first_seen_at, last_active_at,
                       created_at, updated_at
                FROM user_profiles
            """,
            "pg_insert": """
                INSERT INTO user_profiles (
                    user_id, xianyu_user_id, preferences, common_routes,
                    preferred_couriers, price_sensitivity, communication_style,
                    total_orders, total_spent_cents, avg_order_value_cents,
                    credit_score, risk_level, first_seen_at, last_active_at,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (user_id) DO UPDATE SET
                    xianyu_user_id = EXCLUDED.xianyu_user_id,
                    preferences = EXCLUDED.preferences,
                    common_routes = EXCLUDED.common_routes,
                    preferred_couriers = EXCLUDED.preferred_couriers,
                    price_sensitivity = EXCLUDED.price_sensitivity,
                    communication_style = EXCLUDED.communication_style,
                    total_orders = EXCLUDED.total_orders,
                    total_spent_cents = EXCLUDED.total_spent_cents,
                    avg_order_value_cents = EXCLUDED.avg_order_value_cents,
                    credit_score = EXCLUDED.credit_score,
                    risk_level = EXCLUDED.risk_level,
                    last_active_at = EXCLUDED.last_active_at,
                    updated_at = EXCLUDED.updated_at
            """,
        },
    }

    def __init__(self, config: MigrationConfig):
        self.config = config
        self._source_conn: Optional[sqlite3.Connection] = None
        self._target_pool: Optional[asyncpg.Pool] = None
        self._stats = {
            "tables_migrated": 0,
            "rows_migrated": 0,
            "rows_failed": 0,
            "start_time": None,
            "end_time": None,
        }

    @contextmanager
    def _sqlite_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """SQLite 连接上下文"""
        conn = sqlite3.connect(self.config.source_sqlite_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    async def _pg_pool(self) -> asyncpg.Pool:
        """获取 PostgreSQL 连接池"""
        if not self._target_pool:
            self._target_pool = await asyncpg.create_pool(
                self.config.target_pg_dsn,
                min_size=5,
                max_size=20,
            )
        return self._target_pool

    async def migrate_table(self, table_name: str) -> dict[str, Any]:
        """迁移单个表"""
        mapping = self.TABLE_MAPPINGS.get(table_name)
        if not mapping:
            raise MigrationError(f"Unknown table: {table_name}")

        logger.info("Starting table migration", table=table_name)

        stats = {
            "table": table_name,
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_failed": 0,
        }

        with self._sqlite_connection() as sqlite_conn:
            cursor = sqlite_conn.execute(mapping["sqlite_sql"])

            # 获取总行数用于进度条
            total_rows = sqlite_conn.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]

            batch = []
            pbar = tqdm(total=total_rows, desc=f"Migrating {table_name}")

            async with (await self._pg_pool()).acquire() as pg_conn:
                for row in cursor:
                    stats["rows_read"] += 1
                    batch.append(tuple(row))

                    if len(batch) >= self.config.batch_size:
                        inserted, failed = await self._insert_batch(
                            pg_conn, mapping["pg_insert"], batch
                        )
                        stats["rows_inserted"] += inserted
                        stats["rows_failed"] += failed
                        pbar.update(len(batch))
                        batch = []

                # 处理剩余批次
                if batch:
                    inserted, failed = await self._insert_batch(
                        pg_conn, mapping["pg_insert"], batch
                    )
                    stats["rows_inserted"] += inserted
                    stats["rows_failed"] += failed
                    pbar.update(len(batch))

            pbar.close()

        logger.info(
            "Table migration complete",
            table=table_name,
            inserted=stats["rows_inserted"],
            failed=stats["rows_failed"],
        )

        return stats

    async def _insert_batch(
        self, pg_conn: asyncpg.Connection, sql: str, batch: list[tuple]
    ) -> tuple[int, int]:
        """批量插入数据"""
        if self.config.dry_run:
            return len(batch), 0

        inserted = 0
        failed = 0

        try:
            # 使用 executemany 提高效率
            result = await pg_conn.executemany(sql, batch)
            inserted = len(batch)
        except Exception as e:
            logger.error("Batch insert failed", error=str(e), batch_size=len(batch))
            # 逐条重试
            for row in batch:
                try:
                    await pg_conn.execute(sql, *row)
                    inserted += 1
                except Exception as e2:
                    logger.error("Row insert failed", error=str(e2), row=row)
                    failed += 1

        return inserted, failed

    async def migrate_all(self) -> dict[str, Any]:
        """执行完整迁移"""
        self._stats["start_time"] = datetime.now().isoformat()

        logger.info(
            "Starting data migration",
            source=self.config.source_sqlite_path,
            target=self.config.target_pg_dsn,
            dry_run=self.config.dry_run,
        )

        for table_name in self.TABLE_MAPPINGS.keys():
            try:
                table_stats = await self.migrate_table(table_name)
                self._stats["tables_migrated"] += 1
                self._stats["rows_migrated"] += table_stats["rows_inserted"]
                self._stats["rows_failed"] += table_stats["rows_failed"]
            except Exception as e:
                logger.error("Table migration failed", table=table_name, error=str(e))
                raise MigrationError(f"Failed to migrate {table_name}: {e}")

        self._stats["end_time"] = datetime.now().isoformat()

        logger.info(
            "Migration complete",
            tables=self._stats["tables_migrated"],
            rows=self._stats["rows_migrated"],
            failed=self._stats["rows_failed"],
        )

        return self._stats

    async def validate(self) -> dict[str, Any]:
        """验证迁移结果"""
        logger.info("Starting validation")

        validation_results = {}

        with self._sqlite_connection() as sqlite_conn:
            async with (await self._pg_pool()).acquire() as pg_conn:
                for table_name in self.TABLE_MAPPINGS.keys():
                    # SQLite 行数
                    sqlite_count = sqlite_conn.execute(
                        f"SELECT COUNT(*) FROM {table_name}"
                    ).fetchone()[0]

                    # PostgreSQL 行数
                    pg_count = await pg_conn.fetchval(
                        f"SELECT COUNT(*) FROM {table_name}"
                    )

                    # 校验和比较（可选）
                    match = sqlite_count == pg_count

                    validation_results[table_name] = {
                        "sqlite_count": sqlite_count,
                        "pg_count": pg_count,
                        "match": match,
                    }

                    if not match:
                        logger.warning(
                            "Validation mismatch",
                            table=table_name,
                            sqlite=sqlite_count,
                            pg=pg_count,
                        )

        return validation_results

    async def cleanup(self) -> None:
        """清理资源"""
        if self._target_pool:
            await self._target_pool.close()


async def main():
    parser = argparse.ArgumentParser(description="XianyuFlow Data Migration Tool")
    parser.add_argument(
        "--source",
        default="sqlite:///data/orders.db",
        help="Source SQLite database path",
    )
    parser.add_argument(
        "--target",
        default="postgresql://xianyu:xianyu2024@localhost:5432/xianyuflow",
        help="Target PostgreSQL DSN",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for inserts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run without actual writes",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate migration results",
    )
    parser.add_argument(
        "--table",
        help="Migrate specific table only",
    )

    args = parser.parse_args()

    # 配置日志
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    config = MigrationConfig(
        source_sqlite_path=args.source.replace("sqlite:///", ""),
        target_pg_dsn=args.target,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    migrator = DataMigrator(config)

    try:
        if args.validate:
            results = await migrator.validate()
            print("\n" + "=" * 60)
            print("Validation Results")
            print("=" * 60)
            for table, result in results.items():
                status = "✓" if result["match"] else "✗"
                print(f"{status} {table}: SQLite={result['sqlite_count']}, PG={result['pg_count']}")
        elif args.table:
            stats = await migrator.migrate_table(args.table)
            print(f"\nMigrated {stats['rows_inserted']} rows to {args.table}")
        else:
            stats = await migrator.migrate_all()
            print("\n" + "=" * 60)
            print("Migration Complete")
            print("=" * 60)
            print(f"Tables migrated: {stats['tables_migrated']}")
            print(f"Rows migrated: {stats['rows_migrated']}")
            print(f"Rows failed: {stats['rows_failed']}")
    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

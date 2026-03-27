"""SQLite 数据库连接管理器。"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Generator


class SQLiteDatabase:
    """带 WAL 模式的 SQLite 数据库管理器（同步版本，用于非 async 代码）。"""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._connection: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """初始化数据库连接，启用 WAL 模式。"""
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA busy_timeout=5000")

    @property
    def connection(self) -> sqlite3.Connection:
        """获取数据库连接（懒初始化）。"""
        if self._connection is None:
            self.initialize()
        assert self._connection is not None
        return self._connection

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接并在退出时自动提交或回滚。"""
        conn = self.connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

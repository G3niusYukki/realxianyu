"""Database client with async SQLAlchemy."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from xianyuflow_common.config import DatabaseConfig

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class Database:
    """Async database client using SQLAlchemy 2.0."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize database client.

        Args:
            config: Database configuration.
        """
        self.config = config
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Create connection pool."""
        self._engine = create_async_engine(
            self.config.dsn,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_pre_ping=True,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session.

        Yields:
            AsyncSession: Database session.

        Raises:
            RuntimeError: If database not connected.
        """
        if not self._session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @property
    def engine(self) -> AsyncEngine:
        """Get SQLAlchemy engine.

        Returns:
            AsyncEngine: The async engine.

        Raises:
            RuntimeError: If database not connected.
        """
        if not self._engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._engine

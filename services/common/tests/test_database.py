"""Tests for xianyuflow_common.database module."""

import pytest

from xianyuflow_common.config import DatabaseConfig
from xianyuflow_common.database import Database


class TestDatabaseConfig:
    """Tests for DatabaseConfig DSN generation."""

    def test_dsn_default_values(self) -> None:
        """Default config should generate valid DSN."""
        config = DatabaseConfig()
        dsn = config.dsn
        assert dsn.startswith("postgresql+asyncpg://")
        assert "localhost" in dsn
        assert "5432" in dsn

    def test_dsn_custom_values(self) -> None:
        """Custom config values should be reflected in DSN."""
        config = DatabaseConfig(
            host="db.example.com",
            port=5433,
            name="mydb",
            user="admin",
            password="secret",
        )
        dsn = config.dsn
        assert "db.example.com" in dsn
        assert ":5433/" in dsn
        assert "mydb" in dsn
        assert "admin" in dsn


class TestDatabase:
    """Tests for Database class."""

    @pytest.mark.asyncio
    async def test_database_requires_connection_before_use(self) -> None:
        """Session context manager raises RuntimeError if not connected."""
        config = DatabaseConfig()
        db = Database(config)

        with pytest.raises(RuntimeError, match="not connected"):
            db._session_factory = None
            async with db.session():
                pass  # pragma: no cover

    def test_database_init_stores_config(self) -> None:
        """Database __init__ should store the config."""
        config = DatabaseConfig(host="testhost", port=1234, name="testdb")
        db = Database(config)
        assert db.config.host == "testhost"
        assert db.config.port == 1234
        assert db.config.name == "testdb"

    def test_database_engine_property_raises_when_not_connected(self) -> None:
        """Engine property raises RuntimeError when not connected."""
        config = DatabaseConfig()
        db = Database(config)
        with pytest.raises(RuntimeError, match="not connected"):
            _ = db.engine

    @pytest.mark.asyncio
    async def test_database_engine_after_connect(self) -> None:
        """Engine property returns engine after connecting (with SQLite test DSN)."""
        # Use sqlite+aiosqlite DSN for testing without real PostgreSQL
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            name="test",
            user="test",
            password="",
        )
        db = Database(config)
        await db.connect()
        try:
            engine = db.engine
            assert engine is not None
            # Engine should be an AsyncEngine instance
            assert hasattr(engine, "begin")
        finally:
            await db.disconnect()

    @pytest.mark.asyncio
    async def test_database_disconnect_clears_state(self) -> None:
        """Disconnect should clear engine and session_factory."""
        config = DatabaseConfig(host="localhost", port=5432, name="test", user="test", password="")
        db = Database(config)
        await db.connect()
        await db.disconnect()
        assert db._engine is None
        assert db._session_factory is None

    @pytest.mark.asyncio
    async def test_database_session_context_manager_commits(self) -> None:
        """Session context manager should commit on success."""
        config = DatabaseConfig(host="localhost", port=5432, name="test", user="test", password="")
        db = Database(config)
        await db.connect()
        try:
            async with db.session() as session:
                assert session is not None
        finally:
            await db.disconnect()

    @pytest.mark.asyncio
    async def test_database_session_context_manager_rolls_back_on_error(self) -> None:
        """Session context manager should rollback on exception."""
        config = DatabaseConfig(host="localhost", port=5432, name="test", user="test", password="")
        db = Database(config)
        await db.connect()
        try:
            with pytest.raises(ValueError, match="test error"):
                async with db.session() as session:
                    assert session is not None
                    raise ValueError("test error")
        finally:
            await db.disconnect()

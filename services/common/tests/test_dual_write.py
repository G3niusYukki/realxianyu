"""Tests for xianyuflow_common.dual_write module."""


from xianyuflow_common.dual_write import (
    _VALID_TABLE_RE,
    MIGRATION_STAGES,
    DualWriteManager,
    ReadMode,
    WriteMode,
)


class TestWriteModeAndReadMode:
    """Tests for WriteMode and ReadMode enums."""

    def test_write_mode_values(self) -> None:
        """WriteMode enum should have expected string values."""
        assert WriteMode.SQLITE_ONLY.value == "sqlite_only"
        assert WriteMode.DUAL_WRITE.value == "dual_write"
        assert WriteMode.PG_ONLY.value == "pg_only"
        assert WriteMode.PG_PRIMARY.value == "pg_primary"

    def test_read_mode_values(self) -> None:
        """ReadMode enum should have expected string values."""
        assert ReadMode.SQLITE_ONLY.value == "sqlite_only"
        assert ReadMode.PG_ONLY.value == "pg_only"
        assert ReadMode.SQLITE_FALLBACK.value == "sqlite_fallback"
        assert ReadMode.PG_FALLBACK.value == "pg_fallback"


class TestDualWriteManagerInit:
    """Tests for DualWriteManager initialization."""

    def test_init_default_values(self) -> None:
        """Default init should use DUAL_WRITE mode."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
        )
        assert manager.write_mode == WriteMode.DUAL_WRITE
        assert manager.read_mode == ReadMode.SQLITE_FALLBACK
        assert manager.sqlite_path == ":memory:"
        assert manager.pg_dsn == "postgresql://localhost/test"

    def test_init_custom_modes(self) -> None:
        """Init should accept custom write/read modes."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
            write_mode=WriteMode.PG_ONLY,
            read_mode=ReadMode.PG_ONLY,
        )
        assert manager.write_mode == WriteMode.PG_ONLY
        assert manager.read_mode == ReadMode.PG_ONLY

    def test_init_stores_paths(self) -> None:
        """Init should store sqlite_path and pg_dsn."""
        manager = DualWriteManager(
            sqlite_path="/path/to/sqlite.db",
            pg_dsn="postgresql://user:pass@host:5432/db",
        )
        assert manager.sqlite_path == "/path/to/sqlite.db"
        assert manager.pg_dsn == "postgresql://user:pass@host:5432/db"

    def test_init_no_connection_on_creation(self) -> None:
        """No database connections should be created on __init__."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
        )
        assert manager._sqlite_pool is None
        assert manager._pg_pool is None


class TestDualWriteManagerMigrationProgress:
    """Tests for migration progress mode switching."""

    def test_set_migration_progress_clamped_to_zero(self) -> None:
        """Negative migration progress should be clamped to 0.0."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
        )
        manager.set_migration_progress(-0.5)
        assert manager._migration_progress == 0.0

    def test_set_migration_progress_clamped_to_one(self) -> None:
        """Progress > 1.0 should be clamped to 1.0."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
        )
        manager.set_migration_progress(1.5)
        assert manager._migration_progress == 1.0

    def test_set_migration_progress_triggers_mode_switch_at_one(self) -> None:
        """Progress >= 1.0 should automatically switch to PG_ONLY mode."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
            write_mode=WriteMode.DUAL_WRITE,
            read_mode=ReadMode.SQLITE_FALLBACK,
        )
        manager.set_migration_progress(1.0)
        assert manager.write_mode == WriteMode.PG_ONLY
        assert manager.read_mode == ReadMode.PG_ONLY

    def test_get_stats(self) -> None:
        """get_stats should return current state."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
            write_mode=WriteMode.DUAL_WRITE,
            read_mode=ReadMode.SQLITE_FALLBACK,
        )
        stats = manager.get_stats()
        assert stats["write_mode"] == "dual_write"
        assert stats["read_mode"] == "sqlite_fallback"
        assert stats["migration_progress"] == 0.0
        assert stats["sqlite_connected"] is False
        assert stats["pg_connected"] is False

    def test_get_stats_updates_after_migration_progress(self) -> None:
        """get_stats should reflect updated migration progress."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
        )
        manager.set_migration_progress(0.75)
        stats = manager.get_stats()
        assert stats["migration_progress"] == 0.75

    def test_migration_progress_half_way_keeps_original_mode(self) -> None:
        """Progress at 0.5 should NOT change write/read modes."""
        manager = DualWriteManager(
            sqlite_path=":memory:",
            pg_dsn="postgresql://localhost/test",
            write_mode=WriteMode.DUAL_WRITE,
            read_mode=ReadMode.PG_FALLBACK,
        )
        manager.set_migration_progress(0.5)
        assert manager.write_mode == WriteMode.DUAL_WRITE
        assert manager.read_mode == ReadMode.PG_FALLBACK


class TestValidTableRegex:
    """Tests for table name validation regex."""

    def test_valid_table_names(self) -> None:
        """Valid table names should pass validation."""
        valid_names = ["users", "order_items", "Product123", "x_y_z", "_private", "a"]
        for name in valid_names:
            assert _VALID_TABLE_RE.match(name), f"{name!r} should be valid"

    def test_invalid_table_names(self) -> None:
        """Invalid table names should not pass validation."""
        invalid_names = ["123table", "users-name", "users.name", "users name", "", " table"]
        for name in invalid_names:
            assert not _VALID_TABLE_RE.match(name), f"{name!r} should be invalid"


class TestMigrationStages:
    """Tests for MIGRATION_STAGES migration stages definition."""

    def test_migration_stages_has_four_stages(self) -> None:
        """MIGRATION_STAGES should define exactly 4 stages."""
        assert len(MIGRATION_STAGES) == 4

    def test_initial_stage_dual_write_sqlite_read(self) -> None:
        """Stage 1 should use DUAL_WRITE with SQLITE_ONLY read mode."""
        stage = MIGRATION_STAGES[0]
        assert stage["name"] == "stage_1_initial"
        assert stage["write_mode"] == WriteMode.DUAL_WRITE
        assert stage["read_mode"] == ReadMode.SQLITE_ONLY
        assert stage["duration_hours"] == 24

    def test_validation_stage_dual_write_sqlite_fallback(self) -> None:
        """Stage 2 should use DUAL_WRITE with SQLITE_FALLBACK read mode."""
        stage = MIGRATION_STAGES[1]
        assert stage["name"] == "stage_2_validation"
        assert stage["write_mode"] == WriteMode.DUAL_WRITE
        assert stage["read_mode"] == ReadMode.SQLITE_FALLBACK
        assert stage["duration_hours"] == 48

    def test_cutover_stage_dual_write_pg_fallback(self) -> None:
        """Stage 3 should use DUAL_WRITE with PG_FALLBACK read mode."""
        stage = MIGRATION_STAGES[2]
        assert stage["name"] == "stage_3_cutover"
        assert stage["write_mode"] == WriteMode.DUAL_WRITE
        assert stage["read_mode"] == ReadMode.PG_FALLBACK
        assert stage["duration_hours"] == 24

    def test_final_stage_pg_only(self) -> None:
        """Final stage should use PG_ONLY for both read and write."""
        stage = MIGRATION_STAGES[3]
        assert stage["name"] == "stage_4_final"
        assert stage["write_mode"] == WriteMode.PG_ONLY
        assert stage["read_mode"] == ReadMode.PG_ONLY
        assert stage["duration_hours"] is None

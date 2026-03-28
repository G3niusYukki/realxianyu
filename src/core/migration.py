"""
Database migration runner with version tracking.

Handles both existing deployments (where DB schema is already applied) and new
deployments. The 11 existing migration files are assumed to already exist in the
DB for existing deployments; only future migrations are executed and tracked.

For new deployments (no schema_versions table):
  - 0000_schema_version.sql runs first and is tracked
  - Remaining 11 existing migrations are recorded in schema_versions but NOT
    executed (their schema is already present in existing production DBs)
  - Future migrations (0013_*.sql onward) are both executed and tracked
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from loguru import logger

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "database" / "migrations"

# The 11 existing migrations that were already applied in existing deployments.
# These are recorded in schema_versions but NOT re-executed (they reference
# tables created by earlier migrations in the same set).
_EXISTING_MIGRATION_NAMES = frozenset(
    {
        "20260304_add_order_callback_dedup.sql",
        "20260306_wave_b4_callbacks_lease_and_dims.sql",
        "20260306_wave_b_virtual_goods.sql",
        "20260306_wave_c_manual_takeover_events.sql",
        "20260306_wave_c_order_events.sql",
        "20260306_wave_d_listing_product_mappings.sql",
        "20260306_wave_d_ops_exception_pool.sql",
        "20260306_wave_d_ops_exception_transition_log.sql",
        "20260306_wave_d_ops_fulfillment_eff_daily.sql",
        "20260306_wave_d_ops_funnel_stage_daily.sql",
        "20260306_wave_d_ops_item_daily_snapshot.sql",
    }
)


def _get_connection(db_path: str) -> sqlite3.Connection:
    """Create a connection to the SQLite database with WAL mode."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _get_applied_names(conn: sqlite3.Connection) -> set[str]:
    """Return the set of migration names already recorded in schema_versions."""
    try:
        cur = conn.execute("SELECT name FROM schema_versions")
        return {row[0] for row in cur.fetchall()}
    except sqlite3.OperationalError:
        return set()


def _version_from_name(name: str) -> int | None:
    """Derive integer version from migration filename.

    Files named 0000_*.sql -> version 0
    Files named NNNN_*.sql -> version NNNN
    """
    try:
        return int(name.split("_")[0])
    except (ValueError, IndexError):
        return None


def _record_migration(conn: sqlite3.Connection, fname: str) -> None:
    """Record a migration name+version in schema_versions (name is the primary key)."""
    version = _version_from_name(fname)
    conn.execute(
        "INSERT OR IGNORE INTO schema_versions (version, name) VALUES (?, ?)",
        (version, fname),
    )
    conn.commit()


def run_migrations(db_path: str) -> list[str]:
    """Run pending database migrations and return list of applied migration names."""
    migrations_dir = MIGRATIONS_DIR
    if not migrations_dir.is_dir():
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return []

    sql_files = sorted(f.name for f in migrations_dir.glob("*.sql"))
    if not sql_files:
        logger.info("No migration files found")
        return []

    applied: list[str] = []
    conn = _get_connection(db_path)
    try:
        applied_names = _get_applied_names(conn)

        # 0000_schema_version.sql creates the tracking table
        init_file = "0000_schema_version.sql"
        if init_file in sql_files and init_file not in applied_names:
            init_path = migrations_dir / init_file
            sql = init_path.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.commit()
            _record_migration(conn, init_file)
            applied.append(init_file)
            applied_names = _get_applied_names(conn)
            logger.info(f"Applied {init_file}")

        # Remaining migrations
        for fname in sql_files:
            if fname == init_file:
                continue
            if fname in applied_names:
                logger.debug(f"Migration already recorded: {fname}")
                continue

            fpath = migrations_dir / fname
            sql = fpath.read_text(encoding="utf-8")

            # Existing migrations are only recorded, not executed
            if fname in _EXISTING_MIGRATION_NAMES:
                _record_migration(conn, fname)
                applied.append(fname)
                logger.info(f"Recorded existing migration: {fname}")
                continue

            # New migrations: execute and record
            # Skip 0013_foreign_keys.sql if virtual_goods_orders doesn't exist (fresh DB)
            if fname.startswith("0013") and fname not in _EXISTING_MIGRATION_NAMES:
                try:
                    cur = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='virtual_goods_orders'"
                    )
                    if cur.fetchone() is None:
                        logger.info(f"Skipping {fname} — virtual_goods_orders table not found (fresh database)")
                        _record_migration(conn, fname)
                        applied.append(fname)
                        continue
                except Exception:
                    pass  # table check failed, try to apply anyway
            try:
                conn.executescript(sql)
                conn.commit()
            except Exception as exc:
                logger.error(f"Failed to apply migration {fname}: {exc}")
                raise

            _record_migration(conn, fname)
            logger.info(f"Applied migration: {fname}")
            applied.append(fname)

        return applied
    finally:
        conn.close()

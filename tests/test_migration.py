import os
import sqlite3
import tempfile

from src.core.migration import run_migrations


def test_migration_idempotent():
    """Running migrations twice should not apply anything the second time."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        applied1 = run_migrations(db_path)
        # First run: should apply 0000_schema_version.sql
        assert len(applied1) >= 1
        # Second run: should not apply anything
        applied2 = run_migrations(db_path)
        assert len(applied2) == 0
    finally:
        # Close all connections before unlinking on Windows
        conn = sqlite3.connect(db_path)
        conn.close()
        # Also clean up any WAL journal files
        for suffix in ("-wal", "-shm"):
            journal_path = db_path + suffix
            if os.path.exists(journal_path):
                os.unlink(journal_path)
        os.unlink(db_path)


def test_0000_creates_table():
    """0000 migration should create schema_versions table."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        run_migrations(db_path)
        conn = sqlite3.connect(db_path)
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_versions'"
        )
        assert cur.fetchone() is not None
        conn.close()
    finally:
        conn = sqlite3.connect(db_path)
        conn.close()
        for suffix in ("-wal", "-shm"):
            journal_path = db_path + suffix
            if os.path.exists(journal_path):
                os.unlink(journal_path)
        os.unlink(db_path)

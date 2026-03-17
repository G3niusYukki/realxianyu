"""Persistent bot-sent message signature store.

Tracks SHA1 signatures of messages sent by the bot so that when WS echoes
them back (with sender == seller), we can distinguish bot-sent from
human-sent messages.  Uses SQLite for crash/restart persistence with an
in-memory dict as a fast read cache.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import time
from pathlib import Path

_SIG_LENGTHS = (100, 30)
_DEFAULT_TTL = 7200.0
_DEFAULT_DB_PATH = os.path.join("data", "bot_sigs.db")


class BotSigStore:
    """In-memory + SQLite dual-write store for bot message signatures."""

    def __init__(self, db_path: str | None = None, ttl: float = _DEFAULT_TTL) -> None:
        self._db_path = Path(db_path or _DEFAULT_DB_PATH)
        self._ttl = max(60.0, float(ttl))
        self._cache: dict[str, float] = {}
        self._ensure_schema()
        self._load_from_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=3000")
        return conn

    def _ensure_schema(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_sent_sigs (
                    sig TEXT PRIMARY KEY,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bot_sigs_created ON bot_sent_sigs(created_at)")
            conn.commit()

    def _load_from_db(self) -> None:
        """Load unexpired signatures into memory cache on startup."""
        cutoff = time.time() - self._ttl
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT sig, created_at FROM bot_sent_sigs WHERE created_at > ?",
                    (cutoff,),
                ).fetchall()
            for sig, created_at in rows:
                self._cache[sig] = created_at
        except Exception:
            pass

    @staticmethod
    def _make_sigs(chat_id: str, text: str) -> list[str]:
        sigs = []
        for length in _SIG_LENGTHS:
            sig = hashlib.sha1(f"{chat_id}:{str(text or '')[:length]}".encode()).hexdigest()[:16]
            sigs.append(sig)
        return sigs

    def record(self, chat_id: str, text: str) -> None:
        """Record that the bot sent this message."""
        now = time.time()
        sigs = self._make_sigs(chat_id, text)
        for sig in sigs:
            self._cache[sig] = now
        try:
            with self._connect() as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO bot_sent_sigs(sig, created_at) VALUES (?, ?)",
                    [(sig, now) for sig in sigs],
                )
                conn.commit()
        except Exception:
            pass

    def is_bot_sent(self, chat_id: str, text: str) -> bool:
        """Check whether this message was recently sent by the bot."""
        sigs = self._make_sigs(chat_id, text)
        for sig in sigs:
            if sig in self._cache:
                return True
        try:
            with self._connect() as conn:
                placeholders = ",".join("?" for _ in sigs)
                cutoff = time.time() - self._ttl
                row = conn.execute(
                    f"SELECT 1 FROM bot_sent_sigs WHERE sig IN ({placeholders}) AND created_at > ? LIMIT 1",
                    (*sigs, cutoff),
                ).fetchone()
                if row:
                    for sig in sigs:
                        self._cache[sig] = time.time()
                    return True
        except Exception:
            pass
        return False

    def cleanup(self) -> None:
        """Remove expired entries from both cache and DB."""
        now = time.time()
        cutoff = now - self._ttl
        stale = [k for k, ts in self._cache.items() if ts < cutoff]
        for k in stale:
            del self._cache[k]
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM bot_sent_sigs WHERE created_at <= ?", (cutoff,))
                conn.commit()
        except Exception:
            pass

"""
SQLite session store.

Tracks pipeline session state (pending → processing → complete/failed).
SQLite is the right choice for hackathon MVP; swap to PostgreSQL for production
by updating the connection string in config.py.
"""

from __future__ import annotations

import contextlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import structlog

log = structlog.get_logger()

DB_PATH = Path("bankers_wrapped.db")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(db_path: Path = DB_PATH) -> None:
    """Create the sessions table if it doesn't exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id   TEXT PRIMARY KEY,
                user_id      TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'pending',
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL,
                output_url   TEXT DEFAULT '',
                metadata     TEXT DEFAULT '{}',
                error        TEXT DEFAULT ''
            )
        """)
        conn.commit()


class SessionStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        init_db(db_path)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, session_id: str, user_id: str) -> None:
        now = _now()
        with contextlib.closing(self._conn()) as conn:
            with conn:
                conn.execute(
                    """INSERT INTO sessions
                       (session_id, user_id, status, created_at, updated_at)
                       VALUES (?, ?, 'pending', ?, ?)""",
                    (session_id, user_id, now, now),
                )

    def set_processing(self, session_id: str) -> None:
        with contextlib.closing(self._conn()) as conn:
            with conn:
                conn.execute(
                    "UPDATE sessions SET status='processing', updated_at=? WHERE session_id=?",
                    (_now(), session_id),
                )

    def set_complete(
        self, session_id: str, output_url: str, metadata: dict  # type: ignore[type-arg]
    ) -> None:
        with contextlib.closing(self._conn()) as conn:
            with conn:
                conn.execute(
                    """UPDATE sessions
                       SET status='complete', output_url=?, metadata=?, updated_at=?
                       WHERE session_id=?""",
                    (output_url, json.dumps(metadata), _now(), session_id),
                )

    def set_failed(self, session_id: str, error: str) -> None:
        with contextlib.closing(self._conn()) as conn:
            with conn:
                conn.execute(
                    "UPDATE sessions SET status='failed', error=?, updated_at=? WHERE session_id=?",
                    (error[:1000], _now(), session_id),
                )

    def get(self, session_id: str) -> dict | None:  # type: ignore[type-arg]
        with contextlib.closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["metadata"] = json.loads(d.get("metadata") or "{}")
        return d

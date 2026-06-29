"""
SQLite session store.

Tracks pipeline session state (pending → processing → complete/failed).
SQLite is the right choice for hackathon MVP; swap to PostgreSQL for production
by updating the connection string in config.py.
"""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

import structlog

log = structlog.get_logger()

# Override with SESSION_DB_PATH to point at a Railway persistent volume (e.g.
# /data/bankers_wrapped.db) so sessions survive redeploys. Railway's default
# filesystem is ephemeral — without a volume, the SQLite DB is wiped on deploy.
DB_PATH = Path(os.environ.get("SESSION_DB_PATH", "bankers_wrapped.db"))


def _now() -> str:
    return datetime.now(UTC).isoformat()


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
                error        TEXT DEFAULT '',
                events       TEXT DEFAULT '[]'
            )
        """)
        # Add events column to existing DBs without it
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("ALTER TABLE sessions ADD COLUMN events TEXT DEFAULT '[]'")
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
        with contextlib.closing(self._conn()) as conn, conn:
                conn.execute(
                    """INSERT INTO sessions
                       (session_id, user_id, status, created_at, updated_at)
                       VALUES (?, ?, 'pending', ?, ?)""",
                    (session_id, user_id, now, now),
                )

    def set_processing(self, session_id: str) -> None:
        with contextlib.closing(self._conn()) as conn, conn:
                conn.execute(
                    "UPDATE sessions SET status='processing', updated_at=? WHERE session_id=?",
                    (_now(), session_id),
                )

    def set_complete(
        self, session_id: str, output_url: str, metadata: dict  # type: ignore[type-arg]
    ) -> None:
        with contextlib.closing(self._conn()) as conn, conn:
                conn.execute(
                    """UPDATE sessions
                       SET status='complete', output_url=?, metadata=?, updated_at=?
                       WHERE session_id=?""",
                    (output_url, json.dumps(metadata), _now(), session_id),
                )

    def set_failed(self, session_id: str, error: str) -> None:
        with contextlib.closing(self._conn()) as conn, conn:
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

    def append_event(self, session_id: str, event: str, detail: str = "") -> None:
        """Append a progress event to the session's event log."""
        with contextlib.closing(self._conn()) as conn, conn:
            row = conn.execute(
                "SELECT events FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if not row:
                return
            events: list[dict[str, object]] = json.loads(row["events"] or "[]")
            events.append({"event": event, "detail": detail, "ts": time.time()})
            conn.execute(
                "UPDATE sessions SET events=?, updated_at=? WHERE session_id=?",
                (json.dumps(events), _now(), session_id),
            )

    def get_events(self, session_id: str) -> list[dict[str, object]]:
        """Return all progress events for a session, in arrival order."""
        with contextlib.closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT events FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
        if not row:
            return []
        return json.loads(row["events"] or "[]")  # type: ignore[no-any-return]

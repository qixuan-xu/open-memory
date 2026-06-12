from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone
import json
import sqlite3
from pathlib import Path
from typing import Iterator

from backend.app.core.config import get_settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    category TEXT NOT NULL,
    importance REAL NOT NULL,
    initial_importance REAL NOT NULL,
    current_importance REAL NOT NULL,
    importance_reason TEXT NOT NULL,
    last_reassessed_at TEXT,
    review_status TEXT NOT NULL DEFAULT 'inbox',
    reviewed_at TEXT,
    source TEXT NOT NULL,
    tags TEXT NOT NULL,
    metadata TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    categories TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS long_term_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_type TEXT NOT NULL,
    text TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_day TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class MemoryStore:
    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or get_settings().database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            self._migrate_events(conn)

    def _migrate_events(self, conn: sqlite3.Connection) -> None:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(events)")}
        migrations = {
            "initial_importance": "ALTER TABLE events ADD COLUMN initial_importance REAL",
            "current_importance": "ALTER TABLE events ADD COLUMN current_importance REAL",
            "importance_reason": "ALTER TABLE events ADD COLUMN importance_reason TEXT",
            "last_reassessed_at": "ALTER TABLE events ADD COLUMN last_reassessed_at TEXT",
            "review_status": "ALTER TABLE events ADD COLUMN review_status TEXT DEFAULT 'inbox'",
            "reviewed_at": "ALTER TABLE events ADD COLUMN reviewed_at TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                conn.execute(statement)
        conn.execute("UPDATE events SET initial_importance = importance WHERE initial_importance IS NULL")
        conn.execute("UPDATE events SET current_importance = importance WHERE current_importance IS NULL")
        conn.execute(
            "UPDATE events SET importance_reason = 'Initial classifier estimate' WHERE importance_reason IS NULL"
        )
        conn.execute("UPDATE events SET review_status = 'inbox' WHERE review_status IS NULL")

    def add_event(
        self,
        text: str,
        category: str,
        importance: float,
        source: str,
        tags: list[str],
        metadata: dict,
        importance_reason: str,
        review_status: str,
        started_at: datetime | None,
        ended_at: datetime | None,
    ) -> sqlite3.Row:
        now = utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events
                (
                    text, category, importance, initial_importance, current_importance,
                    importance_reason, review_status, source, tags, metadata, started_at, ended_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    text,
                    category,
                    importance,
                    importance,
                    importance,
                    importance_reason,
                    review_status,
                    source,
                    json.dumps(tags, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                    started_at.isoformat() if started_at else None,
                    ended_at.isoformat() if ended_at else None,
                    now,
                ),
            )
            return conn.execute("SELECT * FROM events WHERE id = ?", (cursor.lastrowid,)).fetchone()

    def list_events_for_day(self, day: date) -> list[sqlite3.Row]:
        start = f"{day.isoformat()}T00:00:00"
        end = f"{day.isoformat()}T23:59:59"
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT * FROM events
                    WHERE created_at BETWEEN ? AND ? AND review_status != 'ignored'
                    ORDER BY created_at ASC
                    """,
                    (start, end),
                )
            )

    def recent_events(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    "SELECT * FROM events WHERE review_status != 'ignored' ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
            )

    def list_inbox_events(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT * FROM events
                    WHERE review_status = 'inbox'
                    ORDER BY current_importance DESC, created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            )

    def get_event(self, event_id: int) -> sqlite3.Row | None:
        with self.connect() as conn:
            return conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

    def update_event_review(
        self,
        event_id: int,
        review_status: str | None = None,
        text: str | None = None,
        importance: float | None = None,
    ) -> sqlite3.Row | None:
        existing = self.get_event(event_id)
        if existing is None:
            return None

        next_status = review_status or existing["review_status"]
        next_text = text or existing["text"]
        next_importance = existing["current_importance"] if importance is None else importance
        now = utc_now()
        reviewed_at = now if review_status in {"kept", "ignored"} else existing["reviewed_at"]
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE events
                SET text = ?, importance = ?, current_importance = ?, review_status = ?,
                    reviewed_at = ?, last_reassessed_at = ?, importance_reason = ?
                WHERE id = ?
                """,
                (
                    next_text,
                    next_importance,
                    next_importance,
                    next_status,
                    reviewed_at,
                    now if importance is not None else existing["last_reassessed_at"],
                    "User reassessed importance" if importance is not None else existing["importance_reason"],
                    event_id,
                ),
            )
            return conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

    def delete_event(self, event_id: int) -> bool:
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
            return cursor.rowcount > 0

    def recent_daily_summaries(self, limit: int = 14) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(conn.execute("SELECT * FROM daily_summaries ORDER BY day DESC LIMIT ?", (limit,)))

    def recent_reflections(self, limit: int = 14) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(conn.execute("SELECT * FROM reflections ORDER BY created_at DESC LIMIT ?", (limit,)))

    def save_daily_summary(self, day: date, summary: str, categories: dict) -> sqlite3.Row:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO daily_summaries (day, summary, categories, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(day) DO UPDATE SET
                    summary = excluded.summary,
                    categories = excluded.categories,
                    created_at = excluded.created_at
                """,
                (day.isoformat(), summary, json.dumps(categories, ensure_ascii=False), now),
            )
            return conn.execute("SELECT * FROM daily_summaries WHERE day = ?", (day.isoformat(),)).fetchone()

    def add_long_term_memory(self, memory_type: str, text: str, confidence: float, source_day: date) -> sqlite3.Row:
        now = utc_now()
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT * FROM long_term_memories WHERE memory_type = ? AND text = ?",
                (memory_type, text),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE long_term_memories SET confidence = ?, updated_at = ? WHERE id = ?",
                    (max(confidence, existing["confidence"]), now, existing["id"]),
                )
                return conn.execute("SELECT * FROM long_term_memories WHERE id = ?", (existing["id"],)).fetchone()
            cursor = conn.execute(
                """
                INSERT INTO long_term_memories
                (memory_type, text, confidence, source_day, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (memory_type, text, confidence, source_day.isoformat(), now, now),
            )
            return conn.execute("SELECT * FROM long_term_memories WHERE id = ?", (cursor.lastrowid,)).fetchone()

    def list_long_term_memories(self, limit: int = 100) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    "SELECT * FROM long_term_memories ORDER BY confidence DESC, updated_at DESC LIMIT ?",
                    (limit,),
                )
            )

    def save_reflection(self, day: date, text: str) -> sqlite3.Row:
        now = utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO reflections (day, text, created_at) VALUES (?, ?, ?)",
                (day.isoformat(), text, now),
            )
            return conn.execute("SELECT * FROM reflections WHERE id = ?", (cursor.lastrowid,)).fetchone()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

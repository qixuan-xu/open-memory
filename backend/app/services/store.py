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

    def add_event(
        self,
        text: str,
        category: str,
        importance: float,
        source: str,
        tags: list[str],
        metadata: dict,
        started_at: datetime | None,
        ended_at: datetime | None,
    ) -> sqlite3.Row:
        now = utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events
                (text, category, importance, source, tags, metadata, started_at, ended_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    text,
                    category,
                    importance,
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
                    "SELECT * FROM events WHERE created_at BETWEEN ? AND ? ORDER BY created_at ASC",
                    (start, end),
                )
            )

    def recent_events(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(conn.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,)))

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

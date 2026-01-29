import sqlite3
import json
import time
import asyncio
from typing import List, Optional
from functools import partial
from .base import BaseStorage, WebhookEvent

class SQLiteStorage(BaseStorage):
    """
    Persistent storage using SQLite.
    Runs blocking SQLite operations in a separate thread to avoid blocking the async loop.
    """
    def __init__(self, db_path: str = "webhooks.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    created_at REAL,
                    next_retry_at REAL,
                    last_error TEXT,
                    headers TEXT,
                    timeout REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status_retry ON events (status, next_retry_at)")

    async def _run_in_thread(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args))

    def _add_event_sync(self, event: WebhookEvent):
        with sqlite3.connect(self.db_path) as conn:
            headers_json = json.dumps(event.headers) if event.headers else None
            conn.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.id, event.url, json.dumps(event.payload),
                    event.status, event.attempts, event.created_at,
                    event.next_retry_at, event.last_error,
                    headers_json, event.timeout
                )
            )

    async def add_event(self, event: WebhookEvent) -> None:
        await self._run_in_thread(self._add_event_sync, event)

    def _get_pending_sync(self, limit: int, now: float) -> List[WebhookEvent]:
        events = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, url, payload, status, attempts, created_at, next_retry_at, last_error, headers, timeout
                FROM events
                WHERE status IN ('pending', 'failed') AND next_retry_at <= ?
                LIMIT ?
                """,
                (now, limit)
            )
            rows = cursor.fetchall()
            if rows:
                ids = [r[0] for r in rows]
                placeholders = ','.join('?' * len(ids))
                conn.execute(
                    f"UPDATE events SET status='processing' WHERE id IN ({placeholders})",
                    ids
                )

            for row in rows:
                events.append(WebhookEvent(
                    id=row[0],
                    url=row[1],
                    payload=json.loads(row[2]),
                    status="processing",
                    attempts=row[4],
                    created_at=row[5],
                    next_retry_at=row[6],
                    last_error=row[7],
                    headers=json.loads(row[8]) if row[8] else None,
                    timeout=row[9] if row[9] else 10.0
                ))
        return events

    async def get_pending_events(self, limit: int = 100) -> List[WebhookEvent]:
        now = time.time()
        return await self._run_in_thread(self._get_pending_sync, limit, now)

    def _update_event_sync(self, event: WebhookEvent):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE events 
                SET status=?, attempts=?, next_retry_at=?, last_error=?
                WHERE id=?
                """,
                (event.status, event.attempts, event.next_retry_at, event.last_error, event.id)
            )

    async def update_event(self, event: WebhookEvent) -> None:
        await self._run_in_thread(self._update_event_sync, event)

    def _get_event_sync(self, event_id: str) -> Optional[WebhookEvent]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM events WHERE id=?", (event_id,))
            row = cursor.fetchone()
            if row:
                return WebhookEvent(
                    id=row[0],
                    url=row[1],
                    payload=json.loads(row[2]),
                    status=row[3],
                    attempts=row[4],
                    created_at=row[5],
                    next_retry_at=row[6],
                    last_error=row[7],
                    headers=json.loads(row[8]) if row[8] else None,
                    timeout=row[9] if row[9] else 10.0
                )
        return None

    async def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        return await self._run_in_thread(self._get_event_sync, event_id)

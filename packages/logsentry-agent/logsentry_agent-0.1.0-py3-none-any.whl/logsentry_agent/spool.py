from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path


class SpoolQueue:
    def __init__(self, path: Path, max_mb: int) -> None:
        self.path = path
        self.max_bytes = max_mb * 1024 * 1024
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS spool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _db_size(self) -> int:
        if not self.path.exists():
            return 0
        return os.path.getsize(self.path)

    def enqueue(self, payload: dict) -> None:
        payload_text = json.dumps(payload, separators=(",", ":"))
        with self._connect() as conn:
            conn.execute("INSERT INTO spool (payload) VALUES (?)", (payload_text,))
            conn.commit()
        self._evict_if_needed()

    def dequeue_batch(self, limit: int) -> list[tuple[int, dict]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, payload FROM spool ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        results = []
        for row_id, payload in rows:
            results.append((row_id, json.loads(payload)))
        return results

    def delete(self, ids: list[int]) -> None:
        if not ids:
            return
        with self._connect() as conn:
            conn.executemany("DELETE FROM spool WHERE id = ?", [(row_id,) for row_id in ids])
            conn.commit()

    def pending_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM spool").fetchone()
        return int(row[0]) if row else 0

    def _evict_if_needed(self) -> None:
        if self._db_size() <= self.max_bytes:
            return
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM spool WHERE id IN (SELECT id FROM spool ORDER BY id ASC LIMIT 100)"
            )
            conn.commit()

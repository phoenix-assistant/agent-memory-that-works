"""SQLite-backed memory store."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agentmem.models import Memory, MemoryType

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL DEFAULT 'semantic',
    importance REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    access_count INTEGER NOT NULL DEFAULT 0,
    embedding TEXT,
    metadata TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance);
"""


class MemoryStore:
    """SQLite-backed persistent memory store."""

    def __init__(self, path: str | Path) -> None:
        path = Path(path).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        self._db_path = path / "memories.db"
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    # -- CRUD -----------------------------------------------------------------

    def save(self, mem: Memory) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO memories
               (id, content, memory_type, importance, created_at, last_accessed, access_count, embedding, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mem.id,
                mem.content,
                mem.memory_type.value,
                mem.importance,
                mem.created_at.isoformat(),
                mem.last_accessed.isoformat(),
                mem.access_count,
                json.dumps(mem.embedding) if mem.embedding else None,
                json.dumps(mem.metadata),
            ),
        )
        self._conn.commit()

    def get(self, memory_id: str) -> Optional[Memory]:
        row = self._conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        return self._row_to_memory(row) if row else None

    def delete(self, memory_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def list_all(self, memory_type: Optional[MemoryType] = None) -> list[Memory]:
        if memory_type:
            rows = self._conn.execute(
                "SELECT * FROM memories WHERE memory_type = ? ORDER BY importance DESC",
                (memory_type.value,),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM memories ORDER BY importance DESC").fetchall()
        return [self._row_to_memory(r) for r in rows]

    def search_keyword(self, query: str, limit: int = 10) -> list[Memory]:
        """Simple keyword search (case-insensitive LIKE)."""
        rows = self._conn.execute(
            "SELECT * FROM memories WHERE content LIKE ? ORDER BY importance DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    def update_importance(self, memory_id: str, importance: float) -> None:
        self._conn.execute("UPDATE memories SET importance = ? WHERE id = ?", (importance, memory_id))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- Internal -------------------------------------------------------------

    @staticmethod
    def _row_to_memory(row: sqlite3.Row) -> Memory:
        return Memory(
            id=row["id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            importance=row["importance"],
            created_at=datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc)
            if "+" not in row["created_at"] else datetime.fromisoformat(row["created_at"]),
            last_accessed=datetime.fromisoformat(row["last_accessed"]).replace(tzinfo=timezone.utc)
            if "+" not in row["last_accessed"] else datetime.fromisoformat(row["last_accessed"]),
            access_count=row["access_count"],
            embedding=json.loads(row["embedding"]) if row["embedding"] else None,
            metadata=json.loads(row["metadata"]),
        )

"""Memory data models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class Memory:
    content: str
    memory_type: MemoryType = MemoryType.SEMANTIC
    importance: float = 0.5
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    embedding: Optional[list[float]] = field(default=None, repr=False)
    metadata: dict = field(default_factory=dict)

    def touch(self) -> None:
        """Record an access."""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1

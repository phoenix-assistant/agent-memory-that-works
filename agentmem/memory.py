"""Main AgentMemory interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from agentmem.consolidator import (
    find_duplicates,
    find_keyword_duplicates,
    importance_decay,
    merge_memories,
)
from agentmem.models import Memory, MemoryType
from agentmem.retriever import Embedder, MemoryRetriever
from agentmem.store import MemoryStore


class AgentMemory:
    """High-level memory interface for AI agents.

    Usage::

        mem = AgentMemory(path="~/.agentmem/default")
        mem.remember("User prefers TypeScript", importance=0.8)
        results = mem.recall("programming preferences")
        mem.consolidate()
    """

    def __init__(
        self,
        path: str | Path = "~/.agentmem/default",
        embedder: Optional[Embedder] = None,
    ) -> None:
        self._store = MemoryStore(path)
        self._retriever = MemoryRetriever(embedder)

    # -- Core API -------------------------------------------------------------

    def remember(
        self,
        content: str,
        *,
        importance: float = 0.5,
        memory_type: MemoryType | str = MemoryType.SEMANTIC,
        metadata: Optional[dict] = None,
    ) -> Memory:
        """Store a memory."""
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)
        mem = Memory(
            content=content,
            importance=importance,
            memory_type=memory_type,
            metadata=metadata or {},
        )
        # Generate embedding if embedder available
        emb = self._retriever.embed(content)
        if emb:
            mem.embedding = emb
        self._store.save(mem)
        return mem

    def recall(
        self,
        query: str,
        *,
        limit: int = 10,
        memory_type: Optional[MemoryType | str] = None,
    ) -> list[Memory]:
        """Retrieve relevant memories."""
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)

        # Try semantic search first
        query_emb = self._retriever.embed(query)
        if query_emb:
            candidates = self._store.list_all(memory_type)
            results = self._retriever.rank_semantic(query_emb, candidates, limit=limit)
            if results:
                for m in results:
                    m.touch()
                    self._store.save(m)
                return results

        # Fallback to keyword
        candidates = self._store.search_keyword(query, limit=limit * 3)
        if memory_type:
            candidates = [m for m in candidates if m.memory_type == memory_type]
        results = self._retriever.rank_keyword(query, candidates, limit=limit)
        for m in results:
            m.touch()
            self._store.save(m)
        return results

    def forget(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        return self._store.delete(memory_id)

    def consolidate(
        self,
        *,
        decay: bool = True,
        merge: bool = True,
        half_life_days: float = 30.0,
        similarity_threshold: float = 0.85,
        min_importance: float = 0.01,
    ) -> dict:
        """Consolidate memories: decay importance, merge duplicates, prune."""
        stats = {"decayed": 0, "merged": 0, "pruned": 0}
        all_mems = self._store.list_all()

        # 1. Importance decay
        if decay:
            for mem in all_mems:
                new_imp = importance_decay(mem, half_life_days)
                if new_imp != mem.importance:
                    self._store.update_importance(mem.id, new_imp)
                    mem.importance = new_imp
                    stats["decayed"] += 1

        # 2. Merge duplicates
        if merge:
            pairs = (
                find_duplicates(all_mems, similarity_threshold)
                if any(m.embedding for m in all_mems)
                else find_keyword_duplicates(all_mems, threshold=similarity_threshold)
            )
            merged_ids: set[str] = set()
            for a, b in pairs:
                if a.id in merged_ids or b.id in merged_ids:
                    continue
                merged = merge_memories(a, b)
                loser = b if merged.id == a.id else a
                self._store.save(merged)
                self._store.delete(loser.id)
                merged_ids.add(loser.id)
                stats["merged"] += 1

        # 3. Prune low-importance
        for mem in self._store.list_all():
            if mem.importance < min_importance:
                self._store.delete(mem.id)
                stats["pruned"] += 1

        return stats

    # -- Utility --------------------------------------------------------------

    def count(self) -> int:
        return self._store.count()

    def list_all(self, memory_type: Optional[MemoryType] = None) -> list[Memory]:
        return self._store.list_all(memory_type)

    def close(self) -> None:
        self._store.close()

    def __enter__(self) -> AgentMemory:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

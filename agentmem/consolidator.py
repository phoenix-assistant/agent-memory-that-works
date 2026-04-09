"""Memory consolidation — merge duplicates, decay importance."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from agentmem.models import Memory
from agentmem.retriever import cosine_similarity


def importance_decay(mem: Memory, half_life_days: float = 30.0) -> float:
    """Ebbinghaus-inspired decay. Frequently accessed memories decay slower."""
    now = datetime.now(timezone.utc)
    age_days = (now - mem.created_at).total_seconds() / 86400
    # Access count slows decay
    effective_half_life = half_life_days * (1 + math.log1p(mem.access_count))
    decay_factor = 0.5 ** (age_days / effective_half_life)
    return mem.importance * decay_factor


def find_duplicates(
    memories: list[Memory],
    similarity_threshold: float = 0.85,
) -> list[tuple[Memory, Memory]]:
    """Find pairs of memories with high semantic similarity (requires embeddings)."""
    pairs: list[tuple[Memory, Memory]] = []
    for i, a in enumerate(memories):
        if not a.embedding:
            continue
        for b in memories[i + 1 :]:
            if not b.embedding:
                continue
            if cosine_similarity(a.embedding, b.embedding) >= similarity_threshold:
                pairs.append((a, b))
    return pairs


def find_keyword_duplicates(
    memories: list[Memory],
    threshold: float = 0.8,
) -> list[tuple[Memory, Memory]]:
    """Find near-duplicate memories using token overlap (no embeddings needed)."""
    pairs: list[tuple[Memory, Memory]] = []
    for i, a in enumerate(memories):
        a_tokens = set(a.content.lower().split())
        if not a_tokens:
            continue
        for b in memories[i + 1 :]:
            b_tokens = set(b.content.lower().split())
            if not b_tokens:
                continue
            overlap = len(a_tokens & b_tokens) / max(len(a_tokens | b_tokens), 1)
            if overlap >= threshold:
                pairs.append((a, b))
    return pairs


def merge_memories(a: Memory, b: Memory) -> Memory:
    """Merge two memories, keeping the higher-importance one and combining metadata."""
    primary, secondary = (a, b) if a.importance >= b.importance else (b, a)
    primary.importance = max(a.importance, b.importance)
    primary.access_count = a.access_count + b.access_count
    primary.metadata = {**secondary.metadata, **primary.metadata}
    if not primary.content.endswith(secondary.content):
        # Append unique info from secondary if it adds value
        if len(secondary.content) < len(primary.content) * 0.5:
            primary.content = f"{primary.content} ({secondary.content})"
    return primary

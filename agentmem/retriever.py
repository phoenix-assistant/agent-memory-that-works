"""Memory retrieval — semantic (optional) + keyword fallback."""

from __future__ import annotations

import math
from typing import Optional, Protocol

from agentmem.models import Memory


class Embedder(Protocol):
    """Anything that turns text into a vector."""

    def embed(self, text: str) -> list[float]: ...


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class SentenceTransformerEmbedder:
    """Optional embedder using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
        except ImportError as e:
            raise ImportError("pip install agentmem[embeddings]  # requires sentence-transformers") from e
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()


class MemoryRetriever:
    """Retrieve memories by semantic similarity or keyword fallback."""

    def __init__(self, embedder: Optional[Embedder] = None) -> None:
        self._embedder = embedder

    @property
    def has_embedder(self) -> bool:
        return self._embedder is not None

    def embed(self, text: str) -> Optional[list[float]]:
        if self._embedder:
            return self._embedder.embed(text)
        return None

    def rank_semantic(self, query_embedding: list[float], memories: list[Memory], limit: int = 10) -> list[Memory]:
        scored: list[tuple[float, Memory]] = []
        for mem in memories:
            if mem.embedding:
                sim = cosine_similarity(query_embedding, mem.embedding)
                # Boost by importance
                score = sim * 0.7 + mem.importance * 0.3
                scored.append((score, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]

    def rank_keyword(self, query: str, memories: list[Memory], limit: int = 10) -> list[Memory]:
        """Simple keyword ranking: count query term occurrences."""
        terms = query.lower().split()
        scored: list[tuple[float, Memory]] = []
        for mem in memories:
            content_lower = mem.content.lower()
            hits = sum(1 for t in terms if t in content_lower)
            if hits > 0:
                score = (hits / len(terms)) * 0.7 + mem.importance * 0.3
                scored.append((score, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]

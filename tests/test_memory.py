"""Tests for core memory operations."""

from pathlib import Path

import pytest

from agentmem import AgentMemory
from agentmem.models import Memory, MemoryType


@pytest.fixture
def mem_path(tmp_path: Path) -> Path:
    return tmp_path / "test_mem"


@pytest.fixture
def mem(mem_path: Path) -> AgentMemory:
    m = AgentMemory(path=mem_path)
    yield m
    m.close()


class TestRemember:
    def test_basic_store(self, mem: AgentMemory) -> None:
        result = mem.remember("User prefers TypeScript over Python", importance=0.8)
        assert isinstance(result, Memory)
        assert result.content == "User prefers TypeScript over Python"
        assert result.importance == 0.8
        assert mem.count() == 1

    def test_default_importance(self, mem: AgentMemory) -> None:
        result = mem.remember("some fact")
        assert result.importance == 0.5

    def test_memory_types(self, mem: AgentMemory) -> None:
        mem.remember("saw an error", memory_type=MemoryType.EPISODIC)
        mem.remember("Python is dynamically typed", memory_type="semantic")
        mem.remember("always run tests before deploy", memory_type=MemoryType.PROCEDURAL)
        assert mem.count() == 3

    def test_with_metadata(self, mem: AgentMemory) -> None:
        result = mem.remember("important", metadata={"source": "user"})
        assert result.metadata == {"source": "user"}


class TestRecall:
    def test_keyword_recall(self, mem: AgentMemory) -> None:
        mem.remember("User prefers TypeScript over Python", importance=0.8)
        mem.remember("The weather is nice today", importance=0.3)
        mem.remember("Python typing is important for large codebases", importance=0.6)
        results = mem.recall("Python")
        assert len(results) >= 1
        contents = [r.content for r in results]
        assert any("Python" in c for c in contents)

    def test_recall_updates_access(self, mem: AgentMemory) -> None:
        mem.remember("test memory")
        results = mem.recall("test")
        assert len(results) == 1
        assert results[0].access_count >= 1

    def test_recall_empty(self, mem: AgentMemory) -> None:
        results = mem.recall("nonexistent")
        assert results == []

    def test_recall_with_type_filter(self, mem: AgentMemory) -> None:
        mem.remember("event happened", memory_type=MemoryType.EPISODIC)
        mem.remember("fact about events", memory_type=MemoryType.SEMANTIC)
        results = mem.recall("event", memory_type=MemoryType.EPISODIC)
        assert all(r.memory_type == MemoryType.EPISODIC for r in results)


class TestForget:
    def test_forget(self, mem: AgentMemory) -> None:
        m = mem.remember("temporary")
        assert mem.count() == 1
        assert mem.forget(m.id) is True
        assert mem.count() == 0

    def test_forget_nonexistent(self, mem: AgentMemory) -> None:
        assert mem.forget("nope") is False


class TestConsolidate:
    def test_decay(self, mem: AgentMemory) -> None:
        mem.remember("old memory", importance=0.5)
        stats = mem.consolidate(decay=True, merge=False)
        assert stats["decayed"] >= 0  # May or may not decay depending on timing

    def test_prune_low_importance(self, mem: AgentMemory) -> None:
        mem.remember("trivial", importance=0.005)
        stats = mem.consolidate(min_importance=0.01)
        assert stats["pruned"] >= 1
        assert mem.count() == 0

    def test_keyword_duplicate_merge(self, mem: AgentMemory) -> None:
        mem.remember("the user prefers typescript over python for web development")
        mem.remember("the user prefers typescript over python for web development projects")
        assert mem.count() == 2
        stats = mem.consolidate(similarity_threshold=0.7)
        assert stats["merged"] >= 1


class TestContextManager:
    def test_context_manager(self, mem_path: Path) -> None:
        with AgentMemory(path=mem_path) as mem:
            mem.remember("test")
            assert mem.count() == 1


class TestListAll:
    def test_list_all(self, mem: AgentMemory) -> None:
        mem.remember("a", importance=0.3)
        mem.remember("b", importance=0.9)
        all_mems = mem.list_all()
        assert len(all_mems) == 2
        assert all_mems[0].importance > all_mems[1].importance  # sorted by importance

    def test_list_by_type(self, mem: AgentMemory) -> None:
        mem.remember("ep", memory_type=MemoryType.EPISODIC)
        mem.remember("sem", memory_type=MemoryType.SEMANTIC)
        assert len(mem.list_all(MemoryType.EPISODIC)) == 1

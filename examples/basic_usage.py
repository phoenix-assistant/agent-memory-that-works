"""Basic usage of agentmem."""

from agentmem import AgentMemory, MemoryType

# Create memory instance (stores in ~/.agentmem/demo)
mem = AgentMemory(path="~/.agentmem/demo")

# Store memories with different types and importance
mem.remember("User prefers TypeScript over Python", importance=0.8)
mem.remember("Deployed v2.1 to production on 2024-03-15", memory_type=MemoryType.EPISODIC, importance=0.6)
mem.remember("Always run tests before deploying", memory_type=MemoryType.PROCEDURAL, importance=0.9)
mem.remember("User's timezone is America/Los_Angeles", importance=0.7)

# Recall relevant memories
print("=== Recall: programming preferences ===")
for m in mem.recall("programming preferences"):
    print(f"  [{m.memory_type.value}] {m.content} (importance: {m.importance:.2f})")

print("\n=== Recall: deployment ===")
for m in mem.recall("deployment"):
    print(f"  [{m.memory_type.value}] {m.content} (importance: {m.importance:.2f})")

# Consolidate: decay stale memories, merge duplicates
print(f"\nMemories before consolidation: {mem.count()}")
stats = mem.consolidate()
print(f"Consolidation stats: {stats}")
print(f"Memories after consolidation: {mem.count()}")

# List all memories
print("\n=== All memories ===")
for m in mem.list_all():
    print(f"  [{m.memory_type.value}] {m.content} (importance: {m.importance:.2f}, accessed: {m.access_count}x)")

mem.close()

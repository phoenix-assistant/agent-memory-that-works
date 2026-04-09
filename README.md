<p align="center">
  <h1 align="center">🧠 Agent Memory That Actually Works</h1>
  <p align="center">Human-like memory for AI agents — learning, forgetting, and retrieval that scales.</p>
</p>

<p align="center">
  <a href="https://pypi.org/project/agentmem/"><img src="https://img.shields.io/pypi/v/agentmem?color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/agentmem/"><img src="https://img.shields.io/pypi/pyversions/agentmem" alt="Python"></a>
  <a href="https://github.com/phoenix-assistant/agent-memory-that-works/blob/main/LICENSE"><img src="https://img.shields.io/github/license/phoenix-assistant/agent-memory-that-works" alt="License"></a>
  <a href="https://github.com/phoenix-assistant/agent-memory-that-works/actions"><img src="https://img.shields.io/github/actions/workflow/status/phoenix-assistant/agent-memory-that-works/ci.yml?label=CI" alt="CI"></a>
</p>

---

Every agent framework ships with naive memory: dump everything into context, run semantic search, pray. **agentmem** gives your agents human-like memory — importance-weighted storage, Ebbinghaus forgetting curves, automatic consolidation, and MCP-compatible retrieval.

## Quick Start

```bash
pip install agentmem
```

```python
from agentmem import AgentMemory

mem = AgentMemory()
mem.remember("User prefers TypeScript over Python", importance=0.8)
mem.remember("Meeting with Alice at 3pm today", memory_type="episodic")
results = mem.recall("programming preferences", top_k=5)
mem.consolidate()  # merge duplicates, decay stale memories
```

## Why agentmem?

| Feature | agentmem | Mem0 | LangChain Memory | MemPalace |
|---------|----------|------|------------------|-----------|
| Open source | ✅ | ❌ (cloud) | ✅ | ✅ |
| Forgetting curves | ✅ | ❌ | ❌ | ❌ |
| Importance scoring | ✅ | ❌ | ❌ | Partial |
| Memory consolidation | ✅ | ❌ | ❌ | ❌ |
| MCP server | ✅ | ❌ | ❌ | ❌ |
| Framework agnostic | ✅ | ✅ | ❌ | ✅ |
| Local-first (SQLite) | ✅ | ❌ | ✅ | ✅ |
| Memory types (episodic/semantic/procedural) | ✅ | ❌ | ❌ | Partial |

## Memory Types

- **Episodic** — Raw experiences and events ("User asked about deployment at 2pm")
- **Semantic** — Learned facts and preferences ("User prefers dark mode")
- **Procedural** — Patterns and skills ("When user says 'deploy', run the CI pipeline first")

## API Reference

| Method | Description |
|--------|-------------|
| `AgentMemory(path=...)` | Create memory instance (SQLite-backed) |
| `.remember(content, importance=0.5, memory_type="semantic", metadata={})` | Store a memory |
| `.recall(query, top_k=10)` | Retrieve relevant memories |
| `.forget(memory_id)` | Remove a specific memory |
| `.consolidate()` | Merge duplicates, apply decay, prune low-importance |
| `.get(memory_id)` | Fetch a single memory by ID |
| `.list(memory_type=None, limit=100)` | List memories with optional type filter |
| `.stats()` | Memory store statistics |

## MCP Server

agentmem runs as an [MCP](https://modelcontextprotocol.io/) tool server, making it usable by any MCP-compatible agent.

```bash
# Run the MCP server
python -m agentmem.mcp_server
```

Or add to your MCP config:

```json
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": ["-m", "agentmem.mcp_server"]
    }
  }
}
```

**MCP Tools exposed:** `remember`, `recall`, `forget`, `consolidate`

## How It Works

### Ebbinghaus Forgetting Curve

Memories decay over time based on the Ebbinghaus forgetting curve. Each access strengthens the memory (spaced repetition). High-importance memories decay slower. Low-importance, rarely-accessed memories are pruned during consolidation.

### Consolidation

`consolidate()` performs three operations:
1. **Duplicate detection** — finds semantically similar memories and merges them
2. **Importance decay** — applies time-based decay to all memories
3. **Pruning** — removes memories below the importance threshold

## Installation

```bash
# Core (SQLite, no embeddings)
pip install agentmem

# With semantic search (sentence-transformers)
pip install agentmem[embeddings]

# Development
pip install agentmem[dev]
```

## Roadmap

1. 🔌 Pluggable vector backends (pgvector, Chroma, Qdrant)
2. 🌐 REST API server mode
3. 🔗 LangChain / LlamaIndex adapter packages
4. 🤖 AutoGen / CrewAI integration
5. 📊 Memory visualization dashboard
6. 👥 Multi-agent shared memory
7. 🏢 Enterprise: audit logs, PII scrubbing, memory policies
8. 🧪 LongMemEval benchmark suite
9. 🗜️ Memory compression for long-running agents
10. ☁️ Hosted cloud service (managed memory-as-a-service)

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/phoenix-assistant/agent-memory-that-works.git
cd agent-memory-that-works
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).

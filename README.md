# Agent Memory That Actually Works
> The memory layer for AI agents that learns, forgets, and retrieves like a human — not a database.

## Problem

**Who:** AI engineers and product teams building production agents at companies shipping LLM-powered products (startups through enterprise, any agent framework).

**Pain:** Every agent framework ships with naive memory: dump everything into context, run semantic search, pray. Real agents need to learn from experience, prioritize recent over stale, consolidate redundant memories, and forget irrelevant noise. Without this, agents hallucinate past facts, repeat mistakes, and hit context limits. Teams spend weeks building custom memory — and it still breaks.

**Current solutions:** Mem0 is commercial/cloud-only with vendor lock-in. MemPalace achieves 100% on LongMemEval but isn't production-ready open source. Hindsight (7.8k★) focuses on reflection/self-critique, not retrieval. LangChain/LlamaIndex memory modules are shallow key-value or naive vector stores. Our own `learning-agent-memory` and `agent-memory-system` repos are fragmented — two half-solutions.

## Solution

**What:** A production-grade, open-source persistent memory library for any agent framework — with human-like learning, forgetting, consolidation, and MCP-compatible retrieval.

**How:** Hierarchical memory with episodic (raw experiences), semantic (learned facts), and procedural (patterns/skills) layers. Importance scoring drives forgetting. Spaced repetition strengthens high-signal memories. MCP tool interface means any agent can use it with zero framework coupling.

**Why us:** We consolidate our two existing repos into one production system, seeded with real-world agent deployment experience. Framework-agnostic MCP interface means we win across the entire ecosystem — LangChain, LlamaIndex, CrewAI, AutoGen, custom frameworks.

## Why Now

- MCP is becoming the standard agent tool protocol — a memory layer as an MCP server is instantly usable by every MCP-compatible agent
- MemPalace's 100% LongMemEval score proves the technical bar is achievable; no open-source project has hit it in production
- Hindsight's 7.8k stars show massive demand; their gap is retrieval quality
- Agent frameworks are proliferating — teams need memory that works across all of them
- OpenAI, Anthropic, Google all shipping agent frameworks with primitive memory — third-party memory layer is a clear gap

## Market Landscape

**TAM:** $8B — AI agent infrastructure market (2025, growing 40%+ CAGR)
**SAM:** $1.5B — memory, context, and retrieval layer for agents
**Target:** $1M ARR Year 1 (hosted API + enterprise support), $10M ARR Year 3

### Competitors

| Company | Funding | Users | Gap We Exploit |
|---------|---------|-------|----------------|
| Mem0 | $23M | Unknown | Commercial/cloud-only, vendor lock-in, no forgetting |
| MemPalace | OSS | Niche | Not production-ready, no MCP, research-first |
| Hindsight | OSS (7.8k★) | Growing | Reflection-focused, weak retrieval, no forgetting layer |
| LangChain Memory | OSS | Millions | Shallow, no importance scoring, tightly coupled |
| Zep | $3.5M | Unknown | Narrow use case (chatbot history), not general agent memory |

### Why We Win

We're the only production-grade, framework-agnostic, open-source memory system with human-like forgetting and learning. MCP compatibility gives us instant reach across every agent framework without integration work. Our existing repos give us a head start and real-world insights. MemPalace proved 100% LongMemEval is achievable — we ship it as a production library.

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Agent (any framework)                      │
│  LangChain │ LlamaIndex │ CrewAI │ AutoGen │ Custom     │
└──────────────────┬──────────────────────────────────────┘
                   │ MCP Tool Calls / Python SDK / REST
┌──────────────────▼──────────────────────────────────────┐
│              Memory Server (MCP-compatible)              │
│  store() │ retrieve() │ forget() │ consolidate()        │
└────┬──────────────┬──────────────────────────────────────┘
     │              │
┌────▼──────┐  ┌────▼───────────────────────────────────┐
│ Episodic  │  │           Memory Engine                  │
│ Store     │  │  importance scorer │ forgetting curve    │
│ (raw      │  │  consolidation     │ spaced repetition   │
│ events)   │  │  deduplication     │ conflict resolution │
└───────────┘  └────────────────────────────────────────┘
     │              │
┌────▼──────────────▼────────────────────────────────────┐
│              Storage Layer                              │
│  SQLite (local) │ Postgres (production) │ Redis (cache) │
│  pgvector / Chroma / Qdrant (embeddings)                │
└────────────────────────────────────────────────────────┘
```

### Stack
| Component | Technology | Why |
|-----------|------------|-----|
| Core Library | Python | Ecosystem fit — all agent frameworks are Python |
| MCP Server | FastMCP / Python MCP SDK | Standard protocol, zero framework coupling |
| Vector Store | Pluggable (pgvector default) | Avoid lock-in, support any setup |
| Importance Scoring | LLM + heuristics | Flexible, tunable per use case |
| Storage | SQLite → Postgres | Simple local dev, production-scale upgrade |
| Embeddings | Pluggable (OpenAI/local) | Privacy + cost options |

### Key Technical Decisions
1. **MCP-first, SDK second** — MCP server means any agent can use memory without code changes. Python SDK for tight integration. This is how we win adoption across all frameworks without fragmentation.
2. **Merge `learning-agent-memory` + `agent-memory-system`** — Our two repos solve complementary problems. `learning-agent-memory` has the learning loop; `agent-memory-system` has the retrieval layer. Unified into one production system.
3. **Human forgetting curve** — Ebbinghaus-inspired decay with importance weighting. High-signal memories strengthen with use; low-signal memories decay and consolidate. This is the differentiator that benchmarks don't test but production needs.

## Build Plan

**Timeline:** 6 weeks to production v1

### Week 1-2: Foundation
- Audit and extract best code from `learning-agent-memory` + `agent-memory-system`
- Core memory engine: store, retrieve, importance scoring, basic forgetting
- SQLite backend + pgvector backend
- Pluggable embedding providers (OpenAI, local)
- Test suite targeting LongMemEval benchmark

### Week 3-4: Core Product
- MCP server implementation (memory as MCP tools)
- Python SDK with LangChain + LlamaIndex adapters
- Forgetting curve + consolidation pipeline
- Conflict resolution (contradictory memories)
- CLI: `agentmem inspect`, `agentmem stats`, `agentmem export`

### Week 5-6: Production Ready
- Async support (FastAPI-based server)
- Benchmark suite (LongMemEval + custom)
- Documentation (Docusaurus)
- PyPI publish: `pip install agentmem`
- Landing page + benchmark results page

### Month 2-3: Growth
- AutoGen + CrewAI adapters
- REST API hosted service (cloud option)
- Memory visualization dashboard
- Multi-agent shared memory (agent teams)
- Persistence across agent restarts (stateful agent sessions)

### Month 4-6: Moat
- Enterprise: audit logs, memory policies, PII scrubbing
- Fine-tuned importance scoring model (trained on production data)
- Memory compression for long-running agents
- Partnerships with major agent framework maintainers

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OpenAI/Anthropic ship native memory | H | M | MCP-first means we work alongside them, not against |
| Fragmentation of agent frameworks | M | M | MCP server = framework agnostic by design |
| Performance at scale (millions of memories) | M | H | Redis caching layer + memory compression from M4 |
| LLM costs for importance scoring | M | M | Local model option + heuristic fallback |
| Existing repos create confusion/conflict | L | M | Archive both, clear migration guide to unified repo |

## Monetization

**Model:** Open-source core. Hosted API (cloud memory service) + enterprise support.

**Year 1 Path to $1M ARR:**
| Segment | Price | Customers | ARR |
|---------|-------|-----------|-----|
| Hosted API (startups) | $99/mo | 300 | $356K |
| Hosted API (growth) | $499/mo | 50 | $300K |
| Enterprise support | $25K/yr | 10 | $250K |
| Enterprise custom | $50K/yr | 2 | $100K |
| **Total** | | | **$1.006M** |

**Year 3 Vision:** $10M ARR via enterprise memory-as-a-service (agent teams at Fortune 500 need auditable, compliant memory layers).

## Verdict

🟢 BUILD

**Reasoning:** Memory is the unsexy infrastructure problem blocking every production agent deployment. We have two repos proving we've thought about this deeply — now we consolidate into the definitive open-source solution. MCP compatibility gives instant reach across the entire ecosystem. MemPalace proves 100% LongMemEval is achievable; Hindsight's 7.8k stars prove the demand is there. We build the production-grade version that ships to PyPI and becomes the default choice.

**First customer:** Teams actively struggling with agent memory failures — find them in LangChain Discord, LlamaIndex Slack, and r/MachineLearning threads complaining about agent context limits. Direct outreach to 10 teams building production agents.

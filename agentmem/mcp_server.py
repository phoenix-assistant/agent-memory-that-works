"""MCP-compatible tool server for agent memory.

Exposes remember, recall, forget, consolidate as MCP tools.
Run with: python -m agentmem.mcp_server
"""

from __future__ import annotations

import json
import sys
from typing import Any

from agentmem.memory import AgentMemory

# MCP tool definitions
TOOLS = [
    {
        "name": "remember",
        "description": (
            "Store a memory for later retrieval. "
            "Memories can be episodic (events), semantic (facts), or procedural (how-to)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The memory content to store"},
                "importance": {"type": "number", "description": "Importance score 0-1 (default 0.5)", "default": 0.5},
                "memory_type": {
                    "type": "string",
                    "enum": ["episodic", "semantic", "procedural"],
                    "default": "semantic",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "recall",
        "description": (
            "Retrieve relevant memories matching a query. "
            "Uses semantic search when embeddings are available, keyword fallback otherwise."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 10)", "default": 10},
                "memory_type": {
                    "type": "string",
                    "enum": ["episodic", "semantic", "procedural"],
                    "description": "Filter by memory type",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "forget",
        "description": "Delete a specific memory by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string", "description": "ID of memory to delete"},
            },
            "required": ["memory_id"],
        },
    },
    {
        "name": "consolidate",
        "description": "Consolidate memories: decay stale importance, merge duplicates, prune low-value memories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "half_life_days": {"type": "number", "default": 30.0},
                "min_importance": {"type": "number", "default": 0.01},
            },
        },
    },
]


class MCPServer:
    """Minimal MCP stdio server for agent memory."""

    def __init__(self, memory_path: str = "~/.agentmem/default") -> None:
        self._mem = AgentMemory(path=memory_path)

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return self._response(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "agentmem", "version": "0.1.0"},
            })

        if method == "tools/list":
            return self._response(req_id, {"tools": TOOLS})

        if method == "tools/call":
            return self._handle_tool_call(req_id, params)

        if method == "notifications/initialized":
            return {}  # No response needed for notifications

        return self._error(req_id, -32601, f"Method not found: {method}")

    def _handle_tool_call(self, req_id: Any, params: dict) -> dict:
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "remember":
                mem = self._mem.remember(
                    args["content"],
                    importance=args.get("importance", 0.5),
                    memory_type=args.get("memory_type", "semantic"),
                )
                result = {"id": mem.id, "stored": True}

            elif name == "recall":
                memories = self._mem.recall(
                    args["query"],
                    limit=args.get("limit", 10),
                    memory_type=args.get("memory_type"),
                )
                result = [
                    {
                        "id": m.id,
                        "content": m.content,
                        "type": m.memory_type.value,
                        "importance": round(m.importance, 3),
                        "access_count": m.access_count,
                    }
                    for m in memories
                ]

            elif name == "forget":
                deleted = self._mem.forget(args["memory_id"])
                result = {"deleted": deleted}

            elif name == "consolidate":
                stats = self._mem.consolidate(
                    half_life_days=args.get("half_life_days", 30.0),
                    min_importance=args.get("min_importance", 0.01),
                )
                result = stats

            else:
                return self._error(req_id, -32602, f"Unknown tool: {name}")

            return self._response(req_id, {
                "content": [{"type": "text", "text": json.dumps(result)}],
            })

        except Exception as e:
            return self._response(req_id, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            })

    @staticmethod
    def _response(req_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error(req_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def run_stdio(self) -> None:
        """Run as MCP stdio server."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue
            response = self.handle_request(request)
            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="agentmem MCP server")
    parser.add_argument("--path", default="~/.agentmem/default", help="Memory storage path")
    args = parser.parse_args()
    server = MCPServer(memory_path=args.path)
    server.run_stdio()


if __name__ == "__main__":
    main()

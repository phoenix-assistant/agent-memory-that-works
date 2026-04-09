"""Tests for MCP server."""

from pathlib import Path

import pytest

from agentmem.mcp_server import MCPServer


@pytest.fixture
def server(tmp_path: Path) -> MCPServer:
    return MCPServer(memory_path=str(tmp_path / "mcp_test"))


class TestMCPServer:
    def test_initialize(self, server: MCPServer) -> None:
        resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert resp["result"]["serverInfo"]["name"] == "agentmem"

    def test_tools_list(self, server: MCPServer) -> None:
        resp = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = resp["result"]["tools"]
        names = [t["name"] for t in tools]
        assert "remember" in names
        assert "recall" in names
        assert "forget" in names
        assert "consolidate" in names

    def test_remember_and_recall(self, server: MCPServer) -> None:
        # Remember
        resp = server.handle_request({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "remember", "arguments": {"content": "test memory", "importance": 0.9}},
        })
        assert "error" not in resp

        # Recall
        resp = server.handle_request({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "recall", "arguments": {"query": "test"}},
        })
        assert "error" not in resp

    def test_unknown_method(self, server: MCPServer) -> None:
        resp = server.handle_request({"jsonrpc": "2.0", "id": 5, "method": "bogus", "params": {}})
        assert "error" in resp

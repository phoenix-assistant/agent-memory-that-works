"""Example: Using agentmem with LangChain.

agentmem works alongside any framework. This shows how to wire it
into a LangChain agent as a tool.
"""

from agentmem import AgentMemory

# Initialize memory
mem = AgentMemory(path="~/.agentmem/langchain-agent")


def remember_tool(content: str, importance: float = 0.5) -> str:
    """LangChain-compatible tool: store a memory."""
    m = mem.remember(content, importance=importance)
    return f"Stored memory {m.id}"


def recall_tool(query: str) -> str:
    """LangChain-compatible tool: recall memories."""
    results = mem.recall(query, limit=5)
    if not results:
        return "No relevant memories found."
    return "\n".join(f"- {m.content} (importance: {m.importance:.2f})" for m in results)


# Usage with LangChain (pseudo-code — requires langchain installed):
#
# from langchain.tools import Tool
# from langchain.agents import initialize_agent
#
# tools = [
#     Tool(name="Remember", func=remember_tool, description="Store a fact for later"),
#     Tool(name="Recall", func=recall_tool, description="Retrieve relevant memories"),
# ]
#
# agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
# agent.run("Remember that the user prefers dark mode, then recall their UI preferences")

if __name__ == "__main__":
    # Demo without LangChain
    print(remember_tool("User prefers dark mode", importance=0.7))
    print(remember_tool("App uses React frontend", importance=0.6))
    print(recall_tool("UI preferences"))
    mem.close()

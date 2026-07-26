"""CLI entrypoint for the ForgeMCP LangGraph agent (converted from Agent.ipynb).

Loads MCP tools from the ForgeMCP server, compiles the graph, and runs a simple
input loop, resolving any HITL approval interrupts via stdin.
"""

import asyncio
import uuid

from langchain_mcp_adapters.client import MultiServerMCPClient

from Agent.service import get_mcp_server
from Agent import nodes
from Agent.graph import compile_graph, run_graph


async def main():
    client = MultiServerMCPClient(get_mcp_server())
    tools = await client.get_tools()
    nodes.set_tools(tools)

    graph = compile_graph()

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    while True:
        question = input("\nYou: ")
        if question.strip().lower() in {"exit", "quit"}:
            break

        result = await run_graph(graph, question, config)
        print(f"\nAssistant: {result.get('final_answer', '')}")


if __name__ == "__main__":
    asyncio.run(main())

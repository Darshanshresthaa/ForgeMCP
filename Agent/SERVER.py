
import asyncio
import uuid

from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from Agent.service import get_mcp_server, get_db_uri
from Agent.nodes import set_tools
from Agent.graph import compiled_graph_with_postgres, run_graph




async def main():
    client = MultiServerMCPClient(get_mcp_server())
    tools = await client.get_tools()

    set_tools(tools)  #passing list of tools

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

   
    async with compiled_graph_with_postgres(get_db_uri()) as graph:

        while True:
            question = input("\nYou: ").strip()

            if question.lower() in {"end", "exit", "quit"}:
                print(
                    """
============================================================

Thank you for using ForgeMCP.

Keep coding.
Keep learning.
Keep building.

Every project you complete,
every bug you fix,
and every challenge you overcome
makes you a better engineer.

Success is not achieved overnight.
It is built through consistent effort,
continuous learning,
and persistence.

"The expert in anything was once a beginner."

Goodbye, and happy coding!

============================================================
"""
                )
                break

            try:
                result = await run_graph(
                    graph=graph,
                    question=question,
                    config=config,
                    messages=[HumanMessage(content=question)],
                )

                for k, v in result.items():
                    if k == "messages":
                        continue
                    print(f"{k}: {v}")
                    print()

                print()
                print("=" * 90)
                print()

            except KeyboardInterrupt:
                print("\nSession interrupted by user.")
                break

            except Exception as e:
                print(f"\nAn unexpected error occurred:\n{e}")


if __name__ == "__main__":
    asyncio.run(main())

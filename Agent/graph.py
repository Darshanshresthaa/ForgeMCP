"""Graph wiring for the ForgeMCP LangGraph agent (converted from Agent.ipynb)."""

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from Agent.state import State
from Agent import nodes


def build_graph() -> StateGraph:
    """Wire up the StateGraph. Call nodes.set_tools(tools) before compiling/running."""
    builder = StateGraph(State)

    # Nodes
    builder.add_node("intent_classifier_node", nodes.intent_classifier_node)
    builder.add_node("llm_answer_node", nodes.llm_answer_node)

    builder.add_node("normal_tools", nodes.normal_tools)

    builder.add_node("tool_safety_node", nodes.tool_safety_node)
    builder.add_node("dangerous_tools", nodes.dangerous_tools)

    builder.add_node("execute_tools", nodes.execute_tools)
    builder.add_node("tool_response_node", nodes.tool_response_node)

    builder.add_edge(START, "intent_classifier_node")

    builder.add_conditional_edges(
        "intent_classifier_node",
        nodes.router,
        {
            "tools_required": "normal_tools",
            "llm_answer": "llm_answer_node",
        },
    )

    builder.add_conditional_edges(
        "normal_tools",
        nodes.tool_selection_router,
        {
            "safety_check": "tool_safety_node",
            "end": END,
        },
    )

    builder.add_conditional_edges(
        "tool_safety_node",
        nodes.tool_safety_router,
        {
            "hitl": "dangerous_tools",
            "normal": "execute_tools",
        },
    )

    builder.add_conditional_edges(
        "dangerous_tools",
        nodes.approval_routing,
        {
            "tool_execute": "execute_tools",
            "end": END,
        },
    )

    builder.add_edge("execute_tools", "tool_response_node")

    builder.add_edge("tool_response_node", END)
    builder.add_edge("llm_answer_node", END)

    return builder


def compile_graph():
    """Build and compile the graph with an in-memory checkpointer."""
    builder = build_graph()
    memory = InMemorySaver()
    return builder.compile(checkpointer=memory)


async def run_graph(graph, question: str, config: dict):
    """Run the graph end-to-end, prompting on stdin for any Human-In-The-Loop approval."""
    result = await graph.ainvoke(
        {"question": question},
        config=config,
    )

    while "__interrupt__" in result:
        interrupt_data = result["__interrupt__"][0].value

        print(interrupt_data["message"])

        if interrupt_data["type"] == "approval":
            value = input("(y/n): ").lower() == "y"
        else:
            value = input("> ")

        result = await graph.ainvoke(
            Command(resume=value),
            config=config,
        )

    return result

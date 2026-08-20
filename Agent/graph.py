
from contextlib import asynccontextmanager

from langchain_core.messages import BaseMessage
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from Agent.state import State
from Agent import nodes


def build_graph() -> StateGraph:

    """Wire up the StateGraph. Call nodes.set_tools(tools) before compiling/running."""
    
    builder = StateGraph(State)

    # Nodes
    builder.add_node("planner_node", nodes.planner_node)
    builder.add_node("intent_classifier_node", nodes.intent_classifier_node)

    builder.add_node("llm_answer_node", nodes.llm_answer_node)
    builder.add_node("normal_tools", nodes.normal_tools)

    builder.add_node("tool_safety_node", nodes.tool_safety_node)
    builder.add_node("dangerous_tools", nodes.dangerous_tools)

    builder.add_node("execute_tools", nodes.execute_tools)
    builder.add_node("tool_response_node", nodes.tool_response_node)

    builder.add_node("update_task_node", nodes.update_task_node)

    builder.add_node("summary_node", nodes.summary_node)

    builder.add_edge(START, "planner_node")

    
    builder.add_conditional_edges(
        "planner_node",
        nodes.planner_router,
        {
            "intent_classifier": "intent_classifier_node",
            "summary": "summary_node",
        },
    )

  
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
            "end": "update_task_node",
        },
    )

    # Tool safety if/else
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
            "end": "update_task_node",
        },
    )

    builder.add_edge("execute_tools", "tool_response_node")
    builder.add_edge("tool_response_node", "update_task_node")
    builder.add_edge("llm_answer_node", "update_task_node")

    # Loop back over remaining subtasks, or wrap up with the summary
    builder.add_conditional_edges(
        "update_task_node",
        nodes.planner_router,
        {
            "intent_classifier": "intent_classifier_node",
            "summary": "summary_node",
        },
    )

    builder.add_edge("summary_node", END)

    return builder


# def compile_graph():

#   """ cOMPLE GRAPH WITH Inmemory RAM soore"""

#     builder = build_graph()
#     memory = InMemorySaver()
#     return builder.compile(checkpointer=memory)



async def run_graph(
    graph,
    question: str,
    config: dict,
    messages: list[BaseMessage] | None = None,
):
    """Run the graph end-to-end, prompting on stdin for any Human-In-The-Loop approval."""
    messages = nodes.balance_context_window(messages or [])

    result = await graph.ainvoke(
        {
            "question": question,
            "messages": messages,
        },
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

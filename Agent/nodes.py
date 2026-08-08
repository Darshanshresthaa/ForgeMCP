"""Node functions for the ForgeMCP LangGraph agent (converted from agent_copy.ipynb)."""

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.types import interrupt

from Agent.service import get_llm
from Agent.state import State, RouterDecision, ToolSafetyDecision, PlannerOutput
from Agent.Prompts.planner_prompt import planner_prompt
from Agent.Prompts.router_prompt import router_prompt
from Agent.Prompts.llm_answer_node_prompt import llm_answer_prompt
from Agent.Prompts.tool_response_node_prompt import tool_response_prompt
from Agent.Prompts.tool_safety_node_prompt import tool_safety_prompt
from Agent.Prompts.summary_prompt import summary_prompt


model = get_llm()

# Populated at runtime via set_tools() once MultiServerMCPClient.get_tools() resolves.
tools: list = []
llm_with_tools = None

MAX_MESSAGES = 20


def set_tools(tool_list: list) -> None:

    """Inject the loaded MCP tools. Must be called before the graph is run."""
    
    global tools, llm_with_tools
    tools = tool_list
    llm_with_tools = model.bind_tools(tools)


def balance_context_window(messages: list[BaseMessage]) -> list[BaseMessage]:
    """
    Keep the conversation history within the maximum context window.

    When the limit is exceeded, remove the oldest conversation turn
    (the oldest HumanMessage and AIMessage).
    """
    if len(messages) <= MAX_MESSAGES:
        return messages

    return messages[2:]



def planner_node(state: State):

    """Break the user's request down into an ordered list of subtasks."""

    chain = planner_prompt | model.with_structured_output(PlannerOutput)

    plan = chain.invoke(
        {
            "question": state.question,
            "messages": state.messages,
        }
    )

    if plan.tasks:
        current_task = plan.tasks[0].description
    else:
        current_task = None

    return {
        "subtasks": plan.tasks,
        "current_task_index": 0,
        "current_task": current_task,
        "plan_completed": len(plan.tasks) == 0,
    }


def planner_router(state: State):

    """After planning (or after finishing a task), continue the plan or summarize."""

    if state.plan_completed:
        return "summary"

    return "intent_classifier"


def intent_classifier_node(state: State):

    """Identify whether a tool is needed OR the current subtask can be answered directly by the llm."""

    router_llm = router_prompt | model.with_structured_output(RouterDecision)

    current_task = state.subtasks[state.current_task_index]
    result = router_llm.invoke(
        {
            "question": current_task.description,
            "messages": state.messages,
        }
    )
    return {"router_decision": result}


def router(state: State):

    """Route to llm if no tool is needed, else route to the tools node."""

    if state.router_decision.decision == "tool":
        return "tools_required"
    return "llm_answer"


def llm_answer_node(state: State):

    """LLM answer node used when the current subtask needs no tool."""

    chain = llm_answer_prompt | model

    answer = ""
    current = state.subtasks[state.current_task_index]

    for chunk in chain.stream(
        {
            "question": current.description,
            "messages": state.messages,
        }
    ):
        if chunk.content:
            answer += chunk.content

    return {
        "final_answer": answer,
        "execution_log": [f"Task: {current.description}\n{answer}"],
        "messages": [AIMessage(content=answer)],
    }


def normal_tools(state: State):

    """Select the appropriate tool and extract its arguments for the current subtask."""

    current = state.subtasks[state.current_task_index]

    result = llm_with_tools.invoke(current.description)

    if not result.tool_calls:
        answer = (
            result.content
            or "I couldn't determine which action to take. Could you rephrase your request?"
        )

        return {
            "final_answer": answer,
            "tool_name": None,
            "tool_arguments": {},
            "tool_calls": [],
            "messages": [AIMessage(content=answer)],
        }

    tool_call = result.tool_calls[0]

    return {
        "tool_calls": result.tool_calls,
        "tool_arguments": tool_call["args"],
        "tool_name": tool_call["name"],
        "final_answer": "",
    }


def tool_selection_router(state: State):

    """If a tool was selected, go to safety check, else end."""

    if state.tool_name:
        return "safety_check"
    return "end"


def tool_safety_node(state: State):

    """Safety check: is this a normal read operation or a destructive one."""

    selected_tool = None
    for tool in tools:
        if tool.name == state.tool_name:
            selected_tool = tool
            break

    if selected_tool is None:
        return {
            "final_answer": f"Unknown tool: {state.tool_name}",
            "requires_hitl": False,
        }

    chain = tool_safety_prompt | model.with_structured_output(ToolSafetyDecision)

    current = state.subtasks[state.current_task_index]
    result = chain.invoke(
        {
            "question": current.description,
            "tool_name": selected_tool.name,
            "tool_description": selected_tool.description,
            "messages": state.messages,
        }
    )

    return {
        "tool_safety": result,
        "requires_hitl": result.decision == "hitl",
    }


def tool_safety_router(state: State):

    """Route to normal execution if read-only, else to Human-In-The-Loop."""

    if state.requires_hitl:
        return "hitl"
    return "normal"


def dangerous_tools(state: State):

    """Implement Human-In-The-Loop approval for destructive operations."""

    reason = state.tool_safety.reason if state.tool_safety else ""

    decision = interrupt(
        {
            "type": "approval",
            "message": (
                f"The assistant wants to run '{state.tool_name}' with arguments \n\n"
                f"{state.tool_arguments}.\nReason: {reason}\nApprove? (y/n)"
            ),
        }
    )

    approved = bool(decision)
    update: dict[str, Any] = {"approved": approved}

    if not approved:
        update["final_answer"] = "Action cancelled — not approved by user."

    return update


def approval_routing(state: State):

    """If a destructive tool was approved by the user, execute it; else end."""

    if state.approved:
        return "tool_execute"
    return "end"


async def execute_tools(state: State):

    """Actual tool invocation, passing the previously selected arguments."""

    selected_tool = None

    for tool in tools:
        if tool.name == state.tool_name:
            selected_tool = tool
            break

    if selected_tool is None:
        return {"final_answer": f"Tool {state.tool_name} not found"}

    try:
        result = await selected_tool.ainvoke(state.tool_arguments)
        return {"tool_result": result}
    except Exception as ex:
        return {"final_answer": f"Tool failed: {ex} \n\n {str(ex)}"}


def tool_response_node(state: State):

    """Final answer generated by the llm based on what the tool returned."""

    chain = tool_response_prompt | model

    current = state.subtasks[state.current_task_index]

    response = chain.invoke(
        {
            "question": current.description,
            "tool_name": state.tool_name,
            "tool_result": state.tool_result,
            "messages": state.messages,
        }
    )

    return {
        "final_answer": response.content,
        "execution_log": [f"Task: {current.description}\n{response.content}"],
        "messages": [AIMessage(content=response.content)],
    }


def update_task_node(state: State):

    """Mark the current subtask as completed and advance to the next one."""

    tasks = state.subtasks.copy()

    task = tasks[state.current_task_index]

    if state.tool_result is not None:
        task.status = "completed"
        task.result = state.tool_result
    else:
        task.status = "completed"
        task.result = state.final_answer

    next_index = state.current_task_index + 1

    finished = next_index >= len(tasks)

    return {
        "subtasks": tasks,
        "current_task_index": next_index,
        "plan_completed": finished,
    }


def summary_node(state: State):

    """Summarize the full execution plan and log into a final Markdown report."""

    chain = summary_prompt | model

    plan = ""
    for i, task in enumerate(state.subtasks, start=1):
        plan += f"{i}. {task.description}\n\n"

    response = chain.invoke(
        {
            "question": state.question,
            "plan": plan,
            "execution_log": "\n\n".join(state.execution_log),
        }
    )

    return {
        "final_answer": response.content,
        "messages": [AIMessage(content=response.content)],
    }

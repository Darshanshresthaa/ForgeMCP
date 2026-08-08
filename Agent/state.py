from pydantic import BaseModel, Field

from typing import Literal, Any, Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class RouterDecision(BaseModel):
    decision: Literal["tool", "llm"] = Field(
        description="Return 'tool' if a tool is required, otherwise return 'llm'."
    )

    tool_name: str | None = Field(
        default=None,
        description="Exact tool name to execute if decision is 'tool'."
    )

    tool_description: str | None = Field(
        default=None,
        description="Description of the selected tool."
    )


class ToolSafetyDecision(BaseModel):
    decision: Literal["hitl", "safe"] = Field(
        description=(
            "Return 'hitl' if the tool modifies, creates, deletes, merges, "
            "or performs any irreversible action. "
            "Return 'safe' if the tool is read-only."
        )
    )

    reason: str = Field(
        description="Short explanation for the decision."
    )


class TaskPlan(BaseModel):
    description: str = Field(
        description="Description of the task."
    )

    status: Literal["pending", "running", "completed", "failed"] = Field(
        default="pending",
        description="Current execution status of the task."
    )

    result: Any | None = Field(
        default=None,
        description="Result produced after executing the task."
    )


class PlannerOutput(BaseModel):
    tasks: list[TaskPlan] = Field(
        description="Ordered list of planned tasks."
    )


class State(BaseModel):
    question: str = Field(default="", description="User query.")

    final_answer: str = Field(default="", description="Final answer shown to the user.")

    router_decision: RouterDecision | None = Field(
        default=None,
        description="Decision returned by the router."
    )

    tool_safety: ToolSafetyDecision | None = Field(
        default=None,
        description="Safety decision for the selected tool."
    )

    requires_hitl: bool = Field(
        default=False,
        description="Whether human approval is required."
    )

    approved: bool = Field(default=False, description="Whether the human approved a HITL tool call.")

    tool_result: Any = Field(default=None, description="Result returned by the executed tool.")

    tool_arguments: dict[str, Any] = Field(default_factory=dict)

    tool_name: str | None = None

    tool_calls: list[Any] = Field(default_factory=list)

    messages: Annotated[list[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="Conversation history."
    )

    # Planner / multi-task execution

    subtasks: list[TaskPlan] = Field(
        default_factory=list,
        description="Ordered list of planned tasks."
    )

    current_task_index: int = Field(
        default=0,
        description="Zero-based index of the task currently being executed."
    )

    current_task: str | None = Field(
        default=None,
        description="The current task selected for execution."
    )

    execution_log: list[str] = Field(
        default_factory=list,
        description="Execution log for completed tasks."
    )

    plan_completed: bool = Field(
        default=False,
        description="Whether all planned tasks have been executed successfully."
    )

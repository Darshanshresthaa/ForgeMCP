from pydantic import BaseModel,Field

from typing import Literal,Any

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

from langchain_core.prompts import ChatPromptTemplate

summary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an AI assistant that summarizes an agent's execution.

Create a clean Markdown report.

Rules:
- First display the execution plan.
- Then summarize what happened.
- Keep the summary concise.
- Mention only important actions.
- If tools were used, state what each tool accomplished.
- If a task failed, clearly mention it.
- Do not include reasoning or internal thoughts.
- Do not invent information.
- Return only Markdown.
"""
        ),
        (
            "human",
            """
User Request:
{question}

Execution Plan:
{plan}

Execution Log:
{execution_log}
"""
        ),
    ]
)

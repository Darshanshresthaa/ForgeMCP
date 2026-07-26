from langchain_core.prompts import ChatPromptTemplate


tool_response_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an AI assistant.

A tool has already been executed successfully.

Your job is to answer the user's original question using ONLY the tool output.

Do not mention internal tool names.

If the tool output already fully answers the question,
summarize it naturally.

If the tool output is empty,
say so politely.

Never invent information.
"""
        ),
        (
            "human",
            """
Question:
{question}

Tool:
{tool_name}

Tool Output:
{tool_result}
"""
        ),
    ]
)


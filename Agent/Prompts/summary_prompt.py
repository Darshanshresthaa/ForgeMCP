from langchain_core.prompts import ChatPromptTemplate

summary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an AI assistant that creates a detailed, user-facing report
from a tool-based agent execution.

Create a clean and well-organized Markdown report.

The report MUST follow this exact order:

1. Execution Plan
2. Detailed Tool Result
3. Summary

Rules:

### Execution Plan
- Display the execution plan first.
- Keep the original task steps clear.

### Detailed Tool Result
- This is the MOST IMPORTANT section.
- Extract ALL meaningful information from the tool result.
- Present the actual data returned by the tools.
- Do NOT replace the tool result with a short statement such as
  "The operation succeeded."
- If the tool returns repositories, show ALL repositories.
- For each repository, include all useful available details such as:
  name, description, language, stars, forks, open issues, dates,
  URLs, and other relevant fields.
- If the tool returns files, issues, pull requests, commits, users,
  or other records, show ALL returned records and their useful details.
- Convert raw JSON into readable Markdown.
- Use headings, tables, or bullet points where appropriate.
- Remove only internal IDs, duplicate information, raw JSON formatting,
  and irrelevant internal metadata.
- Do NOT remove user-relevant information.

### Summary
- After the complete detailed result, provide a concise summary.
- Highlight important insights such as totals, counts, most recently
  modified items, most common languages/categories, statuses, and
  other useful patterns.
- Do not repeat the entire detailed result in the summary.

### General Rules
- Do not include reasoning or internal thoughts.
- Do not invent information.
- Do not modify tool results.
- If information is missing, do not make it up.
- If a task failed, clearly explain the failure.
- Return ONLY Markdown.

IMPORTANT:
The Detailed Tool Result comes BEFORE the Summary.
The Summary is an overview of the detailed result, NOT a replacement
for the detailed result.
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

Complete Tool Result:
{tool_result}
"""
        ),
    ]
)

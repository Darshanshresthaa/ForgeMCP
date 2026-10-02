from MCP.github_client import github_get
from MCP.server import mcp


@mcp.tool
def search_code(
    query: str,
    repo: str | None = None,
    language: str | None = None,
    limit: int = 10,
):
    """Search code on GitHub by keyword. Optional repo ('owner/name') and language filters. Requires GITHUB_TOKEN."""

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    q = query

    if repo:
        q += f" repo:{repo}"

    if language:
        q += f" language:{language}"

    try:
        result = github_get(
            "/search/code",
            params={"q": q, "per_page": limit},
        )

        return {
            "total_count": result["total_count"],
            "results": [
                {
                    "file": item["name"],
                    "path": item["path"],
                    "repository": item["repository"]["full_name"],
                    "url": item["html_url"],
                }
                for item in result["items"]
            ],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to search code for '{query}': {e}") from e

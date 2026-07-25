from MCP.github_client import github_get
from MCP.server import mcp


@mcp.tool
def search_repos(
    query: str,
    limit: int = 10,
):
    """Search GitHub repos globally by keyword/name. Use list_repositories to browse a known user's repos instead."""

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not (1 <= limit <= 100):
        raise ValueError("limit must be between 1 and 100.")

    try:
        repos = github_get(
            "/search/repositories",
            params={
                "q": query,
                "per_page": limit,
            },
        )

        return repos["items"]

    except Exception as e:
        raise RuntimeError(
            f"Failed to search repositories for '{query}': {e}"
        ) from e
from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

from MCP.helper import get_authenticated_username


@mcp.tool
def list_tags(
    username: str,
    repo_name: str,
    limit: int = 10,
    page: int = 1
    ):

    """List all Tags repository tags."""

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    if not username:
        username = get_authenticated_username()
    try:
        return github_get(
            f"/repos/{username}/{repo_name}/tags",
            params={
                "per_page": limit,
                "page": page,
            },
        )
    except Exception as e:
        raise RuntimeError(f"Failed to list tags: {e}")
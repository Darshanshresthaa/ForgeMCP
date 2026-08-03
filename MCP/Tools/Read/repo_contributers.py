from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

from MCP.helper import get_authenticated_username


@mcp.tool
def repo_contributors( 
    repo_name: str,
    limit: int = 10,
    username: str | None = None
    ):

    """List repository contributors."""

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    if  username is None:
        username = get_authenticated_username()

    try:
        contributors = github_get(
            f"/repos/{username}/{repo_name}/contributors",
            params={"per_page": limit},
        )

        return [
            {
                "username": contributor["login"],
                "contributions": contributor["contributions"],
                "profile": contributor["html_url"],
            }
            for contributor in contributors
        ]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch contributors: {e}")
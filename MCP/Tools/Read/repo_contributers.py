from fastmcp import FastMCP
from MCP.github_client import github_get


mcp = FastMCP("ForgeMCP")


@mcp.tool
def repo_contributors(username: str, repo_name: str, limit: int = 10):
    """List repository contributors."""

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

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
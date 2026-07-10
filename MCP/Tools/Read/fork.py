
from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

@mcp.tool
def list_forks(username: str,repo_name: str,limit: int = 10,page: int = 1):
    """List repository forks os check is repo orginal or copy."""

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    try:
        forks = github_get(
            f"/repos/{username}/{repo_name}/forks",
            params={
                "per_page": limit,
                "page": page,
            },
        )

        return [
            {
                "source_repo": f"{username}/{repo_name}",
                "fork_owner": fork["owner"]["login"],
                "fork_repo": fork["full_name"],
                "url": fork["html_url"],
                "stars": fork.get("stargazers_count", 0),
                "updated": fork["updated_at"],
            }
            for fork in forks
        ]

    except Exception as ex:
        raise RuntimeError(f"Failed to list forks: {ex}")
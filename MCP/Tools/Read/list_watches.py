from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

from helper import get_authenticated_username

@mcp.tool
def list_watchers( 
    username: str,
    repo_name: str,
    limit: int = 10
    ):
    
    """List users watching/subscribed to a repository."""


    if not username:
        username = get_authenticated_username()

    try:
        watchers = github_get(
            f"/repos/{username}/{repo_name}/subscribers",
            params={"per_page": limit},
        )

        return [
            {
                "username": watcher["login"],
                "profile_url": watcher["html_url"],
            }
            for watcher in watchers
        ]

    except Exception as ex:
        raise RuntimeError(f"Failed to list watchers: {ex}")
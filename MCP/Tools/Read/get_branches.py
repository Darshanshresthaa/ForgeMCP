from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp


@mcp.tool
def get_branches(username: str, repo_name: str):
    """List repository branches."""

    try:
        branches = github_get(f"/repos/{username}/{repo_name}/branches")

        return [
            {
                "branch_name": branch["name"],
                "is_protected": branch["protected"],
            }
            for branch in branches
        ]

    except Exception as ex:
        raise RuntimeError(f"Failed to get branches: {ex}")
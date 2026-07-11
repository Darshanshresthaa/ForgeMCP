from fastmcp import FastMCP
from MCP.github_client import git_delete

from MCP.server import mcp


@mcp.tool
def delete_repository(
    username: str,
    repo_name: str,
    confirm: bool = False,
):
    """Delete a GitHub repository."""

    if not confirm:
        raise ValueError(
            "Set confirm=True to permanently delete the repository."
        )

    try:
        git_delete(
            f"/repos/{username}/{repo_name}"
        )

        return {
            "status": "success",
            "repository": f"{username}/{repo_name}",
        }

    except Exception as e:
        raise RuntimeError(f"Failed to delete repository '{username}/{repo_name}': {e}") from e
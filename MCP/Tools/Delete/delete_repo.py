from fastmcp import FastMCP
from MCP.github_client import git_delete

from MCP.server import mcp
from MCP.helper import get_authenticated_username


@mcp.tool
def delete_repository(
    # username: str,
    repo_name: str,
    confirm: bool = False,
    username: str | None = None,
):
    """Delete a GitHub repository."""


    if not confirm:
        raise ValueError(
            "Set confirm=True to permanently delete the repository."
        )

    if  username is None:
        username = get_authenticated_username()

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
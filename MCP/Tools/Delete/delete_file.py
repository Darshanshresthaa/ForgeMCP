from fastmcp import FastMCP
from MCP.github_client import github_get,git_delete

from MCP.server import mcp
from helper import get_authenticated_username



@mcp.tool
def delete_file(
    username: str,
    repo_name: str,
    path: str,
    message: str,
    branch: str = "main",
    confirm: bool = False,
):
    """Permanently delete one file from a repo. Requires confirm=True. Destructive."""

    if not confirm:
        raise ValueError(
            "Set confirm=True to permanently delete the file."
        )

    if not username:
        username = get_authenticated_username()
        

    try:

        file = github_get(
            f"/repos/{username}/{repo_name}/contents/{path}",
            params={"ref": branch},
        )

        payload = {
            "message": message,
            "sha": file["sha"],
            "branch": branch,
        }

        git_delete(
            f"/repos/{username}/{repo_name}/contents/{path}",
            json=payload,
        )

        return {
            "status": "success",
            "file": path,
            "branch": branch,
        }

    except Exception as e:
        raise RuntimeError(f"Failed to delete file '{path}': {e}") from e
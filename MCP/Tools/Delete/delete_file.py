from fastmcp import FastMCP
from MCP.github_client import github_get,git_delete


mcp = FastMCP("ForgeMCP")

@mcp.tool
def delete_file(
    username: str,
    repo_name: str,
    path: str,
    message: str,
    branch: str = "main",
    confirm: bool = False,
):
    """Delete a file from a GitHub repository."""

    if not confirm:
        raise ValueError(
            "Set confirm=True to permanently delete the file."
        )

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
        return {
            "status": "error",
            "message": str(e),
        }
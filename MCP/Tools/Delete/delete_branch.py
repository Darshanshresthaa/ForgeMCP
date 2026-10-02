from MCP.github_client import github_get, git_delete
from MCP.server import mcp
from MCP.helper import get_authenticated_username


@mcp.tool
def delete_branch(
    repo_name: str,
    branch_name: str,
    confirm: bool = False,
    username: str | None = None,
):
    """Delete a branch from a GitHub repository. The default branch cannot be deleted."""

    if not confirm:
        raise ValueError("Set confirm=True to permanently delete the branch.")

    if username is None:
        username = get_authenticated_username()

    try:
        repo = github_get(f"/repos/{username}/{repo_name}")

        if branch_name == repo["default_branch"]:
            raise ValueError(
                f"'{branch_name}' is the default branch and cannot be deleted."
            )

        git_delete(f"/repos/{username}/{repo_name}/git/refs/heads/{branch_name}")

        return {
            "status": "success",
            "repository": f"{username}/{repo_name}",
            "deleted_branch": branch_name,
        }

    except Exception as e:
        raise RuntimeError(f"Failed to delete branch '{branch_name}': {e}") from e
